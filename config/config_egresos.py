# -*- coding: utf-8 -*-
"""
config/config_egresos.py
Configuración del módulo de Egresos.
"""

import json
import sys
from pathlib import Path


def _carpeta_datos():
    """Carpeta de datos de la app."""
    if getattr(sys, 'frozen', False):
        carpeta = Path.home() / "Documents" / "Contabilidad App"
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    else:
        return Path(__file__).parent.parent


_CARPETA_DATOS = _carpeta_datos()

# Archivos de configuración de egresos
CONFIG_EGRESOS_FILE = _CARPETA_DATOS / "config_egresos.json"
PROVEEDORES_TC_FILE = _CARPETA_DATOS / "proveedores_tc.json"
PROVEEDORES_SUCURSAL_FILE = _CARPETA_DATOS / "proveedores_sucursal.json"
OBSERVACIONES_FILE = _CARPETA_DATOS / "observaciones_egresos.json"


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
CONFIG_EGRESOS_DEFAULT = {
    "rfc_receptor": "",
    "nombre_receptor": "",
    "certificado_cer": "",
    "certificado_key": "",
    "password_fiel": "",
    "ultima_descarga": "",
}


def cargar_config_egresos():
    """Carga la configuración de Egresos."""
    if CONFIG_EGRESOS_FILE.exists():
        try:
            with open(CONFIG_EGRESOS_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in CONFIG_EGRESOS_DEFAULT.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(CONFIG_EGRESOS_DEFAULT)


def guardar_config_egresos(cfg):
    """Guarda la configuración de Egresos."""
    with open(CONFIG_EGRESOS_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ============================================================
# PROVEEDORES CON TC (aunque salgan como PPD)
# ============================================================
def cargar_proveedores_tc():
    """Carga la lista de proveedores que se pagan con TC."""
    if PROVEEDORES_TC_FILE.exists():
        try:
            with open(PROVEEDORES_TC_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def guardar_proveedores_tc(proveedores):
    """Guarda la lista de proveedores TC."""
    with open(PROVEEDORES_TC_FILE, "w", encoding="utf-8") as f:
        json.dump(proveedores, f, ensure_ascii=False, indent=2)


# ============================================================
# PROVEEDORES POR SUCURSAL
# ============================================================
def cargar_proveedores_sucursal():
    """
    Carga la lista de proveedores con sucursal asignada.
    Formato: {RFC: "Animalia" | "Baalak" | "Preguntar"}
    """
    if PROVEEDORES_SUCURSAL_FILE.exists():
        try:
            with open(PROVEEDORES_SUCURSAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def guardar_proveedores_sucursal(proveedores):
    """Guarda la lista de proveedores por sucursal."""
    with open(PROVEEDORES_SUCURSAL_FILE, "w", encoding="utf-8") as f:
        json.dump(proveedores, f, ensure_ascii=False, indent=2)


# ============================================================
# MAPEO DE OBSERVACIONES (palabras clave)
# ============================================================
OBSERVACIONES_DEFAULT = {
    "GASOLINA": ["gasolina", "combustible", "pemex", "gas"],
    "INTERNET": ["internet", "telmex", "megacable", "izzi"],
    "CELULAR": ["celular", "telcel", "movistar", "at&t"],
    "ESCUELA": ["escuela", "colegiatura", "educación"],
    "MEMBRESIA": ["membresía", "membresia", "suscripción", "amazon"],
    "GASTOS EN GENERAL": [
        "papelería", "limpieza", "ferretería",
        "medicamento", "alimento", "material",
    ],
    "TRANSPORTE": ["transporte", "ado", "pasaje", "vuelo"],
    "HONORARIOS": ["honorarios", "consultoría", "asesoría"],
}


def cargar_observaciones():
    """Carga el mapeo de observaciones (palabras clave)."""
    if OBSERVACIONES_FILE.exists():
        try:
            with open(OBSERVACIONES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(OBSERVACIONES_DEFAULT)


def guardar_observaciones(obs):
    """Guarda el mapeo de observaciones."""
    with open(OBSERVACIONES_FILE, "w", encoding="utf-8") as f:
        json.dump(obs, f, ensure_ascii=False, indent=2)



# ============================================================
# SOLICITUDES SAT PENDIENTES
# ============================================================
SOLICITUD_ACTIVA_FILE = _CARPETA_DATOS / "solicitud_sat_activa.json"


def cargar_solicitud_activa():
    """
    Carga la solicitud activa (si hay una en curso).

    Devuelve un dict:
      {
        "id_solicitud": "...",
        "rfc": "...",
        "anio": 2026,
        "mes_idx": 9,
        "mes_nombre": "septiembre",
        "fecha_solicitud": "2026-10-02T14:30:00",
      }
    O None si no hay.
    """
    if not SOLICITUD_ACTIVA_FILE.exists():
        return None
    try:
        with open(SOLICITUD_ACTIVA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def guardar_solicitud_activa(datos):
    """Guarda la solicitud activa."""
    with open(SOLICITUD_ACTIVA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def limpiar_solicitud_activa():
    """Elimina el archivo de solicitud activa."""
    try:
        if SOLICITUD_ACTIVA_FILE.exists():
            SOLICITUD_ACTIVA_FILE.unlink()
    except Exception:
        pass


def horas_desde_solicitud(datos):
    """Devuelve cuántas horas han pasado desde que se creó la solicitud."""
    from datetime import datetime
    if not datos:
        return None
    try:
        fecha = datetime.fromisoformat(datos.get("fecha_solicitud", ""))
        delta = datetime.now() - fecha
        return delta.total_seconds() / 3600
    except Exception:
        return None