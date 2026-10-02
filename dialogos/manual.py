# -*- coding: utf-8 -*-
"""
dialogos/manual.py
Visor del manual de usuario integrado en la app.
"""

import tkinter as tk
import ttkbootstrap as ttk
from pathlib import Path


def abrir_manual(app):
    from ui.utils import configurar_ventana
    from tkinter import messagebox

    raiz = Path(__file__).parent.parent
    ruta_manual = raiz / "MANUAL.md"

    if not ruta_manual.exists():
        messagebox.showwarning(
            "Manual no encontrado",
            "No se encontro MANUAL.md en la raiz del proyecto."
        )
        return

    try:
        with open(ruta_manual, "r", encoding="utf-8") as f:
            contenido = f.read()
    except Exception as e:
        messagebox.showerror(
            "Error",
            "No se pudo leer MANUAL.md: " + str(e)
        )
        return

    ventana = ttk.Toplevel(app)
    ventana.title("Manual de Usuario")
    configurar_ventana(app, ventana, ancho=900, alto=700,
                       min_ancho=700, min_alto=500)

    header = ttk.Frame(ventana, padding=10)
    header.pack(fill="x")
    ttk.Label(
        header,
        text="Manual de Usuario",
        font=("Segoe UI", 16, "bold"),
    ).pack(side="left")

    def _abrir_externo():
        import sys
        import os
        if sys.platform.startswith("win"):
            os.startfile(str(ruta_manual))
        elif sys.platform == "darwin":
            os.system('open "' + str(ruta_manual) + '"')
        else:
            os.system('xdg-open "' + str(ruta_manual) + '"')

    ttk.Button(
        header,
        text="Abrir en editor externo",
        command=_abrir_externo,
        bootstyle="secondary-outline",
    ).pack(side="right", padx=5)

    contenedor = ttk.Frame(ventana)
    contenedor.pack(fill="both", expand=True, padx=10, pady=5)

    canvas = tk.Canvas(contenedor, borderwidth=0, highlightthickness=0)
    scrollbar = ttk.Scrollbar(contenedor, orient="vertical",
                              command=canvas.yview)
    frame_interno = ttk.Frame(canvas)

    frame_interno.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas_window = canvas.create_window((0, 0), window=frame_interno,
                                          anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_canvas_configure(event):
        canvas.itemconfigure(canvas_window, width=event.width)

    canvas.bind("<Configure>", _on_canvas_configure)

    _renderizar(frame_interno, contenido)

    def _on_mousewheel(event):
        try:
            if not canvas.winfo_exists():
                return
            import sys as _sys
            if _sys.platform == "darwin":
                delta = -1 * event.delta
            else:
                delta = -1 * (event.delta // 120)
            canvas.yview_scroll(int(delta), "units")
        except Exception:
            pass

    canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
    ventana.bind("<Escape>", lambda e: ventana.destroy())
    canvas.yview_moveto(0)


def _limpiar(texto):
    """Quita ** y backticks del texto."""
    texto = texto.replace("**", "")
    texto = texto.replace("`", "")
    return texto


def _renderizar(parent, texto):
    """Renderiza el markdown con estilos basicos."""
    for linea in texto.split("\n"):
        s = linea.strip()

        if s == "---":
            ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
            continue

        if s.startswith("### "):
            ttk.Label(
                parent,
                text=s[4:].strip(),
                font=("Segoe UI", 12, "bold"),
                bootstyle="info",
            ).pack(anchor="w", pady=(12, 4), padx=5)
            continue

        if s.startswith("## "):
            ttk.Label(
                parent,
                text=s[3:].strip(),
                font=("Segoe UI", 14, "bold"),
            ).pack(anchor="w", pady=(16, 6), padx=5)
            continue

        if s.startswith("# "):
            ttk.Label(
                parent,
                text=s[2:].strip(),
                font=("Segoe UI", 18, "bold"),
                bootstyle="info",
            ).pack(anchor="w", pady=(20, 10), padx=5)
            continue

        if s.startswith("- ") or s.startswith("* "):
            txt = _limpiar(s[2:].strip())
            ttk.Label(
                parent,
                text="   -  " + txt,
                font=("Segoe UI", 10),
                wraplength=820,
                justify="left",
            ).pack(anchor="w", padx=20, pady=2)
            continue

        if not s:
            ttk.Label(parent, text="", font=("Segoe UI", 4)).pack()
            continue

        if s.startswith("```"):
            continue

        if s.startswith("|"):
            txt = _limpiar(s.replace("|", "  ").strip())
            if txt and not txt.startswith("---"):
                ttk.Label(
                    parent,
                    text=txt,
                    font=("Consolas", 9),
                    wraplength=820,
                    justify="left",
                ).pack(anchor="w", padx=20, pady=1)
            continue

        txt = _limpiar(s)
        if txt:
            ttk.Label(
                parent,
                text=txt,
                font=("Segoe UI", 10),
                wraplength=820,
                justify="left",
            ).pack(anchor="w", pady=2, padx=5)