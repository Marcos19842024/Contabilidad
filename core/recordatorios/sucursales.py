# core/recordatorios/sucursales.py
"""
Catálogo de sucursales configurable.
Se guarda en ~/Documents/Vet Suite/recordatorios/sucursales.json
"""

from core.rutas_recordatorios import CARPETA_DATOS, _cargar_json, _guardar_json
from pathlib import Path


SUCURSALES_FILE = CARPETA_DATOS / "sucursales.json"


SUCURSALES_DEFAULT = {
    "sucursal_activa": "BAALAK_CENTRAL",
    "sucursales": [
        {
            "id": "BAALAK_CENTRAL",
            "nombre": "Clínica Veterinaria Baalak (Central)",
            "nombre_corto": "Baalak (Central)",
            "activa": True,
            "coordenadas": {"lat": 19.831218, "lng": -90.534602},
        },
        {
            "id": "BAALAK_PRADO",
            "nombre": "Clínica Veterinaria Baalak (Prado)",
            "nombre_corto": "Baalak (Prado)",
            "activa": False,
            "coordenadas": {"lat": 19.832604, "lng": -90.551841},
        },
        {
            "id": "ANIMALIA",
            "nombre": "Clínica Veterinaria Animalia",
            "nombre_corto": "Animalia",
            "activa": False,
            "coordenadas": {"lat": 18.143160, "lng": -94.454624},
        },
    ],
}


def cargar_sucursales() -> dict:
    """Carga el catálogo de sucursales."""
    data = _cargar_json(SUCURSALES_FILE, None)
    if not data:
        _guardar_json(SUCURSALES_FILE, SUCURSALES_DEFAULT)
        return dict(SUCURSALES_DEFAULT)
    # Asegurar campos por defecto
    for k, v in SUCURSALES_DEFAULT.items():
        data.setdefault(k, v)
    return data


def guardar_sucursales(data: dict):
    """Guarda el catálogo de sucursales."""
    _guardar_json(SUCURSALES_FILE, data)


def sucursal_activa() -> dict:
    """Devuelve el dict de la sucursal activa."""
    data = cargar_sucursales()
    activa_id = data.get("sucursal_activa", "BAALAK_CENTRAL")
    for s in data["sucursales"]:
        if s["id"] == activa_id:
            return s
    # Fallback
    return data["sucursales"][0]


def nombre_clinica_activa() -> str:
    """Nombre completo de la sucursal activa."""
    return sucursal_activa().get("nombre", "")


def nombre_corto_activo() -> str:
    """Nombre corto de la sucursal activa."""
    return sucursal_activa().get("nombre_corto", "")


def sucursales_activas() -> list:
    """Lista de sucursales activas para el selector."""
    data = cargar_sucursales()
    return [s for s in data["sucursales"] if s.get("activa", True)]


def cambiar_sucursal_activa(sucursal_id: str):
    """Cambia la sucursal activa y guarda."""
    data = cargar_sucursales()
    data["sucursal_activa"] = sucursal_id
    guardar_sucursales(data)