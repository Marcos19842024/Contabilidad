# -*- coding: utf-8 -*-
"""
config/temas.py
Tema visual global. Persiste en config_ui.json → clave "tema".

También expone utilidades de colores según tema claro/oscuro.
"""

from core import config_ui


TEMA_DEFAULT = "darkly"


# ---------------------------------------------------------------
# API pública del tema
# ---------------------------------------------------------------

def obtener_tema() -> str:
    return config_ui.get_seccion("tema", TEMA_DEFAULT) or TEMA_DEFAULT


def guardar_tema(tema: str):
    config_ui.set_seccion("tema", tema)


# ---------------------------------------------------------------
# Colores según tema oscuro/claro
# ---------------------------------------------------------------

TEMAS_OSCUROS = {
    "bootstrap-dark", "pydata-dark", "nord-dark", "solarized-dark",
    "catppuccin-dark", "gruvbox-dark", "dracula-dark", "tokyo-night-dark",
    "one-dark", "everforest-dark", "vapor-dark", "minty-dark",
    "pulse-dark", "united-dark", "sandstone-dark", "darkly", "cyborg",
    "superhero", "solar", "vapor",
}


def tema_es_oscuro(tema=None):
    # FIX: antes usaba TEMA global (no definido al importar) → NameError
    t = tema or obtener_tema()
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
    return {
        "texto_normal":    "#000000",
        "texto_operacion": "#007700",
        "fondo_entry":     "#ffffff",
        "campo_ok":        "#c8e6c9",
        "campo_error":     "#ffcdd2",
        "campo_normal":    "#ffffff",
    }


# COLORES como dict mutable compartido (mismo objeto en todos los imports)
COLORES = _colores_adaptados()


def refrescar_colores():
    COLORES.clear()
    COLORES.update(_colores_adaptados())
    return COLORES


def obtener_colores_sidebar():
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
    return {
        "bg":        "#ffffff",
        "hover":     "#e3f2fd",
        "active":    "#1976d2",
        "fg":        "#000000",
        "fg_suave":  "#546e7a",
        "separador": "#e0e0e0",
        "version":   "#90a4ae",
    }


# ---------------------------------------------------------------
# Compatibilidad retro: antes existía una constante TEMA global
# ---------------------------------------------------------------
# Si algún archivo viejo hacía `from config.temas import TEMA`,
# lo dejamos funcionar evaluando perezosamente. Mejor aún: revisa
# con un grep si alguien la importa; si nadie, bórrala.
def __getattr__(name):
    if name == "TEMA":
        return obtener_tema()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")