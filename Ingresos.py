# -*- coding: utf-8 -*-
"""
Sistema de Ingresos - Contabilidad
Interfaz moderna con ttkbootstrap.
Registros por año (un archivo JSON por año).
"""

import os
import sys
import re
import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
import shutil
from tkinter import messagebox, filedialog

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from lector_facturas import procesar_factura, agrupar_por_categoria


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

BASE_DIR = Path.home() / "Documents"


def _carpeta_datos():
    """
    Carpeta única de datos de la app.
    Compartida entre años.
    """
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Contabilidad App"
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    else:
        return Path(__file__).parent


_CARPETA_DATOS = _carpeta_datos()

# Archivos compartidos entre años
HISTORIAL_FILE = _CARPETA_DATOS / "historial_autocompletado.json"
CONFIG_FILE = _CARPETA_DATOS / "config_ui.json"


def _ruta_registros(anio):
    """Devuelve la ruta al archivo de registros del año indicado."""
    return _CARPETA_DATOS / f"registros_ingresos_{anio}.json"


def cargar_db(anio):
    """Carga los registros del año indicado."""
    ruta = _ruta_registros(anio)
    if ruta.exists():
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def guardar_db(regs, anio):
    """Guarda los registros en el archivo del año indicado."""
    ruta = _ruta_registros(anio)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(regs, f, ensure_ascii=False, indent=2)


# ============================================================
# CONFIGURACIÓN DE TEMA
# ============================================================
CONFIG_DEFAULT = {"tema": "darkly"}


def cargar_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in CONFIG_DEFAULT.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(CONFIG_DEFAULT)


def guardar_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


CONFIG = cargar_config()
TEMA = CONFIG.get("tema", CONFIG_DEFAULT["tema"])

TEMAS_OSCUROS = {
  "bootstrap-dark",
  "pydata-dark",
  "nord-dark",
  "solarized-dark",
  "catppuccin-dark",
  "gruvbox-dark",
  "dracula-dark",
  "tokyo-night-dark",
  "one-dark"
  "everforest-dark",
  "vapor-dark",
  "minty-dark",
  "pulse-dark",
  "united-dark",
  "sandstone-dark"}


def tema_es_oscuro(tema=None):
    t = tema or TEMA
    return t.lower() in TEMAS_OSCUROS


def _colores_adaptados():
    oscuro = tema_es_oscuro()
    if oscuro:
        return {
            "texto_normal": "#ffffff",
            "texto_operacion": "#00ff00",
            "fondo_entry": "#2b2b2b",
            "campo_ok": "#1b5e20",
            "campo_error": "#7f1d1d",
            "campo_normal": "#2b2b2b",
        }
    else:
        return {
            "texto_normal": "#000000",
            "texto_operacion": "#007700",
            "fondo_entry": "#ffffff",
            "campo_ok": "#c8e6c9",
            "campo_error": "#ffcdd2",
            "campo_normal": "#ffffff",
        }


COLORES = _colores_adaptados()


def refrescar_colores():
    global COLORES
    COLORES = _colores_adaptados()


# ============================================================
# DEFINICIÓN DE CAMPOS
# ============================================================
CAMPOS = [
    # GENERAL
    ("no_factura",       "No. DE FACTURA",           "GENERAL",        "text"),
    ("qvet",             "QVET",                     "GENERAL",        "text"),
    ("fecha",            "FECHA DE EMISIÓN",         "GENERAL",        "date"),
    ("nombre",           "NOMBRE",                   "GENERAL",        "text"),
    ("rfc",              "RFC",                      "GENERAL",        "text"),
    ("fecha_impresion",  "FECHA DE TIMBRADO",        "GENERAL",        "date"),
    ("folio_fiscal",     "FOLIO FISCAL",             "GENERAL",        "text"),
    # U
    ("u_importe",        "IMPORTE",                  "U",              "number"),
    ("u_iva",            "IVA (16%)",                "U",              "number"),
    # ACCESORIOS
    ("ac_importe",       "IMPORTE",                  "ACCESORIOS",     "number"),
    ("ac_iva",           "IVA (16%)",                "ACCESORIOS",     "number"),
    # MEDICAMENTOS
    ("med_importe",      "IMPORTE (sin IVA)",        "MEDICAMENTOS",   "number"),
    ("med_sin_iva",      "SIN IVA",                  "MEDICAMENTOS",   "number"),
    ("med_iva",          "IVA (16%)",                "MEDICAMENTOS",   "number"),
    # HIGIENE
    ("hig_importe",      "IMPORTE (sin IVA)",        "HIGIENE",        "number"),
    ("hig_sin_iva",      "SIN IVA",                  "HIGIENE",        "number"),
    ("hig_iva",          "IVA 16%",                  "HIGIENE",        "number"),
    ("hig_sin_ieps_6",   "SIN IEPS 6%",              "HIGIENE",        "number"),
    ("hig_ieps_6",       "IEPS 6%",                  "HIGIENE",        "number"),
    ("hig_sin_ieps_7",   "SIN IEPS 7%",              "HIGIENE",        "number"),
    ("hig_ieps_7",       "IEPS 7%",                  "HIGIENE",        "number"),
    # ESTETICA
    ("est_importe",      "IMPORTE",                  "ESTETICA",       "number"),
    ("est_iva",          "IVA (16%)",                "ESTETICA",       "number"),
    # TRANSPORTE
    ("tra_importe",      "IMPORTE",                  "TRANSPORTE",     "number"),
    ("tra_iva",          "IVA (16%)",                "TRANSPORTE",     "number"),
    # PENSION
    ("pen_importe",      "IMPORTE",                  "PENSION",        "number"),
    ("pen_iva",          "IVA (16%)",                "PENSION",        "number"),
    # VACUNA
    ("vac_importe",      "IMPORTE",                  "VACUNA",         "number"),
    # CLINICA
    ("cli_importe",      "IMPORTE",                  "CLINICA",        "number"),
    # TOTAL
    ("total",            "TOTAL (auto)",             "TOTAL",          "number"),
    # TIPO DE PAGO
    ("efectivo",         "EFECTIVO",                 "TIPO DE PAGO",   "number"),
    ("tc",               "TARJETA CRÉDITO",          "TIPO DE PAGO",   "number"),
    ("td",               "TARJETA DÉBITO",           "TIPO DE PAGO",   "number"),
    ("cheque",           "CHEQUE",                   "TIPO DE PAGO",   "number"),
    ("transfer",         "TRANSFERENCIA",            "TIPO DE PAGO",   "number"),
    ("vale",             "VALE",                     "TIPO DE PAGO",   "number"),
]

CAMPOS_DICT = {c[0]: c for c in CAMPOS}

REGLAS_AUTO = {
    "med_iva": ("med_sin_iva", 0.16),
    "hig_iva": ("hig_sin_iva", 0.16),
    "hig_ieps_6": ("hig_sin_ieps_6", 0.06),
    "hig_ieps_7": ("hig_sin_ieps_7", 0.07),
    "u_iva": ("u_importe", 0.16),
    "ac_iva": ("ac_importe", 0.16),
    "est_iva": ("est_importe", 0.16),
    "tra_iva": ("tra_importe", 0.16),
    "pen_iva": ("pen_importe", 0.16),
}

CATEGORIAS_PARA_TOTAL = [
    "u_importe", "ac_importe", "med_importe", "hig_importe",
    "est_importe", "tra_importe", "pen_importe", "vac_importe", "cli_importe",
    "med_sin_iva", "hig_sin_iva",
    "hig_sin_ieps_6", "hig_sin_ieps_7",
    "u_iva", "ac_iva", "med_iva", "hig_iva", "hig_ieps_6", "hig_ieps_7",
    "est_iva", "tra_iva", "pen_iva",
]

CAMPOS_TIPO_PAGO = ["efectivo", "tc", "td", "cheque", "transfer", "vale"]

# ============================================================
# MAPEO DE SERIES A CENTROS
# ============================================================
# Cada serie del XML corresponde a un centro específico.
# Ajusta este diccionario si agregas más series o centros.
def centro_desde_serie(serie):
    """
    Devuelve el nombre del centro según la serie del XML.
    Acepta variantes como 'S1', 'S1/', 's1', 'S-1'.
    """
    if not serie:
        return None
    # Limpiar: quitar '/', espacios, guiones, y pasar a mayúsculas
    s = str(serie).strip().upper()
    s = s.replace("/", "").replace("-", "").replace(" ", "")
    # Mapear con las variantes limpias
    mapeo = {
        "S1": "Central",
        "PRADOS": "Prado",
        "PRADO": "Prado",
    }
    return mapeo.get(s)


# ============================================================
# RUTAS DE CARPETAS DE FACTURAS
# ============================================================
def ruta_ingreso(centro, anio=None, mes=None):
    hoy = datetime.now()
    anio = anio or hoy.year
    mes = mes or hoy.month
    return (BASE_DIR / f"Contabilidad {anio}" /
            f"Contabilidad {MESES_ES[mes-1]}" /
            "Ingreso" / f"Facturas {centro.capitalize()}")


def ruta_deposito(anio=None, mes=None):
    hoy = datetime.now()
    anio = anio or hoy.year
    mes = mes or hoy.month
    return (BASE_DIR / f"Contabilidad {anio}" /
            f"Contabilidad {MESES_ES[mes-1]}" /
            "Ingreso" / "Deposito")


def parse_fecha(txt):
    if not txt:
        return datetime.now().strftime("%d-%m-%Y")
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(txt.strip(), fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return txt.replace("/", "-")


def mes_anio_desde_fecha(fecha_str):
    """
    A partir de una fecha en formato 'dd/mm/aaaa' devuelve (mes_nombre, anio).
    Devuelve (None, None) si no se puede parsear.
    """
    if not fecha_str:
        return None, None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            dt = datetime.strptime(str(fecha_str).strip(), fmt)
            return MESES_ES[dt.month - 1], dt.year
        except ValueError:
            continue
    return None, None

# ============================================================
# HISTORIAL Y VALIDACIONES
# ============================================================
def cargar_historial():
    if HISTORIAL_FILE.exists():
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"nombre": [], "rfc": []}


def guardar_historial(hist):
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


def actualizar_historial(regs):
    hist = cargar_historial()
    nombres = set(hist.get("nombre", []))
    rfcs = set(hist.get("rfc", []))
    for r in regs:
        n = str(r.get("nombre", "")).strip()
        c = str(r.get("rfc", "")).strip()
        if n:
            nombres.add(n)
        if c:
            rfcs.add(c)
    hist["nombre"] = sorted(nombres)
    hist["rfc"] = sorted(rfcs)
    guardar_historial(hist)
    return hist


def existe_valor_unico(registros, clave, valor, ignorar_id=None):
    v = str(valor).strip().lower()
    if not v:
        return False
    for r in registros:
        if ignorar_id is not None and r.get("id") == ignorar_id:
            continue
        if str(r.get(clave, "")).strip().lower() == v:
            return True
    return False


def obtener_no_factura_numerico(no_factura):
    s = str(no_factura).strip()
    digitos = "".join(c for c in s if c.isdigit())
    if not digitos:
        return None
    try:
        return int(digitos)
    except ValueError:
        return None


def obtener_consecutivo_esperado(registros, centro=None, anio=None, mes=None,
        ignorar_id=None):
    numeros = []
    for r in registros:
        if ignorar_id is not None and r.get("id") == ignorar_id:
            continue
        if centro and r.get("centro") != centro:
            continue
        if anio and r.get("anio") != anio:
            continue
        if mes and r.get("mes") != mes:
            continue
        n = obtener_no_factura_numerico(r.get("no_factura", ""))
        if n is not None:
            numeros.append(n)
    if not numeros:
        return None
    return max(numeros) + 1


# ============================================================
# GESTIÓN DE ARCHIVOS ADJUNTOS
# ============================================================
def carpeta_de_registro(reg):
    try:
        centro = reg.get("centro", "Central")
        anio = int(reg.get("anio", datetime.now().year))
        mes_nombre = reg.get("mes", MESES_ES[datetime.now().month - 1])
        mes_idx = MESES_ES.index(mes_nombre) + 1
        fecha_carpeta = parse_fecha(reg.get("fecha", ""))
        return ruta_ingreso(centro, anio, mes_idx) / fecha_carpeta
    except Exception:
        return None


def archivos_del_registro(reg):
    carpeta = carpeta_de_registro(reg)
    if not carpeta or not carpeta.exists():
        return []
    no_factura = str(reg.get("no_factura", "")).strip()
    if not no_factura:
        return []
    prefijo = no_factura.lower()
    encontrados = []
    for archivo in carpeta.iterdir():
        if not archivo.is_file():
            continue
        nombre = archivo.name.lower()
        if not nombre.startswith(prefijo):
            continue
        resto = nombre[len(prefijo):]
        if resto == "" or resto[0] in (".", "-", "_", " "):
            encontrados.append(archivo)
    return encontrados


def eliminar_archivos_de_registro(reg):
    eliminados, errores = [], []
    for archivo in archivos_del_registro(reg):
        try:
            archivo.unlink()
            eliminados.append(archivo)
        except Exception as e:
            errores.append((archivo, str(e)))
    return eliminados, errores


def eliminar_carpeta_si_vacia(reg):
    carpeta = carpeta_de_registro(reg)
    if not carpeta:
        return False, "No se pudo determinar la carpeta."
    if not carpeta.exists():
        return False, "La carpeta ya no existe."
    try:
        contenido = list(carpeta.iterdir())
    except Exception as e:
        return False, f"No se pudo leer la carpeta: {e}"
    if contenido:
        return False, f"La carpeta aún contiene {len(contenido)} archivo(s)/carpeta(s)."
    try:
        carpeta.rmdir()
        return True, str(carpeta)
    except Exception as e:
        return False, f"No se pudo eliminar la carpeta: {e}"


def carpeta_destino_factura(reg):
    carpeta = carpeta_de_registro(reg)
    if carpeta:
        carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def nombre_destino(no_factura, ruta_origen):
    ext = Path(ruta_origen).suffix
    return f"{no_factura}{ext}"


def adjuntar_archivos(reg, rutas_origen):
    carpeta = carpeta_destino_factura(reg)
    if not carpeta:
        return [], [(None, "No se pudo determinar la carpeta destino.")]
    no_factura = str(reg.get("no_factura", "")).strip()
    copiados, errores = [], []
    for origen in rutas_origen:
        try:
            origen = Path(origen)
            if not origen.is_file():
                errores.append((origen, "No es un archivo válido."))
                continue
            destino = carpeta / nombre_destino(no_factura, origen)
            shutil.copy2(origen, destino)
            copiados.append((origen, destino))
        except Exception as e:
            errores.append((origen, str(e)))
    return copiados, errores


# ============================================================
# UTILIDADES DE MONEDA Y EXPRESIONES
# ============================================================
def formatear_moneda(valor):
    try:
        return f"{float(valor):,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def limpiar_moneda(texto):
    if not texto:
        return 0.0
    texto = str(texto).replace("$", "").replace(",", "").replace(" ", "").strip()
    try:
        return float(texto)
    except ValueError:
        return 0.0


def tokenizar(texto):
    tokens = []
    num = ""
    for c in texto:
        if c in "+*/()":
            if num:
                tokens.append(num)
                num = ""
            tokens.append(c)
        elif c == "-":
            if not tokens or tokens[-1] in ("+", "-", "*", "/", "("):
                num += c
            else:
                if num:
                    tokens.append(num)
                    num = ""
                tokens.append(c)
        elif c == " ":
            if num:
                tokens.append(num)
                num = ""
        else:
            num += c
    if num:
        tokens.append(num)
    return tokens


def evaluar_expresion(texto):
    if texto is None:
        return 0.0
    texto = str(texto).strip()
    if not texto:
        return 0.0
    texto = texto.replace("$", "").replace(",", "").strip()
    if not any(op in texto for op in "+*/()"):
        if texto.count("-") == 0 or (texto.count("-") == 1 and texto.startswith("-")):
            return limpiar_moneda(texto)
    permitidos = set("0123456789.+-*/() ")
    if not all(c in permitidos for c in texto):
        return 0.0
    try:
        tokens = tokenizar(texto)
        if not tokens:
            return 0.0
        pos = [0]

        def parse_expresion():
            valor = parse_termino()
            while pos[0] < len(tokens) and tokens[pos[0]] in ("+", "-"):
                op = tokens[pos[0]]
                pos[0] += 1
                der = parse_termino()
                valor = valor + der if op == "+" else valor - der
            return valor

        def parse_termino():
            valor = parse_factor()
            while pos[0] < len(tokens) and tokens[pos[0]] in ("*", "/"):
                op = tokens[pos[0]]
                pos[0] += 1
                der = parse_factor()
                if op == "*":
                    valor *= der
                else:
                    if der == 0:
                        raise ZeroDivisionError()
                    valor /= der
            return valor

        def parse_factor():
            if pos[0] >= len(tokens):
                raise ValueError("Expresión incompleta")
            tok = tokens[pos[0]]
            if tok == "(":
                pos[0] += 1
                valor = parse_expresion()
                if pos[0] >= len(tokens) or tokens[pos[0]] != ")":
                    raise ValueError("Falta paréntesis")
                pos[0] += 1
                return valor
            elif tok == "-":
                pos[0] += 1
                return -parse_factor()
            else:
                pos[0] += 1
                return float(tok)

        resultado = parse_expresion()
        if pos[0] != len(tokens):
            raise ValueError("Sobran tokens")
        return round(resultado, 2)
    except Exception:
        return 0.0


