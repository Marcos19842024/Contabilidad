"""
lector_facturas.py
Lee facturas CFDI 4.0 (XML) + PDF de representación impresa.
Clasifica conceptos por descripción usando catalogo_qvet.json (editado a mano).
"""
import sys
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


# ============================================================
# CARGA DEL CATÁLOGO DEL QVET
# ============================================================
_CATALOGO = None


def cargar_catalogo():
    """Carga catalogo_qvet.json (solo lectura, va en el bundle)."""
    global _CATALOGO
    if _CATALOGO is not None:
        return _CATALOGO

    # Buscar primero en la carpeta de datos del usuario
    ruta_usuario = _carpeta_datos() / "catalogo_qvet.json"
    ruta_recurso = _ruta_recurso("catalogo_qvet.json")

    ruta = ruta_usuario if ruta_usuario.exists() else ruta_recurso

    if not ruta.exists():
        print(f"⚠️  No se encontró catalogo_qvet.json")
        _CATALOGO = {}
        return _CATALOGO

    with open(ruta, "r", encoding="utf-8") as f:
        _CATALOGO = json.load(f)

    print(f"✅ Catálogo cargado: {len(_CATALOGO)} productos desde {ruta}")
    return _CATALOGO


def cargar_excepciones_manuales():
    """Carga categorias_manuales.json (editables por el usuario)."""
    global _EXCEPCIONES_MANUALES
    if _EXCEPCIONES_MANUALES is not None:
        return _EXCEPCIONES_MANUALES

    # Las excepciones SIEMPRE se leen/escriben en la carpeta de datos
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
    """Guarda las excepciones en la carpeta de datos del usuario."""
    global _EXCEPCIONES_MANUALES
    _EXCEPCIONES_MANUALES = dict(exc)

    carpeta = _carpeta_datos()
    ruta = carpeta / "categorias_manuales.json"

    # Backup diario
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


_EXCEPCIONES_MANUALES = None


def _carpeta_datos():
    """
    Carpeta única de datos de la app (NO por año).
    Compartida entre años: catálogo, excepciones, backups.
    """
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Contabilidad App"
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    else:
        return Path(__file__).parent


