# -*- coding: utf-8 -*-
"""
excel/egresos.py
Genera los Excel de Egresos (PUE y PPD).
"""

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ============================================================
# ESTILOS
# ============================================================
THIN = Side(border_style="thin", color="808080")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTRO = Alignment(horizontal="center", vertical="center", wrap_text=True)
DERECHA = Alignment(horizontal="right", vertical="center")
IZQUIERDA = Alignment(horizontal="left", vertical="center")
BOLD_WHITE = Font(bold=True, color="FFFFFF", size=11)
BOLD_DARK = Font(bold=True, color="000000", size=10)
FUENTE_NORMAL = Font()
FUENTE_LINK = Font(color="0563C1", underline="single")
FORMATO_MONEDA = '"$"#,##0.00'
FORMATO_FECHA = "DD/MM/YYYY"

COLOR_PUE = "1F4E3D"
COLOR_PPD = "2E5A88"


# ============================================================
# GENERAR EXCEL PUE
# ============================================================
def generar_excel_pue(facturas, ruta_xlsx, mes_nombre, anio):
    """
    Genera el Excel de facturas PUE.
    
    Columnas:
      # | No. FACTURA | UUID | RFC EMISOR | NOMBRE O RAZÓN SOCIAL DEL EMISOR |
      FECHA | TOTAL | METODO DE PAGO | OBSERVACIONES
    """
    # Ordenar por fecha ascendente, luego por folio
    def _clave_orden(f):
        fecha_str = f.get("fecha", "")
        try:
            partes = fecha_str.split("/")
            if len(partes) == 3:
                fecha = (int(partes[2]), int(partes[1]), int(partes[0]))
            else:
                fecha = (0, 0, 0)
        except Exception:
            fecha = (0, 0, 0)
        return (fecha, str(f.get("folio", "")))

    facturas = sorted(facturas, key=_clave_orden)
    wb = Workbook()
    ws = wb.active
    ws.title = f"PUE {mes_nombre.capitalize()} {anio}"[:31]

    # Encabezados
    encabezados = [
        ("A", "#", 6),
        ("B", "No. FACTURA", 20),
        ("C", "UUID", 38),
        ("D", "RFC EMISOR", 16),
        ("E", "NOMBRE O RAZÓN SOCIAL DEL EMISOR", 50),
        ("F", "FECHA", 12),
        ("G", "TOTAL", 14),
        ("H", "METODO DE PAGO", 16),
        ("I", "OBSERVACIONES", 30),
    ]

    for letra, titulo, ancho in encabezados:
        c = ws[f"{letra}1"]
        c.value = titulo
        c.font = BOLD_WHITE
        c.fill = PatternFill("solid", fgColor=COLOR_PUE)
        c.alignment = CENTRO
        c.border = BORDER
        ws.column_dimensions[letra].width = ancho

    # Filas
    fila = 2
    for idx, f in enumerate(facturas, 1):
        # Número de línea enumerado al vuelo
        ws[f"A{fila}"] = idx
        ws[f"A{fila}"].alignment = CENTRO
        ws[f"A{fila}"].border = BORDER

        # No. FACTURA (con enlace al PDF)
        c = ws[f"B{fila}"]
        c.value = f.get("folio", "")
        c.alignment = IZQUIERDA
        c.border = BORDER
        ruta_pdf = _obtener_ruta_pdf_egreso(f)
        if ruta_pdf:
            c.hyperlink = ruta_pdf
            c.font = FUENTE_LINK

        # UUID
        ws[f"C{fila}"] = f.get("uuid", "")
        ws[f"C{fila}"].alignment = IZQUIERDA
        ws[f"C{fila}"].border = BORDER

        # RFC EMISOR
        ws[f"D{fila}"] = f.get("rfc_emisor", "")
        ws[f"D{fila}"].alignment = CENTRO
        ws[f"D{fila}"].border = BORDER

        # NOMBRE EMISOR
        ws[f"E{fila}"] = f.get("nombre_emisor", "")
        ws[f"E{fila}"].alignment = IZQUIERDA
        ws[f"E{fila}"].border = BORDER

        # FECHA
        ws[f"F{fila}"] = f.get("fecha", "")
        ws[f"F{fila}"].alignment = CENTRO
        ws[f"F{fila}"].border = BORDER

        # TOTAL
        ws[f"G{fila}"] = float(f.get("total", 0))
        ws[f"G{fila}"].number_format = FORMATO_MONEDA
        ws[f"G{fila}"].alignment = DERECHA
        ws[f"G{fila}"].border = BORDER

        # METODO DE PAGO
        ws[f"H{fila}"] = f.get("forma_pago_texto", "")
        ws[f"H{fila}"].alignment = CENTRO
        ws[f"H{fila}"].border = BORDER

        # OBSERVACIONES
        ws[f"I{fila}"] = f.get("observacion", "")
        ws[f"I{fila}"].alignment = IZQUIERDA
        ws[f"I{fila}"].border = BORDER

        fila += 1

    # Fila de totales
    ws[f"F{fila}"] = "TOTAL:"
    ws[f"F{fila}"].font = BOLD_DARK
    ws[f"F{fila}"].alignment = DERECHA
    ws[f"G{fila}"] = f"=SUM(G2:G{fila-1})"
    ws[f"G{fila}"].font = BOLD_DARK
    ws[f"G{fila}"].number_format = FORMATO_MONEDA
    ws[f"G{fila}"].alignment = DERECHA

    wb.save(ruta_xlsx)
    return ruta_xlsx


