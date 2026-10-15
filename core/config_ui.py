# -*- coding: utf-8 -*-
"""
core/config_ui.py
Acceso único a config_ui.json (configuración COMPARTIDA entre los 4 módulos).

Contenido actual:
  - "tema"        → string con el nombre del tema ttkbootstrap
  - "veterinaria" → dict con {nombre, sucursal_activa, sucursales: [...]}

Regla de oro: NADIE fuera de este módulo debe leer/escribir config_ui.json
directamente. Siempre usar leer()/escribir()/get_seccion()/set_seccion().
"""

import json
import sys
import threading
from pathlib import Path


# ---------------------------------------------------------------
# Ruta del archivo (dev vs prod)
# ---------------------------------------------------------------

def _carpeta_datos():
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Vet Suite"
    else:
        carpeta = Path(__file__).parent.parent
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


CONFIG_UI_FILE = _carpeta_datos() / "config_ui.json"

# Lock simple para evitar escrituras concurrentes desde hilos
_LOCK = threading.RLock()


# ---------------------------------------------------------------
# Lectura / escritura atómica
# ---------------------------------------------------------------

def leer() -> dict:
    """
    Devuelve el contenido completo de config_ui.json.
    Si el archivo no existe, lo crea con un esqueleto vacío.
    """
    with _LOCK:
        if not CONFIG_UI_FILE.exists():
            try:
                CONFIG_UI_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(CONFIG_UI_FILE, "w", encoding="utf-8") as f:
                    json.dump({}, f)
            except Exception:
                pass
            return {}
        try:
            with open(CONFIG_UI_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}


def escribir(data: dict):
    """
    Escribe el dict completo en config_ui.json.
    Escritura atómica: escribe a .tmp y renombra (evita corrupción si
    el proceso muere a mitad).
    """
    if not isinstance(data, dict):
        raise TypeError("config_ui.json debe ser un dict en la raíz")
    with _LOCK:
        CONFIG_UI_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_UI_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(CONFIG_UI_FILE)


# ---------------------------------------------------------------
# Acceso por sección (merge no destructivo)
# ---------------------------------------------------------------

def get_seccion(nombre: str, default=None):
    """Devuelve el valor de una sección (clave de primer nivel)."""
    return leer().get(nombre, default)


def set_seccion(nombre: str, valor):
    """
    Actualiza SOLO una sección sin pisar las demás.
    Hace merge si ambas son dicts; si no, reemplaza.
    """
    with _LOCK:
        data = leer()
        actual = data.get(nombre)
        if isinstance(actual, dict) and isinstance(valor, dict):
            actual.update(valor)
            data[nombre] = actual
        else:
            data[nombre] = valor
        escribir(data)


def existe() -> bool:
    return CONFIG_UI_FILE.exists()


# ---------------------------------------------------------------
# Módulos activos (activar/desactivar desde Config General)
# ---------------------------------------------------------------

def modulos_activos() -> dict:
    """
    Devuelve {id_modulo: bool} tal como está guardado en config_ui.json.
    Si la clave no existe o no es dict, devuelve {}.
    El default (módulo nuevo = activo) lo resuelve modulo_esta_activo().
    """
    valor = get_seccion("modulos_activos", {})
    return dict(valor) if isinstance(valor, dict) else {}


def modulo_esta_activo(modulo_id: str, default: bool = True) -> bool:
    """
    True/False para un módulo concreto.
    Si no está en config_ui.json, devuelve `default` (el del registro).
    """
    return bool(modulos_activos().get(modulo_id, default))


def set_modulo_activo(modulo_id: str, activo: bool) -> None:
    """
    Marca/desmarca un módulo. Merge no destructivo (no toca los demás).
    """
    set_seccion("modulos_activos", {modulo_id: bool(activo)})


def resetear():
    """Borra el archivo (útil para tests)."""
    with _LOCK:
        try:
            if CONFIG_UI_FILE.exists():
                CONFIG_UI_FILE.unlink()
        except Exception:
            pass