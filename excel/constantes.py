# -*- coding: utf-8 -*-
"""
excel/constantes.py
Constantes para la generación del Excel de resumen.
"""

# ============================================================
# COLORES POR SECCIÓN (formato openpyxl: hex sin #)
# ============================================================
COLORES_SECCION_EXCEL = {
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

# ============================================================
# COLUMNAS DEL EXCEL
# letra → (título, sección, tipo)
# ============================================================
COLUMNAS_EXCEL = {
    "A":  ("No. DE FACTURA",              "GENERAL",       "link_factura"),
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
    "AB": ("Total Remisiones",            "TOTAL",         "total_remisiones"),
    "AC": ("Total Factura",               "TOTAL",         "total_factura"),
    "AD": ("EFECTIVO",                    "TIPO DE PAGO",  "money"),
    "AE": ("TARJETA",                     "TIPO DE PAGO",  "money"),
    "AF": ("CHEQUE",                      "TIPO DE PAGO",  "money"),
    "AG": ("TRANSF.",                     "TIPO DE PAGO",  "money"),
    "AH": ("VALE",                        "TIPO DE PAGO",  "money"),
    "AI": ("FECHA DE TIMBRADO",           "CONTROL",       "date"),
    "AJ": ("FECHA FICHA DE DEPÓSITO",     "CONTROL",       "date"),
    "AK": ("MONTO DE FICHA DE DEPOSITO",  "CONTROL",       "money"),
    "AL": ("FECHA SANTANDER TARJETA",     "CONTROL",       "date"),
    "AM": ("EDO. CUENTA SANTANDER DEBITO","CONTROL",       "money"),
    "AN": ("EDO. CUENTA SANTANDER CREDITO","CONTROL",      "money"),
    "AO": ("FECHA SANTANDER TRANSFERENCIA","CONTROL",      "date"),
    "AP": ("TRANSFERENCIA SANTANDER",     "CONTROL",       "money"),
    "AQ": ("FOLIO FISCAL",                "CONTROL",       "text"),
}

# ============================================================
# MAPA DE CLAVES (letra → clave del registro)
# ============================================================
MAPA_CLAVES_EXCEL = {
    "A": "__link_factura__",
    "B": "qvet",
    "C": "fecha",
    "D": "nombre",
    "E": "rfc",
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
    "AB": "__total_remisiones__",
    "AC": "__total_factura__",
    "AD": "efectivo",
    "AE": "__tarjeta__",
    "AF": "cheque",
    "AG": "transfer",
    "AH": "vale",
    "AI": "fecha_impresion",
    "AJ": "",
    "AK": "__efectivo_dup__",
    "AL": "",
    "AM": "td",
    "AN": "tc",
    "AO": "",
    "AP": "__transfer_dup__",
    "AQ": "folio_fiscal",
}

# ============================================================
# FÓRMULAS AUTOMÁTICAS POR COLUMNA
# ============================================================
FORMULAS_AUTO_EXCEL = {
    "G":  "=F{r}*0.16",
    "I":  "=H{r}*0.16",
    "L":  "=K{r}*0.16",
    "O":  "=N{r}*0.16",
    "Q":  "=P{r}*0.06",
    "S":  "=R{r}*0.07",
    "U":  "=T{r}*0.16",
    "W":  "=V{r}*0.16",
    "Y":  "=X{r}*0.16",
    "AB": "=F{r}+G{r}+H{r}+I{r}+J{r}+K{r}+L{r}+M{r}+N{r}+O{r}+P{r}+Q{r}+R{r}+S{r}+T{r}+U{r}+V{r}+W{r}+X{r}+Y{r}+Z{r}+AA{r}",
    "AC": "=AD{r}+AE{r}+AF{r}+AG{r}+AH{r}",
}

# ============================================================
# GRUPOS DE ENCABEZADOS (columna_ini, columna_fin, texto)
# ============================================================
GRUPOS_EXCEL = [
    (6,  7,  "U"),
    (8,  9,  "ACCESORIOS"),
    (10, 12, "MEDICAMENTOS"),
    (13, 19, "HIGIENE"),
    (20, 21, "ESTETICA"),
    (22, 23, "TRANSPORTE"),
    (24, 25, "PENSION"),
    (26, 26, "VACUNA"),
    (27, 27, "CLINICA"),
    (28, 29, "TOTAL"),
    (30, 34, "TIPO DE PAGO"),
    (35, 43, "CONTROL"),
]