# ============================================================
# GENERAR EXCEL PPD
# ============================================================
def generar_excel_ppd(facturas, ruta_xlsx, mes_nombre, anio):
    """
    Genera el Excel de facturas PPD.
    
    Columnas:
      # | FECHA | FACTURA | QVET | PROVEEDOR | UUID | METODO |
      SUBTOTAL | IVA | IEPS | TOTAL | REFERENCIA
    """
    # Ordenar por fecha ascendente, luego por folio
    def _clave_orden(f):
        fecha_str = f.get("fecha", "")
        try:
            partes = fecha_str.split("/")
            if len(partes) == 3:
                fecha = (int(partes[2]), int(partes[1]), int(partes[0]))
            else:
                fecha = (0, 0, 0)
        except Exception:
            fecha = (0, 0, 0)
        return (fecha, str(f.get("folio", "")))

    facturas = sorted(facturas, key=_clave_orden)

    wb = Workbook()
    ws = wb.active
    ws.title = f"PPD {mes_nombre.capitalize()} {anio}"[:31]

    encabezados = [
        ("A", "#", 6),
        ("B", "FECHA", 12),
        ("C", "FACTURA", 20),
        ("D", "QVET", 12),
        ("E", "PROVEEDOR", 50),
        ("F", "UUID", 38),
        ("G", "METODO", 10),
        ("H", "SUBTOTAL", 14),
        ("I", "IVA", 12),
        ("J", "IEPS", 12),
        ("K", "TOTAL", 14),
        ("L", "REFERENCIA", 20),
    ]

    for letra, titulo, ancho in encabezados:
        c = ws[f"{letra}1"]
        c.value = titulo
        c.font = BOLD_WHITE
        c.fill = PatternFill("solid", fgColor=COLOR_PPD)
        c.alignment = CENTRO
        c.border = BORDER
        ws.column_dimensions[letra].width = ancho

        fila = 2
    for idx, f in enumerate(facturas, 1):
        # Número de línea enumerado al vuelo
        ws[f"A{fila}"] = idx
        ws[f"A{fila}"].alignment = CENTRO
        ws[f"A{fila}"].border = BORDER

        ws[f"B{fila}"] = f.get("fecha", "")
        ws[f"B{fila}"].alignment = CENTRO
        ws[f"B{fila}"].border = BORDER

        # FACTURA (con enlace al PDF)
        c = ws[f"C{fila}"]
        c.value = f.get("folio", "")
        c.alignment = IZQUIERDA
        c.border = BORDER
        ruta_pdf = _obtener_ruta_pdf_egreso(f)
        if ruta_pdf:
            c.hyperlink = ruta_pdf
            c.font = FUENTE_LINK

        # QVET (vacío, manual)
        ws[f"D{fila}"] = ""
        ws[f"D{fila}"].alignment = CENTRO
        ws[f"D{fila}"].border = BORDER

        # PROVEEDOR
        ws[f"E{fila}"] = f.get("nombre_emisor", "")
        ws[f"E{fila}"].alignment = IZQUIERDA
        ws[f"E{fila}"].border = BORDER

        # UUID
        ws[f"F{fila}"] = f.get("uuid", "")
        ws[f"F{fila}"].alignment = IZQUIERDA
        ws[f"F{fila}"].border = BORDER

        # METODO
        ws[f"G{fila}"] = "PPD"
        ws[f"G{fila}"].alignment = CENTRO
        ws[f"G{fila}"].border = BORDER

        # SUBTOTAL
        ws[f"H{fila}"] = float(f.get("subtotal", 0))
        ws[f"H{fila}"].number_format = FORMATO_MONEDA
        ws[f"H{fila}"].alignment = DERECHA
        ws[f"H{fila}"].border = BORDER

        # IVA
        ws[f"I{fila}"] = float(f.get("iva", 0))
        ws[f"I{fila}"].number_format = FORMATO_MONEDA
        ws[f"I{fila}"].alignment = DERECHA
        ws[f"I{fila}"].border = BORDER

        # IEPS
        ws[f"J{fila}"] = float(f.get("ieps", 0))
        ws[f"J{fila}"].number_format = FORMATO_MONEDA
        ws[f"J{fila}"].alignment = DERECHA
        ws[f"J{fila}"].border = BORDER

        # TOTAL
        ws[f"K{fila}"] = float(f.get("total", 0))
        ws[f"K{fila}"].number_format = FORMATO_MONEDA
        ws[f"K{fila}"].alignment = DERECHA
        ws[f"K{fila}"].border = BORDER

        # REFERENCIA (vacío, manual)
        ws[f"L{fila}"] = ""
        ws[f"L{fila}"].alignment = CENTRO
        ws[f"L{fila}"].border = BORDER

        fila += 1

    # Totales
    ws[f"E{fila}"] = "TOTAL:"
    ws[f"E{fila}"].font = BOLD_DARK
    ws[f"E{fila}"].alignment = DERECHA
    for letra in ["H", "I", "J", "K"]:
        c = ws[f"{letra}{fila}"]
        c.value = f"=SUM({letra}2:{letra}{fila-1})"
        c.font = BOLD_DARK
        c.number_format = FORMATO_MONEDA
        c.alignment = DERECHA

    wb.save(ruta_xlsx)
    return ruta_xlsx


