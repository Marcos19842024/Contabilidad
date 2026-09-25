# -*- coding: utf-8 -*-
"""
core/persistencia.py
Carga/guarda registros por año, historial de autocompletado y validaciones.
"""

import json
from pathlib import Path

from core.rutas import HISTORIAL_FILE, ruta_registros


# ============================================================
# REGISTROS POR AÑO
# ============================================================
def cargar_db(anio):
    """Carga los registros del año indicado."""
    ruta = ruta_registros(anio)
    if ruta.exists():
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def guardar_db(regs, anio):
    """Guarda los registros en el archivo del año indicado."""
    ruta = ruta_registros(anio)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(regs, f, ensure_ascii=False, indent=2)


# ============================================================
# HISTORIAL DE AUTOCOMPLETADO
# ============================================================
def cargar_historial():
    """Carga el historial de nombres y RFCs."""
    if HISTORIAL_FILE.exists():
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"nombre": [], "rfc": []}


def guardar_historial(hist):
    """Guarda el historial de autocompletado."""
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


def actualizar_historial(regs):
    """Actualiza el historial con los nombres y RFCs de los registros dados."""
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


# ============================================================
# VALIDACIONES
# ============================================================
def existe_valor_unico(registros, clave, valor, ignorar_id=None):
    """Verifica si un valor ya existe en la clave dada (case-insensitive)."""
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
    """Extrae el valor numérico de un No. de factura."""
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
    """Devuelve el siguiente No. de factura esperado (max + 1) para el filtro."""
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