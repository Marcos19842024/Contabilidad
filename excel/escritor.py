# -*- coding: utf-8 -*-
"""
excel/escritor.py
Escritura de filas, encabezados y totales en una hoja de Excel.
"""

from datetime import datetime

from openpyxl.styles import PatternFill, Font

from excel.constantes import (
    COLORES_SECCION_EXCEL,
    COLUMNAS_EXCEL,
    MAPA_CLAVES_EXCEL,
    FORMULAS_AUTO_EXCEL,
    GRUPOS_EXCEL,
)
from excel.estilos import (
    BORDER,
    CENTRO,
    DERECHA,
    IZQUIERDA,
    BOLD_WHITE,
    BOLD_DARK,
    FUENTE_NORMAL,
    SIN_RELLENO,
    FILL_TOTAL,
    FORMATO_MONEDA,
    FORMATO_FECHA,
)


# Fuente para hipervínculos
FUENTE_LINK = Font(color="0563C1", underline="single")


def escribir_encabezados(ws):
    """Escribe fila 1 (grupos) y fila 2 (columnas) con estilos."""
    # --- Fila 1: grupos ---
    for ini, fin, texto in GRUPOS_EXCEL:
        c = ws.cell(row=1, column=ini, value=texto)
        c.font = BOLD_DARK
        c.alignment = CENTRO

        for col in range(ini, fin + 1):
            celda = ws.cell(row=1, column=col)
            celda.border = BORDER
            celda.alignment = CENTRO

        if ini != fin:
            ws.merge_cells(start_row=1, start_column=ini,
                           end_row=1, end_column=fin)

    # --- Fila 2: columnas ---
    for letra, (titulo, seccion, tipo) in COLUMNAS_EXCEL.items():
        c = ws[f"{letra}2"]
        c.value = titulo
        c.font = BOLD_WHITE
        c.fill = PatternFill("solid", fgColor=COLORES_SECCION_EXCEL[seccion])
        c.alignment = CENTRO
        c.border = BORDER


def _buscar_letra_por_clave(clave_buscada):
    """Devuelve la letra de columna cuya clave coincide."""
    for letra, clave in MAPA_CLAVES_EXCEL.items():
        if clave == clave_buscada:
            return letra
    return None


def _obtener_ruta_pdf(reg):
    """
    Construye la ruta relativa al PDF de un registro.
    La ruta es relativa al Excel (que está en .../Ingreso/Deposito/).
    El PDF está en .../Ingreso/Facturas <Centro>/<Fecha>/<NoFactura>.PDF.
    """
    try:
        from core.adjuntos import archivos_del_registro

        adjuntos = archivos_del_registro(reg)
        if not adjuntos:
            return None

        # Buscar el PDF
        pdf = None
        for a in adjuntos:
            if a.suffix.lower() == ".pdf":
                pdf = a
                break

        if not pdf:
            return None

        # Construir la ruta relativa desde el Excel (que está en Deposito)
        # Excel:  .../Ingreso/Deposito/Resumen.xlsx
        # PDF:    .../Ingreso/Facturas <Centro>/<Fecha>/<archivo>.PDF
        # Ruta:   ../Facturas <Centro>/<Fecha>/<archivo>.PDF

        centro = reg.get("centro", "Central")
        fecha = reg.get("fecha", "").replace("/", "-")

        # El "../" sube desde Deposito/ a Ingreso/
        return f"../Facturas {centro}/{fecha}/{pdf.name}"

    except Exception:
        return None


