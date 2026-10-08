# core/recordatorios/plantillas.py
"""
Plantillas fijas para los recordatorios de citas y vacunas.
Portado de la app Android (BaalakApps).

Las plantillas replican EXACTAMENTE el formato de la app Android.
"""

from core.recordatorios.sucursales import cargar_sucursales
from core.recordatorios.formatear import extraer_nombre_clinica


def plantilla_citas() -> dict:
    """Plantilla fija para recordatorios de citas."""
    return {
        "id": "citas",
        "nombre": "Recordatorios de Citas",
        "descripcion": "Para seguimiento de citas médicas",
        "encabezados": [
            "FECHA", "INICIO", "TIPO VISITA", "PROPIETARIO",
            "MASCOTA", "TELÉFONO", "ASUNTO", "AGENDA", "ESTADO",
        ],
    }


def plantilla_vacunas() -> dict:
    """Plantilla fija para recordatorios de vacunas."""
    return {
        "id": "vacunas",
        "nombre": "Recordatorios de Vacunas",
        "descripcion": "Para seguimiento de vacunación de mascotas",
        "encabezados": [
            "CLIENTE", "TELÉFONO 1", "MASCOTA",
            "TIPO DE RECORDATORIO", "VACUNA", "PRÓXIMA FECHA",
        ],
    }


def obtener_plantilla(tipo: str) -> dict:
    """Devuelve la plantilla según tipo: 'citas' o 'vacunas'."""
    if tipo == "citas":
        return plantilla_citas()
    if tipo == "vacunas":
        return plantilla_vacunas()
    return {}