def _ruta_recurso(nombre_archivo):
    """
    Devuelve la ruta de un archivo empaquetado como recurso (solo lectura).
    Si corremos desde ejecutable, lo busca en el bundle.
    Si no, en la carpeta del script.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller guarda los recursos en sys._MEIPASS
        return Path(sys._MEIPASS) / nombre_archivo
    else:
        return Path(__file__).parent / nombre_archivo


def normalizar(texto):
    """Normaliza un texto para comparar."""
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
    """
    Busca la descripción en el catálogo del QVET.
    Prioridad:
      1. Excepciones manuales (categorias_manuales.json)
      2. Catálogo (catalogo_qvet.json)
    Si no se encuentra, devuelve "U" (huérfano).
    """
    if not descripcion:
        return "U"

    desc_norm = normalizar(descripcion)

    # 1. Excepciones manuales
    exc = cargar_excepciones_manuales()
    if desc_norm in exc:
        return exc[desc_norm]

    # 2. Catálogo
    catalogo = cargar_catalogo()
    if desc_norm in catalogo:
        return catalogo[desc_norm]

    # 3. Por prefijo más largo
    mejor_match = None
    mejor_len = 0
    for clave, cat in catalogo.items():
        if desc_norm.startswith(clave) and len(clave) > mejor_len:
            mejor_match = cat
            mejor_len = len(clave)
    if mejor_match:
        return mejor_match

    # 4. Inversa
    for clave, cat in catalogo.items():
        if desc_norm in clave and len(clave) - len(desc_norm) < 20:
            return cat

    # 5. Huérfano: sin clasificación en el catálogo
    # El usuario los reclasificará después. Mientras, van a U.
    return "U"


# ============================================================
# LECTOR DE XML (CFDI 4.0)
# ============================================================
def leer_xml_factura(ruta_xml):
    """
    Lee un XML CFDI 4.0 y devuelve un dict con los datos principales.
    """
    NS = {
        "cfdi": "http://www.sat.gob.mx/cfd/4",
        "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
    }

    tree = ET.parse(ruta_xml)
    root = tree.getroot()

    # --- Datos generales ---
    serie = (root.get("Serie") or "").strip()
    folio = (root.get("Folio") or "").strip()
    no_factura = folio
    qvet = f"{serie}/{folio}".upper() if serie and folio else serie.upper()

    fecha = _iso_a_ddmmyyyy(root.get("Fecha", ""))
    total = float(root.get("Total", 0) or 0)
    subtotal = float(root.get("SubTotal", 0) or 0)

    # --- Receptor ---
    receptor = root.find("cfdi:Receptor", NS)
    rfc_receptor = receptor.get("Rfc", "") if receptor is not None else ""
    nombre_receptor = receptor.get("Nombre", "") if receptor is not None else ""

    # --- Conceptos ---
    conceptos = []
    for conc in root.findall("cfdi:Conceptos/cfdi:Concepto", NS):
        remision = (conc.get("NoIdentificacion") or "").strip()
        descripcion_xml = (conc.get("Descripcion") or "").strip()
        importe = float(conc.get("Importe", 0) or 0)

        tiene_iva = False
        tasa_iva = 0.0
        tiene_ieps = False
        tasa_ieps = 0.0

        for traslado in conc.findall(
                "cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado", NS):
            impuesto = traslado.get("Impuesto", "")
            tipo = traslado.get("TipoFactor", "")
            if tipo == "Exento":
                continue
            if impuesto == "002":
                tiene_iva = True
                try:
                    tasa_iva = float(traslado.get("TasaOCuota", 0) or 0)
                except ValueError:
                    tasa_iva = 0.0
            elif impuesto == "003":
                tiene_ieps = True
                try:
                    tasa_ieps = float(traslado.get("TasaOCuota", 0) or 0)
                except ValueError:
                    tasa_ieps = 0.0

        conceptos.append({
            "remision": remision,
            "descripcion": descripcion_xml,
            "importe": importe,
            "tiene_iva": tiene_iva,
            "tasa_iva": tasa_iva,
            "tiene_ieps": tiene_ieps,
            "tasa_ieps": tasa_ieps,
            "categoria": None,
        })

    # --- Impuestos totales ---
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

    # --- Folio fiscal ---
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
        "conceptos": conceptos,
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
# LECTOR DE PDF: extrae nombres por remisión
# ============================================================
def _conv_numero_simple(s):
    """Convierte string numérico a float (acepta formato europeo y americano)."""
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
        "pagos": {"efectivo": X, "tc": Y, "td": Z, "cheque": W, "transfer": V, "vale": U}
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

    # ============================================================
    # 1. Productos por remisión
    # ============================================================
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
            # Formato real del PDF de QVET:
            # NOMBRE CANTIDAD no aplica P.V.P Dto. Impuesto Importe
            # Ej: "HEMOFINN C/TABS 6,00 no aplica 55,00 0,00 16,00% 330,00"
            # Ej: "BAYTRIL F.150 MG C/TAB 5,00 no aplica 57,00 0,00 0,00% 285,00"
            m_prod = re.match(
                r"^(.+?)\s+"                             # 1. nombre
                r"(\d+[,.]\d+)\s+"                       # 2. cantidad
                r"no\s+aplica\s+"                        #    "no aplica"
                r"([\d.,]+)\s+"                          # 3. PVP
                r"([\d.,]+)\s+"                          # 4. Dto
                r"([\d.,]+)\s*%?\s*"                     # 5. Tasa (con o sin %)
                r"(?:([\d.,]+)\s+)?"                     # 6. campo extra opcional
                r"([\d.,]+)",                            # 7. Importe
                linea, re.IGNORECASE
            )
            if m_prod:
                nombre = m_prod.group(1).strip()
                nombre = re.sub(r"[\s,;:.]+$", "", nombre)
                cantidad_str = m_prod.group(2).replace(",", ".")
                pvp_str = m_prod.group(3)
                tasa_str = m_prod.group(5)          # ← puede ser "0," o "16,00"
                importe_str = m_prod.group(7)       # ← ahora es el grupo 7

                # Interpretar la tasa
                # "0," → 0.0 ; "16,00" → 16.0
                try:
                    tasa_iva_pdf = _conv_numero_simple(tasa_str) / 100.0
                except Exception:
                    tasa_iva_pdf = 0.0

                if nombre and len(nombre) > 1:
                    productos_por_remision[remision_actual].append({
                        "nombre": nombre,
                        "cantidad": float(cantidad_str) if cantidad_str else 1.0,
                        "precio_sin_iva": _conv_numero_simple(pvp_str),
                        "tasa_iva_pdf": tasa_iva_pdf,
                        "importe_pdf": _conv_numero_simple(importe_str),
                    })

    # ============================================================
    # 2. Desglose de pagos
    # ============================================================
    pagos = {
        "efectivo": 0.0,
        "tc": 0.0,
        "td": 0.0,
        "cheque": 0.0,
        "transfer": 0.0,
        "vale": 0.0,
    }

    MAPA_FORMA_PAGO = {
        "01": "efectivo",
        "02": "cheque",
        "03": "transfer",
        "04": "tc",
        "28": "td",
    }

    def _conv_numero(s):
        """
        Convierte un string numérico a float, aceptando tanto
        formato europeo (1.350,00) como americano (1,350.00).
        """
        s = s.strip()
        if not s:
            return 0.0
        tiene_punto = "." in s
        tiene_coma = "," in s

        if tiene_punto and tiene_coma:
            # ¿Cuál es el decimal? El último que aparece
            pos_punto = s.rfind(".")
            pos_coma = s.rfind(",")
            if pos_coma > pos_punto:
                # Formato europeo: 1.350,00 → 1350.00
                s = s.replace(".", "").replace(",", ".")
            else:
                # Formato americano: 1,350.00 → 1350.00
                s = s.replace(",", "")
        elif tiene_coma:
            # Solo coma: 1350,00 → 1350.00 (europeo)
            s = s.replace(",", ".")
        # else: solo punto → ya está bien (americano)

        try:
            return float(s)
        except ValueError:
            return 0.0

    # Patrón de pago: "DD/MM/YYYY NN FORMA_PAGO IMPORTE [resto]"
    # Ejemplo europeo: "29/08/2026 04 T. CREDITO 1.350,00 0,00% 0,00 3.825,00 3.825,00"
    # El IMPORTE es el primer número después de la forma de pago
    patron_pago = re.compile(
        r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"                      # fecha
        r"(\d{2})\s+"                                          # código SAT
        r"(T\.\s*CREDITO|T\.\s*DEBITO|EFECTIVO|"
        r"CHEQUE|TRANSFERENCIA|TRANSF\.?|VALE)"
        r"\s+"
        r"([\d.,]+)",                                          # importe (format agnóstico)
        re.IGNORECASE
    )

    for match in patron_pago.finditer(texto):
        codigo = match.group(2)
        importe_str = match.group(4)
        importe = _conv_numero(importe_str)
        clave = MAPA_FORMA_PAGO.get(codigo)
        if clave and importe > 0:
            pagos[clave] += importe

    # Fallback: si el regex principal no encontró nada
    if not any(v > 0 for v in pagos.values()):
        for i, linea in enumerate(lineas):
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
                # Buscar el importe justo después de la forma de pago
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
    """Lee el TOTAL del PDF."""
    try:
        import pdfplumber
    except ImportError:
        return None

    with pdfplumber.open(ruta_pdf) as pdf:
        texto = "\n".join((p.extract_text() or "") for p in pdf.pages)

    # Buscar "TOTAL $ X,XXX.XX"
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
    """Lee FormaPago del XML."""
    NS = {
        "cfdi": "http://www.sat.gob.mx/cfd/4",
        "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
    }
    try:
        tree = ET.parse(ruta_xml)
        root = tree.getroot()
        forma = (root.get("FormaPago") or "").strip()
    except Exception:
        return None

    mapa = {
        "01": "efectivo",
        "02": "cheque",
        "03": "transfer",
        "04": "tc",
        "28": "td",
    }
    return mapa.get(forma)


# ============================================================
# CRUCE FINAL: XML + PDF + CATÁLOGO
# ============================================================
def procesar_factura(ruta_xml=None, ruta_pdf=None):
    """
    Lee el XML (obligatorio) y opcionalmente el PDF.
    Devuelve datos de la factura + desglose de pagos.
    """
    if not ruta_xml:
        return {"error": "El XML es obligatorio"}

    datos = leer_xml_factura(ruta_xml)

    productos_por_remision = {}
    pagos = {}
    total_pdf = None

    if ruta_pdf:
        pdf_data = leer_pdf_completo(ruta_pdf)
        productos_por_remision = pdf_data.get("productos", {})
        pagos = pdf_data.get("pagos", {})
        total_pdf = _leer_total_pdf(ruta_pdf)

    # ============================================================
    # Emparejar conceptos del XML con productos del PDF
    # Cada concepto del XML recibe SOLO los productos del PDF que
    # coinciden con su tratamiento de IVA.
    # ============================================================
    from collections import defaultdict

    # Agrupar conceptos por remisión
    conceptos_por_remision = defaultdict(list)
    for conc in datos["conceptos"]:
        rem = conc["remision"]
        conceptos_por_remision[rem].append(conc)

    for rem, conceptos_rem in conceptos_por_remision.items():
        productos = productos_por_remision.get(rem, [])

        if not productos:
            for conc in conceptos_rem:
                conc["categoria"] = clasificar_por_descripcion(conc["descripcion"])
                conc["productos_pdf"] = []
                conc["nombres_pdf"] = []
            continue

        # Separar productos del PDF por su tasa de IVA
        productos_sin_iva = [p for p in productos if p.get("tasa_iva_pdf", 0) == 0]
        productos_con_iva = [p for p in productos if p.get("tasa_iva_pdf", 0) > 0]

        # ✅ FIX: cada grupo de productos se asigna SOLO UNA VEZ
        # Marcamos qué grupos ya se usaron para no repetirlos.
        con_iva_usado = False
        sin_iva_usado = False

        for conc in conceptos_rem:
            tiene_iva_xml = conc["tiene_iva"]

            if tiene_iva_xml and productos_con_iva and not con_iva_usado:
                productos_asignados = productos_con_iva
                con_iva_usado = True
            elif not tiene_iva_xml and productos_sin_iva and not sin_iva_usado:
                productos_asignados = productos_sin_iva
                sin_iva_usado = True
            else:
                productos_asignados = []

            if productos_asignados:
                nombres = [p["nombre"] for p in productos_asignados]
                categorias = [clasificar_por_descripcion(n) for n in nombres]
                if len(set(categorias)) == 1:
                    conc["categoria"] = categorias[0]
                else:
                    from collections import Counter
                    conc["categoria"] = Counter(categorias).most_common(1)[0][0]

                conc["descripcion"] = " + ".join(nombres)
                conc["nombres_pdf"] = nombres
                for p in productos_asignados:
                    p["remision"] = rem
                conc["productos_pdf"] = productos_asignados
            else:
                conc["categoria"] = clasificar_por_descripcion(conc["descripcion"])
                conc["nombres_pdf"] = []
                conc["productos_pdf"] = []

    # Ajustar total si el PDF lo tiene redondeado
    if total_pdf is not None:
        if abs(datos["total"] - total_pdf) < 1.0:
            print(f"ℹ️  Total ajustado: XML=${datos['total']} → PDF=${total_pdf}")
            datos["total"] = round(total_pdf, 2)

    # Guardar pagos
    datos["pagos"] = pagos

    # Fallback: usar FormaPago del XML si el PDF no trajo pagos
    if not any(v > 0 for v in pagos.values()):
        forma_xml = _leer_forma_pago_xml(ruta_xml)
        if forma_xml:
            pagos[forma_xml] = datos["total"]
            datos["pagos"] = pagos
            print(f"ℹ️  Pagos del PDF no detectados. Usando FormaPago del XML: {forma_xml}")

    return datos


def agrupar_por_categoria(datos, ajustar_centavos=True):
    """
    Agrupa conceptos por categoría.
    Devuelve:
      - agrupado: totales por categoría
      - detalle: lista de términos para construir la expresión
      - avisos_reclasificacion: productos con IVA en categorías sin IVA
    """
    # Extraer datos de la factura para los avisos
    info_factura = {
        "no_factura": datos.get("no_factura", ""),
        "nombre": datos.get("nombre", ""),
        "folio_fiscal": datos.get("folio_fiscal", ""),
        "fecha": datos.get("fecha", ""),
        "total": datos.get("total", 0.0),
    }

    agrupado = {}
    detalle = {}
    avisos_reclasificacion = []
    CATEGORIAS_SIN_IVA = ("VACUNA", "CLINICA")

    # Categorías válidas en la app
    CATEGORIAS_VALIDAS = {
        "U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
        "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA"
    }

    # Categorías que manejan IVA
    CATEGORIAS_CON_IVA = {
        "U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
        "ESTETICA", "TRANSPORTE", "PENSION"
    }

    # ============================================================
    # Bucle principal: agrupar conceptos
    # ============================================================
    for conc in datos.get("conceptos", []):
        cat = conc.get("categoria") or "CLINICA"

        # Si la categoría no es válida (por ejemplo, "ALIMENTOS"),
        # forzarla a "U".
        if cat not in CATEGORIAS_VALIDAS:
            cat = "U"
            conc["categoria"] = "U"

        # Si la categoría NO maneja IVA (VACUNA, CLINICA) pero el
        # concepto SÍ tiene IVA, moverlo a U y marcar el original.
        if cat in CATEGORIAS_SIN_IVA and conc.get("tiene_iva") and conc.get("tasa_iva", 0) > 0:
            conc["categoria_original_para_aviso"] = cat
            cat = "U"
            conc["categoria"] = "U"

        if cat not in agrupado:
            agrupado[cat] = {
                "importe": 0.0, "sin_iva": 0.0, "iva": 0.0,
                "sin_ieps_6": 0.0, "ieps_6": 0.0,
                "sin_ieps_7": 0.0, "ieps_7": 0.0,
            }

        imp = conc["importe"]
        tiene_iva = conc["tiene_iva"]
        tasa_iva = conc["tasa_iva"]
        tiene_ieps = conc["tiene_ieps"]
        tasa_ieps = conc["tasa_ieps"]
        productos_pdf = conc.get("productos_pdf", [])

        # Construir expresiones del concepto
        termino_expresion = None
        termino_expresion_iva = None

        if productos_pdf:
            # Helper: formatea un número sin decimales si son .00
            def _fmt(v):
                if abs(v - round(v)) < 0.001:
                    return f"{v:.0f}"
                return f"{v:.2f}"

            # Agrupar los productos por remisión
            from collections import defaultdict
            por_remision = defaultdict(list)
            for p in productos_pdf:
                rem = p.get("remision", "")
                imp_pdf = p.get("importe_pdf", 0.0)
                por_remision[rem].append(imp_pdf)

            # Construir cada remisión:
            #   - 1 producto → "180"
            #   - 2+ productos → "(180+180)"
            grupos = []
            for rem, importes in por_remision.items():
                if len(importes) == 1:
                    grupos.append(_fmt(importes[0]))
                else:
                    suma = "+".join(_fmt(x) for x in importes)
                    grupos.append(f"({suma})")

            # Unir todos los grupos con "+"
            if len(grupos) == 1:
                suma_total = grupos[0]
            else:
                suma_total = "+".join(grupos)

            if tiene_iva and tasa_iva > 0 and cat in CATEGORIAS_CON_IVA:
                # === CON IVA ===
                # IMPORTE: (suma)/1.16
                termino_expresion = f"({suma_total})/{1+tasa_iva:.2f}"

                # IVA: ((suma)-(suma)/1.16)
                # Envolver TODO entre paréntesis para que al unir varios
                # términos con "+" no se rompa la precedencia.
                termino_expresion_iva = (
                    f"(({suma_total})-({suma_total})/{1+tasa_iva:.2f})"
                )

            else:
                # === SIN IVA ===
                termino_expresion = suma_total

        # ============================================================
        # Clasificar en la categoría correcta
        # ============================================================
        if cat in ("MEDICAMENTOS", "HIGIENE"):
            if tiene_iva:
                agrupado[cat]["sin_iva"] += imp
                agrupado[cat]["iva"] += round(imp * tasa_iva, 2)
                if termino_expresion:
                    detalle.setdefault(f"{cat}__sin_iva", []).append(termino_expresion)
                if termino_expresion_iva:
                    detalle.setdefault(f"{cat}__iva", []).append(termino_expresion_iva)
            else:
                agrupado[cat]["importe"] += imp
                if termino_expresion:
                    detalle.setdefault(f"{cat}__importe", []).append(termino_expresion)

            if cat == "HIGIENE" and tiene_ieps:
                if abs(tasa_ieps - 0.06) < 0.001:
                    agrupado[cat]["sin_ieps_6"] += imp
                    agrupado[cat]["ieps_6"] += round(imp * 0.06, 2)
                    if termino_expresion:
                        detalle.setdefault(f"{cat}__sin_ieps_6", []).append(termino_expresion)
                elif abs(tasa_ieps - 0.07) < 0.001:
                    agrupado[cat]["sin_ieps_7"] += imp
                    agrupado[cat]["ieps_7"] += round(imp * 0.07, 2)
                    if termino_expresion:
                        detalle.setdefault(f"{cat}__sin_ieps_7", []).append(termino_expresion)
        else:
            agrupado[cat]["importe"] += imp
            if termino_expresion:
                detalle.setdefault(f"{cat}__importe", []).append(termino_expresion)
            if tiene_iva:
                agrupado[cat]["iva"] += round(imp * tasa_iva, 2)
                if termino_expresion_iva:
                    detalle.setdefault(f"{cat}__iva", []).append(termino_expresion_iva)

    # ============================================================
    # Detectar productos que tenían IVA en categorías sin IVA
    # (VACUNA, CLINICA) y fueron movidos a U automáticamente.
    # ============================================================
    vistos = set()
    for conc in datos.get("conceptos", []):
        cat = conc.get("categoria_original_para_aviso")
        if not cat:
            continue

        nombres = conc.get("nombres_pdf", [])
        if not nombres:
            nombres = [conc.get("descripcion", "?")]

        for nombre in nombres:
            clave = (cat, nombre.strip().upper())
            if clave in vistos:
                continue
            vistos.add(clave)

            avisos_reclasificacion.append({
                "categoria_actual": cat,
                "producto": nombre,
                "remision": conc.get("remision", ""),
                "importe": conc.get("importe", 0.0),
                **info_factura,
            })

    # Redondear
    for cat, vals in agrupado.items():
        for k in vals:
            vals[k] = round(vals[k], 2)

    # ============================================================
    # Ajuste de centavos
    # ============================================================
    if ajustar_centavos:
        suma_bases = 0.0
        suma_exentas = 0.0
        for cat, vals in agrupado.items():
            if cat in ("MEDICAMENTOS", "HIGIENE"):
                suma_bases += vals["sin_iva"]
                suma_exentas += vals["importe"]
            else:
                suma_bases += vals["importe"]
        suma_impuestos = sum(
            vals["iva"] + vals["ieps_6"] + vals["ieps_7"]
            for vals in agrupado.values()
        )
        total_calculado = suma_bases + suma_exentas + suma_impuestos
        total_objetivo = datos.get("total", 0)
        dif = round(total_objetivo - total_calculado, 2)

        if abs(dif) == 0.01:
            for cat in ["U", "ACCESORIOS", "ESTETICA", "TRANSPORTE",
                        "MEDICAMENTOS", "HIGIENE"]:
                if cat in agrupado and agrupado[cat]["iva"] > 0:
                    agrupado[cat]["iva"] = round(agrupado[cat]["iva"] + dif, 2)
                    print(f"ℹ️  Ajustando centavos: ${dif} → sumada al IVA de {cat}")
                    break

    return agrupado, detalle, avisos_reclasificacion


def agregar_producto_catalogo(nombre, categoria):
    """
    Agrega un producto a las excepciones manuales (categorias_manuales.json).
    
    Parámetros:
      - nombre: nombre del producto (se normaliza a mayúsculas sin acentos)
      - categoria: una de las 9 categorías válidas
    
    Devuelve:
      - (True, mensaje) si todo bien
      - (False, mensaje) si hay error
    """
    nombre_norm = normalizar(nombre)
    if not nombre_norm:
        return False, "El nombre está vacío"
    
    CATEGORIAS_VALIDAS = {"U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
                          "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA"}
    if categoria not in CATEGORIAS_VALIDAS:
        return False, f"Categoría inválida: {categoria}"
    
    # Cargar excepciones actuales
    exc = cargar_excepciones_manuales()
    exc = dict(exc)
    
    # Agregar / sobreescribir
    ya_existia = nombre_norm in exc
    exc[nombre_norm] = categoria
    
    # Guardar
    guardar_excepciones_manuales(exc)
    
    if ya_existia:
        return True, f"Producto actualizado: {nombre} → {categoria}"
    return True, f"Producto agregado: {nombre} → {categoria}"


# ============================================================
# PRUEBA RÁPIDA
# ============================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python lector_facturas.py <ruta_xml> [ruta_pdf]")
        sys.exit(1)
    ruta_xml = sys.argv[1]
    ruta_pdf = sys.argv[2] if len(sys.argv) > 2 else None

    datos = procesar_factura(ruta_xml, ruta_pdf)

    print("\n=== DATOS DE LA FACTURA ===")
    for k in ["no_factura", "qvet", "fecha", "fecha_impresion", "rfc",
              "nombre", "folio_fiscal", "total", "subtotal",
              "iva_total", "base_con_iva", "base_exenta"]:
        print(f"  {k:20}: {datos.get(k)}")

    print("\n=== CONCEPTOS ===")
    for c in datos["conceptos"]:
        iva_txt = f"IVA {c['tasa_iva']*100:.0f}%" if c["tiene_iva"] else "Exento"
        print(f"  [{c['remision']}] {c['categoria']:12} "
              f"${c['importe']:>8,.2f}  {iva_txt:12}  {c['descripcion']}")

    print("\n=== PAGOS ===")
    for k, v in datos.get("pagos", {}).items():
        if v:
            print(f"  {k:10}: ${v:,.2f}")

    print("\n=== AGRUPADO POR CATEGORÍA ===")
    agr, det, avisos = agrupar_por_categoria(datos)
    for cat, vals in agr.items():
        print(f"  {cat}:")
        for k, v in vals.items():
            if v:
                print(f"     {k:14} = ${v:,.2f}")

    if avisos:
        print("\n=== AVISOS DE RECLASIFICACIÓN ===")
        for a in avisos:
            print(f"  [{a['categoria_actual']}] {a['producto']} "
                  f"(remisión {a['remision']}) — ${a['importe']:,.2f}")