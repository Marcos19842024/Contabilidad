"""
modulos/lector_facturas.py
Lee facturas CFDI 4.0 (XML) + PDF de representación impresa.

ESTRATEGIA (v3):
  - El PDF es la FUENTE DE PRODUCTOS: nombre, cantidad, descuento,
    importe, remisión. Cada producto viene en UNA línea.
  - El XML solo aporta cabecera (RFC, nombre, folio, fecha, total).
  - El tipo de impuesto (IVA/IEPS/sin impuesto) se infiere de la
    tasa que aparece en la columna "Impuesto" del PDF.
  - El "Importe" del PDF se guarda tal cual y la fórmula del Excel
    lleva el divisor para que la celda contigua multiplique por la tasa.

REGLAS:
  - SIEMPRE deben venir XML + PDF. Si falta uno → error.
  - El total del XML NUNCA se pisa con el del PDF.
  - Cada columna del Excel tiene un único tratamiento fiscal.
  - Se valida que la suma de importes por remisión coincida con el
    total de la remisión (renglón que solo es un número).
"""
import sys
import os
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# --- Asegurar que la raíz del proyecto esté en sys.path ---
_raiz = Path(__file__).resolve().parent.parent
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

from core.rutas import _CARPETA_DATOS as _CARPETA_DATOS_INGRESOS


# ============================================================
# RUTAS
# ============================================================
def _carpeta_datos():
    return _CARPETA_DATOS_INGRESOS


def _ruta_recurso(nombre_archivo):
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / nombre_archivo
    else:
        return Path(__file__).parent.parent / nombre_archivo


def ruta_catalogo_usuario():
    """Ruta donde vive el catálogo del usuario."""
    return _carpeta_datos() / "catalogo_qvet.json"


def recargar_catalogo():
    """Fuerza recarga del catálogo (limpia la caché global)."""
    global _CATALOGO
    _CATALOGO = None
    return cargar_catalogo()


# ============================================================
# CATÁLOGO
# ============================================================
_CATALOGO = None
_EXCEPCIONES_MANUALES = None


def cargar_catalogo():
    global _CATALOGO
    if _CATALOGO is not None:
        return _CATALOGO

    ruta_usuario = ruta_catalogo_usuario()
    ruta_recurso = _ruta_recurso("catalogo_qvet.json")
    ruta = ruta_usuario if ruta_usuario.exists() else ruta_recurso

    if not ruta.exists():
        print("⚠️  No se encontró catalogo_qvet.json")
        _CATALOGO = {}
        return _CATALOGO

    with open(ruta, "r", encoding="utf-8") as f:
        _CATALOGO = json.load(f)
    print(f"✅ Catálogo cargado: {len(_CATALOGO)} productos desde {ruta}")
    return _CATALOGO


def cargar_excepciones_manuales():
    global _EXCEPCIONES_MANUALES
    if _EXCEPCIONES_MANUALES is not None:
        return _EXCEPCIONES_MANUALES

    ruta = _carpeta_datos() / "categorias_manuales.json"
    if ruta.exists():
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                _EXCEPCIONES_MANUALES = json.load(f)
        except Exception:
            _EXCEPCIONES_MANUALES = {}
    else:
        _EXCEPCIONES_MANUALES = {}
    return _EXCEPCIONES_MANUALES


def guardar_excepciones_manuales(exc):
    global _EXCEPCIONES_MANUALES
    _EXCEPCIONES_MANUALES = dict(exc)

    carpeta = _carpeta_datos()
    ruta = carpeta / "categorias_manuales.json"

    if ruta.exists():
        hoy = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir = carpeta / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup = backup_dir / f"categorias_manuales_{hoy}.json"
        try:
            import shutil
            shutil.copy2(ruta, backup)
        except Exception:
            pass

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(exc, f, ensure_ascii=False, indent=2, sort_keys=True)


def normalizar(texto):
    if not texto:
        return ""
    t = str(texto).strip().upper()
    reemplazos = {
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "À": "A", "È": "E", "Ì": "I", "Ò": "O", "Ù": "U",
        "Ñ": "N", "Ü": "U",
    }
    for a, b in reemplazos.items():
        t = t.replace(a, b)
    t = re.sub(r"\s+", " ", t)
    return t