def agrupar_facturas_descargadas(carpeta, archivos_por_correo=None):
    """
    Agrupa los archivos descargados.
    
    Estrategia:
      1. Si se pasa `archivos_por_correo` ({message_id: [paths]}), 
         agrupa por correo (XML y PDF vienen juntos).
      2. Si no, usa el método anterior (agrupar por folio del nombre).
    
    Devuelve:
      {
        "grupo_1": {
            "xml": Path,
            "pdf": Path,
            "no_factura": "196",
            "serie": "Prados",
            "uuid": "..."
        },
        ...
      }
    """
    import xml.etree.ElementTree as ET
    from collections import defaultdict

    grupos = {}
    contador = 0

    # ---- Método 1: agrupar por correo ----
    if archivos_por_correo:
        for _, archivos in archivos_por_correo.items():
            xml_path = None
            pdf_path = None

            for ruta_str in archivos:
                ruta = Path(ruta_str)
                if not ruta.exists():
                    continue
                ext = ruta.suffix.lower()
                if ext == ".xml" and xml_path is None:
                    xml_path = ruta
                elif ext == ".pdf" and pdf_path is None:
                    pdf_path = ruta

            if not xml_path:
                continue  # sin XML, no se puede procesar

            # Leer folio y serie del XML
            try:
                NS = {"cfdi": "http://www.sat.gob.mx/cfd/4"}
                tree = ET.parse(str(xml_path))
                root = tree.getroot()
                folio = (root.get("Folio") or "").strip()
                serie = (root.get("Serie") or "").strip()
                if folio.isdigit():
                    folio = str(int(folio))
                uuid = ""
                for elem in root.iter():
                    if elem.tag.endswith("TimbreFiscalDigital"):
                        uuid = elem.get("UUID", "")
                        break
            except Exception:
                continue

            contador += 1
            grupos[contador] = {
                "xml": xml_path,
                "pdf": pdf_path,
                "no_factura": folio,
                "serie": serie,
                "uuid": uuid,
            }

        return grupos

    # ---- Método 2 (fallback): agrupar por folio del nombre ----
    for archivo in sorted(carpeta.glob("*.xml")):
        try:
            NS = {"cfdi": "http://www.sat.gob.mx/cfd/4"}
            tree = ET.parse(str(archivo))
            root = tree.getroot()
            folio = (root.get("Folio") or "").strip()
            serie = (root.get("Serie") or "").strip()
            if folio.isdigit():
                folio = str(int(folio))
            if not folio:
                continue
            uuid = ""
            for elem in root.iter():
                if elem.tag.endswith("TimbreFiscalDigital"):
                    uuid = elem.get("UUID", "")
                    break
            contador += 1
            grupos[f"grupo_{contador}"] = {
                "xml": archivo,
                "pdf": None,
                "no_factura": folio,
                "serie": serie,
                "uuid": uuid,
            }
        except Exception:
            continue

    # Asociar PDFs por nombre (fallback antiguo)
    for archivo in sorted(carpeta.glob("*.pdf")):
        nombre = archivo.stem
        no_factura = None
        partes = nombre.split("_")
        if partes and partes[-1].isdigit():
            no_factura = str(int(partes[-1]))
        if not no_factura:
            m = re.search(r"_(\d+)$", nombre)
            if m:
                no_factura = str(int(m.group(1)))
        if not no_factura:
            digitos = re.findall(r"\d+", nombre)
            if digitos:
                no_factura = str(int(max(digitos, key=len)))
        if not no_factura:
            continue
        for clave, grp in grupos.items():
            if grp.get("no_factura") == no_factura and grp.get("pdf") is None:
                grp["pdf"] = archivo
                break

    return grupos


def obtener_colores_sidebar():
    """
    Devuelve un diccionario con los colores del sidebar según el tema actual.
    Si el tema es oscuro → colores oscuros.
    Si el tema es claro → colores claros.
    """
    oscuro = tema_es_oscuro()
    if oscuro:
        return {
            "bg":       "#1e2a38",   # azul oscuro profundo
            "hover":    "#2c3e50",   # hover más claro
            "active":   "#3498db",   # activo (azul brillante)
            "fg":       "#ffffff",   # texto principal
            "fg_suave": "#cfd8dc",   # texto secundario
            "separador": "#34495e",  # línea separadora
            "version":  "#607d8b",   # texto versión
        }
    else:
        return {
            "bg":       "#ffffff",   # blanco
            "hover":    "#e3f2fd",   # azul muy claro al hover
            "active":   "#1976d2",   # azul medio
            "fg":       "#000000",   # texto negro
            "fg_suave": "#546e7a",   # texto gris
            "separador": "#e0e0e0",  # gris claro
            "version":  "#90a4ae",   # gris
        }
# ============================================================
# WIDGETS PERSONALIZADOS
# ============================================================
class EntryMoneda(ttk.Entry):
    """Entry con formato moneda, evaluación de expresiones y colores."""

    def __init__(self, master=None, callback=None, **kw):
        super().__init__(master, justify="right", **kw)
        self.callback = callback
        self._ultimo_valor = 0.0
        self._ultima_expresion = ""
        self.insert(0, "0.00")
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyRelease>", self._on_key_release)
        self._pintar()

    def _tiene_operacion(self, texto):
        if any(op in texto for op in "+*/()"):
            return True
        if texto.count("-") > 0 and not texto.strip().startswith("-"):
            return True
        if texto.strip().startswith("-") and texto.count("-") > 1:
            return True
        return False

    def _on_key_release(self, e):
        self._pintar()

    def _pintar(self):
        texto = self.get()
        try:
            color_fg = COLORES["texto_operacion"] if self._tiene_operacion(texto) else COLORES["texto_normal"]
            self.configure(foreground=color_fg)
            try:
                self.configure(background=COLORES["fondo_entry"])
            except Exception:
                pass
        except Exception:
            pass

    def _on_focus_in(self, e):
        self.delete(0, tk.END)
        if self._ultima_expresion:
            self.insert(0, self._ultima_expresion)
        elif self._ultimo_valor:
            self.insert(0, f"{self._ultimo_valor:.2f}")
        self._pintar()

    def _on_focus_out(self, e):
        texto = self.get().strip()
        if self._tiene_operacion(texto):
            self._ultima_expresion = texto.replace(",", "").replace("$", "").strip()
            self._ultimo_valor = evaluar_expresion(texto)
        else:
            try:
                valor_actual = limpiar_moneda(texto)
            except Exception:
                valor_actual = None
            if (valor_actual is not None
                    and abs(valor_actual - self._ultimo_valor) < 0.01
                    and self._ultima_expresion):
                pass
            else:
                self._ultima_expresion = ""
                self._ultimo_valor = limpiar_moneda(texto)
        self.delete(0, tk.END)
        self.insert(0, formatear_moneda(self._ultimo_valor))
        self._pintar()
        if self.callback:
            self.callback()

    def get_valor(self):
        texto = self.get().strip()
        if self._tiene_operacion(texto):
            return evaluar_expresion(texto)
        return limpiar_moneda(texto)

    def set_valor(self, v, expresion=None):
        self._ultimo_valor = float(v or 0)
        self._ultima_expresion = expresion or ""
        self.delete(0, tk.END)
        self.insert(0, formatear_moneda(self._ultimo_valor))
        self._pintar()


class EntryAutoComplete(ttk.Entry):
    """Entry con autocompletado optimizado con debounce."""

    def __init__(self, master=None, opciones=None, **kw):
        super().__init__(master, **kw)
        self.opciones = opciones or []
        self._lista = None
        self._listbox = None
        self._after_id = None
        self._ultimo_filtro = ""
        self._teclas_ignoradas = {
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "Meta_L", "Meta_R",
            "Caps_Lock", "Num_Lock", "Scroll_Lock",
            "Left", "Right", "Up", "Down", "Home", "End",
            "Page_Up", "Page_Down", "Escape", "Tab",
            "Return", "KP_Enter", "BackSpace", "Delete",
        }
        self.bind("<KeyRelease>", self._on_key)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Escape>", lambda e: self._cerrar_lista())

    def set_opciones(self, ops):
        self.opciones = ops or []

    def _on_key(self, e):
        if e.keysym in self._teclas_ignoradas:
            return
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(150, self._buscar)

    def _on_focus_out(self, e):
        self.after(120, self._cerrar_lista)

    def _buscar(self):
        self._after_id = None
        txt = self.get().strip().lower()
        if not txt:
            self._cerrar_lista()
            return
        if txt == self._ultimo_filtro and self._lista is not None:
            return
        self._ultimo_filtro = txt
        coincidencias = [o for o in self.opciones if txt in o.lower()][:8]
        if not coincidencias:
            self._cerrar_lista()
            return
        self._mostrar_lista(coincidencias)

    def _mostrar_lista(self, items):
        if self._lista is None or not self._lista.winfo_exists():
            self._crear_lista()
        self._listbox.delete(0, tk.END)
        for it in items:
            self._listbox.insert(tk.END, it)
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = max(self.winfo_width(), 200)
        h = min(len(items) * 22 + 4, 180)
        try:
            self._lista.wm_geometry(f"{w}x{h}+{x}+{y}")
            self._lista.deiconify()
            self._lista.lift()
        except Exception:
            pass

    def _crear_lista(self):
        self._lista = ttk.Toplevel(self)
        self._lista.wm_overrideredirect(True)
        try:
            self._lista.attributes("-topmost", True)
        except Exception:
            pass
        frame = ttk.Frame(self._lista, borderwidth=1, relief="solid")
        frame.pack(fill="both", expand=True)
        self._listbox = tk.Listbox(
            frame, font=("Segoe UI", 9), activestyle="none",
            highlightthickness=0, borderwidth=0,
        )
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._seleccionar)
        self._listbox.bind("<Double-Button-1>", self._seleccionar)
        self._listbox.bind("<Return>", self._seleccionar)
        self._listbox.bind("<Escape>", lambda e: self._cerrar_lista())

    def _seleccionar(self, e=None):
        if not self._listbox:
            return
        sel = self._listbox.curselection()
        if sel:
            valor = self._listbox.get(sel[0])
            self.delete(0, tk.END)
            self.insert(0, valor)
            self.icursor(tk.END)
        self._cerrar_lista()
        self.focus_set()

    def _cerrar_lista(self):
        if self._lista is not None and self._lista.winfo_exists():
            try:
                self._lista.withdraw()
            except Exception:
                pass
        self._ultimo_filtro = ""


# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
class AppIngresos(ttk.Window):
    def __init__(self):
        super().__init__(themename=TEMA)
        self.title("Sistema de Ingresos - Contabilidad")
        self.geometry("1250x880")
        self.minsize(1000, 700)

        # Año del archivo de registros cargado actualmente
        try:
            self._anio_cargado = int(datetime.now().year)
        except Exception:
            self._anio_cargado = datetime.now().year

        self.registros = cargar_db(self._anio_cargado)
        self.id_actual = None
        self.entradas = {}
        self.widgets_ordenados = []
        self.historial = actualizar_historial(self.registros)
        self._configurar_estilos()
        self._construir_ui()
        self._refrescar_tabla()
        self._recalcular_total()
        self._actualizar_titulo()
        self._ultima_factura_xml = None
        self._ultima_factura_pdf = None

    # ------------------------------------------------------------
    def _construir_ui(self):
        # ============================================================
        # BARRA LATERAL (colores según tema)
        # ============================================================
        self.colores_sidebar = obtener_colores_sidebar()

        # Estado del sidebar: True = expandido, False = colapsado
        self.sidebar_expandido = True
        self.sidebar_ancho_expandido = 220
        self.sidebar_ancho_colapsado = 60

        # Contenedor principal
        self.contenedor_principal = ttk.Frame(self)
        self.contenedor_principal.pack(fill="both", expand=True)

        # ---------- Barra lateral ----------
        self.sidebar = tk.Frame(
            self.contenedor_principal,
            bg=self.colores_sidebar["bg"],
            width=self.sidebar_ancho_expandido,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ---------- Encabezado del sidebar ----------
        self.header_sidebar = tk.Frame(
            self.sidebar,
            bg=self.colores_sidebar["bg"],
            height=80
        )
        self.header_sidebar.pack(fill="x", side="top")
        self.header_sidebar.pack_propagate(False)

        # Texto del logo (solo visible cuando expandido)
        self.lbl_logo_texto = tk.Label(
            self.header_sidebar,
            text="Sistema de\nIngresos",
            font=("Segoe UI", 15, "bold"),
            bg=self.colores_sidebar["bg"],
            fg=self.colores_sidebar["fg"],
            justify="left",
        )
        self.lbl_logo_texto.pack(side="left", padx=15, pady=10)

        # Botón de hamburguesa del header (visible SOLO cuando expandido)
        self.btn_hamburguesa_header = tk.Label(
            self.header_sidebar,
            text="☰",
            font=("Segoe UI", 18),
            bg=self.colores_sidebar["bg"],
            fg=self.colores_sidebar["fg"],
            cursor="hand2",
        )
        self.btn_hamburguesa_header.pack(side="right", padx=12, pady=10)
        self.btn_hamburguesa_header.bind("<Button-1>", lambda e: self._toggle_sidebar())

        # ---------- Separador ----------
        self.separador_sidebar = tk.Frame(
            self.sidebar,
            bg=self.colores_sidebar["separador"],
            height=1
        )
        self.separador_sidebar.pack(fill="x", pady=(0, 10))

        # ---------- Botones del menú ----------
        menu_items = [
            ("⚡", "Sincronizar",   self._sincronizar),
            ("📥", "Leer factura",  self._leer_factura),
            ("🏷️", "Reclasificar",  self._abrir_reclasificador),
            ("📊", "Generar Excel", self._generar_excel),
            ("📈", "Reportes",      self._ver_reportes),
            ("🎨", "Cambiar tema",  self._elegir_tema),
            ("📜", "Ver logs",      self._ver_logs),
            ("🔧", "Reset caché",   self._reset_cache),
        ]

        self._botones_menu = []
        for icono, texto, comando in menu_items:
            btn_frame = tk.Frame(
                self.sidebar,
                bg=self.colores_sidebar["bg"],
                cursor="hand2",
                height=50,
            )
            btn_frame.pack(fill="x", padx=0, pady=0)
            btn_frame.pack_propagate(False)

            lbl_icono = tk.Label(
                btn_frame,
                text=icono,
                font=("Segoe UI Emoji", 16),
                bg=self.colores_sidebar["bg"],
                fg=self.colores_sidebar["fg"],
                width=3,
            )
            lbl_icono.pack(side="left", padx=(12, 0), pady=10)

            lbl_texto = tk.Label(
                btn_frame,
                text=texto,
                font=("Segoe UI", 12),
                bg=self.colores_sidebar["bg"],
                fg=self.colores_sidebar["fg_suave"],
                anchor="w",
            )
            lbl_texto.pack(side="left", padx=(8, 10), pady=10, fill="x", expand=True)

            # Hover + click
            def _on_enter(e, frame=btn_frame, ic=lbl_icono, tx=lbl_texto):
                if not self.sidebar_expandido:
                    return
                c = self.colores_sidebar
                frame.configure(bg=c["hover"])
                ic.configure(bg=c["hover"])
                tx.configure(bg=c["hover"], fg=c["fg"])

            def _on_leave(e, frame=btn_frame, ic=lbl_icono, tx=lbl_texto):
                c = self.colores_sidebar
                frame.configure(bg=c["bg"])
                ic.configure(bg=c["bg"])
                tx.configure(bg=c["bg"], fg=c["fg_suave"])

            def _on_click(e, cmd=comando):
                cmd()

            for widget in (btn_frame, lbl_icono, lbl_texto):
                widget.bind("<Enter>", _on_enter)
                widget.bind("<Leave>", _on_leave)
                widget.bind("<Button-1>", _on_click)

            self._botones_menu.append({
                "frame": btn_frame,
                "icono": lbl_icono,
                "texto": lbl_texto,
            })

        # ---------- Versión al pie ----------
        self.lbl_version = tk.Label(
            self.sidebar,
            text="v1.0",
            font=("Segoe UI", 8),
            bg=self.colores_sidebar["bg"],
            fg=self.colores_sidebar["version"],
        )
        self.lbl_version.pack(side="bottom", pady=10)

        # ---------- Contenido principal ----------
        self.contenido = ttk.Frame(self.contenedor_principal)
        self.contenido.pack(side="left", fill="both", expand=True)

        # ============================================================
        # BARRA SUPERIOR DE CONFIGURACIÓN + BOTONES PRINCIPALES
        # ============================================================
        top = ttk.LabelFrame(self.contenido, text="Configuración", padding=10)
        top.pack(fill="x", padx=10, pady=5)

        # --- Fila única con todo ---
        # Selector: Centro
        ttk.Label(top, text="Centro:").grid(row=0, column=1, padx=5, sticky="e")
        self.var_centro = ttk.StringVar(value="Central")
        ttk.Combobox(top, textvariable=self.var_centro, values=["Central", "Prado"],
                     width=12, state="readonly", bootstyle="primary").grid(
            row=0, column=2, padx=5)

        # Selector: Año
        ttk.Label(top, text="Año:").grid(row=0, column=3, padx=5, sticky="e")
        self.var_anio = ttk.StringVar(value=str(datetime.now().year))
        ttk.Entry(top, textvariable=self.var_anio, width=6,
                  style="Custom.TEntry").grid(row=0, column=4, padx=5)

        # Selector: Mes
        ttk.Label(top, text="Mes:").grid(row=0, column=5, padx=5, sticky="e")
        self.var_mes = ttk.StringVar(value=MESES_ES[datetime.now().month-1])
        ttk.Combobox(top, textvariable=self.var_mes, values=MESES_ES,
                     width=11, state="readonly", bootstyle="primary").grid(
            row=0, column=6, padx=5)

        # Botón: Abrir carpeta
        ttk.Button(top, text="📁 Abrir carpeta",
                   command=self._abrir_carpeta_ingreso,
                   bootstyle="info-outline").grid(row=0, column=7, padx=10)

        # Botones principales (a la derecha)
        ttk.Button(top, text="🆕 Nuevo", command=self._nuevo,
                   bootstyle="info-outline").grid(row=0, column=10, padx=3)

        self.btn_guardar = ttk.Button(top, text="💾 Guardar", command=self._guardar,
                                      bootstyle="info-outline")
        self.btn_guardar.grid(row=0, column=11, padx=3)

        self.btn_toggle_tabla = ttk.Button(
            top, text="👁️ Ocultar tabla", command=self._toggle_tabla,
            bootstyle="info-outline")
        self.btn_toggle_tabla.grid(row=0, column=12, padx=3)

        # Espacio flexible: empuja los botones de la derecha hacia el borde
        top.columnconfigure(8, weight=1)
        top.columnconfigure(9, weight=0)

        # ============================================================
        # FORMULARIO CON SCROLL
        # ============================================================
        cont = ttk.Frame(self.contenido)
        cont.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas_form = tk.Canvas(cont, borderwidth=0, highlightthickness=0)
        scroll = ttk.Scrollbar(cont, orient="vertical", command=self.canvas_form.yview)
        self.frame_form = ttk.Frame(self.canvas_form)

        self.frame_form.bind("<Configure>",
                             lambda e: self.canvas_form.configure(
                                 scrollregion=self.canvas_form.bbox("all")))
        self.canvas_window = self.canvas_form.create_window(
            (0, 0), window=self.frame_form, anchor="nw")
        self.canvas_form.configure(yscrollcommand=scroll.set)
        self.canvas_form.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.canvas_form.bind("<Configure>", self._on_canvas_configure)

        # Construir grupos de campos
        grupo_actual = None
        frame_grupo = None
        col = 0
        for clave, etiqueta, grupo, tipo in CAMPOS:
            if grupo != grupo_actual:
                grupo_actual = grupo
                frame_grupo = ttk.LabelFrame(self.frame_form, text=grupo, padding=8)
                frame_grupo.pack(fill="x", padx=5, pady=4)
                col = 0
            fila = col // 3
            columnas = (col % 3) * 2
            ttk.Label(frame_grupo, text=etiqueta + ":").grid(
                row=fila, column=columnas, padx=5, pady=3, sticky="e")

            if tipo == "date":
                w = DateEntry(frame_grupo, width=15, dateformat="%d/%m/%Y",
                              bootstyle="primary")
            elif tipo == "number":
                if clave == "total":
                    w = EntryMoneda(frame_grupo, callback=None, width=20,
                                    style="Custom.TEntry")
                    w.configure(state="readonly")
                elif clave in REGLAS_AUTO:
                    w = EntryMoneda(frame_grupo, callback=None, width=20,
                                    style="Custom.TEntry")
                else:
                    w = EntryMoneda(frame_grupo, callback=self._recalcular_total,
                                    width=20, style="Custom.TEntry")
            else:
                if clave in ("nombre", "rfc"):
                    w = EntryAutoComplete(frame_grupo,
                                          opciones=self.historial.get(clave, []),
                                          width=35 if clave == "nombre" else 20,
                                          style="Custom.TEntry")
                else:
                    w = ttk.Entry(frame_grupo, width=20, style="Custom.TEntry")
                # Forzar mayúsculas al escribir manualmente
                self._forzar_mayusculas(w)

            w.grid(row=fila, column=columnas + 1, padx=5, pady=3, sticky="w")
            self.entradas[clave] = w
            self.widgets_ordenados.append(w)
            col += 1

        # Conectar auto-cálculo de IVA
        for clave_iva, (clave_base, tasa) in REGLAS_AUTO.items():
            base = self.entradas[clave_base]
            iva = self.entradas[clave_iva]
            base.bind("<FocusOut>",
                      lambda e, b=base, i=iva, t=tasa: self._auto_iva(b, i, t), add="+")

        # --- Label de alerta de total ---
        self.lbl_alerta_total = ttk.Label(self.contenido, text="", bootstyle="danger")
        self.lbl_alerta_total.pack(fill="x", padx=15, pady=(0, 5))

        # ============================================================
        # TABLA
        # ============================================================
        self.frame_tabla = ttk.LabelFrame(self.contenido, text="Registros guardados", padding=5)
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)
        cols_vis = ["no_factura", "fecha", "nombre", "rfc", "total",
            "efectivo", "tc", "td", "cheque", "transfer",
            "folio_fiscal", "adjuntos"]
        self.tabla = ttk.Treeview(self.frame_tabla, columns=cols_vis,
            show="headings", height=8,
            bootstyle="primary")
        for c in cols_vis:
            if c == "adjuntos":
                self.tabla.heading(c, text="📎")
                self.tabla.column(c, width=45, anchor="center")
            else:
                self.tabla.heading(c, text=CAMPOS_DICT[c][1])
                self.tabla.column(c, width=100, anchor="center")
        self.tabla.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(self.frame_tabla, orient="vertical",
                           command=self.tabla.yview)
        sb.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=sb.set)

        # ---- MENÚ CONTEXTUAL para la tabla ----
        self._crear_menu_contextual_tabla()

        # ---- Enter salta al siguiente campo ----
        for w in self.widgets_ordenados:
            w.bind("<Return>", self._enter_siguiente, add="+")
            w.bind("<KP_Enter>", self._enter_siguiente, add="+")

        # ---- Validación visual No. Factura y QVET ----
        w_nf = self.entradas.get("no_factura")
        if w_nf:
            w_nf.bind("<KeyRelease>", self._validar_no_factura_visual, add="+")
            w_nf.bind("<FocusOut>", self._validar_no_factura_visual, add="+")
        w_qv = self.entradas.get("qvet")
        if w_qv:
            w_qv.bind("<KeyRelease>", self._validar_qvet_visual, add="+")
            w_qv.bind("<FocusOut>", self._validar_qvet_visual, add="+")

        # ---- Scroll con rueda del mouse ----
        self._bind_mousewheel(self.frame_form)

        # ---- Atajo Ctrl+T / Cmd+T ----
        self.bind("<Control-t>", lambda e: self._toggle_tabla())
        self.bind("<Command-t>", lambda e: self._toggle_tabla())
        self.bind("<Control-b>", lambda e: self._toggle_sidebar())
        self.bind("<Command-b>", lambda e: self._toggle_sidebar())

        # Validación inicial
        self._validar_no_factura_visual()
        self._validar_qvet_visual()

        # ---- Refrescar tabla y título al cambiar centro/año/mes ----
        def _on_cambio_anio(*args):
            try:
                anio = int(self.var_anio.get())
            except Exception:
                return
            if self._anio_cargado != anio:
                self.registros = cargar_db(anio)
                self._anio_cargado = anio
            self._refrescar_tabla()
            self._actualizar_titulo()

        def _on_cambio_reporte_otros(*args):
            self._refrescar_tabla()
            self._actualizar_titulo()

        self.var_anio.trace_add("write", _on_cambio_anio)
        self.var_centro.trace_add("write", _on_cambio_reporte_otros)
        self.var_mes.trace_add("write", _on_cambio_reporte_otros)
        # ---- Iniciar con el sidebar cerrado ----
        self.after(50, self._toggle_sidebar)

    # ---------------- BARRA LATERAL ----------------
    def _toggle_sidebar(self):
        """Expande o colapsa la barra lateral."""
        if self.sidebar_expandido:
            # ---- Colapsar ----
            self.sidebar.configure(width=self.sidebar_ancho_colapsado)

            # Ocultar el texto "Sistema de Ingresos" y dejar solo el ☰
            self.lbl_logo_texto.pack_forget()

            # Mover el ☰ al centro del header
            self.btn_hamburguesa_header.pack_forget()
            self.btn_hamburguesa_header.pack(side="top", pady=20)

            # Ocultar los textos de todos los botones de la lista
            for btn in self._botones_menu:
                btn["texto"].pack_forget()

            # Centrar los íconos
            for btn in self._botones_menu:
                btn["icono"].pack_configure(padx=(18, 0))

            self.sidebar_expandido = False

        else:
            # ---- Expandir ----
            self.sidebar.configure(width=self.sidebar_ancho_expandido)

            # Reponer el texto del header
            self.lbl_logo_texto.pack(side="left", padx=15, pady=10)

            # Mover el ☰ de vuelta a la derecha del header
            self.btn_hamburguesa_header.pack_forget()
            self.btn_hamburguesa_header.pack(side="right", padx=12, pady=10)

            # Reponer los textos de la lista
            for btn in self._botones_menu:
                btn["icono"].pack_configure(padx=(12, 0))
                btn["texto"].pack(side="left", padx=(8, 10), pady=10,
                                  fill="x", expand=True)

            self.sidebar_expandido = True

    # ---------------- MENÚ CONTEXTUAL DE LA TABLA ----------------
    def _crear_menu_contextual_tabla(self):
        """Crea el menú que aparece al hacer clic derecho en un registro."""
        self.menu_contextual = tk.Menu(self, tearoff=0)

        self.menu_contextual.add_command(
            label="✏️  Editar",
            command=self._editar
        )
        self.menu_contextual.add_command(
            label="🗑️  Eliminar",
            command=self._eliminar
        )
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(
            label="📎  Adjuntar factura",
            command=self._adjuntar_factura
        )
        self.menu_contextual.add_command(
            label="📂  Ver adjuntos",
            command=self._ver_adjuntos
        )

        # Bindings: clic derecho en Mac es Button-2 y Control+Click
        self.tabla.bind("<Button-3>", self._mostrar_menu_contextual)   # Windows/Linux
        self.tabla.bind("<Button-2>", self._mostrar_menu_contextual)   # Mac
        self.tabla.bind("<Control-Button-1>", self._mostrar_menu_contextual)  # Mac

    def _mostrar_menu_contextual(self, event):
        """Muestra el menú contextual en la posición del cursor."""
        # Identificar el registro bajo el cursor
        item = self.tabla.identify_row(event.y)
        if not item:
            return
        # Seleccionar el registro antes de mostrar el menú
        self.tabla.selection_set(item)
        # Mostrar el menú
        try:
            self.menu_contextual.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_contextual.grab_release()

    # ---------------- SCROLL ----------------
    def _on_mousewheel(self, event):
        if sys.platform == "darwin":
            delta = -1 * event.delta
        elif sys.platform.startswith("win"):
            delta = -1 * (event.delta // 120)
        else:
            delta = -1 if event.num == 5 else 1
        self.canvas_form.yview_scroll(int(delta), "units")

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")
        for hijo in widget.winfo_children():
            self._bind_mousewheel(hijo)

    def _on_canvas_configure(self, event):
        self.canvas_form.itemconfigure(self.canvas_window, width=event.width)

    # ---------------- ENTER ----------------
    def _enter_siguiente(self, event):
        widget_actual = event.widget

        if isinstance(widget_actual, EntryAutoComplete) and widget_actual._lista:
            widget_actual._seleccionar()
            return "break"

        if isinstance(widget_actual, EntryMoneda):
            texto = widget_actual.get().strip()
            if widget_actual._tiene_operacion(texto):
                widget_actual._ultima_expresion = texto.replace(",", "").replace("$", "").strip()
                widget_actual._ultimo_valor = evaluar_expresion(texto)
            else:
                widget_actual._ultima_expresion = ""
                widget_actual._ultimo_valor = limpiar_moneda(texto)
            widget_actual.delete(0, tk.END)
            widget_actual.insert(0, formatear_moneda(widget_actual._ultimo_valor))
            widget_actual._pintar()
            if widget_actual.callback:
                widget_actual.callback()

        try:
            idx = self.widgets_ordenados.index(widget_actual)
        except ValueError:
            return
        if idx + 1 < len(self.widgets_ordenados):
            siguiente = self.widgets_ordenados[idx + 1]
            siguiente.focus_set()
            try:
                siguiente.selection_range(0, tk.END)
            except Exception:
                pass
        else:
            self.btn_guardar.focus_set()
        return "break"

    # ---------------- CÁLCULOS AUTOMÁTICOS ----------------
    def _auto_iva(self, entrada_base, entrada_iva, tasa):
        base = entrada_base.get_valor()
        if base != 0:
            entrada_iva.set_valor(round(base * tasa, 2))
            self._recalcular_total()

    def _recalcular_total(self, *args):
        """
        TOTAL muestra la suma de tipo de pago.
        Compara con la suma de categorías y alerta si hay diferencia > $0.01.
        """
        total_pago = 0.0
        for clave in CAMPOS_TIPO_PAGO:
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                total_pago += w.get_valor()

        total_categorias = 0.0
        for clave in CATEGORIAS_PARA_TOTAL:
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                total_categorias += w.get_valor()

        w_total = self.entradas.get("total")
        if isinstance(w_total, EntryMoneda):
            w_total.configure(state="normal")
            w_total.set_valor(round(total_pago, 2))
            w_total.configure(state="readonly")

        if total_pago > 0 and total_categorias > 0:
            dif = abs(total_pago - total_categorias)
            if dif > 0.01:
                try:
                    w_total.configure(foreground="red")
                    self.lbl_alerta_total.configure(
                        text=f"⚠️ Diferencia: ${dif:,.2f} "
                             f"(pago: ${total_pago:,.2f} / "
                             f"categorías: ${total_categorias:,.2f})"
                    )
                except Exception:
                    pass
            else:
                try:
                    w_total.configure(foreground=COLORES["texto_normal"])
                    self.lbl_alerta_total.configure(text="")
                except Exception:
                    pass
        else:
            try:
                w_total.configure(foreground=COLORES["texto_normal"])
                self.lbl_alerta_total.configure(text="")
            except Exception:
                pass

    # ---------------- VALIDACIÓN VISUAL ----------------
    def _validar_campo_unico(self, clave, event=None):
        w = self.entradas.get(clave)
        if not w:
            return
        valor = w.get().strip()
        if not valor:
            self._pintar_entry(w, None)
            return
        duplicado = existe_valor_unico(self.registros, clave, valor,
                                       ignorar_id=self.id_actual)
        color = COLORES["campo_error"] if duplicado else COLORES["campo_ok"]
        self._pintar_entry(w, color)

    def _validar_no_factura_visual(self, event=None):
        self._validar_campo_unico("no_factura", event)

    def _validar_qvet_visual(self, event=None):
        self._validar_campo_unico("qvet", event)

    @staticmethod
    def _pintar_entry(widget, color_fondo):
        try:
            if color_fondo:
                widget.configure(background=color_fondo)
            else:
                widget.configure(background="")
        except Exception:
            pass

    @staticmethod
    def _forzar_mayusculas(widget):
        """Convierte automáticamente a mayúsculas lo que se escriba en el widget."""
        def _convertir(event):
            # Ignorar teclas especiales
            if event.keysym in ("BackSpace", "Delete", "Left", "Right",
                                "Up", "Down", "Home", "End", "Tab",
                                "Shift_L", "Shift_R", "Control_L", "Control_R",
                                "Alt_L", "Alt_R"):
                return
            texto_actual = widget.get()
            texto_mayus = texto_actual.upper()
            if texto_actual != texto_mayus:
                pos = widget.index(tk.INSERT)
                widget.delete(0, tk.END)
                widget.insert(0, texto_mayus)
                try:
                    widget.icursor(pos)
                except Exception:
                    pass

        widget.bind("<KeyRelease>", _convertir, add="+")

    # ---------------- CRUD ----------------
    def _leer_form(self):
        d = {}
        for clave, _, _, tipo in CAMPOS:
            w = self.entradas[clave]
            if tipo == "number":
                if isinstance(w, EntryMoneda):
                    texto = w.get().strip()
                    if w._tiene_operacion(texto):
                        w._ultima_expresion = texto.replace(",", "").replace("$", "").strip()
                        w._ultimo_valor = evaluar_expresion(texto)
                        w.delete(0, tk.END)
                        w.insert(0, formatear_moneda(w._ultimo_valor))
                    else:
                        w._ultimo_valor = limpiar_moneda(texto)

                    d[clave] = w._ultimo_valor
                    d[f"{clave}__expr"] = w._ultima_expresion
                else:
                    d[clave] = limpiar_moneda(w.get())
            elif tipo == "date":
                if isinstance(w, DateEntry):
                    d[clave] = w.entry.get()
                else:
                    d[clave] = w.get()
            else:
                d[clave] = w.get().strip().upper()
        d["centro"] = self.var_centro.get()
        d["anio"] = int(self.var_anio.get())
        d["mes"] = self.var_mes.get()
        return d

    def _escribir_form(self, r):
        for clave, _, _, tipo in CAMPOS:
            w = self.entradas[clave]
            valor = r.get(clave, "")
            if tipo == "number":
                if isinstance(w, EntryMoneda):
                    expr = r.get(f"{clave}__expr", "")
                    w.set_valor(float(valor or 0), expresion=expr)
            elif tipo == "date":
                if isinstance(w, DateEntry):
                    try:
                        w.entry.delete(0, tk.END)
                        w.entry.insert(0, str(valor))
                    except Exception:
                        pass
                else:
                    w.delete(0, tk.END)
                    w.insert(0, str(valor))
            else:
                w.delete(0, tk.END)
                w.insert(0, str(valor))

    def _nuevo(self):
        self.id_actual = None
        self._ultima_factura_xml = None
        self._ultima_factura_pdf = None
        hoy = datetime.now().strftime("%d/%m/%Y")
        for clave, _, _, tipo in CAMPOS:
            w = self.entradas[clave]
            if tipo == "number" and isinstance(w, EntryMoneda):
                w.set_valor(0, expresion="")
            elif tipo == "date":
                if isinstance(w, DateEntry):
                    try:
                        w.entry.delete(0, tk.END)
                        w.entry.insert(0, hoy)
                    except Exception:
                        pass
            else:
                w.delete(0, tk.END)
        for clave in ("nombre", "rfc"):
            w = self.entradas[clave]
            if isinstance(w, EntryAutoComplete):
                w.set_opciones(self.historial.get(clave, []))

        try:
            anio_actual = int(self.var_anio.get())
        except Exception:
            anio_actual = datetime.now().year
        esperado = obtener_consecutivo_esperado(
            self.registros,
            centro=self.var_centro.get(),
            anio=anio_actual,
            mes=self.var_mes.get()
        )
        if esperado is not None:
            self.entradas["no_factura"].insert(0, str(esperado))

        self._recalcular_total()
        self._validar_no_factura_visual()
        self._validar_qvet_visual()
        self.entradas["no_factura"].focus_set()

    def _guardar(self):
        w_foco = self.focus_get()
        if w_foco is not None:
            try:
                w_foco.event_generate("<FocusOut>")
            except Exception:
                pass
            self.update_idletasks()

        datos = self._leer_form()

        if not datos["no_factura"]:
            messagebox.showwarning("Falta info", "El No. de Factura es obligatorio.")
            return
        if not datos["qvet"]:
            messagebox.showwarning("Falta info", "El QVET es obligatorio.")
            return

        if self.id_actual is None:
            if existe_valor_unico(self.registros, "no_factura", datos["no_factura"]):
                messagebox.showerror("Duplicado",
                                     f"Ya existe el No. de Factura {datos['no_factura']}.")
                return
            if existe_valor_unico(self.registros, "qvet", datos["qvet"]):
                messagebox.showerror("Duplicado",
                                     f"Ya existe el QVET {datos['qvet']}.")
                return
        else:
            if existe_valor_unico(self.registros, "no_factura",
                                  datos["no_factura"], ignorar_id=self.id_actual):
                messagebox.showerror("Duplicado",
                                     f"Ya existe OTRO registro con No. Factura {datos['no_factura']}.")
                return
            if existe_valor_unico(self.registros, "qvet",
                                  datos["qvet"], ignorar_id=self.id_actual):
                messagebox.showerror("Duplicado",
                                     f"Ya existe OTRO registro con QVET {datos['qvet']}.")
                return

        if self.id_actual is None:
            esperado = obtener_consecutivo_esperado(
                self.registros,
                centro=datos["centro"],
                anio=datos["anio"],
                mes=datos["mes"]
            )
            actual = obtener_no_factura_numerico(datos["no_factura"])
            if esperado is not None and actual is not None and actual != esperado:
                respuesta = messagebox.askyesno(
                    "No. de Factura no consecutivo",
                    f"El último No. de Factura registrado es "
                    f"{esperado - 1}.\n\n"
                    f"El siguiente debería ser: {esperado}\n"
                    f"Pero estás ingresando: {actual}\n\n"
                    "¿Estás seguro de continuar?"
                )
                if not respuesta:
                    return

        for clave, _, _, tipo in CAMPOS:
            if tipo == "date":
                datos[clave] = parse_fecha(datos[clave]).replace("-", "/")

        es_edicion = self.id_actual is not None
        reg_viejo = None
        if es_edicion:
            reg_viejo = next((r for r in self.registros if r["id"] == self.id_actual), None)

        if not es_edicion:
            datos["id"] = int(datetime.now().timestamp() * 1000)
            self.registros.append(datos)
            msg = "Registro guardado."
        else:
            for i, r in enumerate(self.registros):
                if r["id"] == self.id_actual:
                    datos["id"] = self.id_actual
                    self.registros[i] = datos
                    break
            msg = "Registro actualizado."

        # Guardar en el archivo del año que corresponde
        try:
            anio_datos = int(datos.get("anio", self._anio_cargado))
        except Exception:
            anio_datos = self._anio_cargado
        guardar_db(self.registros, anio_datos)

        self.historial = actualizar_historial(self.registros)
        for clave in ("nombre", "rfc"):
            w = self.entradas[clave]
            if isinstance(w, EntryAutoComplete):
                w.set_opciones(self.historial.get(clave, []))

        fecha_carpeta = parse_fecha(datos.get("fecha", ""))
        ruta = ruta_ingreso(datos["centro"], datos["anio"],
                            MESES_ES.index(datos["mes"]) + 1) / fecha_carpeta
        try:
            ruta.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error carpeta", str(e))

        msgs_archivos = []
        if es_edicion and reg_viejo:
            msgs_archivos = self._gestionar_adjuntos_al_editar(reg_viejo, datos)

        if not es_edicion and (self._ultima_factura_xml or self._ultima_factura_pdf):
            rutas_adjuntar = []
            if self._ultima_factura_xml and Path(self._ultima_factura_xml).exists():
                rutas_adjuntar.append(self._ultima_factura_xml)
            if self._ultima_factura_pdf and Path(self._ultima_factura_pdf).exists():
                rutas_adjuntar.append(self._ultima_factura_pdf)

            if rutas_adjuntar:
                try:
                    copiados, errores = adjuntar_archivos(datos, rutas_adjuntar)
                    if copiados:
                        nombres = ", ".join(d.name for _, d in copiados)
                        msgs_archivos.append(f"\n📎 Adjuntados: {nombres}")
                    if errores:
                        for origen, err in errores:
                            msgs_archivos.append(f"⚠️ Error al adjuntar {origen}: {err}")
                except Exception as e:
                    msgs_archivos.append(f"⚠️ Error al adjuntar: {e}")

            self._ultima_factura_xml = None
            self._ultima_factura_pdf = None

        partes = [msg, f"Carpeta: {ruta}"]
        if msgs_archivos:
            partes.append("")
            partes.extend(msgs_archivos)
        messagebox.showinfo("OK", "\n".join(partes))

        self._refrescar_tabla()
        self._nuevo()

    def _gestionar_adjuntos_al_editar(self, reg_viejo, datos_nuevos):
        msgs = []
        no_viejo = str(reg_viejo.get("no_factura", "")).strip()
        no_nuevo = str(datos_nuevos.get("no_factura", "")).strip()
        carpeta_vieja = carpeta_de_registro(reg_viejo)
        carpeta_nueva = carpeta_de_registro(datos_nuevos)
        cambio_no = no_viejo and no_nuevo and no_viejo != no_nuevo
        cambio_carpeta = (carpeta_vieja and carpeta_nueva
                          and carpeta_vieja != carpeta_nueva)
        if not cambio_no and not cambio_carpeta:
            return msgs
        if not carpeta_vieja or not carpeta_vieja.exists():
            return msgs
        adjuntos = archivos_del_registro(reg_viejo)
        if not adjuntos:
            return msgs
        if cambio_carpeta:
            try:
                carpeta_nueva.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                msgs.append(f"⚠️ No se pudo crear la carpeta destino: {e}")
                return msgs
        for archivo in adjuntos:
            try:
                ext = archivo.suffix
                nombre_final = f"{no_nuevo}{ext}" if cambio_no else archivo.name
                carpeta_final = carpeta_nueva if cambio_carpeta else archivo.parent
                destino = carpeta_final / nombre_final
                if destino.resolve() == archivo.resolve():
                    continue
                if destino.exists():
                    msgs.append(f"⚠️ {archivo.name}: ya existe {nombre_final}, no se movió.")
                    continue
                archivo.rename(destino)
                if cambio_no and cambio_carpeta:
                    msgs.append(f"📝➡️ {archivo.name} → {carpeta_final.name}/{nombre_final}")
                elif cambio_no:
                    msgs.append(f"📝 {archivo.name} → {nombre_final}")
                else:
                    msgs.append(f"➡️ {archivo.name} movido a {carpeta_final.name}/")
            except Exception as e:
                msgs.append(f"⚠️ {archivo.name}: {e}")
        if cambio_carpeta and carpeta_vieja.exists():
            try:
                if not any(carpeta_vieja.iterdir()):
                    carpeta_vieja.rmdir()
                    msgs.append(f"🗑️ Carpeta vacía eliminada: {carpeta_vieja.name}/")
            except Exception:
                pass
        return msgs

    def _editar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Editar", "Selecciona un registro.")
            return
        id_sel = int(sel[0])
        for r in self.registros:
            if r["id"] == id_sel:
                self.id_actual = id_sel
                self._escribir_form(r)
                self.var_centro.set(r.get("centro", "Central"))
                self.var_anio.set(str(r.get("anio", datetime.now().year)))
                self.var_mes.set(r.get("mes", MESES_ES[datetime.now().month-1]))
                self._validar_no_factura_visual()
                self._validar_qvet_visual()
                break

    def _eliminar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Eliminar", "Selecciona un registro.")
            return
        id_sel = int(sel[0])
        reg = next((r for r in self.registros if r["id"] == id_sel), None)
        if not reg:
            return
        no_factura = str(reg.get("no_factura", "")).strip()
        fecha_str = reg.get("fecha", "")
        centro = reg.get("centro", "Central")
        archivos = archivos_del_registro(reg)
        carpeta = carpeta_de_registro(reg)
        lineas = [f"¿Eliminar el registro de la factura {no_factura}?",
                  "", f"Centro: {centro}", f"Fecha:  {fecha_str}", ""]
        if carpeta:
            lineas.append(f"Carpeta: {carpeta}")
        if archivos:
            lineas.append("")
            lineas.append(f"Se eliminarán {len(archivos)} archivo(s):")
            for a in archivos:
                lineas.append(f"   • {a.name}")
        lineas.append("")
        lineas.append("¿Continuar?")
        if not messagebox.askyesno("Confirmar", "\n".join(lineas)):
            return
        eliminados, errores = eliminar_archivos_de_registro(reg)
        self.registros = [r for r in self.registros if r["id"] != id_sel]
        guardar_db(self.registros, self._anio_cargado)
        self.historial = actualizar_historial(self.registros)
        carpeta_borrada = False
        motivo_carpeta = ""
        if carpeta and carpeta.exists():
            carpeta_borrada, motivo_carpeta = eliminar_carpeta_si_vacia(reg)
        self._refrescar_tabla()
        self._nuevo()
        partes = ["Registro eliminado."]
        if eliminados:
            partes.append(f"\nArchivos eliminados ({len(eliminados)}):")
            for a in eliminados:
                partes.append(f"   • {a.name}")
        if carpeta_borrada:
            partes.append(f"\nCarpeta eliminada:\n   {motivo_carpeta}")
        elif carpeta and carpeta.exists():
            partes.append(f"\nCarpeta NO eliminada:\n   {motivo_carpeta}")
        if errores:
            partes.append("\n⚠️ Errores:")
            for a, e in errores:
                partes.append(f"   • {a.name}: {e}")
        messagebox.showinfo("Resultado", "\n".join(partes))

    def _leer_factura(self):
        """Lee un XML (y opcionalmente un PDF) y llena el formulario."""
        ruta_xml = filedialog.askopenfilename(
            title="Selecciona el XML de la factura",
            filetypes=[("XML CFDI", "*.xml"), ("Todos", "*.*")]
        )
        if not ruta_xml:
            return

        ruta_pdf = filedialog.askopenfilename(
            title="Selecciona el PDF de la factura (opcional, cancelar para omitir)",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")]
        )

        try:
            datos = procesar_factura(ruta_xml, ruta_pdf or None)
        except Exception as e:
            messagebox.showerror("Error al leer factura",
                                 f"No se pudo procesar la factura:\n{e}")
            return

        resumen, _ = self._llenar_desde_factura(datos)

        self._ultima_factura_xml = ruta_xml
        self._ultima_factura_pdf = ruta_pdf or None

        serie = datos.get("serie", "").strip()
        centro_detectado = centro_desde_serie(serie)
        centro_txt = centro_detectado if centro_detectado else "sin cambios"

        # Recalcular los valores actuales de los combos (ya se cambiaron antes)
        centro_final = self.var_centro.get()
        mes_final = self.var_mes.get()
        anio_final = self.var_anio.get()

        lineas = [
            f"Factura leída: {datos['no_factura']}",
            f"Serie: {serie}",
            f"Centro: {centro_final}",
            f"Año: {anio_final} | Mes: {mes_final.capitalize()}",
            f"Nombre: {datos['nombre']}",
            f"Total: ${datos['total']:,.2f}",
            "",
            "Campos llenados:",
        ]
        lineas.extend(resumen)
        messagebox.showinfo("Factura leída", "\n".join(lineas))

        if not centro_detectado:
            messagebox.showwarning(
                "Serie no reconocida",
                f"La serie '{serie}' no está mapeada a ningún centro.\n\n"
                "Verifica manualmente el Centro antes de guardar.\n\n"
                "Si quieres agregarla, abre el código de ingresos.py "
                "y añade la serie al diccionario 'SERIES_A_CENTRO'."
            )

    def _pedir_credenciales_correo(self):
        """
        Pide las credenciales de Gmail y opciones de filtrado.
        Devuelve (usuario, password, etiqueta) o (None, None, None).
        """
        ventana = ttk.Toplevel(self)
        ventana.title("Configuración de Gmail")
        ventana.geometry("550x450")
        ventana.resizable(False, False)
        ventana.minsize(550, 450)
        ventana.transient(self)
        ventana.grab_set()

        # ---- Contenedor con padding ----
        contenedor = ttk.Frame(ventana, padding=20)
        contenedor.pack(fill="both", expand=True)

        # ---- Encabezado ----
        ttk.Label(contenedor,
                  text="Configuración de Gmail",
                  font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))

        ttk.Label(contenedor,
                  text="Necesitas una 'Contraseña de aplicación' de Google.\n"
                       "Genérala en: myaccount.google.com/apppasswords",
                  justify="center", foreground="gray",
                  font=("Segoe UI", 9)).pack(pady=(0, 20))

        # ---- Formulario (una fila por campo) ----
        form = ttk.Frame(contenedor)
        form.pack(fill="x", expand=False)

        # Columna 0: etiquetas | Columna 1: campos
        form.columnconfigure(0, weight=0)
        form.columnconfigure(1, weight=1)

        cfg_actual = CONFIG.get("correo", {})

        fila = 0

        # ---------- Correo de Gmail ----------
        ttk.Label(form, text="Correo de Gmail:").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_usuario = tk.StringVar(value=cfg_actual.get("usuario", ""))
        ttk.Entry(form, textvariable=var_usuario).grid(
            row=fila, column=1, sticky="ew", pady=8)
        fila += 1

        # ---------- Contraseña de app ----------
        ttk.Label(form, text="Contraseña de app:").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_password = tk.StringVar(value=cfg_actual.get("password_app", ""))
        ttk.Entry(form, textvariable=var_password, show="•").grid(
            row=fila, column=1, sticky="ew", pady=8)
        fila += 1

        # ---------- Etiqueta ----------
        ttk.Label(form, text="Etiqueta de Gmail:").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_etiqueta = tk.StringVar(
            value=cfg_actual.get("etiqueta", "FACTURAS BAALAK"))
        ttk.Entry(form, textvariable=var_etiqueta).grid(
            row=fila, column=1, sticky="ew", pady=8)
        fila += 1

        # Texto de ayuda de la etiqueta
        ttk.Label(form,
                  text="Ejemplo: 'Facturas QVET' o 'Facturas/QVET' (con subcarpeta)",
                  foreground="gray", font=("Segoe UI", 8)).grid(
            row=fila, column=1, sticky="w", pady=(0, 5))
        fila += 1

        # ---------- Filtro de remitente ----------
        ttk.Label(form, text="Filtrar por remitente:").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_remitente = tk.StringVar(
            value=cfg_actual.get("filtro_remitente", ""))
        ttk.Entry(form, textvariable=var_remitente).grid(
            row=fila, column=1, sticky="ew", pady=8)
        fila += 1

        ttk.Label(form,
                  text="Opcional. Ejemplo: 'qvet' o 'facturacion'. Déjalo vacío para descargar todos.",
                  foreground="gray", font=("Segoe UI", 8), wraplength=400).grid(
            row=fila, column=1, sticky="w", pady=(0, 5))
        fila += 1

        # ---------- Días atrás ----------
        ttk.Label(form, text="Correos de los últimos (días):").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_dias = tk.StringVar(value=str(cfg_actual.get("dias_atras", 30)))
        ttk.Entry(form, textvariable=var_dias, width=10).grid(
            row=fila, column=1, sticky="w", pady=8)
        fila += 1

        ttk.Label(form,
                  text="Escribe 0 para descargar todos los correos sin límite de fecha.",
                  foreground="gray", font=("Segoe UI", 8)).grid(
            row=fila, column=1, sticky="w", pady=(0, 5))
        fila += 1

        # ---- Espacio flexible para centrar botones abajo ----
        ttk.Frame(contenedor).pack(fill="y", expand=True)

        resultado = {"ok": False}

        def _guardar():
            u = var_usuario.get().strip()
            p = var_password.get().strip().replace(" ", "")
            e = var_etiqueta.get().strip() or "Facturas QVET"
            r = var_remitente.get().strip()
            try:
                d = int(var_dias.get().strip() or "0")
            except ValueError:
                d = 0

            if not u or not p:
                messagebox.showwarning(
                    "Faltan datos",
                    "Correo y contraseña son obligatorios.",
                    parent=ventana
                )
                return

            CONFIG["correo"] = {
                "usuario": u,
                "password_app": p,
                "etiqueta": e,
                "filtro_remitente": r,
                "dias_atras": d,
            }
            guardar_config(CONFIG)
            resultado["ok"] = True
            ventana.destroy()

        # ---- Botones ----
        fr = ttk.Frame(contenedor)
        fr.pack(fill="x", pady=(15, 0))

        ttk.Button(fr, text="💾 Guardar",
                   command=_guardar,
                   bootstyle="info-outline").pack(side="right", padx=5)

        ventana.wait_window()

        if resultado["ok"]:
            return (CONFIG["correo"]["usuario"],
                    CONFIG["correo"]["password_app"],
                    CONFIG["correo"]["etiqueta"])
        return None, None, None

    def _editar_config_correo(self):
        """
        Abre el diálogo de configuración de Gmail para editar los datos
        ya guardados (correo, contraseña, etiqueta, filtros).
        """
        # Abrir el diálogo (ya carga los valores actuales desde CONFIG)
        usuario, password, etiqueta = self._pedir_credenciales_correo()
        if usuario:
            messagebox.showinfo(
                "Configuración actualizada",
                f"Datos guardados correctamente.\n\n"
                f"Correo: {usuario}\n"
                f"Etiqueta: {etiqueta}\n\n"
                "Ahora puedes sincronizar con ⚡ Sincronizar."
            )

    def _sincronizar(self):
        """
        Flujo unificado: descarga facturas del correo y pregunta al usuario
        qué hacer con ellas.
        Ofrece la opción de editar la configuración si hay errores.
        """
        from correo_facturas import descargar_adjuntos_gmail

        # ---- Bucle: permite reintentar tras editar credenciales ----
        while True:
            # ---- 1. Verificar/obtener configuración ----
            cfg_correo = CONFIG.get("correo", {})
            usuario = cfg_correo.get("usuario", "")
            password = cfg_correo.get("password_app", "")
            etiqueta = cfg_correo.get("etiqueta", "FACTURAS BAALAK")
            filtro_remitente = cfg_correo.get("filtro_remitente", "")
            dias_atras = cfg_correo.get("dias_atras", 30)

            # Si no hay configuración, pedirla
            if not usuario or not password:
                usuario, password, etiqueta = self._pedir_credenciales_correo()
                if not usuario:
                    return
                cfg_correo = CONFIG.get("correo", {})
                filtro_remitente = cfg_correo.get("filtro_remitente", "")
                dias_atras = cfg_correo.get("dias_atras", 30)

            # ---- 2. Preguntar modo con opción de editar ----
            modo = self._preguntar_modo_descarga(dias_atras)
            if modo == "cancelar":
                return
            elif modo == "editar":
                # Abrir el diálogo de configuración
                u, p, e = self._pedir_credenciales_correo()
                if u:
                    messagebox.showinfo(
                        "Configuración actualizada",
                        f"Datos guardados correctamente.\n\n"
                        f"Correo: {u}\n"
                        f"Etiqueta: {e}"
                    )
                # Volver al inicio del bucle para preguntar de nuevo
                continue
            else:
                solo_no_leidos = (modo == "no_leidos")
                break

        # ---- 3. Ventana de progreso ----
        ventana_prog = ttk.Toplevel(self)
        ventana_prog.title("⚡ Sincronizando facturas...")
        ventana_prog.geometry("900x700")
        ventana_prog.transient(self)
        # Flag para saber si el usuario quiere cancelar la descarga
        # ---- Estado de cancelación ----
        estado = {"cancelar": False}

        def _al_intentar_cerrar():
            """Se ejecuta cuando el usuario hace clic en la X."""
            if estado["cancelar"]:
                return
            respuesta = messagebox.askyesno(
                "Cancelar descarga",
                "La descarga está en curso.\n\n"
                "¿Quieres cancelarla?\n\n"
                "Los correos ya descargados quedarán guardados.\n"
                "El proceso se detendrá en el próximo correo.",
                parent=ventana_prog
            )
            if respuesta:
                estado["cancelar"] = True
                log("⚠️ Cancelación solicitada. Esperando a que termine el correo actual...")
                try:
                    self.barra_progreso.stop()
                    self.lbl_progreso.configure(text="⚠️ Cancelando...")
                except Exception:
                    pass

        ventana_prog.protocol("WM_DELETE_WINDOW", _al_intentar_cerrar)

        def debe_cancelar():
            """Devuelve True si el usuario canceló la operación."""
            return estado["cancelar"]

        # Centrar la ventana
        ventana_prog.update_idletasks()
        x = (ventana_prog.winfo_screenwidth() - 900) // 2
        y = (ventana_prog.winfo_screenheight() - 700) // 2
        ventana_prog.geometry(f"900x700+{x}+{y}")

        # ---- Título ----
        ttk.Label(ventana_prog,
                  text="⚡ Sincronizando facturas del correo",
                  font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))

        # ---- Contador grande de progreso ----
        self.lbl_progreso = ttk.Label(
            ventana_prog,
            text="⏳ Preparando...",
            font=("Segoe UI", 11),
            bootstyle="info"
        )
        self.lbl_progreso.pack(pady=5)

        # ---- Barra de progreso indeterminada (para la fase de descarga) ----
        self.barra_progreso = ttk.Progressbar(
            ventana_prog,
            mode="indeterminate",
            bootstyle="info-striped",
            length=600
        )
        self.barra_progreso.pack(pady=5, padx=20, fill="x")
        self.barra_progreso.start(15)  # animación continua

        # ---- Log ----
        frame_log = ttk.LabelFrame(ventana_prog, text="Detalle", padding=5)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        txt_log = tk.Text(frame_log, height=22, width=100,
                          font=("Consolas", 9), wrap="word")
        txt_log.pack(fill="both", expand=True, side="left")

        sb = ttk.Scrollbar(frame_log, orient="vertical", command=txt_log.yview)
        sb.pack(side="right", fill="y")
        txt_log.configure(yscrollcommand=sb.set)

        def log(msg):
            txt_log.insert(tk.END, msg + "\n")
            txt_log.see(tk.END)
            try:
                ventana_prog.update()
            except Exception:
                pass

        def actualizar_progreso(texto):
            """Actualiza el texto grande de progreso."""
            try:
                self.lbl_progreso.configure(text=texto)
                ventana_prog.update()
            except Exception:
                pass

        # ---- 4. Descargar del correo ----
        log("=" * 80)
        log("PASO 1: Descargando adjuntos del correo")
        log("=" * 80)

        carpeta_descargas = _CARPETA_DATOS / "facturas_descargadas"
        if carpeta_descargas.exists():
            for f in carpeta_descargas.iterdir():
                if f.is_file():
                    try:
                        f.unlink()
                    except Exception:
                        pass

        # ---- Detener la animación de la barra ----
        try:
            self.barra_progreso.stop()
            self.barra_progreso.configure(mode="determinate")
            self.barra_progreso["value"] = 100
        except Exception:
            pass

        descargados, errores, info = descargar_adjuntos_gmail(
            usuario=usuario,
            password_app=password,
            etiqueta=etiqueta,
            carpeta_destino=carpeta_descargas,
            solo_no_leidos=solo_no_leidos,
            filtro_remitente=filtro_remitente if filtro_remitente else None,
            dias_atras=dias_atras if dias_atras else None,
            usar_cache=True,
            callback_log=log,
            callback_progreso=actualizar_progreso,
            callback_cancelado=debe_cancelar,
        )

        # ---- 5. Verificar si hubo errores de autenticación ----
        if errores and any("AUTHENTICATIONFAILED" in str(e).upper() or
                            "LOGIN" in str(e).upper() or
                            "IMAP" in str(e).upper() or
                            "authentication" in str(e).lower()
                            for e in errores):
            log("\n" + "=" * 80)
            log("❌ ERROR DE AUTENTICACIÓN")
            log("=" * 80)
            log("Los datos de conexión al correo son incorrectos.")
            log("\nRevisa la configuración.")

            ventana_prog.update_idletasks()

            editar = messagebox.askyesno(
                "Error de autenticación",
                "No se pudo conectar al correo.\n\n"
                "Los datos de conexión son incorrectos (usuario, contraseña "
                "de aplicación, o etiqueta).\n\n"
                "¿Quieres editar la configuración ahora?"
            )
            if editar:
                u, p, e = self._pedir_credenciales_correo()
                if u:
                    messagebox.showinfo(
                        "Configuración actualizada",
                        f"Datos guardados correctamente.\n\n"
                        "Vuelve a intentar con ⚡ Sincronizar."
                    )
            return

        log(f"\n📊 Resumen de descarga:")
        log(f"   Correos encontrados: {info.get('total_correos', 0)}")
        log(f"   Correos procesados:  {info.get('procesados', 0)}")
        log(f"   Omitidos por caché:  {info.get('omitidos_cache', 0)}")
        log(f"   Omitidos por filtro: {info.get('omitidos_filtros', 0)}")
        log(f"   Archivos descargados: {len(descargados)}")
        log(f"   Log completo: {info.get('log', '')}")

        # ---- Si el usuario canceló, salir limpiamente ----
        if estado["cancelar"]:
            log("\n" + "=" * 80)
            log("⚠️ DESCARGA CANCELADA POR EL USUARIO")
            log("=" * 80)
            log(f"Se descargaron {len(descargados)} archivos antes de cancelar.")
            if descargados:
                log(f"Los archivos están en: {carpeta_descargas}")
                log("Puedes procesarlos con '📥 Leer factura' cuando quieras.")
            ventana_prog.protocol("WM_DELETE_WINDOW",
                lambda: ventana_prog.destroy())
            return

        if not descargados:
            log("\n⚠️ No se descargó ningún archivo nuevo.")
            if errores:
                log("Errores:")
                for e in errores:
                    log(f"  • {e}")
            ventana_prog.protocol("WM_DELETE_WINDOW",
                lambda: ventana_prog.destroy())
            return

        # ---- 6. Agrupar por No. de factura ----
        log("\n" + "=" * 80)
        log("PASO 2: Agrupando por No. de factura")
        log("=" * 80)

        archivos_por_correo = info.get("archivos_por_correo", {})
        grupos = agrupar_facturas_descargadas(
            carpeta_descargas,
            archivos_por_correo=archivos_por_correo
        )
        log(f"Facturas únicas detectadas: {len(grupos)}")

        # ---- 7. Preguntar qué hacer ----
        ventana_prog.grab_release()
        respuesta_procesar = self._preguntar_accion_facturas(
            len(descargados), len(grupos), carpeta_descargas
        )
        ventana_prog.grab_set()

        if respuesta_procesar == "cancelar":
            log("\n⏸️ Los archivos quedan en disco. Puedes procesarlos con '📥 Leer factura'.")
            log(f"   Carpeta: {carpeta_descargas}")
            return

        if respuesta_procesar == "solo_guardar":
            log("\n📁 Archivos guardados (sin procesar).")
            log(f"   Carpeta: {carpeta_descargas}")
            messagebox.showinfo(
                "Archivos descargados",
                f"Se descargaron {len(descargados)} archivos.\n\n"
                f"Carpeta: {carpeta_descargas}\n\n"
                "Puedes procesarlos con '📥 Leer factura'."
            )
            return

        # Preparar la barra para mostrar progreso de procesamiento
        try:
            self.barra_progreso.configure(mode="determinate", maximum=len(grupos))
            self.barra_progreso["value"] = 0
        except Exception:
            pass

        # ---- 8. Procesar todas automáticamente ----
        log("\n" + "=" * 80)
        log("PASO 3: Procesando facturas")
        log("=" * 80)

        uuids_existentes = set()
        for r in self.registros:
            ff = str(r.get("folio_fiscal", "")).strip()
            if ff:
                uuids_existentes.add(ff)

        facturas_procesadas = []
        facturas_duplicadas = []
        facturas_sin_xml = []
        facturas_con_error = []

        def _orden_grupo(item):
            clave = item[0]
            try:
                return int(str(clave).replace("grupo_", ""))
            except Exception:
                return 0

        for i, (_, files) in enumerate(sorted(grupos.items(), key=_orden_grupo), 1):
            no_factura = files.get("no_factura", "?")
            log(f"\n[{i}/{len(grupos)}] Procesando factura {no_factura}...")
            try:
                self.barra_progreso["value"] = i
                self.lbl_progreso.configure(
                    text=f"⚙️ Procesando factura {i} de {len(grupos)}: {no_factura}"
                )
                ventana_prog.update()
            except Exception:
                pass

            if not files["xml"]:
                log(f"  ⚠️ No hay XML. Se omite.")
                facturas_sin_xml.append(no_factura)
                continue

            try:
                datos = procesar_factura(
                    str(files["xml"]),
                    str(files["pdf"]) if files["pdf"] else None
                )

                if existe_valor_unico(self.registros, "no_factura",
                                       datos["no_factura"]):
                    log(f"  ⏭️ Ya existe No. de Factura {datos['no_factura']}. Se omite.")
                    facturas_duplicadas.append(datos["no_factura"])
                    continue

                ff = str(datos.get("folio_fiscal", "")).strip()
                if ff and ff in uuids_existentes:
                    log(f"  ⏭️ Ya existe Folio Fiscal {ff[:8]}... Se omite.")
                    facturas_duplicadas.append(datos["no_factura"])
                    continue

                try:
                    anio_factura = int(datos.get("anio", self._anio_cargado))
                except Exception:
                    anio_factura = self._anio_cargado

                if anio_factura != self._anio_cargado:
                    regs_anio = cargar_db(anio_factura)
                else:
                    regs_anio = self.registros

                if existe_valor_unico(regs_anio, "no_factura", datos["no_factura"]):
                    log(f"  ⏭️ Ya existe (en año {anio_factura}). Se omite.")
                    facturas_duplicadas.append(datos["no_factura"])
                    continue

                _, datos_completos = self._llenar_desde_factura(datos)

                # Aplicar QVET desde el asunto del correo (si está disponible)
                qvet_por_archivo = info.get("qvet_por_archivo", {})
                nombre_xml = Path(files["xml"]).name
                qvet_email = qvet_por_archivo.get(nombre_xml, "")
                if qvet_email:
                    self.entradas["qvet"].delete(0, tk.END)
                    self.entradas["qvet"].insert(0, qvet_email.upper())
                    datos_completos["qvet"] = qvet_email.upper()
                    log(f"  🔖 QVET asignado desde el correo: {qvet_email}")
                self._ultima_factura_xml = str(files["xml"])
                self._ultima_factura_pdf = str(files["pdf"]) if files["pdf"] else None

                self._guardar_silencioso(datos_completos)

                if ff:
                    uuids_existentes.add(ff)

                log(f"  ✅ Guardado: No. {datos['no_factura']} | "
                    f"{datos.get('centro', '?')} | "
                    f"{datos.get('mes', '?')} {datos.get('anio', '?')} | "
                    f"Total: ${datos['total']:,.2f}")
                facturas_procesadas.append(datos)

            except Exception as e:
                log(f"  ❌ Error: {e}")
                facturas_con_error.append((no_factura, str(e)))

        # ---- 9. Resumen final ----
        log("\n" + "=" * 80)
        log("RESUMEN FINAL")
        log("=" * 80)
        log(f"✅ Facturas guardadas:  {len(facturas_procesadas)}")
        log(f"⏭️ Facturas duplicadas: {len(facturas_duplicadas)}")
        log(f"⚠️ Facturas sin XML:    {len(facturas_sin_xml)}")
        log(f"❌ Facturas con error:  {len(facturas_con_error)}")

        if facturas_procesadas:
            total_procesado = sum(f.get("total", 0) for f in facturas_procesadas)
            log(f"\n💰 Total procesado: ${total_procesado:,.2f}")

            from collections import defaultdict
            resumen = defaultdict(lambda: {"n": 0, "total": 0.0})
            for f in facturas_procesadas:
                key = (f.get("centro", "?"),
                       f.get("mes", "?"),
                       f.get("anio", "?"))
                resumen[key]["n"] += 1
                resumen[key]["total"] += f.get("total", 0)

            log("\n📊 Desglose:")
            for (centro, mes, anio), data in sorted(resumen.items()):
                log(f"   • {centro:<10} {mes:<12} {anio}   "
                    f"{data['n']:>3} facturas   ${data['total']:>12,.2f}")

        if facturas_duplicadas:
            log(f"\n⏭️ Facturas duplicadas (omitidas):")
            for nf in facturas_duplicadas:
                log(f"   • {nf}")

        if facturas_sin_xml:
            log(f"\n⚠️ Facturas sin XML:")
            for nf in facturas_sin_xml:
                log(f"   • {nf}")

        if facturas_con_error:
            log(f"\n❌ Errores:")
            for nf, err in facturas_con_error:
                log(f"   • {nf}: {err}")

        log(f"\n📄 Log completo guardado en: {info.get('log', '')}")

        self._refrescar_tabla()
        self._nuevo()

        messagebox.showinfo(
            "Sincronización completa",
            f"✅ {len(facturas_procesadas)} facturas guardadas\n"
            f"⏭️ {len(facturas_duplicadas)} duplicadas\n"
            f"⚠️ {len(facturas_sin_xml)} sin XML\n"
            f"❌ {len(facturas_con_error)} con error\n\n"
            f"Log: {info.get('log', '')}"
        )

        # Reponer el comportamiento normal de la X
        try:
            ventana_prog.protocol("WM_DELETE_WINDOW", ventana_prog.destroy)
        except Exception:
            pass

    def _preguntar_accion_facturas(self, num_archivos, num_facturas, carpeta):
        """
        Muestra un diálogo personalizado preguntando qué hacer con las
        facturas descargadas.
        
        Devuelve:
          - "procesar_todas" → procesar automáticamente
          - "solo_guardar"   → solo guardar en disco
        """
        ventana = ttk.Toplevel(self)
        ventana.title("Facturas descargadas")
        ventana.transient(self)
        ventana.grab_set()
        ventana.resizable(False, False)

        # ---- Centrar la ventana ----
        ventana.update_idletasks()
        ancho = 450
        alto = 250
        x = (ventana.winfo_screenwidth() - ancho) // 2
        y = (ventana.winfo_screenheight() - alto) // 2
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

        # ---- Contenedor con padding ----
        contenedor = ttk.Frame(ventana, padding=25)
        contenedor.pack(fill="both", expand=True)

        # ---- Encabezado ----
        ttk.Label(
            contenedor,
            text="📬 Facturas descargadas",
            font=("Segoe UI", 15, "bold"),
        ).pack(pady=(0, 10))

        # ---- Resumen ----
        resumen = (
            f"Se descargaron {num_archivos} archivo(s),\n"
            f"correspondientes a {num_facturas} factura(s) única(s)."
        )
        ttk.Label(
            contenedor,
            text=resumen,
            font=("Segoe UI", 11),
            justify="center",
        ).pack(pady=(0, 5))

        # ---- Ruta de la carpeta ----
        ttk.Label(
            contenedor,
            text=f"📁 {carpeta}",
            font=("Segoe UI", 9),
            foreground="gray",
            wraplength=460,
            justify="center",
        ).pack(pady=(0, 20))

        # ---- Pregunta ----
        ttk.Label(
            contenedor,
            text="¿Qué quieres hacer?",
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(0, 15))

        # ---- Resultado ----
        resultado = {"accion": "cancelar"}

        def _elegir(accion):
            resultado["accion"] = accion
            ventana.destroy()

        # ---- Botón: Procesar todas ----
        ttk.Button(
            contenedor,
            text="✅  Procesar TODAS automáticamente",
            command=lambda: _elegir("procesar_todas"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        # Descripción del botón
        ttk.Label(
            contenedor,
            text="Llena el formulario, guarda y adjunta XML+PDF automáticamente",
            font=("Segoe UI", 8),
            foreground="gray",
        ).pack(pady=(0, 10))

        # ---- Botón: Solo guardar ----
        ttk.Button(
            contenedor,
            text="📁  Solo guardar los archivos",
            command=lambda: _elegir("solo_guardar"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        # Descripción del botón
        ttk.Label(
            contenedor,
            text="Los archivos quedan en disco para procesarlos después con '📥 Leer factura'",
            font=("Segoe UI", 8),
            foreground="gray",
        ).pack(pady=(0, 10))

        # ---- Cerrar con X = Cancelar ----
        ventana.protocol("WM_DELETE_WINDOW", lambda: _elegir("cancelar"))

        # ---- Atajos de teclado ----
        ventana.bind("<Escape>", lambda e: _elegir("cancelar"))

        ventana.wait_window()
        return resultado["accion"]

    def _preguntar_modo_descarga(self, dias_atras):
        """
        Muestra un diálogo personalizado para elegir cómo descargar.
        Devuelve:
          - "no_leidos" → solo correos no leídos
          - "todos"     → todos los correos
          - "editar"    → abrir configuración
        """
        ventana = ttk.Toplevel(self)
        ventana.title("Sincronizar facturas")
        ventana.geometry("450x250")
        ventana.resizable(False, False)
        ventana.transient(self)
        ventana.grab_set()

        # Centrar la ventana
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 450) // 2
        y = (ventana.winfo_screenheight() - 250) // 2
        ventana.geometry(f"450x250+{x}+{y}")

        # ---- Encabezado ----
        ttk.Label(ventana, text="⚡ Sincronizar facturas",
                  font=("Segoe UI", 14, "bold")).pack(pady=(20, 5))

        ttk.Label(ventana, text="¿Cómo quieres descargar?",
                  font=("Segoe UI", 10), foreground="gray").pack(pady=(0, 20))

        # ---- Botones de opción ----
        resultado = {"modo": "cancelar"}

        def _elegir(modo):
            resultado["modo"] = modo
            ventana.destroy()

        # Botón: Solo no leídos
        ttk.Button(
            ventana,
            text="📥  Solo correos NO leídos  (más rápido)",
            command=lambda: _elegir("no_leidos"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        # Botón: Todos los correos
        texto_todos = "📨  Todos los correos"
        if dias_atras:
            texto_todos += f"  (últimos {dias_atras} días)"
        else:
            texto_todos += "  (sin límite de fecha)"
        ttk.Button(
            ventana,
            text=texto_todos,
            command=lambda: _elegir("todos"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        # Separador
        ttk.Separator(ventana).pack(fill="x", padx=20, pady=10)

        # Botón: Editar configuración
        ttk.Button(
            ventana,
            text="⚙️  Editar configuración del correo",
            command=lambda: _elegir("editar"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        ventana.wait_window()
        return resultado["modo"]

    def _guardar_silencioso(self, datos):
        """
        Guarda un registro en el archivo correspondiente SIN mostrar
        diálogos de confirmación. Usado por el flujo automático.
        """
        # Normalizar fechas
        for clave, _, _, tipo in CAMPOS:
            if tipo == "date":
                datos[clave] = parse_fecha(datos[clave]).replace("-", "/")

        # Asignar ID
        datos["id"] = int(datetime.now().timestamp() * 1000)

        # Año del registro
        try:
            anio_datos = int(datos.get("anio", self._anio_cargado))
        except Exception:
            anio_datos = self._anio_cargado

        # Cargar los registros del año destino (por si el año es distinto al activo)
        if anio_datos != self._anio_cargado:
            regs_destino = cargar_db(anio_datos)
        else:
            regs_destino = self.registros

        regs_destino.append(datos)
        guardar_db(regs_destino, anio_datos)

        # Actualizar historial
        self.historial = actualizar_historial(regs_destino)

        # Crear carpeta del registro
        fecha_carpeta = parse_fecha(datos.get("fecha", ""))
        ruta = ruta_ingreso(datos["centro"], datos["anio"],
                            MESES_ES.index(datos["mes"]) + 1) / fecha_carpeta
        try:
            ruta.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # Auto-adjuntar XML y PDF
        rutas_adjuntar = []
        if self._ultima_factura_xml and Path(self._ultima_factura_xml).exists():
            rutas_adjuntar.append(self._ultima_factura_xml)
        if self._ultima_factura_pdf and Path(self._ultima_factura_pdf).exists():
            rutas_adjuntar.append(self._ultima_factura_pdf)

        if rutas_adjuntar:
            try:
                copiados, errores = adjuntar_archivos(datos, rutas_adjuntar)
                # LOG para diagnosticar
                print(f"[GUARDAR-SILENCIOSO] Copiados: {copiados}")
                if errores:
                    print(f"[GUARDAR-SILENCIOSO] Errores: {errores}")
            except Exception as e:
                print(f"[GUARDAR-SILENCIOSO] Excepción al adjuntar: {e}")

        # ---- Eliminar los archivos originales de facturas_descargadas ----
        carpeta_descargas = _CARPETA_DATOS / "facturas_descargadas"
        for ruta in rutas_adjuntar:
            try:
                p = Path(ruta)
                if p.exists() and p.parent == carpeta_descargas:
                    p.unlink()
                    print(f"[GUARDAR-SILENCIOSO] Eliminado de descargas: {p.name}")
            except Exception as e:
                print(f"[GUARDAR-SILENCIOSO] No se pudo eliminar {ruta}: {e}")

        self._ultima_factura_xml = None
        self._ultima_factura_pdf = None

        # Refrescar registros en memoria si es el mismo año
        if anio_datos == self._anio_cargado:
            self.registros = regs_destino

    def _llenar_desde_factura(self, datos):
        """
        Llena el formulario con los datos de la factura.
        Devuelve:
          - resumen (lista de strings)
          - datos_completos (dict con TODOS los campos del formulario)
        """
        # 0. Detectar centro, año y mes según la factura
        serie = datos.get("serie", "").strip()
        centro_detectado = centro_desde_serie(serie)
        if centro_detectado:
            self.var_centro.set(centro_detectado)

        fecha_factura = datos.get("fecha", "")
        mes_detectado, anio_detectado = mes_anio_desde_fecha(fecha_factura)
        if anio_detectado:
            self.var_anio.set(str(anio_detectado))
        if mes_detectado:
            self.var_mes.set(mes_detectado)

        try:
            anio_actual = int(self.var_anio.get())
        except Exception:
            anio_actual = self._anio_cargado
        if self._anio_cargado != anio_actual:
            self.registros = cargar_db(anio_actual)
            self._anio_cargado = anio_actual

        # 1. Limpiar formulario
        self._nuevo()

        # 2. Datos generales
        self.entradas["no_factura"].delete(0, tk.END)
        self.entradas["no_factura"].insert(0, str(datos["no_factura"]).upper())

        self.entradas["qvet"].delete(0, tk.END)
        self.entradas["qvet"].insert(0, str(datos.get("qvet", "")).upper())

        self.entradas["nombre"].delete(0, tk.END)
        self.entradas["nombre"].insert(0, str(datos["nombre"]).upper())

        self.entradas["rfc"].delete(0, tk.END)
        self.entradas["rfc"].insert(0, str(datos["rfc"]).upper())

        self.entradas["folio_fiscal"].delete(0, tk.END)
        self.entradas["folio_fiscal"].insert(0, datos["folio_fiscal"])

        if isinstance(self.entradas["fecha"], DateEntry):
            try:
                self.entradas["fecha"].entry.delete(0, tk.END)
                self.entradas["fecha"].entry.insert(0, datos["fecha"])
            except Exception:
                pass

        if isinstance(self.entradas["fecha_impresion"], DateEntry):
            try:
                self.entradas["fecha_impresion"].entry.delete(0, tk.END)
                self.entradas["fecha_impresion"].entry.insert(0, datos.get("fecha_impresion", ""))
            except Exception:
                pass

        # 3. Agrupar conceptos
        agrupado, detalle = agrupar_por_categoria(datos)

        mapa_campos = {
            "U": {"importe": "u_importe", "iva": "u_iva"},
            "ACCESORIOS": {"importe": "ac_importe", "iva": "ac_iva"},
            "ESTETICA": {"importe": "est_importe", "iva": "est_iva"},
            "TRANSPORTE": {"importe": "tra_importe", "iva": "tra_iva"},
            "VACUNA": {"importe": "vac_importe"},
            "CLINICA": {"importe": "cli_importe"},
            "MEDICAMENTOS": {
                "importe": "med_importe",
                "sin_iva": "med_sin_iva",
                "iva": "med_iva",
            },
            "HIGIENE": {
                "importe": "hig_importe",
                "sin_iva": "hig_sin_iva",
                "iva": "hig_iva",
                "sin_ieps_6": "hig_sin_ieps_6",
                "ieps_6": "hig_ieps_6",
                "sin_ieps_7": "hig_sin_ieps_7",
                "ieps_7": "hig_ieps_7",
            },
        }

        resumen = []
        for cat, valores in agrupado.items():
            if cat not in mapa_campos:
                continue
            for subclave, campo in mapa_campos[cat].items():
                valor = valores.get(subclave, 0.0)
                if valor == 0:
                    continue
                w = self.entradas.get(campo)
                if isinstance(w, EntryMoneda):
                    clave_det = f"{cat}__{subclave}"
                    terminos = detalle.get(clave_det, [])
                    if terminos:
                        expresion = "+".join(terminos)
                    else:
                        expresion = f"{valor:.2f}"
                    w.set_valor(round(valor, 2), expresion=expresion)
                    resumen.append(f"  {cat} → {campo}: ${valor:,.2f}")

        # 4. Tipo de pago
        pagos = datos.get("pagos", {})
        for clave in ("efectivo", "tc", "td", "cheque", "transfer", "vale"):
            valor = pagos.get(clave, 0)
            if valor <= 0:
                continue
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                w.set_valor(round(valor, 2), expresion=f"{valor:.2f}")
                resumen.append(f"  {clave.upper()}: ${valor:,.2f}")

        # 5. Recalcular
        self._recalcular_total()

        # 6. Leer TODOS los campos del formulario para tener el dict completo
        datos_completos = self._leer_form()
        # Preservar los pagos del XML
        datos_completos["pagos"] = pagos

        return resumen, datos_completos

    def _actualizar_titulo(self):
        try:
            self.title(
                f"Sistema de Ingresos — {self.var_centro.get()} "
                f"{self.var_mes.get()} {self.var_anio.get()}"
            )
        except Exception:
            pass


    # ---------------- TABLA ----------------
    def _ver_reportes(self):
        """
        Muestra un árbol años → meses → centros.
        Al hacer doble clic en cualquier nodo, se cambian los selectores
        del formulario para reflejar exactamente ese reporte.
        """
        from collections import defaultdict

        # ============================================================
        # Recolectar datos
        # ============================================================
        # Estructura: {anio: {mes: {centro: [registros]}}}
        datos = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        archivos = sorted(_CARPETA_DATOS.glob("registros_ingresos_*.json"))
        if not archivos:
            messagebox.showinfo("Reportes", "Todavía no hay registros guardados.")
            return

        for archivo in archivos:
            try:
                anio_str = archivo.stem.replace("registros_ingresos_", "")
                anio = int(anio_str)
            except Exception:
                continue
            regs = cargar_db(anio)
            for r in regs:
                mes = r.get("mes", "sin mes")
                centro = r.get("centro", "sin centro")
                datos[anio][mes][centro].append(r)

        if not datos:
            messagebox.showinfo("Reportes", "Todavía no hay registros guardados.")
            return

        # ============================================================
        # Crear la ventana
        # ============================================================
        ventana = ttk.Toplevel(self)
        ventana.title("📊 Reportes disponibles")
        ventana.geometry("600x400")
        ventana.transient(self)
        ventana.resizable(False, True)
        ventana.minsize(None,None)

        # --- Encabezado ---
        header = ttk.Frame(ventana)
        header.pack(fill="x", padx=10, pady=8)
        ttk.Label(header,
                  text="Doble clic (o selecciona + botón) para ir a un reporte:",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")

        # --- Árbol ---
        frame_arbol = ttk.Frame(ventana)
        frame_arbol.pack(fill="both", expand=True, padx=10, pady=5)

        columnas = ("registros", "total", "ultimo_folio")
        arbol = ttk.Treeview(frame_arbol, columns=columnas, show="tree headings",
                             height=10)
        arbol.heading("#0", text="Año / Mes / Centro", anchor="w")
        arbol.heading("registros", text="Registros", anchor="center")
        arbol.heading("total", text="Total", anchor="e")
        arbol.heading("ultimo_folio", text="Último folio", anchor="center")

        arbol.column("#0", width=150, minwidth=150, anchor="w")
        arbol.column("registros", width=50, anchor="center")
        arbol.column("total", width=100, anchor="e")
        arbol.column("ultimo_folio", width=50, anchor="center")

        arbol.pack(fill="both", expand=True, side="left")

        sb = ttk.Scrollbar(frame_arbol, orient="vertical", command=arbol.yview)
        sb.pack(side="right", fill="y")
        arbol.configure(yscrollcommand=sb.set)

        # --- Panel de detalle ---
        panel = ttk.LabelFrame(ventana, text="Detalle del reporte seleccionado")
        panel.pack(fill="x", padx=10, pady=5)

        lbl_detalle = ttk.Label(panel, text="Selecciona un nodo del árbol",
                                font=("Segoe UI", 10), justify="left")
        lbl_detalle.pack(anchor="w", padx=10, pady=8)

        # --- Barra de botones ---
        fr = ttk.Frame(ventana)
        fr.pack(pady=8)

        # Mapa de metadatos: nodo → (anio, mes, centro)
        metadatos = {}

        def _ir_al_nodo(item):
            """Cambia los selectores del formulario al reporte del nodo."""
            md = metadatos.get(item)
            if not md:
                return
            anio, mes, centro = md

            # Cambiar año primero (esto recarga registros del año)
            self.var_anio.set(str(anio))
            if mes:
                self.var_mes.set(mes)
            if centro:
                self.var_centro.set(centro)

            # Recargar y refrescar
            self.registros = cargar_db(anio)
            self._anio_cargado = anio
            self._refrescar_tabla()
            self._actualizar_titulo()
            ventana.destroy()

        def _ir_a_seleccionado():
            sel = arbol.selection()
            if not sel:
                messagebox.showinfo("Reportes", "Selecciona un reporte.")
                return
            _ir_al_nodo(sel[0])

        # ============================================================
        # Poblar árbol
        # ============================================================
        def _orden_mes(m):
            try:
                return MESES_ES.index(m)
            except ValueError:
                return 99

        for anio in sorted(datos.keys(), reverse=True):
            meses_dict = datos[anio]

            # Totales del año
            total_anio = sum(
                len(regs)
                for mes_dict in meses_dict.values()
                for regs in mes_dict.values()
            )
            monto_anio = sum(
                sum(r.get("total", 0) for r in regs)
                for mes_dict in meses_dict.values()
                for regs in mes_dict.values()
            )

            nodo_anio = arbol.insert(
                "", "end",
                text=f"📅 {anio}",
                values=(f"{total_anio} registros", f"${monto_anio:,.2f}", ""),
                open=False,
                tags=("anio",)
            )
            # Si haces clic en un año, elige el primer mes/centro
            primer_mes = sorted(meses_dict.keys(), key=_orden_mes)[0]
            primer_centro = sorted(meses_dict[primer_mes].keys())[0]
            metadatos[nodo_anio] = (anio, primer_mes, primer_centro)

            # Meses
            for mes in sorted(meses_dict.keys(), key=_orden_mes):
                centros_dict = meses_dict[mes]
                total_mes = sum(len(r) for r in centros_dict.values())
                monto_mes = sum(
                    sum(reg.get("total", 0) for reg in regs)
                    for regs in centros_dict.values()
                )

                nodo_mes = arbol.insert(
                    nodo_anio, "end",
                    text=f"📆 {mes.capitalize()}",
                    values=(f"{total_mes} registros", f"${monto_mes:,.2f}", ""),
                    open=False,
                    tags=("mes",)
                )
                # Si haces clic en un mes, elige el primer centro
                primer_centro_mes = sorted(centros_dict.keys())[0]
                metadatos[nodo_mes] = (anio, mes, primer_centro_mes)

                # Centros
                for centro in sorted(centros_dict.keys()):
                    regs = centros_dict[centro]
                    n = len(regs)
                    monto = sum(r.get("total", 0) for r in regs)
                    ultimo_folio = ""
                    if regs:
                        ultimo = max(regs, key=lambda x: x.get("id", 0))
                        ultimo_folio = str(ultimo.get("no_factura", ""))

                    nodo_centro = arbol.insert(
                        nodo_mes, "end",
                        text=f"  🏢 {centro}",
                        values=(f"{n} facturas", f"${monto:,.2f}", ultimo_folio),
                        tags=("centro",)
                    )
                    metadatos[nodo_centro] = (anio, mes, centro)

        # ============================================================
        # Eventos
        # ============================================================
        def _al_seleccionar(event=None):
            sel = arbol.selection()
            if not sel:
                return
            item = sel[0]
            tags = arbol.item(item, "tags")
            md = metadatos.get(item)
            if not md:
                return
            anio, mes, centro = md

            if "anio" in tags:
                lineas = [f"Año {anio}", ""]
                meses_dict = datos.get(anio, {})
                for m in sorted(meses_dict.keys(), key=_orden_mes):
                    centros_dict = meses_dict[m]
                    n = sum(len(r) for r in centros_dict.values())
                    t = sum(sum(x.get("total", 0) for x in r)
                            for r in centros_dict.values())
                    lineas.append(
                        f"  • {m.capitalize():<15} {n:>3} facturas   ${t:>12,.2f}"
                    )
                lbl_detalle.configure(text="\n".join(lineas))

            elif "mes" in tags:
                lineas = [f"{mes.capitalize()} {anio}", ""]
                centros_dict = datos.get(anio, {}).get(mes, {})
                for c in sorted(centros_dict.keys()):
                    regs = centros_dict[c]
                    n = len(regs)
                    t = sum(x.get("total", 0) for x in regs)
                    lineas.append(
                        f"  • {c:<12} {n:>3} facturas   ${t:>12,.2f}"
                    )
                lbl_detalle.configure(text="\n".join(lineas))

            elif "centro" in tags:
                lineas = [f"{centro} — {mes.capitalize()} {anio}", ""]
                regs = datos.get(anio, {}).get(mes, {}).get(centro, [])
                if regs:
                    primeras = sorted(regs, key=lambda x: x.get("id", 0))[:5]
                    for r in primeras:
                        lineas.append(
                            f"  • Factura {r.get('no_factura', '?'):<8} "
                            f"{r.get('fecha', ''):<12} "
                            f"${r.get('total', 0):>10,.2f}"
                        )
                    if len(regs) > 5:
                        lineas.append(f"  ... y {len(regs) - 5} más")
                lbl_detalle.configure(text="\n".join(lineas))

        arbol.bind("<<TreeviewSelect>>", _al_seleccionar)
        arbol.bind("<Double-Button-1>", lambda e: _ir_a_seleccionado())
        arbol.bind("<Return>", lambda e: _ir_a_seleccionado())

        # Expandir el primer año al abrir
        hijos = arbol.get_children()
        if hijos:
            arbol.item(hijos[0], open=True)

    def _refrescar_tabla(self):
        """Carga los registros del año activo y filtra por centro/mes."""
        try:
            anio_activo = int(self.var_anio.get())
        except Exception:
            anio_activo = datetime.now().year

        # Si cambió el año, recargar desde el archivo correspondiente
        if self._anio_cargado != anio_activo:
            self.registros = cargar_db(anio_activo)
            self._anio_cargado = anio_activo

        # ---- Limpiar tabla ----
        for i in self.tabla.get_children():
            self.tabla.delete(i)

        # ---- Filtrar y mostrar (SIN autoajuste) ----
        mes_activo = self.var_mes.get()
        centro_activo = self.var_centro.get()

        filtrados = [
            r for r in self.registros
            if r.get("centro") == centro_activo
            and r.get("anio") == anio_activo
            and r.get("mes") == mes_activo
        ]

        def clave_orden(r):
            n = obtener_no_factura_numerico(r.get("no_factura", ""))
            return (n is None, n or 0, str(r.get("no_factura", "")))
        filtrados.sort(key=clave_orden)

        for r in filtrados:
            try:
                n_adj = len(archivos_del_registro(r))
            except Exception:
                n_adj = 0
            self.tabla.insert("", "end", iid=r["id"],
                values=(r.get("no_factura", ""), r.get("fecha", ""),
                    r.get("nombre", ""), r.get("rfc", ""),
                    formatear_moneda(r.get("total", 0)),
                    formatear_moneda(r.get("efectivo", 0)),
                    formatear_moneda(r.get("tc", 0)),
                    formatear_moneda(r.get("td", 0)),
                    formatear_moneda(r.get("cheque", 0)),
                    formatear_moneda(r.get("transfer", 0)),
                    r.get("folio_fiscal", ""),
                    f"📎 {n_adj}" if n_adj else ""))

    # ---------------- ADJUNTOS ----------------
    def _adjuntar_factura(self):
        reg = None
        if self.id_actual is not None:
            reg = next((r for r in self.registros if r["id"] == self.id_actual), None)
        if reg is None:
            sel = self.tabla.selection()
            if sel:
                reg = next((r for r in self.registros if r["id"] == int(sel[0])), None)
        if reg is None:
            messagebox.showinfo("Adjuntar", "Guarda primero el registro o selecciona uno.")
            return
        no_factura = str(reg.get("no_factura", "")).strip()
        if not no_factura:
            messagebox.showwarning("Falta info", "El registro no tiene No. de Factura.")
            return
        rutas = filedialog.askopenfilenames(
            title=f"Seleccionar factura para {no_factura}",
            filetypes=[("Facturas", "*.pdf *.xml *.PDF *.XML"),
                       ("PDF", "*.pdf"), ("XML", "*.xml"),
                       ("Todos", "*.*")])
        if not rutas:
            return
        carpeta = carpeta_destino_factura(reg)
        existentes = []
        for ruta in rutas:
            destino = carpeta / nombre_destino(no_factura, ruta)
            if destino.exists():
                existentes.append(destino.name)
        if existentes:
            if not messagebox.askyesno("Reemplazar",
                                       "Ya existen:\n" + "\n".join(existentes) +
                                       "\n\n¿Reemplazar?"):
                return
        copiados, errores = adjuntar_archivos(reg, rutas)
        lineas = []
        if copiados:
            lineas.append(f"✅ {len(copiados)} archivo(s) adjuntado(s):")
            for _, d in copiados:
                lineas.append(f"   • {d.name}")
            lineas.append(f"\nCarpeta:\n{carpeta}")
        if errores:
            lineas.append(f"\n⚠️ Errores:")
            for o, e in errores:
                lineas.append(f"   • {o}: {e}")
        messagebox.showinfo("Adjuntar", "\n".join(lineas))
        self._refrescar_tabla()

    def _ver_adjuntos(self):
        reg = None
        if self.id_actual is not None:
            reg = next((r for r in self.registros if r["id"] == self.id_actual), None)
        if reg is None:
            sel = self.tabla.selection()
            if sel:
                reg = next((r for r in self.registros if r["id"] == int(sel[0])), None)
        if reg is None:
            messagebox.showinfo("Ver adjuntos", "Selecciona un registro.")
            return
        adjuntos = archivos_del_registro(reg)
        if not adjuntos:
            if messagebox.askyesno("Sin adjuntos",
                                   "No tiene adjuntos. ¿Adjuntar ahora?"):
                self._adjuntar_factura()
            return
        ventana = ttk.Toplevel(self)
        ventana.title(f"Adjuntos de {reg.get('no_factura', '')}")
        ventana.geometry("250x250")
        ventana.resizable(False, False)
        ventana.transient(self)
        ttk.Label(ventana, text=f"Adjuntos de {reg.get('no_factura', '')}:",
                  font=("Segoe UI", 11, "bold")).pack(pady=8)
        frame = ttk.Frame(ventana)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        lb = tk.Listbox(frame, font=("Consolas", 10))
        lb.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.configure(yscrollcommand=sb.set)
        for a in adjuntos:
            lb.insert(tk.END, a.name)

        def abrir_archivo():
            sel_lb = lb.curselection()
            if not sel_lb:
                return
            self._abrir_archivo(adjuntos[sel_lb[0]])

        def abrir_carpeta():
            carpeta = carpeta_de_registro(reg)
            if carpeta and carpeta.exists():
                self._abrir_carpeta(carpeta)

        lb.bind("<Double-Button-1>", lambda e: abrir_archivo())
        fr = ttk.Frame(ventana)
        fr.pack(pady=8)
        ttk.Button(fr, text="📎 Adjuntar más",
                   command=lambda: (ventana.destroy(), self._adjuntar_factura()),
                   bootstyle="info-outline").pack(side="left", padx=4)

    @staticmethod
    def _abrir_archivo(ruta):
        try:
            if sys.platform.startswith("win"):
                os.startfile(ruta)
            elif sys.platform == "darwin":
                os.system(f'open "{ruta}"')
            else:
                os.system(f'xdg-open "{ruta}"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir:\n{e}")

    def _abrir_carpeta_ingreso(self):
        anio = int(self.var_anio.get())
        mes = MESES_ES.index(self.var_mes.get()) + 1
        ruta = ruta_ingreso(self.var_centro.get(), anio, mes)
        ruta.mkdir(parents=True, exist_ok=True)
        self._abrir_carpeta(ruta)

    @staticmethod
    def _abrir_carpeta(ruta):
        if sys.platform.startswith("win"):
            os.startfile(ruta)
        elif sys.platform == "darwin":
            os.system(f'open "{ruta}"')
        else:
            os.system(f'xdg-open "{ruta}"')

    def _toggle_tabla(self):
        if self.frame_tabla.winfo_ismapped():
            self.frame_tabla.pack_forget()
            self.btn_toggle_tabla.configure(text="👁️ Mostrar tabla")
        else:
            self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)
            self.btn_toggle_tabla.configure(text="👁️ Ocultar tabla")

    def _configurar_estilos(self):
        style = ttk.Style()
        oscuro = tema_es_oscuro()
        color_texto = "#ffffff" if oscuro else "#000000"
        color_fondo = "#2b2b2b" if oscuro else "#ffffff"

        try:
            style.configure("Custom.TEntry",
                            foreground=color_texto,
                            fieldbackground=color_fondo,
                            background=color_fondo)
            style.map("Custom.TEntry",
                      foreground=[("disabled", "#888888"),
                                  ("readonly", color_texto)],
                      fieldbackground=[("readonly", color_fondo),
                                       ("disabled", color_fondo)],
                      background=[("readonly", color_fondo)])
        except Exception as e:
            print(f"[_configurar_estilos] Error: {e}")

    def _elegir_tema(self):
        """Abre una ventana para elegir el tema visual de la aplicación."""
        import ttkbootstrap as _ttk

        try:
            temas = sorted(_ttk.Style().theme_names())
        except Exception:
            temas = ["superhero", "darkly", "cyborg", "flatly", "litera", "minty"]

        ventana = ttk.Toplevel(self)
        ventana.title("🎨 Elegir tema")
        ventana.geometry("300x400")
        ventana.transient(self)
        ventana.grab_set()
        ventana.resizable(False, False)
        ventana.minsize(300, 400)

        # ---- Encabezado ----
        ttk.Label(ventana, text="Selecciona un tema:",
                  font=("Segoe UI", 13, "bold")).pack(pady=(15, 5))

        ttk.Label(ventana,
                  text="Haz clic en un tema para previsualizarlo.\n"
                       "Presiona 'Aplicar y guardar' para conservarlo.",
                  font=("Segoe UI", 9),
                  foreground="gray",
                  justify="center").pack(pady=(0, 10))

        # ---- Contenedor con scroll ----
        cont = ttk.Frame(ventana)
        cont.pack(fill="both", expand=True, padx=15, pady=5)

        # Treeview (tabla) como lista de temas
        tree = ttk.Treeview(cont, columns=("tema",), show="headings",
                            height=12, selectmode="browse")
        tree.heading("tema", text="TEMA")
        tree.column("tema", width=200, anchor="w")

        # Scrollbar
        sb = ttk.Scrollbar(cont, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Llenar la lista
        for tema in temas:
            tree.insert("", "end", iid=tema, values=(tema,))

        # Seleccionar el tema actual
        if TEMA in temas:
            tree.selection_set(TEMA)
            tree.see(TEMA)

        # ---- Scroll con la rueda del mouse ----
        def _on_mousewheel(event):
            if sys.platform == "darwin":
                delta = -1 * event.delta
            elif sys.platform.startswith("win"):
                delta = -1 * (event.delta // 120)
            else:
                delta = -1 if event.num == 5 else 1
            tree.yview_scroll(int(delta), "units")

        def _bind_wheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel, add="+")
            widget.bind("<Button-4>", _on_mousewheel, add="+")
            widget.bind("<Button-5>", _on_mousewheel, add="+")
            for h in widget.winfo_children():
                _bind_wheel(h)

        _bind_wheel(ventana)

        # ---- Variable para el tema seleccionado ----
        var_tema = tk.StringVar(value=TEMA)

        def _preview(tema):
            try:
                _ttk.Style().theme_use(tema)
                global TEMA
                TEMA = tema
                refrescar_colores()
                self._configurar_estilos()
                self._repintar_todo()
                self._repintar_sidebar()
            except Exception as e:
                print(f"[_preview] Error: {e}")

        def _al_seleccionar(event=None):
            """Se ejecuta al hacer clic en un tema de la lista."""
            sel = tree.selection()
            if not sel:
                return
            tema = sel[0]
            var_tema.set(tema)
            _preview(tema)
            lbl_actual.configure(text=f"Tema actual: {tema}")

        tree.bind("<<TreeviewSelect>>", _al_seleccionar)

        # ---- Etiqueta con el tema actual ----
        lbl_actual = ttk.Label(ventana, text=f"Tema actual: {TEMA}",
                                font=("Segoe UI", 10, "bold"),
                                bootstyle="info")
        lbl_actual.pack(pady=8)

        # ---- Botones ----
        def _confirmar():
            nuevo_tema = var_tema.get()
            CONFIG["tema"] = nuevo_tema
            guardar_config(CONFIG)
            messagebox.showinfo(
                "Tema guardado",
                f"Tema cambiado a: {nuevo_tema}\n\n"
                "El cambio ya está aplicado."
            )
            ventana.destroy()

        def _restaurar():
            tema_defecto = "superhero"
            var_tema.set(tema_defecto)
            if tema_defecto in temas:
                tree.selection_set(tema_defecto)
                tree.see(tema_defecto)
            _preview(tema_defecto)
            lbl_actual.configure(text=f"Tema actual: {tema_defecto}")

        fr_btn = ttk.Frame(ventana)
        fr_btn.pack(pady=12)
        ttk.Button(fr_btn, text="✅ Aplicar y guardar",
                   command=_confirmar,
                   bootstyle="info-outline").pack(side="left", padx=5)
        ttk.Button(fr_btn, text="↺ Restaurar",
                   command=_restaurar,
                   bootstyle="info-outline").pack(side="left", padx=5)

    def _repintar_sidebar(self):
        """Aplica los colores del tema actual a todos los widgets del sidebar."""
        self.colores_sidebar = obtener_colores_sidebar()
        c = self.colores_sidebar

        # Contenedores principales
        self.sidebar.configure(bg=c["bg"])
        self.header_sidebar.configure(bg=c["bg"])
        self.separador_sidebar.configure(bg=c["separador"])
        self.lbl_version.configure(bg=c["bg"], fg=c["version"])

        # Encabezado y hamburguesa del header
        self.lbl_logo_texto.configure(bg=c["bg"], fg=c["fg"])
        self.btn_hamburguesa_header.configure(bg=c["bg"], fg=c["fg"])

        # Botones del menú
        for btn in self._botones_menu:
            btn["frame"].configure(bg=c["bg"])
            btn["icono"].configure(bg=c["bg"], fg=c["fg"])
            btn["texto"].configure(bg=c["bg"], fg=c["fg_suave"])

    def _repintar_todo(self):
        for w in self.entradas.values():
            if isinstance(w, EntryMoneda):
                w._pintar()

        color_texto = COLORES["texto_normal"]
        color_fondo = COLORES["fondo_entry"]

        for w in self.entradas.values():
            if isinstance(w, EntryAutoComplete):
                try:
                    w.configure(foreground=color_texto, background=color_fondo)
                except Exception:
                    pass

        self._validar_no_factura_visual()
        self._validar_qvet_visual()
        self.update_idletasks()

    # ---------------- EXCEL ----------------
    def _generar_excel(self):
        if not self.registros:
            messagebox.showwarning("Sin datos", "No hay registros.")
            return
        anio = int(self.var_anio.get())
        mes_idx = MESES_ES.index(self.var_mes.get()) + 1
        mes_nombre = self.var_mes.get()
        filtrados = [r for r in self.registros
                     if r.get("anio") == anio and r.get("mes") == mes_nombre
                     and r.get("centro") == self.var_centro.get()]
        if not filtrados:
            messagebox.showwarning("Sin datos",
                                   f"No hay registros para {self.var_centro.get()} - {mes_nombre} {anio}.")
            return
        carpeta = ruta_deposito(anio, mes_idx)
        carpeta.mkdir(parents=True, exist_ok=True)
        nombre = f"Resumen {mes_nombre} {anio}.xlsx"
        ruta_xlsx = carpeta / nombre
        try:
            self._escribir_excel(ruta_xlsx, filtrados)
        except Exception as e:
            messagebox.showerror("Error al crear Excel", str(e))
            return
        messagebox.showinfo("Excel generado",
                            f"Archivo:\n{ruta_xlsx}\n\nRegistros: {len(filtrados)}")
        self._abrir_carpeta(carpeta)

    def _escribir_excel(self, ruta, regs):
        # ---- Obtener mes y año para el nombre de la hoja ----
        if regs:
            # Tomar el primero registro como referencia
            mes_actual = regs[0].get("mes", "")
            anio_actual = regs[0].get("anio", "")
        else:
            mes_actual = MESES_ES[datetime.now().month - 1]
            anio_actual = datetime.now().year

        # Si por alguna razón el registro no tiene mes/año, usar los del form
        if not mes_actual:
            try:
                mes_actual = self.var_mes.get()
            except Exception:
                mes_actual = MESES_ES[datetime.now().month - 1]
        if not anio_actual:
            try:
                anio_actual = int(self.var_anio.get())
            except Exception:
                anio_actual = datetime.now().year

        # Capitalizar el mes
        nombre_hoja = f"{str(mes_actual).capitalize()} {anio_actual}"

        wb = Workbook()
        ws = wb.active
        ws.title = nombre_hoja[:31]   # por seguridad (máximo 31 caracteres)

        thin = Side(border_style="thin", color="808080")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        centro = Alignment(horizontal="center", vertical="center", wrap_text=True)
        bold_white = Font(bold=True, color="FFFFFF", size=11)
        bold_dark = Font(bold=True, color="000000", size=10)
        formato_moneda = '"$"#,##0.00'
        formato_fecha = "DD/MM/YYYY"

        COLORES_SECCION = {
            "GENERAL": "1F4E3D",
            "U": "2E5A88",
            "ACCESORIOS": "7B3F00",
            "MEDICAMENTOS": "8B1A1A",
            "HIGIENE": "4B6B00",
            "ESTETICA": "6A1B9A",
            "TRANSPORTE": "0D47A1",
            "PENSION": "B85C00",
            "VACUNA": "00695C",
            "CLINICA": "37474F",
            "TOTAL": "000000",
            "TIPO DE PAGO": "4A148C",
            "CONTROL": "455A64",
        }
        fill_total = PatternFill("solid", fgColor="FFD966")

        columnas = {
            "A":  ("No. DE FACTURA",              "GENERAL",       "text"),
            "B":  ("QVET",                        "GENERAL",       "text"),
            "C":  ("FECHA DE EMISIÓN",            "GENERAL",       "date"),
            "D":  ("NOMBRE",                      "GENERAL",       "text"),
            "E":  ("RFC",                         "GENERAL",       "text"),
            "F":  ("IMPORTE",                     "U",             "money"),
            "G":  ("IVA (16%)",                   "U",             "money"),
            "H":  ("IMPORTE",                     "ACCESORIOS",    "money"),
            "I":  ("IVA (16%)",                   "ACCESORIOS",    "money"),
            "J":  ("IMPORTE (sin IVA)",           "MEDICAMENTOS",  "money"),
            "K":  ("SIN IVA",                     "MEDICAMENTOS",  "money"),
            "L":  ("IVA (16%)",                   "MEDICAMENTOS",  "money"),
            "M":  ("IMPORTE (sin IVA)",           "HIGIENE",       "money"),
            "N":  ("SIN IVA",                     "HIGIENE",       "money"),
            "O":  ("IVA (16%)",                   "HIGIENE",       "money"),
            "P":  ("SIN IEPS 6%",                 "HIGIENE",       "money"),
            "Q":  ("IEPS (6%)",                   "HIGIENE",       "money"),
            "R":  ("SIN IEPS 7%",                 "HIGIENE",       "money"),
            "S":  ("IEPS (7%)",                   "HIGIENE",       "money"),
            "T":  ("IMPORTE",                     "ESTETICA",      "money"),
            "U":  ("IVA (16%)",                   "ESTETICA",      "money"),
            "V":  ("IMPORTE",                     "TRANSPORTE",    "money"),
            "W":  ("IVA (16%)",                   "TRANSPORTE",    "money"),
            "X":  ("IMPORTE",                     "PENSION",       "money"),
            "Y":  ("IVA (16%)",                   "PENSION",       "money"),
            "Z":  ("IMPORTE",                     "VACUNA",        "money"),
            "AA": ("IMPORTE",                     "CLINICA",       "money"),
            "AB": ("TOTAL",                       "TOTAL",         "money"),
            # TIPO DE PAGO (5 columnas: efectivo, tarjeta, cheque, transf, vale)
            "AC": ("EFECTIVO",                    "TIPO DE PAGO",  "money"),
            "AD": ("TARJETA",                     "TIPO DE PAGO",  "money"),        # suma TC + TD
            "AE": ("CHEQUE",                      "TIPO DE PAGO",  "money"),
            "AF": ("TRANSF.",                     "TIPO DE PAGO",  "money"),
            "AG": ("VALE",                        "TIPO DE PAGO",  "money"),
            # CONTROL (7 columnas, todas mantienen encabezado pero algunas sin datos)
            "AH": ("FECHA DE TIMBRADO",                "CONTROL",       "date"),
            "AI": ("FECHA FICHA DE DEPÓSITO",           "CONTROL",       "date"),   # sin dato
            "AJ": ("MONTO DE FICHA DE DEPOSITO",        "CONTROL",       "money"),  # mismo que EFECTIVO
            "AK": ("FECHA SANTANDER TARJETA",           "CONTROL",       "date"),   # sin dato
            "AL": ("EDO. CUENTA SANTANDER DEBITO",      "CONTROL",       "money"),  # TD
            "AM": ("EDO. CUENTA SANTANDER CREDITO",     "CONTROL",       "money"),  # TC
            "AN": ("FECHA SANTANDER TRANSFERENCIA",     "CONTROL",       "date"),   # sin dato
            "AO": ("TRANSFERENCIA SANTANDER",           "CONTROL",       "money"),  # mismo que TRANSFER
            "AP": ("FOLIO FISCAL",                      "CONTROL",       "text"),
        }

        mapa_claves = {
            "A": "no_factura", "B": "qvet", "C": "fecha",
            "D": "nombre", "E": "rfc",
            "F": "u_importe", "G": "u_iva",
            "H": "ac_importe", "I": "ac_iva",
            "J": "med_importe", "K": "med_sin_iva", "L": "med_iva",
            "M": "hig_importe", "N": "hig_sin_iva", "O": "hig_iva",
            "P": "hig_sin_ieps_6", "Q": "hig_ieps_6",
            "R": "hig_sin_ieps_7", "S": "hig_ieps_7",
            "T": "est_importe", "U": "est_iva",
            "V": "tra_importe", "W": "tra_iva",
            "X": "pen_importe", "Y": "pen_iva",
            "Z": "vac_importe",
            "AA": "cli_importe",
            "AB": "total",
            "AC": "efectivo",
            "AD": "__tarjeta__",         # marcador especial (suma TC + TD)
            "AE": "cheque",
            "AF": "transfer",
            "AG": "vale",
            "AH": "fecha_impresion",
            "AI": "",                    # FECHA FICHA DE DEPÓSITO (sin dato)
            "AJ": "__efectivo_dup__",    # MONTO FICHA = EFECTIVO
            "AK": "",                    # FECHA SANTANDER TARJETA (sin dato)
            "AL": "td",                  # EDO SANTANDER DEBITO = TD
            "AM": "tc",                  # EDO SANTANDER CREDITO = TC
            "AN": "",                    # FECHA SANTANDER TRANSFERENCIA (sin dato)
            "AO": "__transfer_dup__",    # TRANSFERENCIA SANTANDER = TRANSFER
            "AP": "folio_fiscal",
        }

        FORMULAS_AUTO = {
            "G":  "=F{r}*0.16",
            "I":  "=H{r}*0.16",
            "L":  "=K{r}*0.16",
            "O":  "=N{r}*0.16",
            "Q":  "=P{r}*0.06",
            "S":  "=R{r}*0.07",
            "U":  "=T{r}*0.16",
            "W":  "=V{r}*0.16",
            "Y":  "=X{r}*0.16",
            "AB": "=AC{r}+AD{r}+AE{r}+AF{r}+AG{r}",
        }

        grupos = [
            (6,  7,  "U"),
            (8,  9,  "ACCESORIOS"),
            (10, 12, "MEDICAMENTOS"),
            (13, 19, "HIGIENE"),
            (20, 21, "ESTETICA"),
            (22, 23, "TRANSPORTE"),
            (24, 25, "PENSION"),
            (26, 26, "VACUNA"),
            (27, 27, "CLINICA"),
            (28, 28, "TOTAL"),
            (29, 33, "TIPO DE PAGO"),   # 5 columnas (AC..AG)
            (34, 42, "CONTROL"),        # 9 columnas (AH..AP)
        ]
        
        for ini, fin, texto in grupos:
            if ini != fin:
                ws.merge_cells(start_row=1, start_column=ini,
                               end_row=1, end_column=fin)
            c = ws.cell(row=1, column=ini, value=texto)
            c.font = bold_dark
            c.alignment = centro
            for col in range(ini, fin + 1):
                ws.cell(row=1, column=col).border = border
                ws.cell(row=1, column=col).alignment = centro

        for letra, (titulo, seccion, tipo) in columnas.items():
            c = ws[f"{letra}2"]
            c.value = titulo
            c.font = bold_white
            c.fill = PatternFill("solid", fgColor=COLORES_SECCION[seccion])
            c.alignment = centro
            c.border = border

        fila = 3
        for r in regs:
            # Calcular valores especiales primero
            valor_tc = float(r.get("tc", 0) or 0)
            valor_td = float(r.get("td", 0) or 0)
            valor_tarjeta = valor_tc + valor_td
            valor_efectivo = float(r.get("efectivo", 0) or 0)
            valor_transfer = float(r.get("transfer", 0) or 0)

            for letra, (titulo, seccion, tipo) in columnas.items():
                clave = mapa_claves[letra]
                c = ws[f"{letra}{fila}"]
                c.border = border

                # ---- Casos especiales ----
                # Buscar letras de columnas auxiliares (se hace una vez por celda)
                def _buscar_letra(clave_buscada):
                    for letra_temp, clave_temp in mapa_claves.items():
                        if clave_temp == clave_buscada:
                            return letra_temp
                    return None

                if clave == "__tarjeta__":
                    # TARJETA = TC + TD (fórmula)
                    letra_tc = _buscar_letra("tc")
                    letra_td = _buscar_letra("td")
                    if letra_tc and letra_td:
                        c.value = f"={letra_tc}{fila}+{letra_td}{fila}"
                        c.number_format = formato_moneda
                    elif valor_tarjeta > 0:
                        c.value = valor_tarjeta
                        c.number_format = formato_moneda
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    continue

                if clave == "__efectivo_dup__":
                    # MONTO DE FICHA = EFECTIVO (fórmula)
                    letra_efectivo = _buscar_letra("efectivo")
                    if letra_efectivo:
                        c.value = f"={letra_efectivo}{fila}"
                        c.number_format = formato_moneda
                    elif valor_efectivo > 0:
                        c.value = valor_efectivo
                        c.number_format = formato_moneda
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    continue

                if clave == "__transfer_dup__":
                    # TRANSFERENCIA SANTANDER = TRANSF. (fórmula)
                    letra_transfer = _buscar_letra("transfer")
                    if letra_transfer:
                        c.value = f"={letra_transfer}{fila}"
                        c.number_format = formato_moneda
                    elif valor_transfer > 0:
                        c.value = valor_transfer
                        c.number_format = formato_moneda
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    continue

                if clave == "":
                    # Campo sin dato (solo encabezado)
                    c.alignment = Alignment(horizontal="center", vertical="center")
                    continue

                # ---- Casos normales ----
                valor = r.get(clave, 0 if tipo == "money" else "")
                expresion = r.get(f"{clave}__expr", "")

                if tipo == "money":
                    if expresion:
                        c.value = f"={expresion}"
                    elif letra in FORMULAS_AUTO:
                        c.value = FORMULAS_AUTO[letra].format(r=fila)
                    else:
                        c.value = float(valor or 0)
                    c.number_format = formato_moneda
                    c.alignment = Alignment(horizontal="right", vertical="center")

                elif tipo == "date":
                    if valor:
                        try:
                            fecha_dt = datetime.strptime(str(valor).strip(), "%d/%m/%Y")
                            c.value = fecha_dt
                            c.number_format = formato_fecha
                        except (ValueError, TypeError):
                            c.value = valor
                    c.alignment = Alignment(horizontal="center", vertical="center")

                else:
                    c.value = valor
                    c.alignment = Alignment(horizontal="left", vertical="center")

            fila += 1

        fila_total = fila
        c_tot = ws.cell(row=fila_total, column=1, value="TOTALES")
        c_tot.font = bold_dark
        c_tot.fill = fill_total
        c_tot.alignment = centro
        c_tot.border = border
        ws.merge_cells(start_row=fila_total, start_column=1,
                       end_row=fila_total, end_column=5)

        for letra, (titulo, seccion, tipo) in columnas.items():
            col_idx = ws[f"{letra}1"].column
            c = ws.cell(row=fila_total, column=col_idx)
            if tipo == "money":
                c.value = f"=SUM({letra}3:{letra}{fila-1})"
                c.number_format = formato_moneda
                c.alignment = Alignment(horizontal="right", vertical="center")
            c.font = bold_dark
            c.fill = fill_total
            c.border = border

        for letra in columnas.keys():
            largo_max = len(str(columnas[letra][0]))
            for ini, fin, texto in grupos:
                col_ini = get_column_letter(ini)
                col_fin = get_column_letter(fin)
                if col_ini <= letra <= col_fin:
                    n = fin - ini + 1
                    largo_max = max(largo_max, len(texto) / n if n else 0)
                    break
            for f in range(3, fila_total):
                celda = ws[f"{letra}{f}"]
                if celda.value is None:
                    continue
                if isinstance(celda.value, datetime):
                    txt = celda.value.strftime("%d/%m/%Y")
                elif isinstance(celda.value, (int, float)):
                    txt = f"${celda.value:,.2f}"
                else:
                    txt = str(celda.value)
                largo_max = max(largo_max, len(txt))
            ancho = min(max(largo_max + 2, 8), 40)
            ws.column_dimensions[letra].width = ancho

        ws.column_dimensions["AP"].width = max(ws.column_dimensions["AP"].width, 38)
        ws.column_dimensions["D"].width = max(ws.column_dimensions["D"].width, 22)

        ws.row_dimensions[1].height = 22
        ws.row_dimensions[2].height = 32
        ws.freeze_panes = "F3"
        wb.save(ruta)

    # ---------------- RECLASIFICADOR ----------------
    def _abrir_reclasificador(self):
        """
        Ventana para editar las categorías de los productos.
        Los cambios se acumulan en memoria; solo se guardan al presionar
        'Guardar cambios'. Incluye opción de 'Deshacer todo'.
        """
        from lector_facturas import (
            cargar_catalogo, cargar_excepciones_manuales,
            guardar_excepciones_manuales
        )

        catalogo = cargar_catalogo()
        excepciones_actuales = dict(cargar_excepciones_manuales())
        excepciones_originales = dict(excepciones_actuales)

        categorias = ["U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
                      "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA"]

        ventana = ttk.Toplevel(self)
        ventana.title("🏷️ Reclasificador de productos")
        ventana.geometry("1100x700")
        ventana.transient(self)
        ventana.resizable(False, False)

        # --- Barra superior ---
        top = ttk.Frame(ventana)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Buscar:").pack(side="left", padx=(0, 5))
        var_buscar = tk.StringVar()
        ttk.Entry(top, textvariable=var_buscar, width=40).pack(side="left", padx=5)

        ttk.Label(top, text="Filtrar:").pack(side="left", padx=(15, 5))
        var_filtro = tk.StringVar(value="TODAS")
        ttk.Combobox(top, textvariable=var_filtro,
                     values=["TODAS"] + categorias,
                     width=15, state="readonly").pack(side="left", padx=5)

        ttk.Label(top, text="Mostrar:").pack(side="left", padx=(15, 5))
        var_origen = tk.StringVar(value="TODOS")
        ttk.Combobox(top, textvariable=var_origen,
                     values=["TODOS", "SOLO MODIFICADOS", "SOLO ORIGINALES"],
                     width=20, state="readonly").pack(side="left", padx=5)

        # --- Contenedor con scroll ---
        contenedor = ttk.Frame(ventana)
        contenedor.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(contenedor, borderwidth=0, highlightthickness=0)
        scroll_v = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        frame_interno = ttk.Frame(canvas)

        frame_interno.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=frame_interno, anchor="nw")
        canvas.configure(yscrollcommand=scroll_v.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_v.pack(side="right", fill="y")

        def _on_canvas_configure(event):
            canvas.itemconfigure(canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Scroll con rueda
        def _on_mousewheel(event):
            if sys.platform == "darwin":
                delta = -1 * event.delta
            elif sys.platform.startswith("win"):
                delta = -1 * (event.delta // 120)
            else:
                delta = -1 if event.num == 5 else 1
            canvas.yview_scroll(int(delta), "units")

        def _bind_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel, add="+")
            widget.bind("<Button-4>", _on_mousewheel, add="+")
            widget.bind("<Button-5>", _on_mousewheel, add="+")
            for hijo in widget.winfo_children():
                _bind_mousewheel(hijo)

        # --- Encabezados ---
        encabezados = ttk.Frame(frame_interno)
        encabezados.pack(fill="x", pady=(0, 5))

        ttk.Label(encabezados, text="DESCRIPCIÓN",
                  font=("Segoe UI", 10, "bold"), width=60, anchor="w").pack(side="left", padx=5)
        ttk.Label(encabezados, text="CATEGORÍA ORIGINAL",
                  font=("Segoe UI", 10, "bold"), width=22, anchor="center").pack(side="left", padx=5)
        ttk.Label(encabezados, text="CATEGORÍA ACTUAL",
                  font=("Segoe UI", 10, "bold"), width=22, anchor="center").pack(side="left", padx=5)
        ttk.Label(encabezados, text="ESTADO",
                  font=("Segoe UI", 10, "bold"), width=15, anchor="center").pack(side="left", padx=5)

        frame_filas = ttk.Frame(frame_interno)
        frame_filas.pack(fill="both", expand=True)

        filas_widgets = []
        estado_sel = {"frame_seleccionado": None}

        # --- Panel inferior ---
        bot = ttk.Frame(ventana)
        bot.pack(fill="x", padx=10, pady=8)

        lbl_contador = ttk.Label(bot, text="")
        lbl_contador.pack(side="left")

        # --- Funciones internas ---
        def _hay_cambios():
            return excepciones_actuales != excepciones_originales

        def _actualizar_contador():
            cambios = sum(
                1 for k, v in excepciones_actuales.items()
                if excepciones_originales.get(k) != v
            )
            lbl_contador.configure(
                text=f"Cambios pendientes: {cambios} | Productos totales: {len(catalogo)}"
            )

        def _seleccionar_fila(fila_dict):
            prev = estado_sel.get("frame_seleccionado")
            if prev is not None:
                try:
                    prev.configure(style="TFrame")
                except Exception:
                    pass
            nuevo = fila_dict.get("frame")
            if nuevo is not None:
                try:
                    nuevo.configure(style="Seleccion.TFrame")
                except Exception:
                    pass
                estado_sel["frame_seleccionado"] = nuevo

        def _al_cambiar(desc, var):
            nueva_cat = var.get()
            cat_original = catalogo.get(desc, "CLINICA")
            cat_previa = excepciones_originales.get(desc, cat_original)

            if nueva_cat == cat_previa:
                excepciones_actuales.pop(desc, None)
            else:
                excepciones_actuales[desc] = nueva_cat

            for fila in filas_widgets:
                if fila["desc"] == desc:
                    if desc in excepciones_actuales and excepciones_actuales[desc] != cat_original:
                        fila["lbl_estado"].configure(text="✏️ Modificado", foreground="blue")
                    elif desc in excepciones_actuales:
                        fila["lbl_estado"].configure(text="⚙️ Excepción", foreground="gray")
                    else:
                        fila["lbl_estado"].configure(text="—", foreground="black")
                    break

            _actualizar_contador()

        def _refrescar_lista(*args):
            nonlocal filas_widgets
            for w in frame_filas.winfo_children():
                w.destroy()
            filas_widgets = []
            estado_sel["frame_seleccionado"] = None

            busqueda = var_buscar.get().strip().lower()
            filtro = var_filtro.get()
            origen_filtro = var_origen.get()

            todos = dict(catalogo)
            for k, v in excepciones_actuales.items():
                todos[k] = v

            items = []
            for desc, cat in sorted(todos.items()):
                if busqueda and busqueda not in desc.lower():
                    continue
                if filtro != "TODAS" and cat != filtro:
                    continue
                es_modificado = desc in excepciones_actuales
                if origen_filtro == "SOLO MODIFICADOS" and not es_modificado:
                    continue
                if origen_filtro == "SOLO ORIGINALES" and es_modificado:
                    continue
                items.append((desc, cat))

            max_items = 500
            for desc, _ in items[:max_items]:
                cat_original = catalogo.get(desc, "CLINICA")
                cat_actual = excepciones_actuales.get(desc, cat_original)

                fila_frame = ttk.Frame(frame_filas, style="TFrame")
                fila_frame.pack(fill="x", pady=1)

                ttk.Label(fila_frame, text=desc, width=60, anchor="w").pack(side="left", padx=5)
                ttk.Label(fila_frame, text=cat_original,
                          width=22, anchor="center").pack(side="left", padx=5)

                var_cat = tk.StringVar(value=cat_actual)
                combo = ttk.Combobox(fila_frame, textvariable=var_cat,
                                     values=categorias, width=20,
                                     state="readonly")
                combo.pack(side="left", padx=5)
                combo.bind(
                    "<<ComboboxSelected>>",
                    lambda e, d=desc, v=var_cat: _al_cambiar(d, v)
                )

                estado_texto = "—"
                color = "black"
                if desc in excepciones_actuales:
                    if excepciones_actuales[desc] != cat_original:
                        estado_texto = "✏️ Modificado"
                        color = "blue"
                    else:
                        estado_texto = "⚙️ Excepción"
                        color = "gray"

                lbl_estado = ttk.Label(fila_frame, text=estado_texto,
                                       width=15, anchor="center",
                                       foreground=color)
                lbl_estado.pack(side="left", padx=5)

                fila_dict = {
                    "desc": desc,
                    "frame": fila_frame,
                    "combo_var": var_cat,
                    "lbl_estado": lbl_estado,
                }

                def _click_en_fila(event, fd=fila_dict):
                    _seleccionar_fila(fd)

                def _bind_click(widget, fd=fila_dict):
                    widget.bind("<Button-1>", _click_en_fila, add="+")
                    for hijo in widget.winfo_children():
                        _bind_click(hijo, fd)

                _bind_click(fila_frame)
                filas_widgets.append(fila_dict)

            if len(items) > max_items:
                ttk.Label(frame_filas,
                          text=f"... y {len(items) - max_items} más. Usa el buscador.",
                          foreground="gray").pack(pady=10)

            _bind_mousewheel(frame_interno)
            _actualizar_contador()

        def _guardar():
            if not _hay_cambios():
                messagebox.showinfo("Sin cambios",
                                    "No hay cambios pendientes.", parent=ventana)
                return

            if not messagebox.askyesno(
                "Guardar cambios",
                f"Se guardarán {len(excepciones_actuales)} excepciones manuales.\n\n"
                "Se hará un backup automático.\n¿Continuar?",
                parent=ventana
            ):
                return

            guardar_excepciones_manuales(excepciones_actuales)
            nonlocal excepciones_originales
            excepciones_originales = dict(excepciones_actuales)
            _refrescar_lista()
            messagebox.showinfo("Guardado",
                                "Los cambios se guardaron correctamente.",
                                parent=ventana)

        def _deshacer_todo():
            if not _hay_cambios():
                messagebox.showinfo("Sin cambios",
                                    "No hay cambios para deshacer.", parent=ventana)
                return

            if not messagebox.askyesno(
                "Deshacer todo",
                "Se revertirán TODOS los cambios sin guardar.\n\n"
                "¿Continuar?",
                parent=ventana
            ):
                return

            excepciones_actuales.clear()
            excepciones_actuales.update(excepciones_originales)
            _refrescar_lista()
            messagebox.showinfo("Deshecho",
                                "Se revirtieron todos los cambios pendientes.",
                                parent=ventana)

        ttk.Button(bot, text="💾 Guardar cambios",
                   command=_guardar,
                   bootstyle="info-outline").pack(side="right", padx=4)
        ttk.Button(bot, text="↶ Deshacer todo",
                   command=_deshacer_todo,
                   bootstyle="info-outline").pack(side="right", padx=4)

        var_buscar.trace_add("write", _refrescar_lista)
        var_filtro.trace_add("write", _refrescar_lista)
        var_origen.trace_add("write", _refrescar_lista)

        style = ttk.Style()
        style.configure("Seleccion.TFrame", background="#cce5ff")

        _refrescar_lista()
        _bind_mousewheel(canvas)
        _bind_mousewheel(frame_interno)

    def _ver_logs(self):
        """Abre la carpeta de logs."""
        carpeta = _CARPETA_DATOS / "logs"
        carpeta.mkdir(parents=True, exist_ok=True)
        self._abrir_carpeta(carpeta)

    def _reset_cache(self):
        """Resetea la caché de correos procesados."""
        ruta = _CARPETA_DATOS / "correos_procesados.json"
        if ruta.exists():
            if not messagebox.askyesno(
                "Reset caché",
                "Esto hará que la próxima sincronización descargue TODOS los correos "
                "de la etiqueta (incluso los ya procesados).\n\n"
                "Los duplicados se detectarán igual, pero se descargarán de nuevo.\n\n"
                "¿Continuar?"
            ):
                return
            try:
                ruta.unlink()
                messagebox.showinfo("Reset caché",
                                     "Caché eliminada correctamente.")
            except Exception as e:
                messagebox.showerror("Error",
                                      f"No se pudo eliminar la caché:\n{e}")
        else:
            messagebox.showinfo("Reset caché",
                                 "No hay caché para eliminar.")
# ============================================================
if __name__ == "__main__":
    app = AppIngresos()
    app.mainloop()