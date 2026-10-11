"""
modulos/lector_facturas.py
Lee facturas CFDI 4.0 (XML) + PDF de representación impresa.
Clasifica conceptos por descripción usando catalogo_qvet.json (editado a mano).

REGLAS:
  - SIEMPRE deben venir XML + PDF. Si falta uno → error.
  - Los productos se leen del PDF (por remisión). El XML solo da cabecera.
  - El total del XML NUNCA se pisa con el del PDF.
  - Cada columna del Excel tiene un único tratamiento fiscal.

Nota: este módulo vive en `modulos/` pero usa las rutas de datos de Ingresos
(core.rutas) para no ensuciar la raíz del proyecto.
"""
import sys
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from collections import defaultdict

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


# ============================================================
# CATÁLOGO
# ============================================================
_CATALOGO = None
_EXCEPCIONES_MANUALES = None


def cargar_catalogo():
    global _CATALOGO
    if _CATALOGO is not None:
        return _CATALOGO

    ruta_usuario = _carpeta_datos() / "catalogo_qvet.json"
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
def leer_xml_factura(ruta_xml):
    NS = {
        "cfdi": "http://www.sat.gob.mx/cfd/4",
        "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
    }

    tree = ET.parse(ruta_xml)
    root = tree.getroot()

    serie = (root.get("Serie") or "").strip()
    folio = (root.get("Folio") or "").strip()
    no_factura = folio
    qvet = f"{serie}/{folio}".upper() if serie and folio else serie.upper()

    fecha = _iso_a_ddmmyyyy(root.get("Fecha", ""))
    total = float(root.get("Total", 0) or 0)
    subtotal = float(root.get("SubTotal", 0) or 0)

    receptor = root.find("cfdi:Receptor", NS)
    rfc_receptor = receptor.get("Rfc", "") if receptor is not None else ""
    nombre_receptor = receptor.get("Nombre", "") if receptor is not None else ""

    iva_total = 0.0
    base_con_iva = 0.0
    base_exenta = 0.0
    for traslado in root.findall(
            "cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado", NS):
        impuesto = traslado.get("Impuesto", "")
        tipo = traslado.get("TipoFactor", "")
        base = float(traslado.get("Base", 0) or 0)
        if impuesto != "002":
            continue
        if tipo == "Exento":
            base_exenta += base
        else:
            base_con_iva += base
            iva_total += float(traslado.get("Importe", 0) or 0)

    folio_fiscal = ""
    fecha_impresion = fecha
    tfd = root.find("cfdi:Complemento/tfd:TimbreFiscalDigital", NS)
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
    s = s.strip()
    if not s:
        return 0.0
    tiene_punto = "." in s
    tiene_coma = "," in s
    if tiene_punto and tiene_coma:
        pos_punto = s.rfind(".")
        pos_coma = s.rfind(",")
        if pos_coma > pos_punto:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif tiene_coma:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def leer_pdf_completo(ruta_pdf):
    """
    Lee el PDF y devuelve:
      {
        "productos": {remision: [productos]},
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

    # ---- Productos por remisión ----
    texto_prod = re.sub(r"[ \t]+", " ", texto)
    lineas = [l.strip() for l in texto_prod.split("\n")]

    productos_por_remision = {}
    remision_actual = None

    for linea in lineas:
        m_rem = re.match(
            r"No\.\s*Remisi[oó]n:\s*(\d+)\s+Fecha de remisi[oó]n",
            linea, re.IGNORECASE
        )
        if m_rem:
            remision_actual = m_rem.group(1)
            if remision_actual not in productos_por_remision:
                productos_por_remision[remision_actual] = []
            continue

        if remision_actual and "no aplica" in linea.lower():
            m_prod = re.match(
                r"^(.+?)\s+"
                r"(\d+[,.]\d+)\s+"
                r"no\s+aplica\s+"
                r"([\d.,]+)\s+"
                r"([\d.,]+)\s+"
                r"(?:([\d.,]+)\s*%\s*)?"
                r"0,\s*"
                r"([\d.,]+)$",
                linea, re.IGNORECASE
            )
            if m_prod:
                nombre = m_prod.group(1).strip()
                nombre = re.sub(r"[\s,;:.]+$", "", nombre)
                cantidad_str = m_prod.group(2).replace(",", ".")
                pvp_str = m_prod.group(3)
                tasa_str = m_prod.group(5)
                importe_str = m_prod.group(6)

                if tasa_str:
                    tasa_iva_pdf = _conv_numero_simple(tasa_str) / 100.0
                else:
                    tasa_iva_pdf = 0.0

                if nombre and len(nombre) > 1:
                    productos_por_remision[remision_actual].append({
                        "nombre": nombre,
                        "cantidad": float(cantidad_str) if cantidad_str else 1.0,
                        "precio_sin_iva": _conv_numero_simple(pvp_str),
                        "tasa_iva_pdf": tasa_iva_pdf,
                        "importe_pdf": _conv_numero_simple(importe_str),
                    })

    # ---- Pagos ----
    pagos = {
        "efectivo": 0.0, "tc": 0.0, "td": 0.0,
        "cheque": 0.0, "transfer": 0.0, "vale": 0.0,
    }

    MAPA_FORMA_PAGO = {
        "01": "efectivo", "02": "cheque", "03": "transfer",
        "04": "tc", "28": "td",
    }

    def _conv_numero(s):
        s = s.strip()
        if not s:
            return 0.0
        tiene_punto = "." in s
        tiene_coma = "," in s
        if tiene_punto and tiene_coma:
            pos_punto = s.rfind(".")
            pos_coma = s.rfind(",")
            if pos_coma > pos_punto:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif tiene_coma:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return 0.0

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
        importe_str = match.group(4)
        importe = _conv_numero(importe_str)
        clave = MAPA_FORMA_PAGO.get(codigo)
        if clave and importe > 0:
            pagos[clave] += importe

    if not any(v > 0 for v in pagos.values()):
        for linea in lineas:
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
                    importe = _conv_numero(m_imp.group(1))
                    if importe > 0:
                        pagos[clave_detectada] += importe

    return {"productos": productos_por_remision, "pagos": pagos}


def _leer_total_pdf(ruta_pdf):
    try:
        import pdfplumber
    except ImportError:
        return None
    with pdfplumber.open(ruta_pdf) as pdf:
        texto = "\n".join((p.extract_text() or "") for p in pdf.pages)
    m = re.search(
        r"TOTAL\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})",
        texto, re.IGNORECASE
    )
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _leer_forma_pago_xml(ruta_xml):
    NS = {
        "cfdi": "http://www.sat.gob.mx/cfd/4",
    }
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
    Lee el XML y el PDF.
    Ambos son OBLIGATORIOS. Si falta uno, se lanza ValueError.
    """
    if not ruta_xml:
        raise ValueError("Falta el XML de la factura.")
    if not ruta_pdf:
        raise ValueError("Falta el PDF de la factura.")

    datos = leer_xml_factura(ruta_xml)

    pdf_data = leer_pdf_completo(ruta_pdf)
    productos_por_remision = pdf_data.get("productos", {})
    pagos = pdf_data.get("pagos", {})
    total_pdf = _leer_total_pdf(ruta_pdf)

    if not productos_por_remision:
        raise ValueError(
            "El PDF no contiene productos legibles.\n\n"
            "Verifica que sea la representación impresa de la factura."
        )

    # Log de diferencia XML vs PDF (no pisamos el XML)
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

    datos["productos_por_remision"] = productos_por_remision
    datos["pagos"] = pagos
    return datos