def clasificar_por_descripcion(descripcion):
    """Devuelve la categoría o 'U' si no se encuentra."""
    if not descripcion:
        return "U"
    desc_norm = normalizar(descripcion)

    exc = cargar_excepciones_manuales()
    if desc_norm in exc:
        return exc[desc_norm]

    catalogo = cargar_catalogo()
    if desc_norm in catalogo:
        return catalogo[desc_norm]

    mejor_match = None
    mejor_len = 0
    for clave, cat in catalogo.items():
        if desc_norm.startswith(clave) and len(clave) > mejor_len:
            mejor_match = cat
            mejor_len = len(clave)
    if mejor_match:
        return mejor_match

    for clave, cat in catalogo.items():
        if desc_norm in clave and len(clave) - len(desc_norm) < 20:
            return cat

    return "U"


# ============================================================
# LECTOR DE XML (solo cabecera)
# ============================================================
NS_CFDI = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
}


def leer_xml_factura(ruta_xml):
    """
    Lee solo la cabecera del XML. Los productos vienen del PDF.
    """
    tree = ET.parse(ruta_xml)
    root = tree.getroot()

    serie = (root.get("Serie") or "").strip()
    folio = (root.get("Folio") or "").strip()
    no_factura = folio
    qvet = f"{serie}/{folio}".upper() if serie and folio else serie.upper()

    fecha = _iso_a_ddmmyyyy(root.get("Fecha", ""))
    total = float(root.get("Total", 0) or 0)
    subtotal = float(root.get("SubTotal", 0) or 0)

    receptor = root.find("cfdi:Receptor", NS_CFDI)
    rfc_receptor = receptor.get("Rfc", "") if receptor is not None else ""
    nombre_receptor = receptor.get("Nombre", "") if receptor is not None else ""

    iva_total = 0.0
    ieps_total = 0.0
    base_con_iva = 0.0
    base_exenta = 0.0
    for traslado in root.findall(
            "cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado", NS_CFDI):
        impuesto = traslado.get("Impuesto", "")
        tipo = traslado.get("TipoFactor", "")
        base = float(traslado.get("Base", 0) or 0)
        imp = float(traslado.get("Importe", 0) or 0)
        if impuesto == "002":
            if tipo == "Exento":
                base_exenta += base
            else:
                base_con_iva += base
                iva_total += imp
        elif impuesto == "003":
            ieps_total += imp

    folio_fiscal = ""
    fecha_impresion = fecha
    tfd = root.find("cfdi:Complemento/tfd:TimbreFiscalDigital", NS_CFDI)
    if tfd is not None:
        folio_fiscal = tfd.get("UUID", "")
        fecha_impresion = _iso_a_ddmmyyyy(tfd.get("FechaTimbrado", ""))

    return {
        "serie": serie,
        "folio": folio,
        "no_factura": no_factura,
        "qvet": qvet,
        "fecha": fecha,
        "fecha_impresion": fecha_impresion,
        "nombre": nombre_receptor,
        "rfc": rfc_receptor,
        "folio_fiscal": folio_fiscal,
        "total": total,
        "subtotal": subtotal,
        "iva_total": round(iva_total, 2),
        "ieps_total": round(ieps_total, 2),
        "base_con_iva": round(base_con_iva, 2),
        "base_exenta": round(base_exenta, 2),
    }