# ============================================================
# ANEXAR A EXCEL EXISTENTE
# ============================================================
def anexar_facturas_al_excel(ruta_xlsx, facturas, tipo):
    """
    Abre un Excel existente de Egresos y anexa solo las facturas nuevas.

    tipo: "PUE" o "PPD".
      - PUE: UUID en columna C, # en A, TOTALES en F/G.
      - PPD: UUID en columna F, # en A, TOTALES en E/H-K.

    Detecta duplicados por UUID.
    Respeta ediciones manuales de las filas existentes.
    Devuelve (nuevos_agregados, omitidos).
    """
    from openpyxl import load_workbook

    if tipo not in ("PUE", "PPD"):
        raise ValueError(f"Tipo inválido: {tipo}")

    # Configuración por tipo
    if tipo == "PUE":
        COL_UUID = 3        # C
        COL_NO_FACTURA = 2  # B
        COLS_TOTALES = ["F", "G"]
    else:  # PPD
        COL_UUID = 6        # F
        COL_NO_FACTURA = 3  # C
        COLS_TOTALES = ["E", "H", "I", "J", "K"]

    wb = load_workbook(ruta_xlsx)
    ws = wb.active

    # --- 1. Leer lo existente y encontrar fila TOTALES ---
    uuids_existentes = set()
    fila_totales_original = None

    fila = 2
    max_fila = ws.max_row + 10
    while fila <= max_fila:
        # Buscar "TOTAL" en la primera columna con texto
        for col in range(1, ws.max_column + 1):
            val = ws.cell(row=fila, column=col).value
            if val and str(val).strip().upper() == "TOTAL:":
                fila_totales_original = fila
                break
        if fila_totales_original:
            break

        # Recoger UUID
        val_uuid = ws.cell(row=fila, column=COL_UUID).value
        if val_uuid:
            uuids_existentes.add(str(val_uuid).strip().upper())

        # Si la fila entera está vacía, parar
        fila_vacia = all(
            ws.cell(row=fila, column=c).value in (None, "")
            for c in range(1, ws.max_column + 1)
        )
        if fila_vacia:
            break
        fila += 1

    if fila_totales_original is None:
        fila_totales_original = fila

    # --- 2. Filtrar nuevas ---
    nuevas = []
    omitidas = 0
    for f in facturas:
        uuid = str(f.get("uuid", "")).strip().upper()
        if uuid and uuid in uuids_existentes:
            omitidas += 1
            continue
        nuevas.append(f)

    if not nuevas:
        return 0, omitidas

    # --- 3. Ordenar las nuevas por fecha + folio ---
    def _clave_orden(f):
        fecha_str = f.get("fecha", "")
        try:
            partes = fecha_str.split("/")
            if len(partes) == 3:
                fecha = (int(partes[2]), int(partes[1]), int(partes[0]))
            else:
                fecha = (0, 0, 0)
        except Exception:
            fecha = (0, 0, 0)
        return (fecha, str(f.get("folio", "")))

    nuevas = sorted(nuevas, key=_clave_orden)

    # --- 4. Deshacer merges de la fila TOTALES ---
    merges_a_quitar = []
    for rango in list(ws.merged_cells.ranges):
        if rango.min_row == fila_totales_original:
            merges_a_quitar.append(str(rango))
    for rango_str in merges_a_quitar:
        try:
            ws.unmerge_cells(rango_str)
        except Exception:
            pass

    # --- 5. Limpiar fila TOTALES ---
    from openpyxl.styles import Font, PatternFill, Alignment, Border
    for col in range(1, ws.max_column + 1):
        celda = ws.cell(row=fila_totales_original, column=col)
        celda.value = None
        celda.font = Font()
        celda.fill = PatternFill()
        celda.border = Border()
        celda.alignment = Alignment()
        celda.number_format = "General"

    # --- 6. Escribir nuevas filas ---
    fila_insercion = fila_totales_original
    for f in nuevas:
        _escribir_fila_egreso(ws, f, fila_insercion, tipo)
        fila_insercion += 1

    # --- 7. Renumerar columna A ---
    for i, fila_num in enumerate(range(2, fila_insercion)):
        ws[f"A{fila_num}"] = i + 1

    # --- 8. Reescribir TOTALES ---
    _escribir_totales_egreso(ws, fila_insercion, tipo)

    wb.save(ruta_xlsx)
    return len(nuevas), omitidas


