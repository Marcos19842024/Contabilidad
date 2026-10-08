# -*- coding: utf-8 -*-
"""
core/persistencia_egresos.py
Carga, guarda y mantiene el historial de los registros de Egresos.
"""

import json

from core.rutas_egresos import (
    ruta_registros_egresos,
    CARPETA_DATOS as _CARPETA_DATOS,
)


# Archivo de historial de Egresos (separado del de Ingresos)
HISTORIAL_EGRESOS_FILE = _CARPETA_DATOS / "historial_egresos.json"


def cargar_db_egresos(anio):
    ruta = ruta_registros_egresos(anio)
    if ruta.exists():
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def guardar_db_egresos(regs, anio):
    ruta = ruta_registros_egresos(anio)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(regs, f, ensure_ascii=False, indent=2)


def existe_uuid_egresos(registros, uuid, ignorar_id=None):
    if not uuid:
        return False
    uuid = str(uuid).strip().upper()
    for r in registros:
        if ignorar_id is not None and r.get("id") == ignorar_id:
            continue
        if str(r.get("uuid", "")).strip().upper() == uuid:
            return True
    return False


# ============================================================
# HISTORIAL DE EGRESOS
# ============================================================
def cargar_historial_egresos():
    if not HISTORIAL_EGRESOS_FILE.exists():
        return {}
    try:
        with open(HISTORIAL_EGRESOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_historial_egresos(historial):
    with open(HISTORIAL_EGRESOS_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def actualizar_historial_egresos(registros):
    historial = {
        "rfc_emisor": [],
        "nombre_emisor": [],
        "observacion": [],
    }
    rfcs = set()
    nombres = set()
    observaciones = set()
    for r in registros:
        rfc = str(r.get("rfc_emisor", "")).strip().upper()
        if rfc:
            rfcs.add(rfc)
        nombre = str(r.get("nombre_emisor", "")).strip().upper()
        if nombre:
            nombres.add(nombre)
        obs = str(r.get("observacion", "")).strip().upper()
        if obs:
            observaciones.add(obs)
    historial["rfc_emisor"] = sorted(rfcs)
    historial["nombre_emisor"] = sorted(nombres)
    historial["observacion"] = sorted(observaciones)
    guardar_historial_egresos(historial)
    return historial


def obtener_historial_emisores():
    h = cargar_historial_egresos()
    rfcs = h.get("rfc_emisor", [])
    nombres = h.get("nombre_emisor", [])
    resultado = []
    for i, rfc in enumerate(rfcs):
        nombre = nombres[i] if i < len(nombres) else ""
        resultado.append({"rfc": rfc, "nombre": nombre})
    return resultado