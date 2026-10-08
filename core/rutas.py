# -*- coding: utf-8 -*-
"""
core/rutas.py
Rutas de carpetas de datos y de facturas por año/mes/centro.
"""

import sys
from datetime import datetime
from pathlib import Path

from config.campos import MESES_ES


BASE_DIR = Path.home() / "Documents"


def _carpeta_datos():
    """
    Carpeta única de datos de la app (NO por año).
    Compartida entre años: catálogo, excepciones, backups, registros.

    - Dev:  <raíz proyecto>/ingresos/
    - Prod: ~/Documents/Vet Suite/ingresos/
    """
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Vet Suite" / "ingresos"
    else:
        carpeta = Path(__file__).parent.parent / "ingresos"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


_CARPETA_DATOS = _carpeta_datos()

# Archivos compartidos entre años
HISTORIAL_FILE = _CARPETA_DATOS / "historial_autocompletado.json"


def ruta_registros(anio):
    """Ruta al archivo de registros del año indicado."""
    return _CARPETA_DATOS / f"registros_ingresos_{anio}.json"


def ruta_ingreso(centro, anio=None, mes=None):
    """Carpeta de facturas de un centro en un mes/año concreto."""
    hoy = datetime.now()
    anio = anio or hoy.year
    mes = mes or hoy.month
    return (
        BASE_DIR / f"Contabilidad {anio}"
        / f"Contabilidad {MESES_ES[mes - 1]}"
        / "Ingreso"
        / f"Facturas {centro.capitalize()}"
    )


def ruta_deposito(anio=None, mes=None):
    """Carpeta de depósitos (Excel resumen) en un mes/año concreto."""
    hoy = datetime.now()
    anio = anio or hoy.year
    mes = mes or hoy.month
    return (
        BASE_DIR / f"Contabilidad {anio}"
        / f"Contabilidad {MESES_ES[mes - 1]}"
        / "Ingreso"
        / "Deposito"
    )


# Archivo de configuración de Gmail (usado por el módulo de Ingresos)
GMAIL_CONFIG_FILE = _CARPETA_DATOS / "gmail_config.json"