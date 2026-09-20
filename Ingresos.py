# -*- coding: utf-8 -*-
"""
Sistema de Ingresos - Contabilidad
Interfaz moderna con ttkbootstrap.
"""

import os
import sys
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
# CONFIGURACIÓN
# ============================================================
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

BASE_DIR = Path.home() / "Documents"
DB_FILE = Path(__file__).parent / "registros_ingresos.json"
HISTORIAL_FILE = Path(__file__).parent / "historial_autocompletado.json"
CONFIG_FILE = Path(__file__).parent / "config_ui.json"

CONFIG_DEFAULT = {
    "tema": "darkly"
}

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

# Temas oscuros
TEMAS_OSCUROS = {"superhero", "darkly", "cyborg", "vapor", "solar"}

def tema_es_oscuro(tema=None):
    t = tema or TEMA
    return t.lower() in TEMAS_OSCUROS

def _colores_adaptados():
    oscuro = tema_es_oscuro()
    if oscuro:
        return {
            "texto_normal":    "#ffffff",
            "texto_operacion": "#00ff00",
            "fondo_entry":     "#2b2b2b",
            "campo_ok":        "#1b5e20",
            "campo_error":     "#7f1d1d",
            "campo_normal":    "#2b2b2b",
        }
    else:
        return {
            "texto_normal":    "#000000",
            "texto_operacion": "#007700",
            "fondo_entry":     "#ffffff",
            "campo_ok":        "#c8e6c9",
            "campo_error":     "#ffcdd2",
            "campo_normal":    "#ffffff",
        }

COLORES = _colores_adaptados()

def refrescar_colores():
    global COLORES
    COLORES = _colores_adaptados()

# ============================================================
# DEFINICIÓN DE CAMPOS
# ============================================================
CAMPOS = [
    ("no_factura",  "No. DE FACTURA",            "GENERAL",        "text"),
    ("qvet",        "QVET",                      "GENERAL",        "text"),
    ("fecha",       "FECHA",                     "GENERAL",        "date"),
    ("nombre",      "NOMBRE",                    "GENERAL",        "text"),
    ("rfc",         "RFC",                       "GENERAL",        "text"),
    ("u_importe",   "IMPORTE",                   "U",              "number"),
    ("u_iva",       "IVA (16%)",                 "U",              "number"),
    ("ac_importe",  "IMPORTE",                   "ACCESORIOS",     "number"),
    ("ac_iva",      "IVA (16%)",                 "ACCESORIOS",     "number"),
    ("med_importe", "IMPORTE (sin IVA)",   "MEDICAMENTOS",   "number"),
    ("med_sin_iva", "SIN IVA",             "MEDICAMENTOS",   "number"),
    ("med_iva",     "IVA (16%)",           "MEDICAMENTOS",   "number"),
    ("hig_importe",     "IMPORTE (sin IVA)", "HIGIENE", "number"),
    ("hig_sin_iva",     "SIN IVA",           "HIGIENE", "number"),
    ("hig_iva",         "IVA 16%",           "HIGIENE", "number"),
    ("hig_sin_ieps_6",  "SIN IEPS 6%",       "HIGIENE", "number"),
    ("hig_ieps_6",      "IEPS 6%",           "HIGIENE", "number"),
    ("hig_sin_ieps_7",  "SIN IEPS 7%",       "HIGIENE", "number"),
    ("hig_ieps_7",      "IEPS 7%",           "HIGIENE", "number"),
    ("est_importe", "IMPORTE",                   "ESTETICA",       "number"),
    ("est_iva",     "IVA (16%)",                 "ESTETICA",       "number"),
    ("tra_importe", "IMPORTE",                   "TRANSPORTE",     "number"),
    ("tra_iva",     "IVA (16%)",                 "TRANSPORTE",     "number"),
    ("pen_importe", "IMPORTE",                   "PENSION",        "number"),
    ("pen_iva",     "IVA (16%)",                 "PENSION",        "number"),
    ("vac_importe", "IMPORTE",                   "VACUNA",         "number"),
    ("cli_importe", "IMPORTE",                   "CLINICA",        "number"),
    ("total",       "TOTAL (auto)",              "TOTAL",          "number"),
    ("efectivo",    "EFECTIVO",                  "TIPO DE PAGO",   "number"),
    ("tc",          "TARJETA CRÉDITO",           "TIPO DE PAGO",   "number"),
    ("td",          "TARJETA DÉBITO",            "TIPO DE PAGO",   "number"),
    ("cheque",      "CHEQUE",                    "TIPO DE PAGO",   "number"),
    ("transfer",    "TRANSFERENCIA",                   "TIPO DE PAGO",   "number"),
    ("vale",        "VALE",                      "TIPO DE PAGO",   "number"),
    ("fecha_impresion",    "FECHA DE IMPRESIÓN",                "CONTROL", "date"),
    ("fecha_ficha",        "FECHA FICHA DE DEPÓSITO",           "CONTROL", "date"),
    ("monto_ficha",        "MONTO DE FICHA DE DEPOSITO",        "CONTROL", "number"),
    ("fecha_santander",    "FECHA SANTANDER",                   "CONTROL", "date"),
    ("edo_santander_deb",  "EDO. CUENTA SANTANDER DEBITO",      "CONTROL", "number"),
    ("edo_santander_cre",  "EDO. CUENTA SANTANDER CREDITO",     "CONTROL", "number"),
    ("fecha_bancomer",     "FECHA BANCOMER",                    "CONTROL", "date"),
    ("transfer_santander", "TRANSFERENCIA SANTANDER",           "CONTROL", "number"),
    ("folio_fiscal",       "FOLIO FISCAL",                      "CONTROL", "text"),
]