# ============================================================
# AGRUPAR POR CATEGORÍA
# ============================================================
# Divisores por tipo fiscal
_DIVISOR = {
    "iva": 1.16,
    "ieps_6": 1.06,
    "ieps_7": 1.07,
    "sin_imp": 1.0,
}


def _fmt_expr(v):
    """Formatea un número para expresión (2 decimales)."""
    return f"{round(float(v), 2):.2f}"


def _construir_formula(grupos_por_remision, divisor):
    """
    Construye la fórmula Excel para una columna.

    grupos_por_remision: lista de listas de valores.
      Ej: [[114, 100], [200], [58]]

    divisor: 1.0 (sin impuesto) o > 1 (1.16, 1.06, 1.07)

    Devuelve el string SIN el "=" inicial.
      - 1 grupo de 1 valor sin divisor → "58"
      - 1 grupo de 1 valor con divisor → "58/1.16"
      - 1 grupo de N valores sin divisor → "(50+30)"
      - 1 grupo de N valores con divisor → "(114+100)/1.16"
      - N grupos sin divisor → "(50+30)+(80)"
      - N grupos con divisor → "((114+100)+(200)+(58))/1.16"
    """
    if not grupos_por_remision:
        return ""

    # Construir cada grupo
    def _grupo_expr(valores):
        if len(valores) == 1:
            return _fmt_expr(valores[0])
        return "(" + "+".join(_fmt_expr(v) for v in valores) + ")"

    grupos_expr = [_grupo_expr(g) for g in grupos_por_remision]

    if divisor == 1.0:
        # Sin impuesto: solo unir con +
        if len(grupos_expr) == 1:
            return grupos_expr[0]
        return "+".join(grupos_expr)

    # Con impuesto: sacar el divisor al final
    cuerpo = "+".join(grupos_expr)
    # Si hay un solo grupo de un solo valor, sin paréntesis adicional
    if len(grupos_por_remision) == 1 and len(grupos_por_remision[0]) == 1:
        return f"{cuerpo}/{divisor}"
    return f"({cuerpo})/{divisor}"


