# -*- coding: utf-8 -*-
"""
dialogos/reclasificador.py
Diálogo para editar las categorías de los productos del catálogo QVET.
Los cambios se acumulan en memoria y solo se guardan al presionar
'Guardar cambios'. Incluye opción de 'Deshacer todo'.
"""

import sys
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from lector_facturas import (
    cargar_catalogo,
    cargar_excepciones_manuales,
    guardar_excepciones_manuales,
)


def abrir_dialogo_reclasificador(app):
    """
    Abre el diálogo del reclasificador de productos.

    Parámetros:
      app: instancia de AppIngresos (para _configurar_ventana)
    """
    catalogo = cargar_catalogo()
    excepciones_actuales = dict(cargar_excepciones_manuales())
    excepciones_originales = dict(excepciones_actuales)

    categorias = ["U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
                  "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA"]

    ventana = ttk.Toplevel(app)
    ventana.title("🏷️ Reclasificador de productos")
    app._configurar_ventana(ventana, ancho=1150, alto=720,
                            min_ancho=900, min_alto=560)

    # --- Barra superior ---
    top = ttk.Frame(ventana)
    top.pack(fill="x", padx=10, pady=8)

    ttk.Label(top, text="Buscar:").pack(side="left", padx=(0, 5))
    var_buscar = tk.StringVar()
    ttk.Entry(top, textvariable=var_buscar, width=40).pack(side="left", padx=5)

    ttk.Label(top, text="Filtrar:").pack(side="left", padx=(15, 5))
    var_filtro = tk.StringVar(value="TODAS")
    ttk.Combobox(top, textvariable=var_filtro,
                 values=["TODAS"] + categorias,
                 width=15, state="readonly").pack(side="left", padx=5)

    ttk.Label(top, text="Mostrar:").pack(side="left", padx=(15, 5))
    var_origen = tk.StringVar(value="TODOS")
    ttk.Combobox(top, textvariable=var_origen,
                 values=["TODOS", "SOLO MODIFICADOS", "SOLO ORIGINALES"],
                 width=20, state="readonly").pack(side="left", padx=5)

    # --- Contenedor con scroll ---
    contenedor = ttk.Frame(ventana)
    contenedor.pack(fill="both", expand=True, padx=10, pady=5)

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

    # Scroll con rueda
    def _on_mousewheel(event):
        if sys.platform == "darwin":
            delta = -1 * event.delta
        elif sys.platform.startswith("win"):
            delta = -1 * (event.delta // 120)
        else:
            delta = -1 if event.num == 5 else 1
        canvas.yview_scroll(int(delta), "units")

    def _bind_mousewheel(widget):
        widget.bind("<MouseWheel>", _on_mousewheel, add="+")
        widget.bind("<Button-4>", _on_mousewheel, add="+")
        widget.bind("<Button-5>", _on_mousewheel, add="+")
        for hijo in widget.winfo_children():
            _bind_mousewheel(hijo)

    # --- Encabezados ---
    encabezados = ttk.Frame(frame_interno)
    encabezados.pack(fill="x", pady=(0, 5))

    ttk.Label(encabezados, text="DESCRIPCIÓN",
              font=("Segoe UI", 10, "bold"), width=60, anchor="w").pack(side="left", padx=5)
    ttk.Label(encabezados, text="CATEGORÍA ORIGINAL",
              font=("Segoe UI", 10, "bold"), width=22, anchor="center").pack(side="left", padx=5)
    ttk.Label(encabezados, text="CATEGORÍA ACTUAL",
              font=("Segoe UI", 10, "bold"), width=22, anchor="center").pack(side="left", padx=5)
    ttk.Label(encabezados, text="ESTADO",
              font=("Segoe UI", 10, "bold"), width=15, anchor="center").pack(side="left", padx=5)

    frame_filas = ttk.Frame(frame_interno)
    frame_filas.pack(fill="both", expand=True)

    filas_widgets = []
    estado_sel = {"frame_seleccionado": None}

    # --- Panel inferior ---
    bot = ttk.Frame(ventana)
    bot.pack(fill="x", padx=10, pady=8)

    lbl_contador = ttk.Label(bot, text="")
    lbl_contador.pack(side="left")

    # --- Funciones internas ---
    def _hay_cambios():
        return excepciones_actuales != excepciones_originales

    def _actualizar_contador():
        cambios = sum(
            1 for k, v in excepciones_actuales.items()
            if excepciones_originales.get(k) != v
        )
        lbl_contador.configure(
            text=f"Cambios pendientes: {cambios} | Productos totales: {len(catalogo)}"
        )

    def _seleccionar_fila(fila_dict):
        prev = estado_sel.get("frame_seleccionado")
        if prev is not None:
            try:
                prev.configure(style="TFrame")
            except Exception:
                pass
        nuevo = fila_dict.get("frame")
        if nuevo is not None:
            try:
                nuevo.configure(style="Seleccion.TFrame")
            except Exception:
                pass
            estado_sel["frame_seleccionado"] = nuevo

    def _al_cambiar(desc, var):
        nueva_cat = var.get()
        cat_original = catalogo.get(desc, "CLINICA")
        cat_previa = excepciones_originales.get(desc, cat_original)

        if nueva_cat == cat_previa:
            excepciones_actuales.pop(desc, None)
        else:
            excepciones_actuales[desc] = nueva_cat

        for fila in filas_widgets:
            if fila["desc"] == desc:
                if desc in excepciones_actuales and excepciones_actuales[desc] != cat_original:
                    fila["lbl_estado"].configure(text="✏️ Modificado", foreground="blue")
                elif desc in excepciones_actuales:
                    fila["lbl_estado"].configure(text="⚙️ Excepción", foreground="gray")
                else:
                    fila["lbl_estado"].configure(text="—", foreground="black")
                break

        _actualizar_contador()

    def _refrescar_lista(*args):
        nonlocal filas_widgets
        for w in frame_filas.winfo_children():
            w.destroy()
        filas_widgets = []
        estado_sel["frame_seleccionado"] = None

        busqueda = var_buscar.get().strip().lower()
        filtro = var_filtro.get()
        origen_filtro = var_origen.get()

        todos = dict(catalogo)
        for k, v in excepciones_actuales.items():
            todos[k] = v

        items = []
        for desc, cat in sorted(todos.items()):
            if busqueda and busqueda not in desc.lower():
                continue
            if filtro != "TODAS" and cat != filtro:
                continue
            es_modificado = desc in excepciones_actuales
            if origen_filtro == "SOLO MODIFICADOS" and not es_modificado:
                continue
            if origen_filtro == "SOLO ORIGINALES" and es_modificado:
                continue
            items.append((desc, cat))

        max_items = 500
        for desc, _ in items[:max_items]:
            cat_original = catalogo.get(desc, "CLINICA")
            cat_actual = excepciones_actuales.get(desc, cat_original)

            fila_frame = ttk.Frame(frame_filas, style="TFrame")
            fila_frame.pack(fill="x", pady=1)

            ttk.Label(fila_frame, text=desc, width=60, anchor="w").pack(side="left", padx=5)
            ttk.Label(fila_frame, text=cat_original,
                      width=22, anchor="center").pack(side="left", padx=5)

            var_cat = tk.StringVar(value=cat_actual)
            combo = ttk.Combobox(fila_frame, textvariable=var_cat,
                                 values=categorias, width=20,
                                 state="readonly")
            combo.pack(side="left", padx=5)
            combo.bind(
                "<<ComboboxSelected>>",
                lambda e, d=desc, v=var_cat: _al_cambiar(d, v)
            )

            estado_texto = "—"
            color = "black"
            if desc in excepciones_actuales:
                if excepciones_actuales[desc] != cat_original:
                    estado_texto = "✏️ Modificado"
                    color = "blue"
                else:
                    estado_texto = "⚙️ Excepción"
                    color = "gray"

            lbl_estado = ttk.Label(fila_frame, text=estado_texto,
                                   width=15, anchor="center",
                                   foreground=color)
            lbl_estado.pack(side="left", padx=5)

            fila_dict = {
                "desc": desc,
                "frame": fila_frame,
                "combo_var": var_cat,
                "lbl_estado": lbl_estado,
            }

            def _click_en_fila(event, fd=fila_dict):
                _seleccionar_fila(fd)

            def _bind_click(widget, fd=fila_dict):
                widget.bind("<Button-1>", _click_en_fila, add="+")
                for hijo in widget.winfo_children():
                    _bind_click(hijo, fd)

            _bind_click(fila_frame)
            filas_widgets.append(fila_dict)

        if len(items) > max_items:
            ttk.Label(frame_filas,
                      text=f"... y {len(items) - max_items} más. Usa el buscador.",
                      foreground="gray").pack(pady=10)

        _bind_mousewheel(frame_interno)
        _actualizar_contador()

    def _guardar():
        if not _hay_cambios():
            messagebox.showinfo("Sin cambios",
                                "No hay cambios pendientes.", parent=ventana)
            return

        if not messagebox.askyesno(
            "Guardar cambios",
            f"Se guardarán {len(excepciones_actuales)} excepciones manuales.\n\n"
            "Se hará un backup automático.\n¿Continuar?",
            parent=ventana
        ):
            return

        guardar_excepciones_manuales(excepciones_actuales)
        nonlocal excepciones_originales
        excepciones_originales = dict(excepciones_actuales)
        _refrescar_lista()
        messagebox.showinfo("Guardado",
                            "Los cambios se guardaron correctamente.",
                            parent=ventana)

    def _deshacer_todo():
        if not _hay_cambios():
            messagebox.showinfo("Sin cambios",
                                "No hay cambios para deshacer.", parent=ventana)
            return

        if not messagebox.askyesno(
            "Deshacer todo",
            "Se revertirán TODOS los cambios sin guardar.\n\n"
            "¿Continuar?",
            parent=ventana
        ):
            return

        excepciones_actuales.clear()
        excepciones_actuales.update(excepciones_originales)
        _refrescar_lista()
        messagebox.showinfo("Deshecho",
                            "Se revirtieron todos los cambios pendientes.",
                            parent=ventana)

    ttk.Button(bot, text="💾 Guardar cambios",
               command=_guardar,
               bootstyle="info-outline").pack(side="right", padx=4)
    ttk.Button(bot, text="↶ Deshacer todo",
               command=_deshacer_todo,
               bootstyle="info-outline").pack(side="right", padx=4)

    var_buscar.trace_add("write", _refrescar_lista)
    var_filtro.trace_add("write", _refrescar_lista)
    var_origen.trace_add("write", _refrescar_lista)

    style = ttk.Style()
    style.configure("Seleccion.TFrame", background="#cce5ff")

    _refrescar_lista()
    _bind_mousewheel(canvas)
    _bind_mousewheel(frame_interno)