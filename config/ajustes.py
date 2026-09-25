# -*- coding: utf-8 -*-
"""
config/ajustes.py
Configuración persistente de la app (tema visual, credenciales de Gmail).
Se guarda en ~/Documents/Contabilidad App/config_ui.json
"""

import json
import sys
from pathlib import Path


def _carpeta_datos():
    """
    Carpeta única de datos de la app.
    Compartida entre años y entre ejecutable/desarrollo.
    """
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Contabilidad App"
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    else:
        return Path(__file__).parent.parent


_CARPETA_DATOS = _carpeta_datos()

CONFIG_FILE = _CARPETA_DATOS / "config_ui.json"

CONFIG_DEFAULT = {"tema": "darkly"}


def cargar_config():
    """Carga config_ui.json o devuelve los valores por defecto."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in CONFIG_DEFAULT.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(CONFIG_DEFAULT)


def guardar_config(cfg):
    """Guarda la configuración en config_ui.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# Configuración global cargada al importar
CONFIG = cargar_config()
TEMA = CONFIG.get("tema", CONFIG_DEFAULT["tema"])