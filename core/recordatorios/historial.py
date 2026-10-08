# core/recordatorios/historial.py
"""
Historial de envíos de recordatorios.
Guarda qué mensajes ya se enviaron a quién y cuándo.
"""

import json
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path

from core.rutas_recordatorios import CARPETA_DATOS


HISTORIAL_FILE = CARPETA_DATOS / "historial_envios.json"


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _cargar() -> dict:
    """Carga el historial completo."""
    if not HISTORIAL_FILE.exists():
        return {}
    try:
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _guardar(data: dict):
    """Guarda el historial completo."""
    HISTORIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _hash_mensaje(mensaje: str) -> str:
    """SHA1 corto del mensaje para identificar variantes."""
    if not mensaje:
        return ""
    return hashlib.sha1(mensaje.encode("utf-8")).hexdigest()[:12]


def _hoy_iso() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------
# API pública
# ---------------------------------------------------------------

def ya_fue_enviado(telefono: str, tipo: str, mensaje: str) -> dict | None:
    """
    Devuelve el registro del envío si ya se envió hoy ese mismo mensaje.
    tipo: 'citas' o 'vacunas'
    Devuelve None si no se ha enviado.
    """
    data = _cargar()
    hoy = _hoy_iso()
    registro = data.get(hoy, {}).get(telefono, {}).get(tipo)

    if not registro:
        return None

    # Solo cuenta si el hash del mensaje coincide (evita confundir variantes)
    if registro.get("hash") != _hash_mensaje(mensaje):
        return None

    return registro


def marcar_enviado(telefono: str, tipo: str, mensaje: str, nombre: str = ""):
    """Registra un envío en el historial."""
    data = _cargar()
    hoy = _hoy_iso()

    if hoy not in data:
        data[hoy] = {}
    if telefono not in data[hoy]:
        data[hoy][telefono] = {}

    data[hoy][telefono][tipo] = {
        "nombre": nombre,
        "hash": _hash_mensaje(mensaje),
        "fecha_envio": datetime.now().isoformat(timespec="seconds"),
        "mensaje": mensaje[:500],  # guardamos solo un fragmento por tamaño
    }
    _guardar(data)


def desmarcar_enviado(telefono: str, tipo: str):
    """Elimina el registro de envío (si el usuario se equivocó)."""
    data = _cargar()
    hoy = _hoy_iso()
    if hoy in data and telefono in data[hoy]:
        data[hoy][telefono].pop(tipo, None)
        if not data[hoy][telefono]:
            data[hoy].pop(telefono)
        if not data[hoy]:
            data.pop(hoy)
        _guardar(data)


def obtener_envios_de_hoy() -> dict:
    """Devuelve el dict del día de hoy."""
    data = _cargar()
    return data.get(_hoy_iso(), {})


def limpiar_historial_antiguo(dias: int = 90):
    """Elimina registros de más de N días."""
    data = _cargar()
    limite = date.today() - timedelta(days=dias)

    nuevas_fechas = {}
    for fecha_str, registros in data.items():
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except Exception:
            continue
        if fecha >= limite:
            nuevas_fechas[fecha_str] = registros

    _guardar(nuevas_fechas)


def estadisticas() -> dict:
    """Devuelve estadísticas del historial."""
    data = _cargar()
    hoy = _hoy_iso()
    registros_hoy = data.get(hoy, {})

    total = len(registros_hoy)
    citas = sum(1 for r in registros_hoy.values() if "citas" in r)
    vacunas = sum(1 for r in registros_hoy.values() if "vacunas" in r)

    return {
        "total_hoy": total,
        "citas_hoy": citas,
        "vacunas_hoy": vacunas,
    }