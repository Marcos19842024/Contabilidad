# -*- coding: utf-8 -*-
"""
core/persistencia_egresos.py
Carga y guarda los registros de Egresos.
"""

import json

from core.rutas_egresos import ruta_registros_egresos


def cargar_db_egresos(anio):
    """Carga los registros de egresos del año."""
    ruta = ruta_registros_egresos(anio)
    if ruta.exists():
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def guardar_db_egresos(regs, anio):
    """Guarda los registros de egresos."""
    ruta = ruta_registros_egresos(anio)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(regs, f, ensure_ascii=False, indent=2)


def existe_uuid_egresos(registros, uuid, ignorar_id=None):
    """Verifica si un UUID ya existe en los registros."""
    if not uuid:
        return False
    uuid = str(uuid).strip().upper()
    for r in registros:
        if ignorar_id is not None and r.get("id") == ignorar_id:
            continue
        if str(r.get("uuid", "")).strip().upper() == uuid:
            return True
    return False