def agrupar_por_categoria(datos, ajustar_centavos=True):
    """
    Agrupa los productos del PDF por categoría y tipo fiscal.

    Devuelve:
      - agrupado: totales por categoría (numéricos, para validación)
      - detalle: fórmulas por columna (string)
      - avisos_reclasificacion: lista de avisos
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

    CATEGORIAS_SIN_IVA = ("VACUNA", "CLINICA")
    CATEGORIAS_VALIDAS = {
        "U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
        "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA",
    }

    # ============================================================
    # Recolectar productos del PDF
    # ============================================================
    productos_por_remision = datos.get("productos_por_remision", {})
    if not productos_por_remision:
        return {}, {}, []

    # Lista de tuplas (remision, producto_dict, tipo_fiscal)
    productos_todos = []

    for rem, prods in productos_por_remision.items():
        for p in prods:
            nombre = p.get("nombre", "")
            cantidad = p.get("cantidad", 1.0)
            importe = p.get("importe_pdf", 0.0)
            tasa_iva = p.get("tasa_iva_pdf", 0.0)

            if tasa_iva > 0:
                tipo = "iva"
            else:
                tipo = "sin_imp"

            productos_todos.append({
                "remision": rem,
                "nombre": nombre,
                "cantidad": cantidad,
                "importe": importe,
                "tipo": tipo,
                "tasa": tasa_iva if tasa_iva > 0 else 0.0,
            })

    # ============================================================
    # Deduplicar por (nombre, cantidad) dentro de la misma remisión
    # ============================================================
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

    # ============================================================
    # Clasificar y separar por categoría + tipo fiscal
    #
    # Estructura intermedia:
    #   buckets[(cat, tipo)][rem] = [importes sin redondear]
    #
    # Importe para buckets "sin_imp" → valor tal cual
    # Importe para buckets con impuesto → valor / (1+tasa)
    # ============================================================
    buckets = defaultdict(lambda: defaultdict(list))

    for p in productos_unicos:
        nombre = p["nombre"]
        importe = p["importe"]
        tipo = p["tipo"]
        tasa = p["tasa"]
        rem = p["remision"]

        cat = clasificar_por_descripcion(nombre)
        if cat not in CATEGORIAS_VALIDAS:
            cat = "U"

        cat_original = cat

        if cat in CATEGORIAS_SIN_IVA and tipo != "sin_imp":
            cat = "U"

        # ✅ Guardar el importe CON impuesto (el original del PDF)
        # El divisor se aplica en la fórmula y en el cálculo numérico,
        # NO antes.
        buckets[(cat, tipo)][rem].append(importe)

        if cat_original in CATEGORIAS_SIN_IVA and cat == "U":
            base_aviso = importe if tipo == "sin_imp" else importe / (1 + tasa)
            avisos_reclasificacion.append({
                "categoria_actual": cat_original,
                "producto": nombre,
                "remision": rem,
                "importe": round(base_aviso, 2),
                **info_factura,
            })

    # ============================================================
    # Calcular agrupado (numérico) y detalle (fórmulas por columna)
    # ============================================================
    def _sumar(bucket_dict):
        return round(sum(sum(g) for g in bucket_dict.values()), 2)

    def _formula(bucket_dict, tipo):
        if not bucket_dict:
            return ""
        divisor = _DIVISOR.get(tipo, 1.0)
        # Ordenar grupos por remisión (orden numérico)
        grupos = [bucket_dict[r] for r in sorted(bucket_dict.keys())]
        return _construir_formula(grupos, divisor)

    # Mapa: (cat, tipo) → clave del campo del registro
    MAPA_CAMPOS = {
        ("U", "sin_imp"): "u_importe",
        ("U", "iva"): "u_importe",       # misma celda, la fórmula se combina

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

    # Detalle: agrupar fórmulas por campo destino
    # Cada campo puede recibir VARIOS buckets (ej. U__sin_imp + U__iva)
    detalle_por_campo = defaultdict(list)

    # Agrupado numérico: mantener estructura por categoría para validación
    for (cat, tipo), buckets_cat in buckets.items():
        campo = MAPA_CAMPOS.get((cat, tipo))
        if not campo:
            continue

        # Fórmula de este bucket (usa importes CON impuesto)
        formula = _formula(buckets_cat, tipo)
        if formula:
            detalle_por_campo[campo].append(formula)

        # Suma numérica CON impuesto
        total_con_imp = _sumar(buckets_cat)

        # Base numérica (sin impuesto)
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

    # Redondear
    for cat, vals in agrupado.items():
        for k in vals:
            vals[k] = round(vals[k], 2)

    # ============================================================
    # Ajuste de centavos (a la base, no al IVA)
    # ============================================================
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
            # Ajustar a la categoría con mayor base
            cat_mayor = None
            monto_mayor = 0.0
            for cat, vals in agrupado.items():
                m = (vals["importe"] + vals["sin_iva"]
                     + vals["sin_ieps_6"] + vals["sin_ieps_7"])
                if m > monto_mayor:
                    monto_mayor = m
                    cat_mayor = cat
            if cat_mayor:
                # Modificar agrupado
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

    # ============================================================
    # Construir detalle final (un string por campo)
    # Si un campo recibe varias fórmulas (ej. U sin_imp + U iva),
    # se combinan con "+".
    # ============================================================
    detalle = {}
    for campo, formulas in detalle_por_campo.items():
        detalle[campo] = "+".join(formulas)

    return agrupado, detalle, avisos_reclasificacion


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

    print("\n=== DATOS DE LA FACTURA ===")
    for k in ["no_factura", "qvet", "fecha", "fecha_impresion", "rfc",
              "nombre", "folio_fiscal", "total", "subtotal"]:
        print(f"  {k:20}: {datos.get(k)}")

    print("\n=== PRODUCTOS POR REMISIÓN ===")
    for rem, prods in datos["productos_por_remision"].items():
        print(f"  Remisión {rem}:")
        for p in prods:
            print(f"    {p['nombre'][:50]:50} ${p['importe_pdf']:>8,.2f} "
                  f"(IVA {p['tasa_iva_pdf']*100:.0f}%)")

    print("\n=== AGRUPADO ===")
    agr, det, avisos = agrupar_por_categoria(datos)
    for cat, vals in agr.items():
        print(f"  {cat}:")
        for k, v in vals.items():
            if v:
                print(f"    {k:14} = {v}")

    print("\n=== DETALLE (fórmulas) ===")
    for campo, expr in det.items():
        print(f"  {campo:20} ={expr}")

    if avisos:
        print("\n=== AVISOS ===")
        for a in avisos:
            print(f"  [{a['categoria_actual']}] {a['producto']} (rem {a['remision']})")