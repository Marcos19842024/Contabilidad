## -*- coding: utf-8 -*-
"""
dialogos/registrar_productos.py
Diálogo para registrar productos en el catálogo de excepciones manuales.
Se usa desde el aviso de reclasificación cuando se lee una factura.
"""

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from lector_facturas import agregar_producto_catalogo


CATEGORIAS = ["U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
              "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA"]


def abrir_dialogo_registrar_productos(app, avisos):
    """
    Abre un diálogo para registrar varios productos en el catálogo.
    """
    if not avisos:
        return

    ventana = ttk.Toplevel(app)
    ventana.title("➕ Registrar productos en el catálogo")
    app._configurar_ventana(ventana, ancho=750, alto=550,
                            min_ancho=650, min_alto=450)

    # ---- Encabezado ----
    ttk.Label(ventana,
              text="➕ Registrar productos en el catálogo",
              font=("Segoe UI", 14, "bold")).pack(pady=(15, 5))

    ttk.Label(ventana,
              text="Elige la categoría correcta para cada producto.\n"
                   "Se guardarán en 'categorias_manuales.json' y se aplicarán\n"
                   "automáticamente la próxima vez que leas una factura.",
              font=("Segoe UI", 9),
              foreground="gray",
              justify="center").pack(pady=(0, 15))

    # ---- Contenedor con scroll ----
    contenedor = ttk.Frame(ventana)
    contenedor.pack(fill="both", expand=True, padx=15, pady=5)

    canvas = tk.Canvas(contenedor, borderwidth=0, highlightthickness=0)
    scroll_v = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
    frame_interno = ttk.Frame(canvas)

    frame_interno.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas_window = canvas.create_window((0, 0), window=frame_interno, anchor="nw")
    canvas.configure(yscrollcommand=scroll_v.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll_v.pack(side="right", fill="y")

    def _on_canvas_configure(event):
        canvas.itemconfigure(canvas_window, width=event.width)
    canvas.bind("<Configure>", _on_canvas_configure)

    # ---- Encabezados de la tabla ----
    enc = ttk.Frame(frame_interno)
    enc.pack(fill="x", pady=(0, 5))

    ttk.Label(enc, text="PRODUCTO",
              font=("Segoe UI", 10, "bold"), width=45, anchor="w").pack(side="left", padx=5)
    ttk.Label(enc, text="CATEGORÍA ACTUAL",
              font=("Segoe UI", 10, "bold"), width=20, anchor="center").pack(side="left", padx=5)
    ttk.Label(enc, text="NUEVA CATEGORÍA",
              font=("Segoe UI", 10, "bold"), width=20, anchor="center").pack(side="left", padx=5)

    # ---- Filas ----
    vars_categorias = []  # Lista de (nombre, StringVar)

    for aviso in avisos:
        producto = aviso.get("producto", "?")
        categoria_actual = aviso.get("categoria_actual", "?")

        fila = ttk.Frame(frame_interno)
        fila.pack(fill="x", pady=2)

        ttk.Label(fila, text=producto, width=45, anchor="w").pack(side="left", padx=5)
        ttk.Label(fila, text=categoria_actual, width=20,
                  anchor="center", foreground="gray").pack(side="left", padx=5)

        var_cat = tk.StringVar(value="U")
        combo = ttk.Combobox(fila, textvariable=var_cat,
                             values=CATEGORIAS, width=18, state="readonly")
        combo.pack(side="left", padx=5)

        vars_categorias.append((producto, var_cat))

    # ---- Scroll con rueda (solo dentro de esta ventana) ----
    def _on_mousewheel(event):
        try:
            if not canvas.winfo_exists():
                return
            if hasattr(event, 'delta') and event.delta:
                delta = -1 * (event.delta // 120) if abs(event.delta) >= 120 else -1
            elif hasattr(event, 'num'):
                delta = -1 if event.num == 5 else 1
            else:
                delta = 0
            canvas.yview_scroll(int(delta), "units")
        except Exception:
            pass

    def _bind_mousewheel(widget):
        widget.bind("<MouseWheel>", _on_mousewheel, add="+")
        widget.bind("<Button-4>", _on_mousewheel, add="+")
        widget.bind("<Button-5>", _on_mousewheel, add="+")
        for hijo in widget.winfo_children():
            _bind_mousewheel(hijo)

    _bind_mousewheel(canvas)
    _bind_mousewheel(frame_interno)

    # ---- Botones ----
    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(fill="x", padx=15, pady=15)

    resultado = {"ok": False}

    def _guardar():
        if not vars_categorias:
            ventana.destroy()
            return

        exitos = []
        errores = []
        for producto, var_cat in vars_categorias:
            categoria = var_cat.get()
            ok, msg = agregar_producto_catalogo(producto, categoria)
            if ok:
                exitos.append(f"✅ {producto} → {categoria}")
            else:
                errores.append(f"❌ {producto}: {msg}")

        lineas = []
        if exitos:
            lineas.append(f"✅ {len(exitos)} producto(s) registrado(s):")
            lineas.extend(exitos)
        if errores:
            lineas.append(f"\n❌ {len(errores)} error(es):")
            lineas.extend(errores)

        messagebox.showinfo(
            "Registro completado",
            "\n".join(lineas),
            parent=ventana
        )

        resultado["ok"] = True
        ventana.destroy()

    def _cancelar():
        ventana.destroy()

    ttk.Button(fr_btn, text="💾 Guardar todos",
               command=_guardar,
               bootstyle="info-outline").pack(side="right", padx=5)
    ttk.Button(fr_btn, text="❌ Cancelar",
               command=_cancelar,
               bootstyle="info-outline").pack(side="right", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", _cancelar)
    ventana.bind("<Escape>", lambda e: _cancelar())

    ventana.wait_window()
    return resultado["ok"]