CAMPOS_DICT = {c[0]: c for c in CAMPOS}

# El IVA/IEPS se calcula desde el campo "SIN IVA" (base con IVA desglosado)
# Solo Medicamentos e Higiene usan este esquema.
REGLAS_AUTO = {
    "med_iva":     ("med_sin_iva",     0.16),
    "hig_iva":     ("hig_sin_iva",     0.16),
    "hig_ieps_6":  ("hig_sin_ieps_6",  0.06),
    "hig_ieps_7":  ("hig_sin_ieps_7",  0.07),
    # El resto de secciones mantiene: importe calcula iva
    "u_iva":       ("u_importe",       0.16),
    "ac_iva":      ("ac_importe",      0.16),
    "est_iva":     ("est_importe",     0.16),
    "tra_iva":     ("tra_importe",     0.16),
    "pen_iva":     ("pen_importe",     0.16),
}

# IMPORTES exentos (no llevan IVA)
BASES_EXENTAS = [
    "u_importe", "ac_importe", "med_importe", "hig_importe",
    "est_importe", "tra_importe", "pen_importe", "vac_importe", "cli_importe",
]

# Bases con IVA (a las que se les calcula IVA)
BASES_CON_IVA = [
    "med_sin_iva", "hig_sin_iva",
    # "u_sin_iva", "ac_sin_iva", "est_sin_iva", "tra_sin_iva", "pen_sin_iva",
]

# Bases con IEPS
BASES_CON_IEPS = [
    "hig_sin_ieps_6", "hig_sin_ieps_7",
]

# Impuestos
IMPUESTOS = [
    "med_iva", "hig_iva", "hig_ieps_6", "hig_ieps_7",
    # más los iva de otras secciones que sí apliquen
]

# Categorías para calcular el total por "suma de categorías"
# (para comparar contra tipo de pago)
CATEGORIAS_PARA_TOTAL = [
    # bases exentas
    "u_importe", "ac_importe", "med_importe", "hig_importe",
    "est_importe", "tra_importe", "pen_importe", "vac_importe", "cli_importe",
    # bases con IVA
    "med_sin_iva", "hig_sin_iva",
    # bases con IEPS
    "hig_sin_ieps_6", "hig_sin_ieps_7",
    # impuestos
    "u_iva", "ac_iva", "med_iva", "hig_iva", "hig_ieps_6", "hig_ieps_7",
    "est_iva", "tra_iva", "pen_iva",
]

# Campos de tipo de pago
CAMPOS_TIPO_PAGO = ["efectivo", "tc", "td", "cheque", "transfer", "vale"]

# ============================================================
# RUTAS
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

def cargar_db():
    if DB_FILE.exists():
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_db(regs):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(regs, f, ensure_ascii=False, indent=2)

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
    """Extrae el número entero de un No. de Factura. Devuelve None si no es numérico."""
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
    """
    Devuelve el siguiente No. de Factura esperado según los registros
    del mismo centro/año/mes. Si no hay registros, devuelve None.
    """
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