def escribir_fila(ws, r, fila, carpeta_adjuntos=None):
    """Escribe UNA fila de registro con estilos, fórmulas y casos especiales."""
    valor_tc = float(r.get("tc", 0) or 0)
    valor_td = float(r.get("td", 0) or 0)
    valor_tarjeta = valor_tc + valor_td
    valor_efectivo = float(r.get("efectivo", 0) or 0)
    valor_transfer = float(r.get("transfer", 0) or 0)

    for letra, (titulo, seccion, tipo) in COLUMNAS_EXCEL.items():
        clave = MAPA_CLAVES_EXCEL[letra]
        c = ws[f"{letra}{fila}"]

        # Reset de estilos base
        c.font = FUENTE_NORMAL
        c.fill = SIN_RELLENO
        c.border = BORDER

        # ============================================================
        # Caso especial: enlace al PDF en el No. de factura
        # ============================================================
        if clave == "__link_factura__":
            no_factura = str(r.get("no_factura", "")).strip()
            c.value = no_factura
            c.alignment = IZQUIERDA

            # Construir el enlace al PDF
            ruta_pdf = _obtener_ruta_pdf(r)
            if ruta_pdf:
                try:
                    c.hyperlink = ruta_pdf
                    c.font = FUENTE_LINK
                except Exception:
                    pass
            continue

        # ============================================================
        # Casos especiales varios
        # ============================================================
        if clave == "__tarjeta__":
            letra_tc = _buscar_letra_por_clave("tc")
            letra_td = _buscar_letra_por_clave("td")
            if letra_tc and letra_td:
                c.value = f"={letra_tc}{fila}+{letra_td}{fila}"
                c.number_format = FORMATO_MONEDA
            elif valor_tarjeta > 0:
                c.value = valor_tarjeta
                c.number_format = FORMATO_MONEDA
            c.alignment = DERECHA
            continue

        if clave == "__efectivo_dup__":
            letra_efectivo = _buscar_letra_por_clave("efectivo")
            if letra_efectivo:
                c.value = f"={letra_efectivo}{fila}"
                c.number_format = FORMATO_MONEDA
            elif valor_efectivo > 0:
                c.value = valor_efectivo
                c.number_format = FORMATO_MONEDA
            c.alignment = DERECHA
            continue

        if clave == "__transfer_dup__":
            letra_transfer = _buscar_letra_por_clave("transfer")
            if letra_transfer:
                c.value = f"={letra_transfer}{fila}"
                c.number_format = FORMATO_MONEDA
            elif valor_transfer > 0:
                c.value = valor_transfer
                c.number_format = FORMATO_MONEDA
            c.alignment = DERECHA
            continue

        # ============================================================
        # Total Remisiones (con rojo si no cuadra)
        # ============================================================
        if clave == "__total_remisiones__":
            # Fórmula: suma de categorías + IVAs (F a AA)
            formula = FORMULAS_AUTO_EXCEL["AB"].format(r=fila)
            c.value = formula
            c.number_format = FORMATO_MONEDA
            c.alignment = DERECHA

            # Verificar si cuadra con Total Factura
            # Comparar los valores almacenados en el registro
            total_remisiones = _calcular_total_remisiones(r)
            total_factura = _calcular_total_factura(r)
            if abs(total_remisiones - total_factura) > 0.01:
                c.font = Font(color="FF0000", bold=True)
            continue

        # ============================================================
        # Total Factura (suma de pagos)
        # ============================================================
        if clave == "__total_factura__":
            formula = FORMULAS_AUTO_EXCEL["AC"].format(r=fila)
            c.value = formula
            c.number_format = FORMATO_MONEDA
            c.alignment = DERECHA
            c.font = Font(bold=True)
            continue

        # ============================================================
        # Campos vacíos (solo encabezado)
        # ============================================================
        if clave == "":
            c.alignment = CENTRO
            continue

        # ============================================================
        # Casos normales
        # ============================================================
        valor = r.get(clave, 0 if tipo == "money" else "")
        expresion = r.get(f"{clave}__expr", "")

        if tipo == "money":
            if expresion:
                c.value = f"={expresion}"
            elif letra in FORMULAS_AUTO_EXCEL:
                c.value = FORMULAS_AUTO_EXCEL[letra].format(r=fila)
            else:
                c.value = float(valor or 0)
            c.number_format = FORMATO_MONEDA
            c.alignment = DERECHA

        elif tipo == "date":
            if valor:
                try:
                    fecha_dt = datetime.strptime(str(valor).strip(), "%d/%m/%Y")
                    c.value = fecha_dt
                    c.number_format = FORMATO_FECHA
                except (ValueError, TypeError):
                    c.value = valor
            c.alignment = CENTRO

        else:
            c.value = valor
            c.alignment = IZQUIERDA


def _calcular_total_remisiones(r):
    """Suma las categorías + IVAs de un registro."""
    claves = [
        "u_importe", "u_iva",
        "ac_importe", "ac_iva",
        "med_importe", "med_sin_iva", "med_iva",
        "hig_importe", "hig_sin_iva", "hig_iva",
        "hig_sin_ieps_6", "hig_ieps_6",
        "hig_sin_ieps_7", "hig_ieps_7",
        "est_importe", "est_iva",
        "tra_importe", "tra_iva",
        "pen_importe", "pen_iva",
        "vac_importe",
        "cli_importe",
    ]
    total = 0.0
    for k in claves:
        try:
            total += float(r.get(k, 0) or 0)
        except (ValueError, TypeError):
            pass
    return round(total, 2)


def _calcular_total_factura(r):
    """Suma los tipos de pago de un registro."""
    claves = ["efectivo", "tc", "td", "cheque", "transfer", "vale"]
    total = 0.0
    for k in claves:
        try:
            total += float(r.get(k, 0) or 0)
        except (ValueError, TypeError):
            pass
    return round(total, 2)


def escribir_fila_totales(ws, fila):
    """Escribe la fila TOTALES con fórmulas =SUM(...)."""
    MERGE_INI = 1
    MERGE_FIN = 5

    c_tot = ws.cell(row=fila, column=MERGE_INI, value="TOTALES")
    c_tot.font = BOLD_DARK
    c_tot.fill = FILL_TOTAL
    c_tot.alignment = CENTRO
    c_tot.border = BORDER

    for col in range(MERGE_INI, MERGE_FIN + 1):
        celda = ws.cell(row=fila, column=col)
        try:
            celda.fill = FILL_TOTAL
            celda.border = BORDER
            celda.alignment = CENTRO
        except Exception:
            pass

    ws.merge_cells(start_row=fila, start_column=MERGE_INI,
                   end_row=fila, end_column=MERGE_FIN)

    for letra, (titulo, seccion, tipo) in COLUMNAS_EXCEL.items():
        col_idx = ws[f"{letra}1"].column
        if MERGE_INI <= col_idx <= MERGE_FIN:
            continue
        c = ws.cell(row=fila, column=col_idx)
        if tipo in ("money", "total_remisiones", "total_factura"):
            c.value = f"=SUM({letra}3:{letra}{fila - 1})"
            c.number_format = FORMATO_MONEDA
            c.alignment = DERECHA
        c.font = BOLD_DARK
        c.fill = FILL_TOTAL
        c.border = BORDER


def ajustar_anchos(ws, fila_total):
    """Ajusta el ancho de las columnas según el contenido."""
    from openpyxl.utils import get_column_letter

    for letra in COLUMNAS_EXCEL.keys():
        largo_max = len(str(COLUMNAS_EXCEL[letra][0]))
        for ini, fin, texto in GRUPOS_EXCEL:
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