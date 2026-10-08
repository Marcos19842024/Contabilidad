# -*- coding: utf-8 -*-
"""
core/rutas_recordatorios.py
Rutas de datos para el módulo de Recordatorios (futuro).
"""

import sys
from pathlib import Path


def _carpeta_datos():
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Vet Suite" / "recordatorios"
    else:
        carpeta = Path(__file__).parent.parent / "recordatorios"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def _carpeta_reportes():
    """Reportes de recordatorios van a ~/Documents/ (visibles)."""
    carpeta = Path.home() / "Documents" / "Vet Suite" / "Reportes Recordatorios"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


CARPETA_DATOS    = _carpeta_datos()
CARPETA_REPORTES = _carpeta_reportes()

HISTORIAL_FILE = CARPETA_DATOS / "historial_recordatorios.json"
AGENDA_CACHE   = CARPETA_DATOS / "agenda_importada.json"
VACUNAS_CACHE  = CARPETA_DATOS / "vacunas_importadas.json"

# core/rutas_recordatorios.py (agregar al final)
import json

def _cargar_json(path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _guardar_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)