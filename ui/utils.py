# -*- coding: utf-8 -*-
"""
ui/utils.py
Funciones compartidas para configurar ventanas y diálogos.
"""

import tkinter as tk

def configurar_ventana(padre, ventana, ancho=500, alto=400,
                       min_ancho=400, min_alto=320,
                       centrar_en_padre=True):
    """
    Configura tamaño, minsize y centrado de un Toplevel.
    Adapta el tamaño si la pantalla es más pequeña.
    """
    # Liberar cualquier grab previo
    try:
        padre.grab_release()
    except Exception:
        pass

    # Adaptar tamaño a la pantalla
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()

    # Dejar margen de 100px
    ancho_max = pantalla_ancho - 100
    alto_max = pantalla_alto - 100

    ancho = min(ancho, ancho_max)
    alto = min(alto, alto_max)
    min_ancho = min(min_ancho, ancho)
    min_alto = min(min_alto, alto)

    ventana.geometry(f"{ancho}x{alto}")
    ventana.minsize(min_ancho, min_alto)
    ventana.transient(padre)
    ventana.grab_set()
    ventana.update_idletasks()

    if centrar_en_padre:
        x = padre.winfo_rootx() + (padre.winfo_width() - ancho) // 2
        y = padre.winfo_rooty() + (padre.winfo_height() - alto) // 2
        x = max(0, x)
        y = max(0, y)
        ventana.geometry(f"+{x}+{y}")


def centrar_ventana(ventana, ancho=None, alto=None):
    """
    Centra una ventana en la pantalla.
    Si no se especifica ancho/alto, usa el tamaño actual.
    """
    ventana.update_idletasks()
    if ancho is None:
        ancho = ventana.winfo_width()
    if alto is None:
        alto = ventana.winfo_height()
    x = (ventana.winfo_screenwidth() - ancho) // 2
    y = (ventana.winfo_screenheight() - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")