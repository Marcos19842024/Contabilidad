## -*- coding: utf-8 -*-
"""
dialogos/registrar_productos.py
Diálogo para registrar productos en el catálogo de excepciones manuales.
Se usa desde el aviso de reclasificación cuando se lee una factura,
y también desde el sync (productos nuevos + mal categorizados).
"""

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from modulos.lector_facturas import agregar_producto_catalogo


CATEGORIAS = ["U", "ACCESORIOS", "MEDICAMENTOS", "HIGIENE",
              "ESTETICA", "TRANSPORTE", "PENSION", "VACUNA", "CLINICA"]


def _es_nuevo(aviso):
    """True si el aviso corresponde a un producto no catalogado."""
    if aviso.get("motivo") == "no_catalogado":
        return True
    # Fallback: si la categoría actual es U y no tiene categoría de origen,
    # lo tratamos como nuevo.
    cat = (aviso.get("categoria_actual") or "").strip().upper()
    return cat == "U"


def abrir_dialogo_registrar_productos(app, avisos):
    """
    Abre un diálogo para registrar varios productos en el catálogo.

    Acepta una lista mezclada de avisos: pueden ser productos nuevos
    (motivo="no_catalogado") o reclasificaciones (VACUNA/CLINICA con IVA).
    Se distinguen visualmente con un badge.
    """
    if not avisos:
        return False

    from ui.utils import configurar_ventana

    ventana = ttk.Toplevel(app)
    ventana.title("➕ Registrar productos en el catálogo")
    configurar_ventana(app, ventana, ancho=820, alto=580,
                       min_ancho=700, min_alto=450)

    # ---- Encabezado ----
    ttk.Label(ventana,
              text="➕ Registrar productos en el catálogo",
              font=("Segoe UI", 14, "bold")).pack(pady=(15, 5))

    # Contar tipos para mostrarlo en el subtítulo
    n_nuevos = sum(1 for a in avisos if _es_nuevo(a))
    n_reclasif = len(avisos) - n_nuevos

    resumen_partes = []
    if n_nuevos:
        resumen_partes.append(f"🆕 {n_nuevos} producto(s) nuevo(s)")
    if n_reclasif:
        resumen_partes.append(f"🏷️ {n_reclasif} para reclasificar")
    subtitulo = " · ".join(resumen_partes) if resumen_partes else "Sin productos"

    ttk.Label(ventana,
              text=f"{subtitulo}\n"
                   "Elige la categoría correcta para cada uno. Se guardarán en\n"
                   "'categorias_manuales.json' y se aplicarán la próxima vez.",
              font=("Segoe UI", 9),
              foreground="gray",
              justify="center").pack(pady=(0, 15))

    # ---- Contenedor con scroll ----
    contenedor = ttk.Frame(ventana)
    contenedor.pack(fill="both", expand=True, padx=15, pady=5)

    canvas = tk.Canvas(contenedor, borderwidth=0, highlightthickness=0)
    scroll_v = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
    frame_interno = ttk.Frame(canvas)

    canvas_window = canvas.create_window((0, 0), window=frame_interno, anchor="nw")
    canvas.configure(yscrollcommand=scroll_v.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll_v.pack(side="right", fill="y")

    def _on_canvas_configure(event):
        canvas.itemconfigure(canvas_window, width=event.width)
        _recalcular_scrollregion()

    canvas.bind("<Configure>", _on_canvas_configure)

    def _recalcular_scrollregion(event=None):
        """
        Ajusta el scrollregion para que:
        - Si el contenido es más grande que el viewport → permite scroll.
        - Si el contenido es más chico → el scrollregion es igual al viewport,
          así no se puede "colar" el área vacía.
        """
        try:
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if not bbox:
                return
            contenido_alto = bbox[3] - bbox[1]
            viewport_alto = canvas.winfo_height()

            if contenido_alto <= viewport_alto:
                # Sin overflow: scrollregion = viewport (no scrollea)
                canvas.configure(scrollregion=(0, 0, bbox[2], viewport_alto))
                scroll_v.state(["disabled"])
            else:
                # Con overflow: scrollregion = contenido real
                canvas.configure(scrollregion=bbox)
                scroll_v.state(["!disabled"])
        except Exception:
            pass

    frame_interno.bind("<Configure>", _recalcular_scrollregion)

    # ---- Encabezados de la tabla ----
    enc = ttk.Frame(frame_interno)
    enc.pack(fill="x", pady=(0, 5))

    ttk.Label(enc, text="", width=4).pack(side="left")  # columna del badge
    ttk.Label(enc, text="PRODUCTO",
              font=("Segoe UI", 10, "bold"), width=42,
              anchor="w").pack(side="left", padx=5)
    ttk.Label(enc, text="CATEGORÍA ACTUAL",
              font=("Segoe UI", 10, "bold"), width=18,
              anchor="center").pack(side="left", padx=5)
    ttk.Label(enc, text="NUEVA CATEGORÍA",
              font=("Segoe UI", 10, "bold"), width=18,
              anchor="center").pack(side="left", padx=5)

    # ---- Filas ----
    vars_categorias = []  # Lista de (nombre, StringVar)

    for aviso in avisos:
        producto = aviso.get("producto", "?")
        categoria_actual = aviso.get("categoria_actual", "?")
        es_nuevo = _es_nuevo(aviso)

        fila = ttk.Frame(frame_interno)
        fila.pack(fill="x", pady=2)

        # Badge visual
        badge_text = "🆕" if es_nuevo else "🏷️"
        badge_color = "info" if es_nuevo else "warning"
        ttk.Label(fila, text=badge_text, width=4,
                  font=("Segoe UI", 11),
                  bootstyle=badge_color).pack(side="left")

        ttk.Label(fila, text=producto, width=42,
                  anchor="w").pack(side="left", padx=5)
        ttk.Label(fila, text=categoria_actual, width=18,
                  anchor="center", foreground="gray").pack(side="left", padx=5)

        var_cat = tk.StringVar(value="U")
        combo = ttk.Combobox(fila, textvariable=var_cat,
                             values=CATEGORIAS, width=16, state="readonly")
        combo.pack(side="left", padx=5)

        vars_categorias.append((producto, var_cat))

    # ---- Scroll con rueda ----
    def _on_mousewheel(event):
        try:
            if not canvas.winfo_exists():
                return
            # Solo scrollear si hay overflow
            if "disabled" in scroll_v.state():
                return

            if hasattr(event, 'delta') and event.delta:
                if abs(event.delta) >= 120:
                    delta = -1 * (event.delta // 120)
                else:
                    # macOS: deltas chicos, usar signo
                    delta = -1 if event.delta > 0 else 1
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

    # Bindear al canvas, al frame, a los hijos y a la ventana completa
    _bind_mousewheel(canvas)
    _bind_mousewheel(frame_interno)
    ventana.bind("<MouseWheel>", _on_mousewheel, add="+")
    ventana.bind("<Button-4>", _on_mousewheel, add="+")
    ventana.bind("<Button-5>", _on_mousewheel, add="+")

    # Después de construir todo, recalcular
    ventana.after(50, _recalcular_scrollregion)

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

    ventana.protocol("WM_DELETE_WINDOW", _cancelar)
    ventana.bind("<Escape>", lambda e: _cancelar())

    ventana.wait_window()
    return resultado["ok"]