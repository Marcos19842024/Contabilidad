# core/geocoding.py
"""
Geocodificación con Nominatim (OpenStreetMap).

Mejoras:
- Caché persistente en disco (evita repetir peticiones).
- Limpieza de direcciones ruidosas (típicas de México).
- 3 intentos con distintas variantes.
- Rate limit: 1 petición por segundo (política de Nominatim).
"""

import time
import json
import urllib.parse
import urllib.request
from pathlib import Path

from core.rutas_estetica import CARPETA_DATOS


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "VetSuite/2.1 (contacto@vetsuite.app)"
CACHE_FILE = CARPETA_DATOS / "geocoding_cache.json"

CIUDAD_DEFECTO = "San Francisco de Campeche"
ESTADO_DEFECTO = "Campeche"
PAIS_DEFECTO = "México"

# Rate limit
_ultima_llamada = 0.0
_cache = None


# ---------------------------------------------------------------
# Caché
# ---------------------------------------------------------------

def _cargar_cache() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}
    else:
        _cache = {}
    return _cache


def _guardar_cache():
    if _cache is None:
        return
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[geocoding] No se pudo guardar caché: {e}")


def _clave(direccion: str, poblacion: str = "") -> str:
    return f"{direccion.strip().lower()}|{poblacion.strip().lower()}"


# ---------------------------------------------------------------
# Rate limit
# ---------------------------------------------------------------

def _esperar_turno():
    global _ultima_llamada
    ahora = time.time()
    delta = ahora - _ultima_llamada
    if delta < 1.05:
        time.sleep(1.05 - delta)
    _ultima_llamada = time.time()


# ---------------------------------------------------------------
# Limpieza de direcciones
# ---------------------------------------------------------------

def _limpiar_direccion(direccion: str) -> str:
    """
    Quita ruido típico de direcciones mexicanas:
    - '/' con referencias ('/ AGUA Y NIEBLA FRAC 2000')
    - 'ENTRE', 'JUNTO A', 'AL LADO DE', 'REFERENCIA'
    - El numeral '#' se convierte en 'num' para que Nominatim lo entienda
    """
    if not direccion:
        return ""
    d = direccion.strip()

    # Cortar por separadores de referencia
    for sep in ["/", " ENTRE ", " JUNTO A ", " AL LADO DE ", " REFERENCIA "]:
        if sep in d.upper():
            d = d.upper().split(sep)[0].strip()

    # '#' → 'num' (Nominatim entiende mejor "num 123" que "#123")
    d = d.replace("#", " num ")

    # Quitar espacios dobles
    while "  " in d:
        d = d.replace("  ", " ")

    return d.strip(" ,.-")


# ---------------------------------------------------------------
# Petición a Nominatim
# ---------------------------------------------------------------

def _consultar(query: str):
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
        "countrycodes": "mx",
    }
    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"

    try:
        _esperar_turno()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[geocoding] Error de red: {e}")
        return None

    if not data:
        return None

    primer = data[0]
    try:
        importance = float(primer.get("importance", 0))
    except (TypeError, ValueError):
        importance = 0.0

    # Bajamos el umbral de 0.4 a 0.3 porque muchas direcciones
    # mexicanas quedan en 0.35 aunque sean correctas
    if importance < 0.30:
        return None

    try:
        return float(primer["lat"]), float(primer["lon"])
    except (KeyError, TypeError, ValueError):
        return None


# ---------------------------------------------------------------
# API pública
# ---------------------------------------------------------------

def geocodificar(direccion: str, poblacion: str = "",
                 forzar: bool = False):
    """
    Devuelve (lat, lng) o None.

    - Usa caché en disco (clave = dirección + población).
    - Limpia la dirección antes de buscar.
    - 3 intentos:
        1. dirección limpia + población + ciudad + estado + país
        2. dirección original + población + ciudad + estado + país
        3. dirección original + ciudad + estado + país
    """
    if not direccion or not direccion.strip():
        return None

    cache = _cargar_cache()
    k = _clave(direccion, poblacion)

    if not forzar and k in cache:
        entry = cache[k]
        if entry.get("lat") is not None:
            return entry["lat"], entry["lng"]
        return None  # fallo cacheado

    limpiada = _limpiar_direccion(direccion)

    intentos = [
        ", ".join(p for p in [limpiada, poblacion, CIUDAD_DEFECTO,
                              ESTADO_DEFECTO, PAIS_DEFECTO] if p),
        ", ".join(p for p in [direccion, poblacion, CIUDAD_DEFECTO,
                              ESTADO_DEFECTO, PAIS_DEFECTO] if p),
        ", ".join(p for p in [direccion, CIUDAD_DEFECTO,
                              ESTADO_DEFECTO, PAIS_DEFECTO] if p),
    ]

    resultado = None
    for q in intentos:
        resultado = _consultar(q)
        if resultado:
            break

    if resultado:
        cache[k] = {"lat": resultado[0], "lng": resultado[1],
                    "query": intentos[0]}
    else:
        cache[k] = {"lat": None, "lng": None}

    _guardar_cache()
    return resultado


def geocodificar_lote(direcciones: list, on_progress=None):
    """
    Geocodifica una lista de (direccion, poblacion).
    Llama a on_progress(i, total) si se pasa.
    Devuelve dict {(direccion, poblacion): (lat, lng) o None}.
    """
    resultados = {}
    total = len(direcciones)
    for i, (dir_, pob) in enumerate(direcciones, 1):
        resultados[(dir_, pob)] = geocodificar(dir_, pob)
        if on_progress:
            on_progress(i, total)
    return resultados