def _escribir_fila_egreso(ws, f, fila, tipo):
    """Escribe una fila de factura en el Excel, según el tipo."""
    # Número de línea (se recalcula al final, pero ponemos uno temporal)
    ws[f"A{fila}"] = fila - 1
    ws[f"A{fila}"].alignment = CENTRO
    ws[f"A{fila}"].border = BORDER

    if tipo == "PUE":
        c = ws[f"B{fila}"]
        c.value = f.get("folio", "")
        c.alignment = IZQUIERDA
        c.border = BORDER
        ruta_pdf = _obtener_ruta_pdf_egreso(f)
        if ruta_pdf:
            c.hyperlink = ruta_pdf
            c.font = FUENTE_LINK

        ws[f"C{fila}"] = f.get("uuid", "")
        ws[f"C{fila}"].alignment = IZQUIERDA
        ws[f"C{fila}"].border = BORDER

        ws[f"D{fila}"] = f.get("rfc_emisor", "")
        ws[f"D{fila}"].alignment = CENTRO
        ws[f"D{fila}"].border = BORDER

        ws[f"E{fila}"] = f.get("nombre_emisor", "")
        ws[f"E{fila}"].alignment = IZQUIERDA
        ws[f"E{fila}"].border = BORDER

        ws[f"F{fila}"] = f.get("fecha", "")
        ws[f"F{fila}"].alignment = CENTRO
        ws[f"F{fila}"].border = BORDER

        ws[f"G{fila}"] = float(f.get("total", 0))
        ws[f"G{fila}"].number_format = FORMATO_MONEDA
        ws[f"G{fila}"].alignment = DERECHA
        ws[f"G{fila}"].border = BORDER

        ws[f"H{fila}"] = f.get("forma_pago_texto", "")
        ws[f"H{fila}"].alignment = CENTRO
        ws[f"H{fila}"].border = BORDER

        ws[f"I{fila}"] = f.get("observacion", "")
        ws[f"I{fila}"].alignment = IZQUIERDA
        ws[f"I{fila}"].border = BORDER

    else:  # PPD
        ws[f"B{fila}"] = f.get("fecha", "")
        ws[f"B{fila}"].alignment = CENTRO
        ws[f"B{fila}"].border = BORDER

        c = ws[f"C{fila}"]
        c.value = f.get("folio", "")
        c.alignment = IZQUIERDA
        c.border = BORDER
        ruta_pdf = _obtener_ruta_pdf_egreso(f)
        if ruta_pdf:
            c.hyperlink = ruta_pdf
            c.font = FUENTE_LINK

        ws[f"D{fila}"] = ""
        ws[f"D{fila}"].alignment = CENTRO
        ws[f"D{fila}"].border = BORDER

        ws[f"E{fila}"] = f.get("nombre_emisor", "")
        ws[f"E{fila}"].alignment = IZQUIERDA
        ws[f"E{fila}"].border = BORDER

        ws[f"F{fila}"] = f.get("uuid", "")
        ws[f"F{fila}"].alignment = IZQUIERDA
        ws[f"F{fila}"].border = BORDER

        ws[f"G{fila}"] = "PPD"
        ws[f"G{fila}"].alignment = CENTRO
        ws[f"G{fila}"].border = BORDER

        ws[f"H{fila}"] = float(f.get("subtotal", 0))
        ws[f"H{fila}"].number_format = FORMATO_MONEDA
        ws[f"H{fila}"].alignment = DERECHA
        ws[f"H{fila}"].border = BORDER

        ws[f"I{fila}"] = float(f.get("iva", 0))
        ws[f"I{fila}"].number_format = FORMATO_MONEDA
        ws[f"I{fila}"].alignment = DERECHA
        ws[f"I{fila}"].border = BORDER

        ws[f"J{fila}"] = float(f.get("ieps", 0))
        ws[f"J{fila}"].number_format = FORMATO_MONEDA
        ws[f"J{fila}"].alignment = DERECHA
        ws[f"J{fila}"].border = BORDER

        ws[f"K{fila}"] = float(f.get("total", 0))
        ws[f"K{fila}"].number_format = FORMATO_MONEDA
        ws[f"K{fila}"].alignment = DERECHA
        ws[f"K{fila}"].border = BORDER

        ws[f"L{fila}"] = ""
        ws[f"L{fila}"].alignment = CENTRO
        ws[f"L{fila}"].border = BORDER


