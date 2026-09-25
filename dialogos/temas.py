# -*- coding: utf-8 -*-
"""
dialogos/temas.py
Diálogo para elegir el tema visual de la aplicación.
"""

import sys
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from config.ajustes import CONFIG, TEMA, guardar_config
from config.temas import refrescar_colores


def abrir_dialogo_temas(app):
    """
    Abre el diálogo para elegir el tema visual.
    
    Parámetros:
      app: instancia de AppIngresos (para acceder a:
           - app._configurar_estilos()
           - app._repintar_todo()
           - app._repintar_sidebar()
    """
    import ttkbootstrap as _ttk
    from config import temas as cfg_temas

    try:
        temas = sorted(_ttk.Style().theme_names())
    except Exception:
        temas = ["superhero", "darkly", "cyborg", "flatly", "litera", "minty"]

    ventana = ttk.Toplevel(app)
    ventana.title("🎨 Elegir tema")
    app._configurar_ventana(ventana, ancho=360, alto=480,
                            min_ancho=320, min_alto=420)

    # Encabezado
    ttk.Label(ventana, text="Selecciona un tema:",
              font=("Segoe UI", 13, "bold")).pack(pady=(15, 5))
    ttk.Label(ventana,
              text="Haz clic en un tema para previsualizarlo.\n"
                   "Presiona 'Aplicar y guardar' para conservarlo.",
              font=("Segoe UI", 9),
              foreground="gray",
              justify="center").pack(pady=(0, 10))

    # Contenedor con scroll
    cont = ttk.Frame(ventana)
    cont.pack(fill="both", expand=True, padx=15, pady=5)

    tree = ttk.Treeview(cont, columns=("tema",), show="headings",
                        height=12, selectmode="browse")
    tree.heading("tema", text="TEMA")
    tree.column("tema", width=200, anchor="w")

    sb = ttk.Scrollbar(cont, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    for tema in temas:
        tree.insert("", "end", iid=tema, values=(tema,))

    if TEMA in temas:
        tree.selection_set(TEMA)
        tree.see(TEMA)

    # Scroll con la rueda
    def _on_mousewheel(event):
        if sys.platform == "darwin":
            delta = -1 * event.delta
        elif sys.platform.startswith("win"):
            delta = -1 * (event.delta // 120)
        else:
            delta = -1 if event.num == 5 else 1
        tree.yview_scroll(int(delta), "units")

    def _bind_wheel(widget):
        widget.bind("<MouseWheel>", _on_mousewheel, add="+")
        widget.bind("<Button-4>", _on_mousewheel, add="+")
        widget.bind("<Button-5>", _on_mousewheel, add="+")
        for h in widget.winfo_children():
            _bind_wheel(h)

    _bind_wheel(ventana)

    var_tema = tk.StringVar(value=TEMA)

    def _preview(tema):
        try:
            _ttk.Style().theme_use(tema)
            # Actualizamos la variable global TEMA en config.ajustes
            from config import ajustes as cfg_ajustes
            cfg_ajustes.TEMA = tema
            # Y también en config.temas (por si lo consulta)
            cfg_temas.TEMA = tema

            refrescar_colores()
            app._configurar_estilos()
            app._repintar_todo()
            app._repintar_sidebar()
        except Exception as e:
            print(f"[_preview] Error: {e}")

    def _al_seleccionar(event=None):
        sel = tree.selection()
        if not sel:
            return
        tema = sel[0]
        var_tema.set(tema)
        _preview(tema)
        lbl_actual.configure(text=f"Tema actual: {tema}")

    tree.bind("<<TreeviewSelect>>", _al_seleccionar)

    lbl_actual = ttk.Label(ventana, text=f"Tema actual: {TEMA}",
                            font=("Segoe UI", 10, "bold"),
                            bootstyle="info")
    lbl_actual.pack(pady=8)

    def _confirmar():
        nuevo_tema = var_tema.get()
        CONFIG["tema"] = nuevo_tema
        guardar_config(CONFIG)
        messagebox.showinfo(
            "Tema guardado",
            f"Tema cambiado a: {nuevo_tema}\n\n"
            "El cambio ya está aplicado."
        )
        ventana.destroy()

    def _restaurar():
        tema_defecto = "superhero"
        var_tema.set(tema_defecto)
        if tema_defecto in temas:
            tree.selection_set(tema_defecto)
            tree.see(tema_defecto)
        _preview(tema_defecto)
        lbl_actual.configure(text=f"Tema actual: {tema_defecto}")

    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(pady=12)
    ttk.Button(fr_btn, text="✅ Aplicar y guardar",
               command=_confirmar,
               bootstyle="info-outline").pack(side="left", padx=5)
    ttk.Button(fr_btn, text="↺ Restaurar",
               command=_restaurar,
               bootstyle="info-outline").pack(side="left", padx=5)