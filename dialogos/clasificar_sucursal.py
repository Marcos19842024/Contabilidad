# -*- coding: utf-8 -*-
"""
dialogos/clasificar_sucursal.py
Diálogo para clasificar facturas entre Animalia y Baalak.
Muestra una lista de facturas con checkboxes.
"""

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox
from pathlib import Path

from sat.guardar_egresos import cargar_db_egresos, guardar_db_egresos
from ui.utils import configurar_ventana


def abrir_dialogo_clasificar_sucursal(app, anio=2026):
    """
    Abre el diálogo para clasificar facturas entre Animalia y Baalak.
    
    Parámetros:
      - app: instancia de AppEgresos.
      - anio: año de las facturas a clasificar.
    """
    # Cargar facturas
    registros = cargar_db_egresos(anio)

    if not registros:
        messagebox.showinfo(
            "Sin facturas",
            f"No hay facturas de {anio} para clasificar.\n\n"
            "Descarga facturas primero.",
            parent=app
        )
        return

    # Crear ventana
    ventana = ttk.Toplevel(app)
    ventana.title("🏢 Clasificar sucursal")
    configurar_ventana(app, ventana, ancho=1000, alto=700,
                       min_ancho=800, min_alto=500)

    # Encabezado
    ttk.Label(
        ventana,
        text="🏢 Clasificar facturas por sucursal",
        font=("Segoe UI", 14, "bold")
    ).pack(pady=(15, 5))

    ttk.Label(
        ventana,
        text=f"Total de facturas: {len(registros)}\n"
             "Marca las que son de Animalia. Las demás se quedan en Baalak.",
        font=("Segoe UI", 9),
        foreground="gray"
    ).pack(pady=(0, 15))

    # Contenedor de filtros
    frame_filtros = ttk.Frame(ventana)
    frame_filtros.pack(fill="x", padx=15, pady=5)

    ttk.Label(frame_filtros, text="Filtrar:").pack(side="left", padx=5)
    var_filtro = tk.StringVar(value="TODAS")
    ttk.Combobox(
        frame_filtros,
        textvariable=var_filtro,
        values=["TODAS", "SOLO ANIMALIA", "SOLO BAALAK"],
        width=20,
        state="readonly"
    ).pack(side="left", padx=5)

    ttk.Label(frame_filtros, text="Buscar:").pack(side="left", padx=(15, 5))
    var_buscar = tk.StringVar()
    ttk.Entry(frame_filtros, textvariable=var_buscar, width=30).pack(side="left", padx=5)

    # Contenedor con scroll
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

    # Encabezados
    enc = ttk.Frame(frame_interno)
    enc.pack(fill="x", pady=(0, 5))

    ttk.Label(enc, text="", width=3).pack(side="left")
    ttk.Label(enc, text="FECHA", font=("Segoe UI", 9, "bold"),
              width=12, anchor="w").pack(side="left", padx=3)
    ttk.Label(enc, text="FOLIO", font=("Segoe UI", 9, "bold"),
              width=15, anchor="w").pack(side="left", padx=3)
    ttk.Label(enc, text="EMISOR", font=("Segoe UI", 9, "bold"),
              width=40, anchor="w").pack(side="left", padx=3)
    ttk.Label(enc, text="TOTAL", font=("Segoe UI", 9, "bold"),
              width=12, anchor="e").pack(side="left", padx=3)
    ttk.Label(enc, text="SUCURSAL", font=("Segoe UI", 9, "bold"),
              width=15, anchor="center").pack(side="left", padx=3)

    # Lista de facturas
    vars_sucursal = {}  # id → StringVar ("Animalia" o "Baalak")

    frame_filas = ttk.Frame(frame_interno)
    frame_filas.pack(fill="both", expand=True)

    filas_widgets = []

    def _refrescar_lista(*args):
        # Limpiar
        for w in frame_filas.winfo_children():
            w.destroy()
        filas_widgets.clear()
        vars_sucursal.clear()

        filtro = var_filtro.get()
        busqueda = var_buscar.get().strip().lower()

        for reg in registros:
            sucursal_actual = reg.get("sucursal", "Baalak")
            emisor = reg.get("nombre_emisor", "").lower()
            rfc = reg.get("rfc_emisor", "").lower()
            folio = reg.get("folio", "").lower()

            # Aplicar filtro
            if filtro == "SOLO ANIMALIA" and sucursal_actual != "Animalia":
                continue
            if filtro == "SOLO BAALAK" and sucursal_actual != "Baalak":
                continue
            if busqueda and busqueda not in emisor and busqueda not in rfc and busqueda not in folio:
                continue

            # Crear fila
            fila = ttk.Frame(frame_filas)
            fila.pack(fill="x", pady=1)

            var = tk.StringVar(value=sucursal_actual)
            vars_sucursal[reg["id"]] = var

            ttk.Label(fila, text="", width=3).pack(side="left")

            ttk.Label(fila, text=reg.get("fecha", ""),
                      width=12, anchor="w", font=("Consolas", 9)).pack(side="left", padx=3)

            ttk.Label(fila, text=reg.get("folio", ""),
                      width=15, anchor="w", font=("Consolas", 9)).pack(side="left", padx=3)

            ttk.Label(fila, text=reg.get("nombre_emisor", "")[:40],
                      width=40, anchor="w", font=("Segoe UI", 9)).pack(side="left", padx=3)

            ttk.Label(fila, text=f"${reg.get('total', 0):,.2f}",
                      width=12, anchor="e", font=("Segoe UI", 9)).pack(side="left", padx=3)

            # Combobox de sucursal
            combo = ttk.Combobox(
                fila,
                textvariable=var,
                values=["Baalak", "Animalia"],
                width=12,
                state="readonly"
            )
            combo.pack(side="left", padx=3)

            fila_dict = {"id": reg["id"], "var": var, "combo": combo}
            filas_widgets.append(fila_dict)

            # Colorear si es Animalia
            def _actualizar_color(v=var, c=combo):
                if v.get() == "Animalia":
                    c.configure(bootstyle="warning")
                else:
                    c.configure(bootstyle="default")

            var.trace_add("write", lambda *a, v=var, c=combo: _actualizar_color(v, c))
            _actualizar_color()

    var_filtro.trace_add("write", _refrescar_lista)
    var_buscar.trace_add("write", _refrescar_lista)

    _refrescar_lista()

    # Botones
    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(fill="x", padx=15, pady=15)

    def _guardar():
        # Actualizar registros con las sucursales marcadas
        for reg in registros:
            if reg["id"] in vars_sucursal:
                reg["sucursal"] = vars_sucursal[reg["id"]].get()

        guardar_db_egresos(registros, anio)

        # Contar
        animalia = sum(1 for r in registros if r.get("sucursal") == "Animalia")
        baalak = sum(1 for r in registros if r.get("sucursal") == "Baalak")

        messagebox.showinfo(
            "Clasificación guardada",
            f"✅ Clasificación guardada\n\n"
            f"• Animalia: {animalia} facturas\n"
            f"• Baalak:   {baalak} facturas",
            parent=ventana
        )
        ventana.destroy()

    def _cancelar():
        ventana.destroy()

    ttk.Button(fr_btn, text="💾 Guardar clasificación",
               command=_guardar,
               bootstyle="info-outline").pack(side="right", padx=5)

    # Botones rápidos
    def _marcar_todas_baalak():
        for v in vars_sucursal.values():
            v.set("Baalak")

    ttk.Button(fr_btn, text="🏢 Todas Baalak",
               command=_marcar_todas_baalak,
               bootstyle="secondary-outline").pack(side="left", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", _cancelar)

    # Scroll con rueda
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

    canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
