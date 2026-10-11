# core/recordatorios/sucursales.py
"""
Adaptador de sucursales para Recordatorios.
La fuente de verdad es config/veterinaria.py (config_ui.json).

Mantiene la API pública que ya usa el módulo.
"""

from config.veterinaria import (
    obtener_veterinaria,
    guardar_veterinaria,
    sucursal_activa as _sucursal_activa,
    nombre_clinica_activa as _nombre_clinica_activa,
    nombre_corto_activo as _nombre_corto_activo,
    sucursales as _sucursales,
    sucursales_activas as _sucursales_activas,
    cambiar_sucursal_activa as _cambiar_sucursal_activa,
)


SUCURSALES_FILE = None  # deprecado


def cargar_sucursales() -> dict:
    vet = obtener_veterinaria()
    return {
        "sucursal_activa": vet.get("sucursal_activa", ""),
        "sucursales": vet.get("sucursales", []),
    }


def guardar_sucursales(data: dict):
    vet = obtener_veterinaria()
    vet["sucursal_activa"] = data.get("sucursal_activa", vet.get("sucursal_activa"))
    vet["sucursales"] = data.get("sucursales", vet.get("sucursales", []))
    guardar_veterinaria(vet)


def sucursal_activa() -> dict:
    return _sucursal_activa()


def nombre_clinica_activa() -> str:
    return _nombre_clinica_activa()


def nombre_corto_activo() -> str:
    return _nombre_corto_activo()


def sucursales_activas() -> list:
    return _sucursales_activas()


def cambiar_sucursal_activa(sucursal_id: str):
    _cambiar_sucursal_activa(sucursal_id)