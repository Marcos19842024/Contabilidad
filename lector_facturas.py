# -*- coding: utf-8 -*-
"""
lector_facturas.py
Lee facturas CFDI 4.0 (XML) + PDF de representación impresa.
Clasifica conceptos por palabras clave y devuelve datos listos para el formulario.
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIGURACIÓN: clasificación por palabras clave
# (Diccionario provisional. Se ajustará con el catálogo del QVET.)
# ============================================================
PALABRAS_CLAVE = {
    "VACUNA": [
        "vacuna", "rabia", "parvovirus", "moquillo", "leptospira",
        "bordetella", "giardia", "polivalente", "triple felina",
    ],
    "MEDICAMENTOS": [
        # Analgésicos / antiinflamatorios
        "paracetamol", "naproxeno", "aspirina", "ibuprofeno",
        "meloxicam", "rimadyl", "carprofeno", "deracoxib",
        "firocoxib", "ketoprofeno", "tramadol", "gabapentina",
        "librela", "solensia", "onsior", "previcox",
        # Antibióticos
        "amoxicilina", "enrofloxacino", "cefalexina", "metronidazol",
        "doxiciclina", "clindamicina", "azitromicina", "ciprofloxacino",
        "bactrim", "synulox",
        # Desparasitantes / antipulgas
        "desparasitante", "antipulgas", "bravecto", "nexgard",
        "simparica", "comfortis", "milbemax", "drontal", "panacur",
        "praziquantel", "ivermectina", "fipronil", "advantix",
        "revolution", "capstar", "cestex",
        # Gastrointestinales
        "omeprazol", "gastrointestinal", "lata gastrointestinal",
        "ranitidina", "metoclopramida", "sucralfato", "probiótico",
        "probotico", "fortiflora",
        # Corticosteroides / otros
        "prednisona", "dexametasona", "betametasona", "triamcinolona",
        "antihistamínico", "antihistaminico", "difenhidramina",
        # Oftálmicos / óticos
        "gotas oftálmicas", "gotas oticas", "gotas óticas",
        "tobramicina", "gentamicina",
        # Genéricos
        "medicamento", "antibiótico", "antibiotico", "jarabe",
    ],
    "HIGIENE": [
        "shampoo", "champú", "champu", "jabón", "jabon",
        "toalla", "paño", "pano", "cepillo dental", "crema dental",
        "pasta dental", "desodorante", "limpiador", "solución",
        "solucion", "enjuague", "sanitizante", "alcohol",
    ],
    "ESTETICA": [
        "dermoplex", "crema", "perfume", "corte", "baño", "bano",
        "estética", "estetica", "peluquería", "peluqueria",
        "afeitado", "estético", "estetico", "hidratante",
        "acondicionador",
    ],
    "ACCESORIOS": [
        "plato", "b gde", "b chico", "b mediano",
        "collar", "correa", "juguete", "ropa", "suéter", "sueter",
        "cama", "transportadora", "bozal", "arnés", "arnes",
        "comedero", "bebedero", "arete", "placa", "identificación",
        "identificacion", "cinturón", "cinturon", "pretal",
    ],
    "PENSION": [
        "cpt", "pensión", "pension", "alimento premium",
        "hospedaje", "guardería", "guarderia", "estancia",
        "alimento", "croquetas", "pienso",
    ],
    "TRANSPORTE": [
        "cremación", "cremacion", "envío", "envio", "traslado",
        "transporte", "flete",
    ],
    "CLINICA": [
        "consulta", "tratamiento", "seguimiento", "eutanasia",
        "cirugía", "cirugia", "hospitalización", "hospitalizacion",
        "rayos x", "ultrasonido", "ecografía", "ecografia",
        "análisis", "analisis", "laboratorio", "inyección",
        "inyeccion", "curaciones", "curación", "curacion",
        "veterinario", "veterinaria", "vacunación", "vacunacion",
        "desparasitación", "desparasitacion", "esterilización",
        "esterilizacion", "profilaxis", "odontología", "odontologia",
        "limpieza dental", "electrocardiograma", "ecg",
    ],
    "U": [
        "urgencia", "emergencia", "crítico", "critico",
    ],
}


def clasificar_producto(descripcion):
    """Devuelve la categoría según palabras clave. Default: 'CLINICA'."""
    if not descripcion:
        return "CLINICA"
    d = descripcion.lower()
    for categoria, palabras in PALABRAS_CLAVE.items():
        for p in palabras:
            if p in d:
                return categoria
    return "CLINICA"  # default razonable para servicios veterinarios


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
    serie = (root.get("Serie") or "").strip()      # "S1"
    folio = (root.get("Folio") or "").strip()      # "8261"
    no_factura = folio                              # solo el folio

    fecha = _iso_a_ddmmyyyy(root.get("Fecha", ""))
    total = float(root.get("Total", 0) or 0)
    subtotal = float(root.get("SubTotal", 0) or 0)

    # --- Receptor (cliente) ---
    receptor = root.find("cfdi:Receptor", NS)
    rfc_receptor = receptor.get("Rfc", "") if receptor is not None else ""
    nombre_receptor = receptor.get("Nombre", "") if receptor is not None else ""

    # --- Conceptos ---
    conceptos = []
    for conc in root.findall("cfdi:Conceptos/cfdi:Concepto", NS):
        remision = (conc.get("NoIdentificacion") or "").strip()
        descripcion = (conc.get("Descripcion") or "").strip()
        importe = float(conc.get("Importe", 0) or 0)

        # Impuestos del concepto
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
            if impuesto == "002":  # IVA
                tiene_iva = True
                try:
                    tasa_iva = float(traslado.get("TasaOCuota", 0) or 0)
                except ValueError:
                    tasa_iva = 0.0
            elif impuesto == "003":  # IEPS
                tiene_ieps = True
                try:
                    tasa_ieps = float(traslado.get("TasaOCuota", 0) or 0)
                except ValueError:
                    tasa_ieps = 0.0

        categoria = clasificar_producto(descripcion)
        conceptos.append({
            "remision": remision,
            "descripcion": descripcion,
            "importe": importe,
            "tiene_iva": tiene_iva,
            "tasa_iva": tasa_iva,
            "tiene_ieps": tiene_ieps,
            "tasa_ieps": tasa_ieps,
            "categoria": categoria,
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

    # --- Folio fiscal (UUID) ---
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
        "qvet": serie,
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
    """Convierte '2026-09-01T19:19:28' a '01/09/2026'."""
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
def leer_pdf_nombres(ruta_pdf):
    """
    Lee el PDF y devuelve {remision: "nombre del producto"}.
    El PDF de Diverza/QVET tiene este patrón:
        No. Remisión: 176881
        Fecha de remisión: 01/09/2026 11:03 a.m.
        B GDE PM
        1,00 no aplica 300,00 0,00 16,00% 0, 300,00
    """
    try:
        import pdfplumber
    except ImportError:
        return {"nombres_por_remision": {},
                "error": "pdfplumber no instalado. Ejecuta: pip install pdfplumber"}

    texto_completo = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text() or ""
            texto_completo.append(t)
    texto = "\n".join(texto_completo)

    # Normalizar espacios
    texto = re.sub(r"[ \t]+", " ", texto)

    nombres = {}

    # Patrón: "No. Remisión: XXXXX" ... "Fecha de remisión: ..." ... nombre (línea siguiente)
    # El nombre es una línea que contiene letras y números, no comas de miles, no "%"
    patron = re.compile(
        r"No\.\s*Remisi[oó]n:\s*(\d+)\s*"
        r"Fecha de remisi[oó]n:\s*[\d/:.\sapm]+?\s*"
        r"([^\n]+?)\s*\n",
        re.IGNORECASE
    )

    for m in patron.finditer(texto):
        remision = m.group(1).strip()
        nombre_crudo = m.group(2).strip()

        # Limpiar el nombre: quitar cantidades, medidas, números al inicio
        # Ej: "B GDE PM1,00 no aplica 300,00 0,00 16,00% 0, 300,00"
        # Queremos solo "B GDE PM"
        nombre = re.split(
            r"\d+[,.]\d+|\d+\s*,\s*\d+\s*(?:no aplica|pza|kg|ml|gr)?",
            nombre_crudo
        )[0].strip()

        # Quitar caracteres raros al final
        nombre = re.sub(r"[\s,;:.]+$", "", nombre)

        if remision and nombre and len(nombre) > 1:
            nombres[remision] = nombre

    # Fallback: buscar patrones alternativos si el principal falla
    if not nombres:
        patron2 = re.compile(
            r"No\.\s*Remisi[oó]n:\s*(\d+)[\s\S]{0,200}?"
            r"Fecha de remisi[oó]n:[\s\S]{0,50}?\n\s*([A-Z][^\n\d]{2,60})",
            re.IGNORECASE
        )
        for m in patron2.finditer(texto):
            remision = m.group(1).strip()
            nombre = m.group(2).strip()
            nombre = re.sub(r"[\s,;:.]+$", "", nombre)
            if remision and nombre:
                nombres[remision] = nombre

    return {"nombres_por_remision": nombres}


# ============================================================
# CRUCE: XML + PDF
# ============================================================
def procesar_factura(ruta_xml=None, ruta_pdf=None):
    """
    Lee el XML (obligatorio) y opcionalmente el PDF.
    Devuelve el dict del XML con los conceptos enriquecidos
    con los nombres reales del PDF.
    """
    if not ruta_xml:
        return {"error": "El XML es obligatorio"}

    datos = leer_xml_factura(ruta_xml)

    # Enriquecer con nombres del PDF
    if ruta_pdf:
        pdf_data = leer_pdf_nombres(ruta_pdf)
        nombres = pdf_data.get("nombres_por_remision", {})
        for conc in datos["conceptos"]:
            rem = conc["remision"]
            if rem in nombres:
                conc["descripcion"] = nombres[rem]
                # Reclasificar con el nombre real
                conc["categoria"] = clasificar_producto(nombres[rem])

    return datos


# ============================================================
# RESUMEN PARA EL FORMULARIO
# ============================================================
def agrupar_por_categoria(datos):
    """
    Toma el dict de `procesar_factura` y devuelve los totales
    listos para volcar en el formulario.

    Estructura de retorno:
    {
        "MEDICAMENTOS": {
            "importe": 200.0,      # exentos
            "sin_iva": 300.0,      # base con IVA
            "iva": 48.0,
        },
        "HIGIENE": {...},
        "U": {"importe": 100.0, "iva": 16.0},
        ...
    }
    """
    agrupado = {}

    for conc in datos.get("conceptos", []):
        cat = conc["categoria"]
        if cat not in agrupado:
            agrupado[cat] = {
                "importe": 0.0,
                "sin_iva": 0.0,
                "iva": 0.0,
                "sin_ieps_6": 0.0,
                "ieps_6": 0.0,
                "sin_ieps_7": 0.0,
                "ieps_7": 0.0,
            }
        imp = conc["importe"]
        tiene_iva = conc["tiene_iva"]
        tasa_iva = conc["tasa_iva"]
        tiene_ieps = conc["tiene_ieps"]
        tasa_ieps = conc["tasa_ieps"]

        if cat in ("MEDICAMENTOS", "HIGIENE"):
            # Nuevo esquema:
            #   - con IVA   -> sin_iva + iva
            #   - sin IVA   -> importe (exento)
            if tiene_iva:
                agrupado[cat]["sin_iva"] += imp
                agrupado[cat]["iva"] += round(imp * tasa_iva, 2)
            else:
                agrupado[cat]["importe"] += imp

            # IEPS solo en HIGIENE
            if cat == "HIGIENE" and tiene_ieps:
                if abs(tasa_ieps - 0.06) < 0.001:
                    agrupado[cat]["sin_ieps_6"] += imp
                    agrupado[cat]["ieps_6"] += round(imp * 0.06, 2)
                elif abs(tasa_ieps - 0.07) < 0.001:
                    agrupado[cat]["sin_ieps_7"] += imp
                    agrupado[cat]["ieps_7"] += round(imp * 0.07, 2)
        else:
            # Esquema tradicional: importe = base (con o sin IVA)
            # Si tiene IVA, se calcula aparte
            agrupado[cat]["importe"] += imp
            if tiene_iva:
                agrupado[cat]["iva"] += round(imp * tasa_iva, 2)

    # Redondear todos los valores
    for cat, vals in agrupado.items():
        for k in vals:
            vals[k] = round(vals[k], 2)

    return agrupado


# ============================================================
# PRUEBA RÁPIDA (ejecutar solo este archivo para probar)
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
    for k in ["no_factura", "fecha", "fecha_impresion", "rfc",
              "nombre", "folio_fiscal", "total", "subtotal",
              "iva_total", "base_con_iva", "base_exenta"]:
        print(f"  {k:20}: {datos.get(k)}")

    print("\n=== CONCEPTOS ===")
    for c in datos["conceptos"]:
        iva_txt = f"IVA {c['tasa_iva']*100:.0f}%" if c["tiene_iva"] else "Exento"
        print(f"  [{c['remision']}] {c['categoria']:12} "
              f"${c['importe']:>8,.2f}  {iva_txt:12}  {c['descripcion']}")

    print("\n=== AGRUPADO POR CATEGORÍA ===")
    agr = agrupar_por_categoria(datos)
    for cat, vals in agr.items():
        print(f"  {cat}:")
        for k, v in vals.items():
            if v:
                print(f"     {k:14} = ${v:,.2f}")