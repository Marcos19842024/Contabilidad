# -*- coding: utf-8 -*-
"""
core/rutas_estetica.py
Rutas de datos para el módulo de Estética y Transportes.
"""

import sys
from pathlib import Path


def _carpeta_datos():
    """
    Carpeta de datos de Estética y Transportes (JSON internos).
    - Dev:  <raíz proyecto>/estetica_transportes/
    - Prod: ~/Documents/Vet Suite/estetica_transportes/
    """
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Vet Suite" / "estetica_transportes"
    else:
        carpeta = Path(__file__).parent.parent / "estetica_transportes"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


CARPETA_DATOS = _carpeta_datos()

CLIENTES_MAESTRO    = CARPETA_DATOS / "clientes_maestro.json"
CLIENTES_EDICIONES  = CARPETA_DATOS / "clientes_ediciones.json"
MASCOTAS_FILE       = CARPETA_DATOS / "mascotas.json"
SERVICIOS_ESTETICA  = CARPETA_DATOS / "servicios_estetica.json"
TARIFAS_TRANSPORTE  = CARPETA_DATOS / "tarifas_transporte.json"
TRANSPORTES_CLIENTE = CARPETA_DATOS / "transportes_cliente.json"