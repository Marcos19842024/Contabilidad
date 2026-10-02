# -*- coding: utf-8 -*-
"""
sat/guardar_egresos.py
Guarda las facturas de Egresos en un archivo JSON por año.
"""
import json
from datetime import datetime
from pathlib import Path


def _carpeta_datos():
    """Carpeta de datos de la app."""
    import sys
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Contabilidad App"
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    else:
        return Path(__file__).parent.parent


def ruta_registros_egresos(anio):
    """Ruta al archivo de registros de egresos del año."""
    return _carpeta_datos() / f"registros_egresos_{anio}.json"


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
    """Verifica si un UUID ya existe."""
    if not uuid:
        return False
    uuid = str(uuid).strip().upper()
    for r in registros:
        if ignorar_id is not None and r.get("id") == ignorar_id:
            continue
        if str(r.get("uuid", "")).strip().upper() == uuid:
            return True
    return False


def guardar_facturas(facturas, anio=None, agregar_sucursal=True):
    """
    Guarda las facturas procesadas en el archivo del año.
    
    Parámetros:
      - facturas: lista de dicts (del procesar_xml).
      - anio: año de los registros. Si es None, se toma de cada factura.
      - agregar_sucursal: si True, agrega el campo "sucursal" (default: "Baalak").
    
    Devuelve:
      - (nuevas, duplicadas)
    """
    if anio is None:
        anio = datetime.now().year

    # Cargar registros existentes
    registros = cargar_db_egresos(anio)

    nuevas = 0
    duplicadas = 0

    for f in facturas:
        uuid = f.get("uuid", "")

        # Verificar duplicado
        if existe_uuid_egresos(registros, uuid):
            duplicadas += 1
            continue

        # Agregar ID y campos extra
        f["id"] = int(datetime.now().timestamp() * 1000) + nuevas
        f["anio"] = anio
        f["mes"] = _mes_desde_fecha(f.get("fecha", ""))
        if agregar_sucursal:
            f["sucursal"] = "Baalak"  # Default

        registros.append(f)
        nuevas += 1

    # Guardar
    guardar_db_egresos(registros, anio)

    return nuevas, duplicadas


def _mes_desde_fecha(fecha):
    """Extrae el mes de una fecha 'dd/mm/yyyy'."""
    from config.campos import MESES_ES
    try:
        partes = fecha.split("/")
        if len(partes) == 3:
            mes_num = int(partes[1])
            return MESES_ES[mes_num - 1]
    except Exception:
        pass
    return ""