def _escribir_totales_egreso(ws, fila, tipo):
    """Reescribe la fila de totales al final."""
    if tipo == "PUE":
        ws[f"F{fila}"] = "TOTAL:"
        ws[f"F{fila}"].font = BOLD_DARK
        ws[f"F{fila}"].alignment = DERECHA
        ws[f"G{fila}"] = f"=SUM(G2:G{fila-1})"
        ws[f"G{fila}"].font = BOLD_DARK
        ws[f"G{fila}"].number_format = FORMATO_MONEDA
        ws[f"G{fila}"].alignment = DERECHA

    else:  # PPD
        ws[f"E{fila}"] = "TOTAL:"
        ws[f"E{fila}"].font = BOLD_DARK
        ws[f"E{fila}"].alignment = DERECHA
        for letra in ["H", "I", "J", "K"]:
            c = ws[f"{letra}{fila}"]
            c.value = f"=SUM({letra}2:{letra}{fila-1})"
            c.font = BOLD_DARK
            c.number_format = FORMATO_MONEDA
            c.alignment = DERECHA


def _obtener_ruta_pdf_egreso(factura):
    """
    Construye la ruta relativa al PDF de una factura de Egreso.

    El Excel está en: Egreso/<Sucursal>/Deposito/ (o similar).
    El PDF está en:   Egreso/<Sucursal>/<Metodo>/<Forma>/<nombre>.PDF

    Nombre del PDF: <serie>-<folio>.PDF o <folio>.PDF
    """
    try:
        folio = factura.get("folio", "")
        if not folio:
            return None

        serie = str(factura.get("serie", "")).strip()
        if serie:
            nombre = f"{serie}-{folio}.PDF"
        else:
            nombre = f"{folio}.PDF"

        # Ruta relativa al Excel (que está en Deposito_Egreso/ o Deposito/)
        carpeta = factura.get("carpeta", "")  # ej: "Baalak/PUE/TC"
        if carpeta:
            return f"../{carpeta}/{nombre}"
        return f"../{nombre}"
    except Exception:
        return None
