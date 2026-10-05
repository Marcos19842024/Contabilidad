# -*- coding: utf-8 -*-
"""
dialogos/config_general.py
Diálogo de configuración general de la aplicación.
Aquí se agrupan las opciones que afectan a toda la app
(tema visual, y las que se agreguen a futuro).
"""

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox


def abrir_dialogo_config_general(app):
    """
    Abre el diálogo de configuración general.

    Parámetros:
      app: instancia de AppPrincipal.
    """
    from ui.utils import configurar_ventana
    from config.ajustes import obtener_tema_actual

    ventana = ttk.Toplevel(app)
    ventana.title("⚙️ Configuración")
    configurar_ventana(app, ventana, ancho=520, alto=420,
                       min_ancho=460, min_alto=360)

    # ---- Encabezado ----
    ttk.Label(
        ventana,
        text="⚙️ Configuración general",
        font=("Segoe UI", 16, "bold"),
    ).pack(pady=(20, 5))

    ttk.Label(
        ventana,
        text="Opciones que afectan a toda la aplicación.",
        font=("Segoe UI", 9),
        foreground="gray",
    ).pack(pady=(0, 20))

    # ============================================================
    # SECCIÓN: APARIENCIA
    # ============================================================
    frame_apariencia = ttk.LabelFrame(ventana, text="🎨 Apariencia",
                                       padding=15)
    frame_apariencia.pack(fill="x", padx=20, pady=5)

    tema_actual = obtener_tema_actual()

    # Fila: Tema
    fila = ttk.Frame(frame_apariencia)
    fila.pack(fill="x", pady=5)

    ttk.Label(
        fila,
        text="Tema visual:",
        font=("Segoe UI", 10, "bold"),
        width=15,
        anchor="w",
    ).pack(side="left")

    lbl_tema = ttk.Label(
        fila,
        text=tema_actual,
        font=("Segoe UI", 10),
        foreground="gray",
    )
    lbl_tema.pack(side="left", padx=(5, 15))

    def _cambiar_tema():
        from dialogos.temas import abrir_dialogo_temas
        abrir_dialogo_temas(ventana)
        # Al cerrar el diálogo de temas, actualizar el label
        try:
            nuevo = obtener_tema_actual()
            lbl_tema.configure(text=nuevo)
        except Exception:
            pass

    ttk.Button(
        fila,
        text="Cambiar tema",
        command=_cambiar_tema,
        bootstyle="info-outline",
    ).pack(side="right")

    ttk.Label(
        frame_apariencia,
        text="El tema afecta a todos los módulos (Ingresos y Egresos).",
        font=("Segoe UI", 8),
        foreground="gray",
    ).pack(anchor="w", pady=(5, 0))

    # ============================================================
    # SECCIÓN: (para futuras opciones)
    # ============================================================
    frame_futuro = ttk.LabelFrame(ventana, text="📋 Más opciones",
                                   padding=15)
    frame_futuro.pack(fill="both", expand=True, padx=20, pady=15)

    ttk.Label(
        frame_futuro,
        text="Aquí se agregarán más opciones de configuración\n"
             "en futuras versiones.",
        font=("Segoe UI", 9),
        foreground="gray",
        justify="center",
    ).pack(pady=20)

    ventana.protocol("WM_DELETE_WINDOW", ventana.destroy)
    ventana.bind("<Escape>", lambda e: ventana.destroy())