def _iso_a_ddmmyyyy(fecha_iso):
    if not fecha_iso:
        return ""
    try:
        if "T" in fecha_iso:
            dt = datetime.strptime(fecha_iso[:19], "%Y-%m-%dT%H:%M:%S")
        else:
            dt = datetime.strptime(fecha_iso[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return fecha_iso


# ============================================================
# LECTOR DE PDF
# ============================================================
def _conv_numero_simple(s):
    """Convierte '1.149,00' → 1149.0 / '18.05' → 18.05 / '120,00' → 120.0."""
    s = s.strip()
    if not s:
        return 0.0
    tiene_punto = "." in s
    tiene_coma = "," in s
    if tiene_punto and tiene_coma:
        pos_punto = s.rfind(".")
        pos_coma = s.rfind(",")
        if pos_coma > pos_punto:
            # Formato MX: 1.149,00 → 1149.00
            s = s.replace(".", "").replace(",", ".")
        else:
            # Formato US: 1,149.00 → 1149.00
            s = s.replace(",", "")
    elif tiene_coma:
        # Solo coma → es decimal MX: 120,00 → 120.00
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


# --- Patrones ---

# Línea de remisión
_RE_REMISION = re.compile(
    r"No\.\s*Remisi[oó]n:\s*(\d+)",
    re.IGNORECASE
)

# Línea que es solo un número (total de remisión)
_RE_TOTAL_REMISION = re.compile(r"^\s*[\d.,]+\s*$")

# Línea de encabezado de tabla
_RE_ENCABEZADO_TABLA = re.compile(
    r"Descripci[oó]n\s+del\s+producto",
    re.IGNORECASE
)

# Línea de producto: nombre + cantidad + unidad + PVP + Dto + Impuesto + Importe
# El ancla es "<cantidad>[,.]<dec> <unidad>"
_RE_PRODUCTO = re.compile(
    r"^(?P<nombre>.+?)\s+"              # nombre (no greedy)
    r"(?P<cantidad>\d+[,.]\d+)\s+"      # cantidad: 1,00
    r"(?P<unidad>[^\d]+?)\s+"           # unidad: "no aplica" o similar (no empieza con número)
    r"(?P<pvp>[\d.,]+)\s+"              # PVP
    r"(?P<dto>[\d.,]+)\s+"              # Dto
    r"(?P<impuesto>"
    r"(?:\d+[,.]\d+\s*%\s*\d*,?)"       # "16,00% 0," / "16,00%15" / "6,00% 0,"
    r"|(?:\d+,)"                        # "0," / "5,"  (sin impuesto)
    r")\s+"
    r"(?P<importe>[\d.,]+)\s*$",
    re.IGNORECASE
)

# Tasas conocidas
_RE_TASA_EN_IMPUESTO = re.compile(r"(\d+[,.]\d+)\s*%")


def _clasificar_tasa_pdf(tasa_num):
    """Devuelve el tipo de impuesto a partir de la tasa numérica."""
    if abs(tasa_num - 16.0) < 0.01:
        return "iva"
    if abs(tasa_num - 6.0) < 0.01:
        return "ieps_6"
    if abs(tasa_num - 7.0) < 0.01:
        return "ieps_7"
    if abs(tasa_num) < 0.01:
        return "sin_imp"
    return "iva"  # fallback


def _parsear_linea_producto(linea):
    """
    Intenta parsear una línea de producto del PDF.
    Devuelve dict o None.
    """
    m = _RE_PRODUCTO.match(linea.strip())
    if not m:
        return None

    nombre = m.group("nombre").strip()
    nombre = re.sub(r"[\s,;:.]+$", "", nombre)
    if not nombre or len(nombre) < 2:
        return None

    cantidad = _conv_numero_simple(m.group("cantidad").replace(",", "."))
    unidad = m.group("unidad").strip()
    pvp = _conv_numero_simple(m.group("pvp"))
    dto = _conv_numero_simple(m.group("dto"))
    impuesto_str = m.group("impuesto")
    importe = _conv_numero_simple(m.group("importe"))

    # Extraer tasa del texto de impuesto
    m_tasa = _RE_TASA_EN_IMPUESTO.search(impuesto_str)
    if m_tasa:
        tasa_num = _conv_numero_simple(m_tasa.group(1).replace(",", "."))
    else:
        tasa_num = 0.0

    return {
        "nombre": nombre,
        "cantidad": cantidad,
        "unidad": unidad,
        "pvp": pvp,
        "descuento_pct": dto,
        "tasa_num": tasa_num,
        "tipo_impuesto": _clasificar_tasa_pdf(tasa_num),
        "importe_pdf": importe,
    }


def _leer_productos_por_remision(texto):
    """
    Devuelve:
      {
        rem: {
          "productos": [ {nombre, cantidad, ..., importe_pdf}, ... ],
          "total_remision": float | None,   # del renglón "525,00" solo
        }
      }
    """
    lineas = [l.rstrip() for l in texto.split("\n")]

    resultado = {}
    rem_actual = None

    for linea in lineas:
        linea_s = linea.strip()

        # --- Detectar remisión ---
        m_rem = _RE_REMISION.search(linea_s)
        if m_rem:
            rem_actual = m_rem.group(1)
            if rem_actual not in resultado:
                resultado[rem_actual] = {
                    "productos": [],
                    "total_remision": None,
                }
            continue

        if rem_actual is None:
            continue

        # --- Saltar líneas no relevantes ---
        if not linea_s:
            continue
        if _RE_ENCABEZADO_TABLA.search(linea_s):
            continue

        # --- Línea de total de remisión (solo un número) ---
        if _RE_TOTAL_REMISION.match(linea_s):
            # Solo la primera cuenta como total (evita sobreescribir si hay más)
            if resultado[rem_actual]["total_remision"] is None:
                resultado[rem_actual]["total_remision"] = \
                    _conv_numero_simple(linea_s)
            continue

        # --- Intento de producto ---
        p = _parsear_linea_producto(linea_s)
        if p:
            resultado[rem_actual]["productos"].append(p)
            continue

        # Si no es producto ni total, es una línea que no nos interesa
        # (por ejemplo, encabezados de pago, TOTAL $, etc.)

    return resultado


def _leer_total_pdf(ruta_pdf):
    try:
        import pdfplumber
    except ImportError:
        return None
    with pdfplumber.open(ruta_pdf) as pdf:
        texto = "\n".join((p.extract_text() or "") for p in pdf.pages)
    m = re.search(
        r"TOTAL\s*\$?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})",
        texto, re.IGNORECASE
    )
    if m:
        return _conv_numero_simple(m.group(1))
    return None


def leer_pdf_completo(ruta_pdf):
    """
    Lee el PDF y devuelve:
      {
        "productos": {rem: {...}},
        "pagos": {...}
      }
    """
    try:
        import pdfplumber
    except ImportError:
        return {"productos": {}, "pagos": {}}

    texto_completo = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text() or ""
            texto_completo.append(t)
    texto = "\n".join(texto_completo)

    productos = _leer_productos_por_remision(texto)

    # ---- Pagos ----
    pagos = {
        "efectivo": 0.0, "tc": 0.0, "td": 0.0,
        "cheque": 0.0, "transfer": 0.0, "vale": 0.0,
    }

    MAPA_FORMA_PAGO = {
        "01": "efectivo", "02": "cheque", "03": "transfer",
        "04": "tc", "28": "td",
    }

    patron_pago = re.compile(
        r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"
        r"(\d{2})\s+"
        r"(T\.\s*CREDITO|T\.\s*DEBITO|EFECTIVO|"
        r"CHEQUE|TRANSFERENCIA|TRANSF\.?|VALE)"
        r"\s+"
        r"([\d.,]+)",
        re.IGNORECASE
    )
    for match in patron_pago.finditer(texto):
        codigo = match.group(2)
        importe = _conv_numero_simple(match.group(4))
        clave = MAPA_FORMA_PAGO.get(codigo)
        if clave and importe > 0:
            pagos[clave] += importe

    if not any(v > 0 for v in pagos.values()):
        for linea in texto.split("\n"):
            linea_upper = linea.upper()
            clave_detectada = None
            if "T. CREDITO" in linea_upper or "T.CREDITO" in linea_upper:
                clave_detectada = "tc"
            elif "T. DEBITO" in linea_upper or "T.DEBITO" in linea_upper:
                clave_detectada = "td"
            elif "EFECTIVO" in linea_upper:
                clave_detectada = "efectivo"
            elif "TRANSFERENCIA" in linea_upper:
                clave_detectada = "transfer"
            elif "CHEQUE" in linea_upper:
                clave_detectada = "cheque"
            elif "VALE" in linea_upper:
                clave_detectada = "vale"

            if clave_detectada:
                m_imp = re.search(
                    r"(?:T\.\s*CREDITO|T\.\s*DEBITO|EFECTIVO|"
                    r"CHEQUE|TRANSFERENCIA|TRANSF\.?|VALE)\s+"
                    r"([\d.,]+)",
                    linea, re.IGNORECASE
                )
                if m_imp:
                    importe = _conv_numero_simple(m_imp.group(1))
                    if importe > 0:
                        pagos[clave_detectada] += importe

    return {"productos": productos, "pagos": pagos}


def _leer_forma_pago_xml(ruta_xml):
    try:
        tree = ET.parse(ruta_xml)
        root = tree.getroot()
        forma = (root.get("FormaPago") or "").strip()
    except Exception:
        return None
    mapa = {"01": "efectivo", "02": "cheque", "03": "transfer",
            "04": "tc", "28": "td"}
    return mapa.get(forma)


# ============================================================
# PROCESAR FACTURA
# ============================================================
def procesar_factura(ruta_xml=None, ruta_pdf=None):
    """
    Lee el XML (cabecera) y el PDF (productos + pagos).
    """
    if not ruta_xml:
        raise ValueError("Falta el XML de la factura.")
    if not ruta_pdf:
        raise ValueError("Falta el PDF de la factura.")

    datos = leer_xml_factura(ruta_xml)

    pdf_data = leer_pdf_completo(ruta_pdf)
    productos_por_rem = pdf_data.get("productos", {})
    pagos = pdf_data.get("pagos", {})
    total_pdf = _leer_total_pdf(ruta_pdf)

    if not productos_por_rem:
        raise ValueError(
            "El PDF no contiene productos legibles.\n\n"
            "Verifica que sea la representación impresa de la factura."
        )

    # Log de diferencia XML vs PDF
    if total_pdf is not None:
        dif = round(datos["total"] - total_pdf, 2)
        if abs(dif) > 0.001:
            print(f"ℹ️  Diferencia XML vs PDF: ${dif:+.2f} "
                  f"(XML=${datos['total']} PDF=${total_pdf}) — se usa XML")

    # Fallback de pagos con FormaPago del XML
    if not any(v > 0 for v in pagos.values()):
        forma_xml = _leer_forma_pago_xml(ruta_xml)
        if forma_xml:
            pagos[forma_xml] = datos["total"]
            print(f"ℹ️  Pagos del PDF no detectados. Usando FormaPago XML: {forma_xml}")

    # ---- Validar suma de productos vs total de cada remisión ----
    remisiones_con_problema = []
    for rem, info in productos_por_rem.items():
        prods = info.get("productos", [])
        total_rem = info.get("total_remision")
        if not prods or total_rem is None:
            continue
        suma = round(sum(p["importe_pdf"] for p in prods), 2)
        if abs(suma - total_rem) > 0.02:
            remisiones_con_problema.append({
                "remision": rem,
                "suma": suma,
                "total": total_rem,
                "dif": round(total_rem - suma, 2),
            })

    if remisiones_con_problema:
        print("⚠️  Remisiones con discrepancia entre suma de productos y total:")
        for r in remisiones_con_problema:
            print(f"    Rem {r['remision']}: suma={r['suma']} "
                  f"total={r['total']} (dif={r['dif']:+.2f})")

    # Reestructurar al formato que espera agrupar_por_categoria
    productos_por_remision = {}
    for rem, info in productos_por_rem.items():
        productos_por_remision[rem] = info["productos"]

    datos["productos_por_remision"] = productos_por_remision
    datos["remisiones_con_problema"] = remisiones_con_problema
    datos["pagos"] = pagos
    return datos


# ============================================================
# AGRUPAR POR CATEGORÍA
# ============================================================
_DIVISOR = {
    "iva": 1.16,
    "ieps_6": 1.06,
    "ieps_7": 1.07,
    "sin_imp": 1.0,
}


def _fmt_expr(v):
    return f"{round(float(v), 2):.2f}"


def _construir_formula(grupos_por_remision, divisor):
    """
    Construye la fórmula Excel.

    grupos_por_remision: lista de listas de valores.
      Ej: [[114, 100], [200], [58]]

    divisor: 1.0 (sin impuesto) o > 1 (1.16, 1.06, 1.07)
    """
    if not grupos_por_remision:
        return ""

    def _grupo_expr(valores):
        if len(valores) == 1:
            return _fmt_expr(valores[0])
        return "(" + "+".join(_fmt_expr(v) for v in valores) + ")"

    grupos_expr = [_grupo_expr(g) for g in grupos_por_remision]

    if divisor == 1.0:
        if len(grupos_expr) == 1:
            return grupos_expr[0]
        return "+".join(grupos_expr)

    cuerpo = "+".join(grupos_expr)
    if len(grupos_por_remision) == 1 and len(grupos_por_remision[0]) == 1:
        return f"{cuerpo}/{divisor}"
    return f"({cuerpo})/{divisor}"


def agrupar_por_categoria(datos, ajustar_centavos=True):
    """
    Agrupa los productos del PDF por categoría y tipo fiscal.

    Devuelve:
      - agrupado: totales por categoría (numéricos)
      - detalle: fórmulas por columna (string)
      - avisos_reclasificacion: VACUNA/CLINICA con IVA, etc.
      - no_catalogados: productos que no están en el catálogo (U)
    """
    info_factura = {
        "no_factura": datos.get("no_factura", ""),
        "nombre": datos.get("nombre", ""),
        "folio_fiscal": datos.get("folio_fiscal", ""),
        "fecha": datos.get("fecha", ""),
        "total": datos.get("total", 0.0),
    }

    agrupado = {}
    avisos_reclasificacion = []
    no_catalogados = []

    CATEGORIAS_SIN_IVA = ("VACUNA", "CLINICA")
    CATEGORIAS_VALIDAS = {
        "U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
        "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA",
    }

    productos_por_remision = datos.get("productos_por_remision", {})
    if not productos_por_remision:
        return {}, {}, [], []

    # Recolectar todos los productos
    productos_todos = []
    for rem, prods in productos_por_remision.items():
        for p in prods:
            tipo = p.get("tipo_impuesto")
            if not tipo:
                tasa = p.get("tasa_num", 0.0)
                tipo = "iva" if tasa > 0 else "sin_imp"
            productos_todos.append({
                "remision": rem,
                "nombre": p.get("nombre", ""),
                "cantidad": p.get("cantidad", 1.0),
                "importe": p.get("importe_pdf", 0.0),
                "tipo": tipo,
                "tasa": p.get("tasa_num", 0.0),
            })

    # Deduplicar por (remisión, nombre, cantidad)
    def _clave_dedup(p):
        return (p["remision"], normalizar(p["nombre"]), round(p["cantidad"], 2))

    vistos = set()
    productos_unicos = []
    for p in productos_todos:
        k = _clave_dedup(p)
        if k in vistos:
            print(f"ℹ️  Deduplicado: {p['nombre']} (remisión {p['remision']})")
            continue
        vistos.add(k)
        productos_unicos.append(p)

    # Clasificar y separar por categoría + tipo fiscal
    buckets = defaultdict(lambda: defaultdict(list))

    for p in productos_unicos:
        nombre = p["nombre"]
        importe = p["importe"]
        tipo = p["tipo"]
        tasa = p["tasa"]
        rem = p["remision"]

        cat = clasificar_por_descripcion(nombre)
        no_catalogado = (cat == "U")

        if cat not in CATEGORIAS_VALIDAS:
            cat = "U"

        cat_original = cat

        if cat in CATEGORIAS_SIN_IVA and tipo != "sin_imp":
            cat = "U"

        buckets[(cat, tipo)][rem].append(importe)

        if cat_original in CATEGORIAS_SIN_IVA and cat == "U":
            base_aviso = importe if tipo == "sin_imp" else importe / (1 + (tasa / 100.0))
            avisos_reclasificacion.append({
                "categoria_actual": cat_original,
                "producto": nombre,
                "remision": rem,
                "importe": round(base_aviso, 2),
                **info_factura,
            })

        if no_catalogado:
            no_catalogados.append({
                "categoria_actual": "U",
                "producto": nombre,
                "remision": rem,
                "importe": round(importe, 2),
                "motivo": "no_catalogado",
                **info_factura,
            })

    # --- Agrupado numérico y fórmulas ---
    def _sumar(bucket_dict):
        return round(sum(sum(g) for g in bucket_dict.values()), 2)

    def _formula(bucket_dict, tipo):
        if not bucket_dict:
            return ""
        divisor = _DIVISOR.get(tipo, 1.0)
        grupos = [bucket_dict[r] for r in sorted(bucket_dict.keys())]
        return _construir_formula(grupos, divisor)

    MAPA_CAMPOS = {
        ("U", "sin_imp"): "u_importe",
        ("U", "iva"): "u_importe",
        ("ACCESORIOS", "sin_imp"): "ac_importe",
        ("ACCESORIOS", "iva"): "ac_importe",
        ("ESTETICA", "sin_imp"): "est_importe",
        ("ESTETICA", "iva"): "est_importe",
        ("TRANSPORTE", "sin_imp"): "tra_importe",
        ("TRANSPORTE", "iva"): "tra_importe",
        ("PENSION", "sin_imp"): "pen_importe",
        ("PENSION", "iva"): "pen_importe",
        ("VACUNA", "sin_imp"): "vac_importe",
        ("CLINICA", "sin_imp"): "cli_importe",
        ("MEDICAMENTOS", "sin_imp"): "med_importe",
        ("MEDICAMENTOS", "iva"): "med_sin_iva",
        ("HIGIENE", "sin_imp"): "hig_importe",
        ("HIGIENE", "iva"): "hig_sin_iva",
        ("HIGIENE", "ieps_6"): "hig_sin_ieps_6",
        ("HIGIENE", "ieps_7"): "hig_sin_ieps_7",
    }

    detalle_por_campo = defaultdict(list)

    for (cat, tipo), buckets_cat in buckets.items():
        campo = MAPA_CAMPOS.get((cat, tipo))
        if not campo:
            continue

        formula = _formula(buckets_cat, tipo)
        if formula:
            detalle_por_campo[campo].append(formula)

        total_con_imp = _sumar(buckets_cat)

        if tipo == "sin_imp":
            base = total_con_imp
        elif tipo == "iva":
            base = round(total_con_imp / 1.16, 2)
        elif tipo == "ieps_6":
            base = round(total_con_imp / 1.06, 2)
        elif tipo == "ieps_7":
            base = round(total_con_imp / 1.07, 2)
        else:
            base = total_con_imp

        if cat not in agrupado:
            agrupado[cat] = {
                "importe": 0.0, "sin_iva": 0.0, "iva": 0.0,
                "sin_ieps_6": 0.0, "ieps_6": 0.0,
                "sin_ieps_7": 0.0, "ieps_7": 0.0,
            }

        if tipo == "sin_imp":
            agrupado[cat]["importe"] += base
        elif tipo == "iva":
            agrupado[cat]["sin_iva"] += base
            agrupado[cat]["iva"] += round(base * 0.16, 2)
        elif tipo == "ieps_6":
            agrupado[cat]["sin_ieps_6"] += base
            agrupado[cat]["ieps_6"] += round(base * 0.06, 2)
        elif tipo == "ieps_7":
            agrupado[cat]["sin_ieps_7"] += base
            agrupado[cat]["ieps_7"] += round(base * 0.07, 2)

    for cat, vals in agrupado.items():
        for k in vals:
            vals[k] = round(vals[k], 2)

    # Ajuste de centavos
    if ajustar_centavos:
        suma_bases = 0.0
        for cat, vals in agrupado.items():
            suma_bases += vals["importe"]
            suma_bases += vals["sin_iva"]
            suma_bases += vals["sin_ieps_6"]
            suma_bases += vals["sin_ieps_7"]
        suma_impuestos = sum(
            vals["iva"] + vals["ieps_6"] + vals["ieps_7"]
            for vals in agrupado.values()
        )
        total_calculado = round(suma_bases + suma_impuestos, 2)
        total_objetivo = round(datos.get("total", 0), 2)
        dif = round(total_objetivo - total_calculado, 2)

        if abs(dif) == 0.01:
            cat_mayor = None
            monto_mayor = 0.0
            for cat, vals in agrupado.items():
                m = (vals["importe"] + vals["sin_iva"]
                     + vals["sin_ieps_6"] + vals["sin_ieps_7"])
                if m > monto_mayor:
                    monto_mayor = m
                    cat_mayor = cat
            if cat_mayor:
                if agrupado[cat_mayor]["importe"] > 0:
                    agrupado[cat_mayor]["importe"] = round(
                        agrupado[cat_mayor]["importe"] + dif, 2)
                elif agrupado[cat_mayor]["sin_iva"] > 0:
                    agrupado[cat_mayor]["sin_iva"] = round(
                        agrupado[cat_mayor]["sin_iva"] + dif, 2)
                elif agrupado[cat_mayor]["sin_ieps_6"] > 0:
                    agrupado[cat_mayor]["sin_ieps_6"] = round(
                        agrupado[cat_mayor]["sin_ieps_6"] + dif, 2)
                elif agrupado[cat_mayor]["sin_ieps_7"] > 0:
                    agrupado[cat_mayor]["sin_ieps_7"] = round(
                        agrupado[cat_mayor]["sin_ieps_7"] + dif, 2)
                print(f"ℹ️  Ajuste de centavos: ${dif:+.2f} → {cat_mayor}")

    detalle = {}
    for campo, formulas in detalle_por_campo.items():
        detalle[campo] = "+".join(formulas)

    return agrupado, detalle, avisos_reclasificacion, no_catalogados


# ============================================================
# AGREGAR PRODUCTO AL CATÁLOGO
# ============================================================
def agregar_producto_catalogo(nombre, categoria):
    nombre_norm = normalizar(nombre)
    if not nombre_norm:
        return False, "El nombre está vacío"

    CATEGORIAS_VALIDAS = {"U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
                          "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA"}
    if categoria not in CATEGORIAS_VALIDAS:
        return False, f"Categoría inválida: {categoria}"

    exc = dict(cargar_excepciones_manuales())
    ya_existia = nombre_norm in exc
    exc[nombre_norm] = categoria
    guardar_excepciones_manuales(exc)

    if ya_existia:
        return True, f"Producto actualizado: {nombre} → {categoria}"
    return True, f"Producto agregado: {nombre} → {categoria}"


# ============================================================
# PRUEBA RÁPIDA
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python lector_facturas.py <ruta_xml> <ruta_pdf>")
        sys.exit(1)
    ruta_xml = sys.argv[1]
    ruta_pdf = sys.argv[2]

    datos = procesar_factura(ruta_xml, ruta_pdf)

    print("\n=== CABECERA ===")
    for k in ["no_factura", "qvet", "fecha", "fecha_impresion", "rfc",
              "nombre", "folio_fiscal", "total", "subtotal"]:
        print(f"  {k:20}: {datos.get(k)}")

    print("\n=== PRODUCTOS POR REMISIÓN (del PDF) ===")
    for rem, prods in datos["productos_por_remision"].items():
        print(f"  Remisión {rem}:")
        for p in prods:
            print(f"    {p['nombre'][:45]:45} ${p['importe_pdf']:>9,.2f} "
                  f"[{p['tipo_impuesto']:8} {p['tasa_num']:5.1f}%] "
                  f"(dto {p['descuento_pct']:.1f}%)")

    if datos.get("remisiones_con_problema"):
        print("\n=== ⚠️ REMISIONES CON DISCREPANCIA ===")
        for r in datos["remisiones_con_problema"]:
            print(f"  Rem {r['remision']}: "
                  f"suma={r['suma']} total={r['total']} dif={r['dif']:+.2f}")

    print("\n=== AGRUPADO ===")
    agr, det, avisos, no_cat = agrupar_por_categoria(datos)
    for cat, vals in agr.items():
        print(f"  {cat}:")
        for k, v in vals.items():
            if v:
                print(f"    {k:14} = {v}")

    print("\n=== DETALLE (fórmulas) ===")
    for campo, expr in det.items():
        print(f"  {campo:20} ={expr}")

    if no_cat:
        print(f"\n=== NO CATALOGADOS ({len(no_cat)}) ===")
        for n in no_cat:
            print(f"  {n['producto']} (rem {n['remision']})")

    if avisos:
        print(f"\n=== AVISOS RECLASIFICACIÓN ({len(avisos)}) ===")
        for a in avisos:
            print(f"  [{a['categoria_actual']}] {a['producto']} (rem {a['remision']})")