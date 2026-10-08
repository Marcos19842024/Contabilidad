# -*- coding: utf-8 -*-
"""
config/ajustes.py
Configuración persistente global de la app (tema visual).
La configuración específica de Gmail vive en:
  core.rutas.GMAIL_CONFIG_FILE  (ingresos/gmail_config.json)

Migración automática: si config_ui.json todavía tiene una clave "correo",
se copia a ingresos/gmail_config.json y se elimina del archivo global.
"""

import json
import sys
from pathlib import Path

from core.rutas import GMAIL_CONFIG_FILE


def _carpeta_datos():
    """
    Carpeta única de datos globales de la app.
    - Dev:  <raíz proyecto>/
    - Prod: ~/Documents/Vet Suite/
    """
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Vet Suite"
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    else:
        return Path(__file__).parent.parent


_CARPETA_DATOS = _carpeta_datos()

CONFIG_FILE = _CARPETA_DATOS / "config_ui.json"

CONFIG_DEFAULT = {"tema": "darkly"}


# ============================================================
# CONFIGURACIÓN GLOBAL DE LA UI (tema)
# ============================================================
def cargar_config():
    """Carga config_ui.json (solo tema y config global)."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # La clave "correo" ya no pertenece aquí (migración abajo)
            cfg.pop("correo", None)
            for k, v in CONFIG_DEFAULT.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(CONFIG_DEFAULT)


def guardar_config(cfg):
    """Guarda config_ui.json (solo tema)."""
    # Nunca persistir la clave "correo" aquí
    cfg = {k: v for k, v in cfg.items() if k != "correo"}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def obtener_tema_actual():
    """Devuelve el tema actual (siempre actualizado desde el archivo)."""
    cfg = cargar_config()
    return cfg.get("tema", CONFIG_DEFAULT["tema"])


# ============================================================
# CONFIGURACIÓN DE GMAIL (específica de Ingresos)
# ============================================================
GMAIL_CONFIG_DEFAULT = {
    "usuario": "",
    "password_app": "",
    "etiqueta": "Facturas QVET",
    "filtro_remitente": "",
    "dias_atras": 30,
}


def cargar_config_correo():
    """Carga ingresos/gmail_config.json o defaults."""
    if GMAIL_CONFIG_FILE.exists():
        try:
            with open(GMAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in GMAIL_CONFIG_DEFAULT.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(GMAIL_CONFIG_DEFAULT)


def guardar_config_correo(cfg):
    """Guarda ingresos/gmail_config.json."""
    GMAIL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GMAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _migrar_config_correo_si_necesario():
    """
    Si el config_ui.json viejo tenía una clave 'correo',
    la copia a ingresos/gmail_config.json y la elimina del global.
    Solo corre si gmail_config.json aún no existe.
    """
    if GMAIL_CONFIG_FILE.exists():
        return  # ya migrado

    if not CONFIG_FILE.exists():
        return

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg_viejo = json.load(f)
    except Exception:
        return

    correo_viejo = cfg_viejo.get("correo")
    if not correo_viejo:
        return

    # Migrar al nuevo archivo
    try:
        guardar_config_correo(correo_viejo)
        print(f"✅ Config de Gmail migrada a {GMAIL_CONFIG_FILE}")
    except Exception as e:
        print(f"⚠️  No se pudo migrar config de Gmail: {e}")
        return

    # Limpiar el global
    cfg_viejo.pop("correo", None)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg_viejo, f, ensure_ascii=False, indent=2)
        print("✅ config_ui.json limpiado (clave 'correo' eliminada)")
    except Exception:
        pass


# Ejecutar migración al importar (una sola vez)
_migrar_config_correo_si_necesario()


# Configuración global cargada al importar
CONFIG = cargar_config()
TEMA = CONFIG.get("tema", CONFIG_DEFAULT["tema"])