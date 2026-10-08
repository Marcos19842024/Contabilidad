# core/geocoding.py
"""
Geocodificación con Nominatim (OpenStreetMap).

Reglas:
- Solo devuelve resultado si coincide con precisión razonable.
- Si no hay coincidencia exacta, devuelve None (se omite).
"""

import time
import json
import urllib.parse
import urllib.request


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "QVET-Contabilidad/1.0 (contacto@qvet.local)"

# Para no saturar el servicio (máx 1 req/seg)
_ultima_llamada = 0.0


def _esperar_turno():
    global _ultima_llamada
    ahora = time.time()
    delta = ahora - _ultima_llamada
    if delta < 1.05:
        time.sleep(1.05 - delta)
    _ultima_llamada = time.time()


def geocodificar(direccion: str, poblacion: str = "",
                 ciudad: str = "Campeche",
                 estado: str = "Campeche",
                 pais: str = "México"):
    """
    Devuelve (lat, lng) si encuentra una coincidencia clara.
    Devuelve None si no encuentra nada o si la coincidencia es ambigua.

    Estrategia:
    - Junta dirección + población + ciudad + estado + país
    - Pide a Nominatim con format=jsonv2, limit=1, addressdetails=1
    - Si el resultado tiene importance >= 0.4, lo acepta
    - Si no, devuelve None
    """
    if not direccion:
        return None

    partes = [direccion]
    if poblacion:
        partes.append(poblacion)
    partes.extend([ciudad, estado, pais])
    query = ", ".join(p.strip() for p in partes if p and p.strip())

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
        print(f"[geocoding] Error: {e}")
        return None

    if not data:
        return None

    primer = data[0]
    try:
        importance = float(primer.get("importance", 0))
    except (TypeError, ValueError):
        importance = 0.0

    # Solo aceptamos si Nominatim considera que es buena coincidencia
    if importance < 0.4:
        print(f"[geocoding] Coincidencia débil ({importance}) para: {query}")
        return None

    try:
        lat = float(primer["lat"])
        lng = float(primer["lon"])
    except (KeyError, TypeError, ValueError):
        return None

    return lat, lng