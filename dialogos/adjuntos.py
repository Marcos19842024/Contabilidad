# -*- coding: utf-8 -*-
"""
dialogos/adjuntos.py
Dialogo para ver los datos de la factura y sus adjuntos.
Permite abrir los archivos y eliminar el registro completo.
"""

import sys
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox
from pathlib import Path

from core.adjuntos import (
    archivos_del_registro,
    carpeta_de_registro,
    eliminar_archivos_de_registro,
    eliminar_carpeta_si_vacia,
)


def abrir_dialogo_adjuntos(app, reg):
    """
    Muestra una ventana con los datos del registro y sus adjuntos.

    Parametros:
      app: instancia de AppIngresos.
      reg: el registro (dict) cuyos adjuntos se quieren ver.

    Devuelve True si el registro fue eliminado, False si solo se cerro.
    """
    from ui.utils import configurar_ventana

    ventana = ttk.Toplevel(app)
    no_factura = reg.get("no_factura", "?")
    ventana.title(f"Factura {no_factura}")
    configurar_ventana(app, ventana, ancho=400, alto=440,
                       min_ancho=350, min_alto=250)

    # ---- Encabezado ----
    ttk.Label(
        ventana,
        text=f"Factura {no_factura}",
        font=("Segoe UI", 15, "bold"),
    ).pack(pady=(15, 10))

    # ==================================================
    # DATOS DE LA FACTURA
    # ==================================================
    frame_datos = ttk.LabelFrame(ventana, text="Datos de la factura", padding=10)
    frame_datos.pack(fill="x", padx=15, pady=5)

    campos_mostrar = [
        ("Fecha", reg.get("fecha", "")),
        ("No. Factura", reg.get("no_factura", "")),
        ("QVET", reg.get("qvet", "")),
        ("Centro", reg.get("centro", "")),
        ("Nombre", reg.get("nombre", "")),
        ("RFC", reg.get("rfc", "")),
        ("Folio Fiscal", reg.get("folio_fiscal", "")),
        ("Total", f"${reg.get('total', 0):,.2f}"),
    ]

    for i, (lbl, valor) in enumerate(campos_mostrar):
        ttk.Label(
            frame_datos, text=f"{lbl}:",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=i, column=0, sticky="e", padx=(0, 8), pady=2)

        # Truncar textos muy largos
        v = str(valor)
        if len(v) > 55:
            v = v[:52] + "..."
        ttk.Label(
            frame_datos, text=v,
            font=("Segoe UI", 9),
        ).grid(row=i, column=1, sticky="w", pady=2)

    # ==================================================
    # ARCHIVOS ADJUNTOS
    # ==================================================
    adjuntos = archivos_del_registro(reg)

    frame_adj = ttk.LabelFrame(ventana, text="Archivos adjuntos", padding=10)
    frame_adj.pack(fill="x", padx=15, pady=10)

    if not adjuntos:
        ttk.Label(
            frame_adj,
            text="No hay archivos adjuntos.",
            font=("Segoe UI", 10),
            foreground="gray",
        ).pack(pady=10)
    else:
        # Un botón por archivo
        for a in adjuntos:
            icono = "📄"
            nombre = a.name.lower()
            if nombre.endswith(".pdf"):
                icono = "📄"
            elif nombre.endswith(".xml"):
                icono = "📋"

            ttk.Button(
                frame_adj,
                text=f"{icono}  {a.name}",
                command=lambda r=a: _abrir_archivo(r),
                bootstyle="secondary-outline",
                width=50,
            ).pack(fill="x", pady=3)

    # ==================================================
    # BOTONES
    # ==================================================
    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(fill="x", padx=15, pady=(5, 15))

    resultado = {"eliminado": False}

    def _eliminar():
        # Confirmar
        archivos_txt = ""
        if adjuntos:
            archivos_txt = (
                f"\n\nSe eliminaran {len(adjuntos)} archivo(s):\n"
                + "\n".join(f"   - {a.name}" for a in adjuntos[:5])
            )
            if len(adjuntos) > 5:
                archivos_txt += f"\n   ... y {len(adjuntos) - 5} mas"

        msg = (
            f"Eliminar el registro de la factura {no_factura}?"
            f"{archivos_txt}\n\n"
            "Esta accion no se puede deshacer."
        )

        if not messagebox.askyesno("Confirmar eliminacion", msg, parent=ventana):
            return

        # Eliminar archivos
        eliminados, errores = eliminar_archivos_de_registro(reg)

        # Eliminar carpeta si queda vacia
        try:
            carpeta = carpeta_de_registro(reg)
            if carpeta and carpeta.exists():
                eliminar_carpeta_si_vacia(reg)
        except Exception:
            pass

        # Marcar resultado
        resultado["eliminado"] = True

        # Mostrar resumen
        partes = ["Registro eliminado."]
        if eliminados:
            partes.append(f"\nArchivos eliminados: {len(eliminados)}")
        if errores:
            partes.append(f"\nErrores: {len(errores)}")
            for a, e in errores[:3]:
                partes.append(f"  - {a.name}: {e}")

        messagebox.showinfo("Eliminado", "\n".join(partes), parent=ventana)
        ventana.destroy()

    ttk.Button(
        fr_btn, text="Eliminar registro",
        command=_eliminar,
        bootstyle="danger-outline",
    ).pack(side="right", padx=5)

    def _cerrar():
        ventana.destroy()

    ventana.protocol("WM_DELETE_WINDOW", _cerrar)
    ventana.bind("<Escape>", lambda e: _cerrar())

    ventana.wait_window()
    return resultado["eliminado"]


def _abrir_archivo(ruta):
    """Abre un archivo con el visor por defecto del sistema."""
    try:
        ruta = str(ruta)
        if sys.platform.startswith("win"):
            import os
            os.startfile(ruta)
        elif sys.platform == "darwin":
            import os
            os.system(f'open "{ruta}"')
        else:
            import os
            os.system(f'xdg-open "{ruta}"')
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")