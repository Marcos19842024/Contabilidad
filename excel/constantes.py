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
    "AC": ("EFECTIVO",                    "TIPO DE PAGO",  "money"),
    "AD": ("TARJETA",                     "TIPO DE PAGO",  "money"),
    "AE": ("CHEQUE",                      "TIPO DE PAGO",  "money"),
    "AF": ("TRANSF.",                     "TIPO DE PAGO",  "money"),
    "AG": ("VALE",                        "TIPO DE PAGO",  "money"),
    "AH": ("FECHA DE TIMBRADO",           "CONTROL",       "date"),
    "AI": ("FECHA FICHA DE DEPÓSITO",     "CONTROL",       "date"),
    "AJ": ("MONTO DE FICHA DE DEPOSITO",  "CONTROL",       "money"),
    "AK": ("FECHA SANTANDER TARJETA",     "CONTROL",       "date"),
    "AL": ("EDO. CUENTA SANTANDER DEBITO","CONTROL",       "money"),
    "AM": ("EDO. CUENTA SANTANDER CREDITO","CONTROL",      "money"),
    "AN": ("FECHA SANTANDER TRANSFERENCIA","CONTROL",      "date"),
    "AO": ("TRANSFERENCIA SANTANDER",     "CONTROL",       "money"),
    "AP": ("FOLIO FISCAL",                "CONTROL",       "text"),
}

# ============================================================
# MAPA DE CLAVES (letra → clave del registro)
# ============================================================
MAPA_CLAVES_EXCEL = {
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
    "AD": "__tarjeta__",
    "AE": "cheque",
    "AF": "transfer",
    "AG": "vale",
    "AH": "fecha_impresion",
    "AI": "",
    "AJ": "__efectivo_dup__",
    "AK": "",
    "AL": "td",
    "AM": "tc",
    "AN": "",
    "AO": "__transfer_dup__",
    "AP": "folio_fiscal",
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
    "AB": "=AC{r}+AD{r}+AE{r}+AF{r}+AG{r}",
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
    (28, 28, "TOTAL"),
    (29, 33, "TIPO DE PAGO"),
    (34, 42, "CONTROL"),
]