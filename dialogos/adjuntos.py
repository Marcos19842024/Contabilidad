# -*- coding: utf-8 -*-
"""
dialogos/adjuntos.py
Diálogo para ver los adjuntos de un registro.
"""

import sys
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from core.adjuntos import archivos_del_registro, carpeta_de_registro


def abrir_dialogo_adjuntos(app, reg):
    """
    Muestra una ventana con los adjuntos del registro dado.

    Parámetros:
      app: instancia de AppIngresos (para _configurar_ventana, _abrir_archivo,
           _adjuntar_factura)
      reg: el registro (dict) cuyos adjuntos se quieren ver
    """
    adjuntos = archivos_del_registro(reg)

    if not adjuntos:
        if messagebox.askyesno("Sin adjuntos",
                               "No tiene adjuntos. ¿Adjuntar ahora?"):
            app._adjuntar_factura()
        return

    ventana = ttk.Toplevel(app)
    ventana.title(f"Adjuntos de {reg.get('no_factura', '')}")
    app._configurar_ventana(ventana, ancho=340, alto=320,
                            min_ancho=300, min_alto=280)

    ttk.Label(ventana, text=f"Adjuntos de {reg.get('no_factura', '')}:",
              font=("Segoe UI", 11, "bold")).pack(pady=8)

    frame = ttk.Frame(ventana)
    frame.pack(fill="both", expand=True, padx=10, pady=5)

    lb = tk.Listbox(frame, font=("Consolas", 10))
    lb.pack(side="left", fill="both", expand=True)

    sb = ttk.Scrollbar(frame, orient="vertical", command=lb.yview)
    sb.pack(side="right", fill="y")
    lb.configure(yscrollcommand=sb.set)

    for a in adjuntos:
        lb.insert(tk.END, a.name)

    def abrir_archivo():
        sel_lb = lb.curselection()
        if not sel_lb:
            return
        app._abrir_archivo(adjuntos[sel_lb[0]])

    lb.bind("<Double-Button-1>", lambda e: abrir_archivo())

    fr = ttk.Frame(ventana)
    fr.pack(pady=8)

    ttk.Button(fr, text="📎 Adjuntar más",
               command=lambda: (ventana.destroy(), app._adjuntar_factura()),
               bootstyle="info-outline").pack(side="left", padx=4)