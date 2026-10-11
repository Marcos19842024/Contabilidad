# -*- coding: utf-8 -*-
"""
config/veterinaria.py
Datos de la veterinaria y sus sucursales.
Persiste en config_ui.json → clave "veterinaria".

Fuente de verdad COMPARTIDA por los 4 módulos:
  - Ingresos        → nombre del negocio en reportes
  - Egresos         → sucursal activa para clasificar proveedores
  - Estética        → origen de rutas (Haversine)
  - Recordatorios   → emisor en los mensajes de WhatsApp
"""

from core import config_ui


SUCURSALES_DEFAULT = [
    {
        "id": "BAALAK_CENTRAL",
        "nombre": "Clínica Veterinaria Baalak (Central)",
        "nombre_corto": "Baalak",
        "direccion": "",
        "telefono": "",
        "activa": True,
        "coordenadas": {"lat": 19.831218, "lng": -90.534602},
    },
    {
        "id": "BAALAK_PRADO",
        "nombre": "Clínica Veterinaria Baalak (Prado)",
        "nombre_corto": "Prado",
        "direccion": "",
        "telefono": "",
        "activa": True,
        "coordenadas": {"lat": 19.832604, "lng": -90.551841},
    },
    {
        "id": "ANIMALIA",
        "nombre": "Clínica Veterinaria Animalia",
        "nombre_corto": "Animalia",
        "direccion": "",
        "telefono": "",
        "activa": True,
        "coordenadas": {"lat": 18.143160, "lng": -94.454624},
    },
]

VETERINARIA_DEFAULT = {
    "nombre": "Vet Suite",
    "sucursal_activa": "BAALAK_CENTRAL",
    "sucursales": SUCURSALES_DEFAULT,
}


# ---------------------------------------------------------------
# API pública
# ---------------------------------------------------------------

def obtener_veterinaria() -> dict:
    vet = config_ui.get_seccion("veterinaria") or {}
    # Merge con defaults sin pisar lo existente
    vet.setdefault("nombre", VETERINARIA_DEFAULT["nombre"])
    vet.setdefault("sucursal_activa", VETERINARIA_DEFAULT["sucursal_activa"])
    vet.setdefault("sucursales", [dict(s) for s in SUCURSALES_DEFAULT])
    return vet


def guardar_veterinaria(data: dict):
    config_ui.set_seccion("veterinaria", data)


def sucursales() -> list:
    return obtener_veterinaria().get("sucursales", [])


def sucursales_activas() -> list:
    return [s for s in sucursales() if s.get("activa", True)]


def obtener_sucursal(sucursal_id: str) -> dict:
    for s in sucursales():
        if s.get("id") == sucursal_id:
            return s
    return sucursal_activa()


def sucursal_activa() -> dict:
    vet = obtener_veterinaria()
    activa_id = vet.get("sucursal_activa", "")
    for s in vet.get("sucursales", []):
        if s.get("id") == activa_id:
            return s
    sucs = vet.get("sucursales", [])
    return sucs[0] if sucs else {}


def nombre_clinica_activa() -> str:
    return sucursal_activa().get("nombre", "")


def nombre_corto_activo() -> str:
    return sucursal_activa().get("nombre_corto", "")


def cambiar_sucursal_activa(sucursal_id: str):
    vet = obtener_veterinaria()
    vet["sucursal_activa"] = sucursal_id
    guardar_veterinaria(vet)


# ---------------------------------------------------------------
# Migración: recordatorios/sucursales.json → config_ui.json
# ---------------------------------------------------------------

def _migrar_sucursales_si_necesario():
    """
    Si existe recordatorios/sucursales.json y config_ui.json aún no
    tiene sucursales migradas, las copia.
    Renombra el viejo a .bak para no volver a migrar.
    """
    try:
        from core.rutas_recordatorios import CARPETA_DATOS as C_REC
    except Exception:
        return

    archivo_viejo = C_REC / "sucursales.json"
    if not archivo_viejo.exists():
        return

    # Si ya hay sucursales en config, no migrar
    cfg_vet = config_ui.get_seccion("veterinaria") or {}
    if cfg_vet.get("sucursales"):
        try:
            archivo_viejo.rename(archivo_viejo.with_suffix(".json.bak"))
        except Exception:
            pass
        return

    try:
        import json as _json
        with open(archivo_viejo, "r", encoding="utf-8") as f:
            data_viejo = _json.load(f)
    except Exception:
        return

    sucs_viejas = data_viejo.get("sucursales", [])
    if not sucs_viejas:
        return

    for s in sucs_viejas:
        s.setdefault("direccion", "")
        s.setdefault("telefono", "")
        s.setdefault("activa", True)

    vet = dict(VETERINARIA_DEFAULT)
    vet["sucursales"] = sucs_viejas
    if data_viejo.get("sucursal_activa"):
        vet["sucursal_activa"] = data_viejo["sucursal_activa"]

    guardar_veterinaria(vet)

    try:
        archivo_viejo.rename(archivo_viejo.with_suffix(".json.bak"))
        print(f"✅ Sucursales migradas a {config_ui.CONFIG_UI_FILE}")
        print(f"   Backup: {archivo_viejo}.bak")
    except Exception:
        pass


_migrar_sucursales_si_necesario()