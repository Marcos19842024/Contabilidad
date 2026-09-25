# -*- coding: utf-8 -*-
"""
config/temas.py
Paletas de colores, detección de tema oscuro y colores del sidebar.
"""

from config.ajustes import TEMA


TEMAS_OSCUROS = {
    "bootstrap-dark",
    "pydata-dark",
    "nord-dark",
    "solarized-dark",
    "catppuccin-dark",
    "gruvbox-dark",
    "dracula-dark",
    "tokyo-night-dark",
    "one-dark",
    "everforest-dark",
    "vapor-dark",
    "minty-dark",
    "pulse-dark",
    "united-dark",
    "sandstone-dark",
}


def tema_es_oscuro(tema=None):
    t = tema or TEMA
    return t.lower() in TEMAS_OSCUROS


def _colores_adaptados():
    oscuro = tema_es_oscuro()
    if oscuro:
        return {
            "texto_normal":    "#ffffff",
            "texto_operacion": "#00ff00",
            "fondo_entry":     "#2b2b2b",
            "campo_ok":        "#1b5e20",
            "campo_error":     "#7f1d1d",
            "campo_normal":    "#2b2b2b",
        }
    else:
        return {
            "texto_normal":    "#000000",
            "texto_operacion": "#007700",
            "fondo_entry":     "#ffffff",
            "campo_ok":        "#c8e6c9",
            "campo_error":     "#ffcdd2",
            "campo_normal":    "#ffffff",
        }


# Colores globales (se recalculan con refrescar_colores)
COLORES = _colores_adaptados()


def refrescar_colores():
    """Recalcula COLORES mutando el mismo dict (para que las referencias externas sigan funcionando)."""
    global COLORES
    nuevos = _colores_adaptados()
    COLORES.clear()
    COLORES.update(nuevos)
    return COLORES


def obtener_colores_sidebar():
    """
    Devuelve un diccionario con los colores del sidebar según el tema actual.
    """
    oscuro = tema_es_oscuro()
    if oscuro:
        return {
            "bg":        "#1e2a38",
            "hover":     "#2c3e50",
            "active":    "#3498db",
            "fg":        "#ffffff",
            "fg_suave":  "#cfd8dc",
            "separador": "#34495e",
            "version":   "#607d8b",
        }
    else:
        return {
            "bg":        "#ffffff",
            "hover":     "#e3f2fd",
            "active":    "#1976d2",
            "fg":        "#000000",
            "fg_suave":  "#546e7a",
            "separador": "#e0e0e0",
            "version":   "#90a4ae",
        }