# ============================================================
# WIDGETS PERSONALIZADOS
# ============================================================
class EntryMoneda(ttk.Entry):
    """Entry con formato moneda, evaluación de expresiones y colores.
    Al entrar al campo muestra la ÚLTIMA EXPRESIÓN escrita por el usuario
    (ej. '1+1'), permitiendo editarla. Al salir, se evalúa.
    """
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
            # El usuario está dejando una operación
            self._ultima_expresion = texto.replace(",", "").replace("$", "").strip()
            self._ultimo_valor = evaluar_expresion(texto)
        else:
            # No hay operación visible
            # Si el texto coincide con el valor formateado Y ya tenemos una expresión,
            # conservarla (no borrarla)
            try:
                valor_actual = limpiar_moneda(texto)
            except Exception:
                valor_actual = None
            if (valor_actual is not None
                    and abs(valor_actual - self._ultimo_valor) < 0.01
                    and self._ultima_expresion):
                # El texto es el valor ya evaluado; conservar la expresión
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

        self.registros = cargar_db()
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

    def _construir_ui(self):
        # --- Barra superior de configuración ---
        top = ttk.LabelFrame(self, text="Configuración", padding=10)
        top.pack(fill="x", padx=10, pady=5)

        ttk.Label(top, text="Centro:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.var_centro = ttk.StringVar(value="Central")
        ttk.Combobox(top, textvariable=self.var_centro, values=["Central", "Prado"],
                     width=15, state="readonly", bootstyle="primary").grid(
            row=0, column=1, padx=5)

        ttk.Label(top, text="Año:").grid(row=0, column=2, padx=5, sticky="e")
        self.var_anio = ttk.StringVar(value=str(datetime.now().year))
        ttk.Entry(top, textvariable=self.var_anio, width=8,
            style="Custom.TEntry").grid(row=0, column=3, padx=5)

        ttk.Label(top, text="Mes:").grid(row=0, column=4, padx=5, sticky="e")
        self.var_mes = ttk.StringVar(value=MESES_ES[datetime.now().month-1])

        def _on_cambio_reporte(*args):
            self._refrescar_tabla()
            self._actualizar_titulo()

        self.var_centro.trace_add("write", _on_cambio_reporte)
        self.var_mes.trace_add("write", _on_cambio_reporte)
        self.var_anio.trace_add("write", _on_cambio_reporte)

        ttk.Combobox(top, textvariable=self.var_mes, values=MESES_ES,
                     width=12, state="readonly", bootstyle="primary").grid(
            row=0, column=5, padx=5)

        ttk.Button(top, text="📁 Abrir carpeta Ingreso",
                   command=self._abrir_carpeta_ingreso,
                   bootstyle="info").grid(row=0, column=6, padx=10)

        ttk.Button(top, text="📊 Reportes",
                   command=self._ver_reportes,
                   bootstyle="primary-outline").grid(row=0, column=8, padx=5)

        ttk.Button(top, text="🎨 Cambiar tema",
                   command=self._elegir_tema,
                   bootstyle="warning-outline").grid(row=0, column=7, padx=10)
        
        ttk.Button(top, text="🏷️ Reclasificar",
                   command=self._abrir_reclasificador,
                   bootstyle="warning-outline").grid(row=0, column=9, padx=5)

        # --- Formulario con scroll ---
        cont = ttk.Frame(self)
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
        self.lbl_alerta_total = ttk.Label(self, text="", bootstyle="danger")
        self.lbl_alerta_total.pack(fill="x", padx=15, pady=(0, 5))

        # --- Barra de botones ---
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=8)

        ttk.Button(bar, text="🆕 Nuevo", command=self._nuevo,
                   bootstyle="secondary").pack(side="left", padx=4)
        self.btn_guardar = ttk.Button(bar, text="💾 Guardar", command=self._guardar,
                                      bootstyle="success")
        self.btn_guardar.pack(side="left", padx=4)
        ttk.Button(bar, text="✏️ Editar", command=self._editar,
                   bootstyle="warning").pack(side="left", padx=4)
        ttk.Button(bar, text="🗑️ Eliminar", command=self._eliminar,
                   bootstyle="danger").pack(side="left", padx=4)
        ttk.Button(bar, text="📥 Leer factura",
                   command=self._leer_factura,
                   bootstyle="info").pack(side="left", padx=4)
        ttk.Button(bar, text="📎 Adjuntar factura",
                   command=self._adjuntar_factura,
                   bootstyle="info").pack(side="left", padx=4)
        ttk.Button(bar, text="📂 Ver adjuntos",
                   command=self._ver_adjuntos,
                   bootstyle="info-outline").pack(side="left", padx=4)
        ttk.Button(bar, text="🔄 Recalcular",
                   command=self._recalcular_total,
                   bootstyle="secondary-outline").pack(side="left", padx=4)
        self.btn_toggle_tabla = ttk.Button(
            bar, text="👁️ Ocultar tabla", command=self._toggle_tabla,
            bootstyle="secondary-outline")
        self.btn_toggle_tabla.pack(side="right", padx=4)
        ttk.Button(bar, text="📊 Generar Excel", command=self._generar_excel,
                   bootstyle="primary").pack(side="right", padx=4)

        # --- Tabla ---
        self.frame_tabla = ttk.LabelFrame(self, text="Registros guardados", padding=5)
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

        # Validación inicial
        self._validar_no_factura_visual()
        self._validar_qvet_visual()

        # ---- Refrescar tabla y título al cambiar centro/año/mes ----
        def _on_cambio_reporte(*args):
            self._refrescar_tabla()
            self._actualizar_titulo()

        self.var_centro.trace_add("write", _on_cambio_reporte)
        self.var_mes.trace_add("write", _on_cambio_reporte)
        self.var_anio.trace_add("write", _on_cambio_reporte)

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
        Opción C:
        - El campo TOTAL muestra la suma de tipo de pago
          (efectivo + tarjeta + cheque + transfer + vale).
        - Adicionalmente compara con la suma de categorías
          (bases + impuestos).
        - Si hay diferencia > $0.01 y ambos son > 0, alerta visual
          (borde rojo + mensaje).
        """
        # Suma por tipo de pago
        total_pago = 0.0
        for clave in CAMPOS_TIPO_PAGO:
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                total_pago += w.get_valor()

        # Suma por categorías
        total_categorias = 0.0
        for clave in CATEGORIAS_PARA_TOTAL:
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                total_categorias += w.get_valor()

        # Actualizar el campo TOTAL (solo lectura, muestra el de pago)
        w_total = self.entradas.get("total")
        if isinstance(w_total, EntryMoneda):
            w_total.configure(state="normal")
            w_total.set_valor(round(total_pago, 2))
            w_total.configure(state="readonly")

        # Alerta si no cuadran
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

    # ---------------- CRUD ----------------
    def _leer_form(self):
        d = {}
        for clave, _, _, tipo in CAMPOS:
            w = self.entradas[clave]
            if tipo == "number":
                if isinstance(w, EntryMoneda):
                    # Si el usuario dejó una operación sin evaluar,
                    # evaluarla y guardarla como expresión
                    texto = w.get().strip()
                    if w._tiene_operacion(texto):
                        w._ultima_expresion = texto.replace(",", "").replace("$", "").strip()
                        w._ultimo_valor = evaluar_expresion(texto)
                        # Refrescar visualmente el campo
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
                d[clave] = w.get().strip()
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
        
        # Sugerir siguiente No. de Factura
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
        # Forzar que el widget con foco dispare su FocusOut antes de leer,
        # así se evalúa la expresión que el usuario acaba de escribir.
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

        # --- Validación de consecutivo ---
        if self.id_actual is None:  # solo al crear un registro nuevo
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

        guardar_db(self.registros)
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

        # Gestión de adjuntos al editar
        msgs_archivos = []
        if es_edicion and reg_viejo:
            msgs_archivos = self._gestionar_adjuntos_al_editar(reg_viejo, datos)

        # Auto-adjuntar la factura leída (si hay archivos pendientes)
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

            # Limpiar rutas pendientes
            self._ultima_factura_xml = None
            self._ultima_factura_pdf = None

        partes = [msg, f"Carpeta: {ruta}"]
        if msgs_archivos:
            partes.append("")
            partes.extend(msgs_archivos)
        messagebox.showinfo("OK", "\n".join(partes))

        self._refrescar_tabla()

        # Limpiar formulario
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
        guardar_db(self.registros)
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
        from tkinter import filedialog, messagebox
        from lector_facturas import procesar_factura

        # 1. XML
        ruta_xml = filedialog.askopenfilename(
            title="Selecciona el XML de la factura",
            filetypes=[("XML CFDI", "*.xml"), ("Todos", "*.*")]
        )
        if not ruta_xml:
            return

        # 2. PDF (opcional)
        ruta_pdf = filedialog.askopenfilename(
            title="Selecciona el PDF de la factura (opcional, cancelar para omitir)",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")]
        )

        # 3. Procesar
        try:
            datos = procesar_factura(ruta_xml, ruta_pdf or None)
        except Exception as e:
            messagebox.showerror("Error al leer factura",
                                 f"No se pudo procesar la factura:\n{e}")
            return

        # 4. Llenar formulario
        resumen = self._llenar_desde_factura(datos)

        # 5. Guardar rutas para auto-adjuntar
        self._ultima_factura_xml = ruta_xml
        self._ultima_factura_pdf = ruta_pdf or None

        # 6. Mostrar resumen
        lineas = [
            f"Factura leída: {datos['no_factura']}",
            f"Nombre: {datos['nombre']}",
            f"Total: ${datos['total']:,.2f}",
            "",
            "Campos llenados:",
        ]
        lineas.extend(resumen)
        messagebox.showinfo("Factura leída", "\n".join(lineas))

    def _llenar_desde_factura(self, datos):
        """
        Llena el formulario con los datos de la factura.
        Devuelve la lista de resumen (para mostrar al usuario).
        """
        # 1. Limpiar formulario
        self._nuevo()

        # 2. Datos generales
        self.entradas["no_factura"].delete(0, tk.END)
        self.entradas["no_factura"].insert(0, datos["no_factura"])

        self.entradas["qvet"].delete(0, tk.END)
        self.entradas["qvet"].insert(0, datos.get("qvet", ""))

        self.entradas["nombre"].delete(0, tk.END)
        self.entradas["nombre"].insert(0, datos["nombre"])

        self.entradas["rfc"].delete(0, tk.END)
        self.entradas["rfc"].insert(0, datos["rfc"])

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

        # 3. Agrupar conceptos y calcular montos por categoría
        from lector_facturas import agrupar_por_categoria
        agrupado, detalle = agrupar_por_categoria(datos)

        # Guardar los importes individuales por campo (para la expresión)
        importes_por_campo = {}

        # Mapa categoría → campos
        mapa_campos = {
            "U":            {"importe": "u_importe", "iva": "u_iva"},
            "ACCESORIOS":   {"importe": "ac_importe", "iva": "ac_iva"},
            "ESTETICA":     {"importe": "est_importe", "iva": "est_iva"},
            "TRANSPORTE":   {"importe": "tra_importe", "iva": "tra_iva"},
            "VACUNA":       {"importe": "vac_importe"},
            "CLINICA":      {"importe": "cli_importe"},
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
                    # Construir la expresión a partir del detalle
                    clave_det = f"{cat}__{subclave}"
                    terminos = detalle.get(clave_det, [])
                    if terminos:
                        expresion = "+".join(terminos)
                    else:
                        expresion = f"{valor:.2f}"

                    w.set_valor(round(valor, 2), expresion=expresion)
                    resumen.append(f"  {cat} → {campo}: ${valor:,.2f}")

        # 4. Llenar el tipo de pago
        pagos = datos.get("pagos", {})
        for clave in ("efectivo", "tc", "td", "cheque", "transfer", "vale"):
            valor = pagos.get(clave, 0)
            if valor <= 0:
                continue
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                w.set_valor(round(valor, 2), expresion=f"{valor:.2f}")
                resumen.append(f"  {clave.upper()}: ${valor:,.2f}")

        # 5. Recalcular el TOTAL del formulario
        self._recalcular_total()

        return resumen

    def _actualizar_titulo(self):
        try:
            self.title(
                f"Sistema de Ingresos — {self.var_centro.get()} "
                f"{self.var_mes.get()} {self.var_anio.get()}"
            )
        except Exception:
            pass

    def _ver_reportes(self):
        """Muestra todos los reportes existentes con su conteo de registros."""
        from collections import defaultdict
        conteos = defaultdict(int)
        for r in self.registros:
            key = (r.get("centro", "?"), r.get("anio", "?"), r.get("mes", "?"))
            conteos[key] += 1

        ventana = ttk.Toplevel(self)
        ventana.title("📊 Reportes disponibles")
        ventana.geometry("520x420")
        ventana.transient(self)

        ttk.Label(ventana, text="Selecciona un reporte:",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(ventana)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        lb = tk.Listbox(frame, font=("Consolas", 10))
        lb.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.configure(yscrollcommand=sb.set)

        items = []
        if not conteos:
            lb.insert(tk.END, "(No hay reportes todavía)")
        else:
            for (centro, anio, mes), n in sorted(conteos.items()):
                txt = f"{centro:>10}  {mes:<12} {anio}   →  {n} registro(s)"
                lb.insert(tk.END, txt)
                items.append((centro, anio, mes))

        def ir_a():
            sel = lb.curselection()
            if not sel:
                return
            centro, anio, mes = items[sel[0]]
            self.var_centro.set(centro)
            self.var_anio.set(str(anio))
            self.var_mes.set(mes)
            self._refrescar_tabla()
            self._actualizar_titulo()
            ventana.destroy()

        lb.bind("<Double-Button-1>", lambda e: ir_a())

        fr = ttk.Frame(ventana)
        fr.pack(pady=8)
        ttk.Button(fr, text="➡️ Ir a este reporte", command=ir_a,
                   bootstyle="success").pack(side="left", padx=4)
        ttk.Button(fr, text="Cerrar", command=ventana.destroy,
                   bootstyle="secondary").pack(side="left", padx=4)

    def _refrescar_tabla(self):
        """Muestra solo los registros del centro/año/mes activos, ordenados por No. Factura."""
        for i in self.tabla.get_children():
            self.tabla.delete(i)

        try:
            anio_activo = int(self.var_anio.get())
        except Exception:
            anio_activo = None
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
        ventana.geometry("520x380")
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
        ttk.Button(fr, text="📄 Abrir archivo", command=abrir_archivo,
                   bootstyle="primary").pack(side="left", padx=4)
        ttk.Button(fr, text="📁 Abrir carpeta", command=abrir_carpeta,
                   bootstyle="info").pack(side="left", padx=4)
        ttk.Button(fr, text="📎 Adjuntar más",
                   command=lambda: (ventana.destroy(), self._adjuntar_factura()),
                   bootstyle="success").pack(side="left", padx=4)
        ttk.Button(fr, text="Cerrar", command=ventana.destroy,
                   bootstyle="secondary").pack(side="left", padx=4)

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
        ventana.geometry("420x520")
        ventana.transient(self)
        ventana.grab_set()

        ttk.Label(ventana, text="Selecciona un tema:",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)

        cont = ttk.Frame(ventana)
        cont.pack(fill="both", expand=True, padx=10, pady=5)
        canvas = tk.Canvas(cont, borderwidth=0, highlightthickness=0)
        sb = ttk.Scrollbar(cont, orient="vertical", command=canvas.yview)
        frame_lista = ttk.Frame(canvas)
        frame_lista.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame_lista, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        var_tema = tk.StringVar(value=TEMA)

        def _preview(tema):
            try:
                _ttk.Style().theme_use(tema)
                global TEMA
                TEMA = tema
                refrescar_colores()
                self._configurar_estilos()
                self._repintar_todo()
            except Exception as e:
                print(f"[_preview] Error: {e}")

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
            var_tema.set("superhero")
            _preview("superhero")

        # Crear un radio button por cada tema
        for tema in temas:
            rb = ttk.Radiobutton(
                frame_lista, text=tema, value=tema, variable=var_tema,
                command=lambda t=tema: _preview(t),
                bootstyle="info",
            )
            rb.pack(anchor="w", padx=10, pady=3, fill="x")

        # Botones inferiores
        fr_btn = ttk.Frame(ventana)
        fr_btn.pack(pady=10)
        ttk.Button(fr_btn, text="✅ Aplicar y guardar",
                   command=_confirmar,
                   bootstyle="success").pack(side="left", padx=5)
        ttk.Button(fr_btn, text="↺ Restaurar",
                   command=_restaurar,
                   bootstyle="secondary-outline").pack(side="left", padx=5)
        ttk.Button(fr_btn, text="Cancelar",
                   command=ventana.destroy,
                   bootstyle="danger-outline").pack(side="left", padx=5)

    def _repintar_todo(self):
        """Repinta todos los EntryMoneda y ttk.Entry según el tema actual."""
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
        """
        Genera el Excel con:
        - Celdas combinadas en encabezados
        - Formato moneda
        - Colores por sección
        - Auto-ajuste de ancho
        - Preservación de expresiones del usuario como fórmulas de Excel
        - Columnas TC y TD en TIPO DE PAGO
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Hoja1"

        thin = Side(border_style="thin", color="808080")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        centro = Alignment(horizontal="center", vertical="center", wrap_text=True)
        bold_white = Font(bold=True, color="FFFFFF", size=11)
        bold_dark = Font(bold=True, color="000000", size=10)
        formato_moneda = '"$"#,##0.00'
        formato_fecha = "DD/MM/YYYY"

        COLORES_SECCION = {
            "GENERAL":      "1F4E3D",
            "U":            "2E5A88",
            "ACCESORIOS":   "7B3F00",
            "MEDICAMENTOS": "8B1A1A",
            "HIGIENE":      "4B6B00",
            "ESTETICA":     "6A1B9A",
            "TRANSPORTE":   "0D47A1",
            "PENSION":      "B85C00",
            "VACUNA":       "00695C",
            "CLINICA":      "37474F",
            "TOTAL":        "000000",
            "TIPO DE PAGO": "4A148C",
            "CONTROL":      "455A64",
        }
        fill_total = PatternFill("solid", fgColor="FFD966")

        # ============================================================
        # DEFINICIÓN DE COLUMNAS
        # ============================================================
        columnas = {
            "A":  ("No. DE FACTURA",              "GENERAL",       "text"),
            "B":  ("QVET",                        "GENERAL",       "text"),
            "C":  ("FECHA",                       "GENERAL",       "date"),
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
            # TIPO DE PAGO (ahora 6 columnas: efectivo, tc, td, cheque, transf, vale)
            "AC": ("EFECTIVO",                    "TIPO DE PAGO",  "money"),
            "AD": ("TC",                          "TIPO DE PAGO",  "money"),
            "AE": ("TD",                          "TIPO DE PAGO",  "money"),
            "AF": ("CHEQUE",                      "TIPO DE PAGO",  "money"),
            "AG": ("TRANSF.",                     "TIPO DE PAGO",  "money"),
            "AH": ("VALE",                        "TIPO DE PAGO",  "money"),
            # CONTROL (empieza en AI, todo corrido 2 columnas)
            "AI": ("FECHA DE IMPRESIÓN",          "CONTROL",       "date"),
            "AJ": ("FECHA FICHA DE DEPÓSITO",     "CONTROL",       "date"),
            "AK": ("MONTO DE FICHA DE DEPOSITO",  "CONTROL",       "money"),
            "AL": ("FECHA SANTANDER",             "CONTROL",       "date"),
            "AM": ("EDO. CUENTA SANTANDER DEBITO","CONTROL",       "money"),
            "AN": ("EDO. CUENTA SANTANDER CREDITO","CONTROL",      "money"),
            "AO": ("FECHA BANCOMER",              "CONTROL",       "date"),
            "AP": ("TRANSFERENCIA SANTANDER",     "CONTROL",       "money"),
            "AQ": ("FOLIO FISCAL",                "CONTROL",       "text"),
        }

        # Mapeo columna → clave del JSON
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
            "AC": "efectivo", "AD": "tc", "AE": "td",
            "AF": "cheque", "AG": "transfer", "AH": "vale",
            "AI": "fecha_impresion", "AJ": "fecha_ficha",
            "AK": "monto_ficha", "AL": "fecha_santander",
            "AM": "edo_santander_deb", "AN": "edo_santander_cre",
            "AO": "fecha_bancomer", "AP": "transfer_santander",
            "AQ": "folio_fiscal",
        }

        # Fórmulas automáticas (todas corridas 2 columnas)
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
            "AB": "=AC{r}+AD{r}+AE{r}+AF{r}+AG{r}+AH{r}",
        }

        # ============================================================
        # FILA 1: GRUPOS (con celdas combinadas)
        # ============================================================
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
            (29, 34, "TIPO DE PAGO"),     # ← ahora 6 columnas (AC..AH)
            (35, 43, "CONTROL"),           # ← ahora 9 columnas (AI..AQ)
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

        # ============================================================
        # FILA 2: SUBENCABEZADOS (con color)
        # ============================================================
        for letra, (titulo, seccion, tipo) in columnas.items():
            c = ws[f"{letra}2"]
            c.value = titulo
            c.font = bold_white
            c.fill = PatternFill("solid", fgColor=COLORES_SECCION[seccion])
            c.alignment = centro
            c.border = border

        # ============================================================
        # FILAS DE DATOS
        # ============================================================
        fila = 3
        for r in regs:
            for letra, (titulo, seccion, tipo) in columnas.items():
                clave = mapa_claves[letra]
                valor = r.get(clave, 0 if tipo == "money" else "")
                expresion = r.get(f"{clave}__expr", "")
                c = ws[f"{letra}{fila}"]
                c.border = border

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

        # ============================================================
        # FILA DE TOTALES
        # ============================================================
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

        # ============================================================
        # AUTO-AJUSTE DE ANCHO
        # ============================================================
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

        ws.column_dimensions["AQ"].width = max(ws.column_dimensions["AQ"].width, 38)
        ws.column_dimensions["D"].width = max(ws.column_dimensions["D"].width, 22)

        ws.row_dimensions[1].height = 22
        ws.row_dimensions[2].height = 32
        ws.freeze_panes = "F3"
        wb.save(ruta)

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

        # ============================================================
        # BARRA SUPERIOR
        # ============================================================
        top = ttk.Frame(ventana)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Buscar:").pack(side="left", padx=(0, 5))
        var_buscar = tk.StringVar()
        entry_buscar = ttk.Entry(top, textvariable=var_buscar, width=40)
        entry_buscar.pack(side="left", padx=5)

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

        # ============================================================
        # CONTENEDOR PRINCIPAL con scroll
        # ============================================================
        contenedor = ttk.Frame(ventana)
        contenedor.pack(fill="both", expand=True, padx=10, pady=5)

        # Canvas + scrollbars
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

        # Ajustar el ancho del frame interno al ancho del canvas
        def _on_canvas_configure(event):
            canvas.itemconfigure(canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        # ----------- SCROLL CON RUEDA DEL MOUSE -----------
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

        # ============================================================
        # ENCABEZADOS DE TABLA
        # ============================================================
        encabezados = ttk.Frame(frame_interno)
        encabezados.pack(fill="x", pady=(0, 5))
        encabezados.configure(style="Encabezados.TFrame")

        ttk.Label(encabezados, text="DESCRIPCIÓN",
                  font=("Segoe UI", 10, "bold"), width=60, anchor="w").pack(side="left", padx=5)
        ttk.Label(encabezados, text="CATEGORÍA ORIGINAL",
                  font=("Segoe UI", 10, "bold"), width=22, anchor="center").pack(side="left", padx=5)
        ttk.Label(encabezados, text="CATEGORÍA ACTUAL",
                  font=("Segoe UI", 10, "bold"), width=22, anchor="center").pack(side="left", padx=5)
        ttk.Label(encabezados, text="ESTADO",
                  font=("Segoe UI", 10, "bold"), width=15, anchor="center").pack(side="left", padx=5)

        # Contenedor donde van las filas dinámicas
        frame_filas = ttk.Frame(frame_interno)
        frame_filas.pack(fill="both", expand=True)

        # Referencias a los widgets de cada fila
        filas_widgets = []
        # Para saber qué fila está seleccionada
        estado_sel = {"frame_seleccionado": None}

        # ============================================================
        # PANEL INFERIOR
        # ============================================================
        bot = ttk.Frame(ventana)
        bot.pack(fill="x", padx=10, pady=8)

        lbl_contador = ttk.Label(bot, text="")
        lbl_contador.pack(side="left")

        # ============================================================
        # FUNCIONES INTERNAS
        # ============================================================
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
            """Marca visualmente una fila como seleccionada."""
            # Quitar selección previa
            prev = estado_sel.get("frame_seleccionado")
            if prev is not None:
                try:
                    prev.configure(style="TFrame")
                except Exception:
                    pass

            # Marcar la nueva
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
            # Limpiar
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

                # Cada fila es un Frame
                fila_frame = ttk.Frame(frame_filas, style="TFrame")
                fila_frame.pack(fill="x", pady=1)

                # Labels y widget que van dentro
                lbl_desc = ttk.Label(fila_frame, text=desc, width=60, anchor="w")
                lbl_desc.pack(side="left", padx=5)

                lbl_orig = ttk.Label(fila_frame, text=cat_original,
                                     width=22, anchor="center")
                lbl_orig.pack(side="left", padx=5)

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

                # ---------- SELECCIÓN DESDE CUALQUIER PARTE ----------
                def _click_en_fila(event, fd=fila_dict):
                    _seleccionar_fila(fd)

                # Aplicar el binding a la fila y a TODOS sus hijos
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

            # Volver a aplicar scroll en todos los hijos
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

        # Botones inferiores
        ttk.Button(bot, text="💾 Guardar cambios",
                   command=_guardar,
                   bootstyle="success").pack(side="right", padx=4)
        ttk.Button(bot, text="↶ Deshacer todo",
                   command=_deshacer_todo,
                   bootstyle="warning").pack(side="right", padx=4)
        ttk.Button(bot, text="Cerrar",
                   command=ventana.destroy,
                   bootstyle="secondary").pack(side="right", padx=4)

        # Conectar búsqueda y filtros
        var_buscar.trace_add("write", _refrescar_lista)
        var_filtro.trace_add("write", _refrescar_lista)
        var_origen.trace_add("write", _refrescar_lista)

        # Estilo visual para la fila seleccionada
        style = ttk.Style()
        style.configure("Seleccion.TFrame", background="#cce5ff")

        # Primera carga
        _refrescar_lista()

        # Aplicar scroll con rueda a TODO el frame (por si acaso)
        _bind_mousewheel(canvas)
        _bind_mousewheel(frame_interno)

# ============================================================
if __name__ == "__main__":
    app = AppIngresos()
    app.mainloop()