# -*- coding: utf-8 -*-
"""
dialogos/sincronizar_preguntas.py
Diálogos auxiliares de la sincronización:
  - preguntar_modo_descarga: no leídos / todos / editar configuración
  - preguntar_accion_facturas: procesar todas / solo guardar
"""

import ttkbootstrap as ttk


def preguntar_modo_descarga(app, dias_atras):
    """
    Muestra un diálogo para elegir cómo descargar.
    Devuelve:
      - "no_leidos" → solo correos no leídos
      - "todos"     → todos los correos
      - "editar"    → abrir configuración
      - "cancelar"  → cerrar sin hacer nada
    """

    print("[DEBUG modo] inicio")
    ventana = ttk.Toplevel(app)
    print(f"[DEBUG modo] Toplevel creado: {ventana}")
    app._configurar_ventana(ventana, ancho=520, alto=340,
                            min_ancho=480, min_alto=320)
    print("[DEBUG modo] configurada")
    ventana.title("Sincronizar facturas")

    # Encabezado
    ttk.Label(ventana, text="⚡ Sincronizar facturas",
              font=("Segoe UI", 14, "bold")).pack(pady=(20, 5))

    ttk.Label(ventana, text="¿Cómo quieres descargar?",
              font=("Segoe UI", 10), foreground="gray").pack(pady=(0, 20))

    resultado = {"modo": "cancelar"}

    def _elegir(modo):
        print(f"[DEBUG modo] eligiendo: {modo}")
        try:
            ventana.grab_release()
            print("[DEBUG modo] grab_release ok")
        except Exception as e:
            print(f"[DEBUG modo] grab_release falló: {e}")
        resultado["modo"] = modo
        ventana.destroy()
        print("[DEBUG modo] ventana destruida")

    # Botón: Solo no leídos
    ttk.Button(
        ventana,
        text="📥  Solo correos NO leídos  (más rápido)",
        command=lambda: _elegir("no_leidos"),
        bootstyle="info-outline",
        width=35,
    ).pack(pady=5)

    # Botón: Todos los correos
    texto_todos = "📨  Todos los correos"
    if dias_atras:
        texto_todos += f"  (últimos {dias_atras} días)"
    else:
        texto_todos += "  (sin límite de fecha)"
    ttk.Button(
        ventana,
        text=texto_todos,
        command=lambda: _elegir("todos"),
        bootstyle="info-outline",
        width=35,
    ).pack(pady=5)

    # Separador
    ttk.Separator(ventana).pack(fill="x", padx=20, pady=10)

    # Botón: Editar configuración
    ttk.Button(
        ventana,
        text="⚙️  Editar configuración del correo",
        command=lambda: _elegir("editar"),
        bootstyle="info-outline",
        width=35,
    ).pack(pady=5)

    # Cerrar con X = cancelar
    ventana.protocol("WM_DELETE_WINDOW", lambda: _elegir("cancelar"))
    ventana.bind("<Escape>", lambda e: _elegir("cancelar"))

    ventana.wait_window()
    return resultado["modo"]


def preguntar_accion_facturas(app, num_archivos, num_facturas, carpeta):
    """
    Pregunta qué hacer con las facturas descargadas.
    Devuelve:
      - "procesar_todas" → procesar automáticamente
      - "solo_guardar"   → solo guardar en disco
      - "cancelar"       → cerrar sin hacer nada
    """
    ventana = ttk.Toplevel(app)
    ventana.title("Facturas descargadas")
    app._configurar_ventana(ventana, ancho=500, alto=380,
                            min_ancho=460, min_alto=340)

    # Contenedor con padding
    contenedor = ttk.Frame(ventana, padding=25)
    contenedor.pack(fill="both", expand=True)

    # Encabezado
    ttk.Label(
        contenedor,
        text="📬 Facturas descargadas",
        font=("Segoe UI", 15, "bold"),
    ).pack(pady=(0, 10))

    # Resumen
    resumen = (
        f"Se descargaron {num_archivos} archivo(s),\n"
        f"correspondientes a {num_facturas} factura(s) única(s)."
    )
    ttk.Label(
        contenedor,
        text=resumen,
        font=("Segoe UI", 11),
        justify="center",
    ).pack(pady=(0, 5))

    # Ruta
    ttk.Label(
        contenedor,
        text=f"📁 {carpeta}",
        font=("Segoe UI", 9),
        foreground="gray",
        wraplength=460,
        justify="center",
    ).pack(pady=(0, 20))

    # Pregunta
    ttk.Label(
        contenedor,
        text="¿Qué quieres hacer?",
        font=("Segoe UI", 11, "bold"),
    ).pack(pady=(0, 15))

    resultado = {"accion": "cancelar"}

    def _elegir(accion):
        try:
            ventana.grab_release()
        except Exception:
            pass
        resultado["accion"] = accion
        ventana.destroy()

    # Botón: Procesar todas
    ttk.Button(
        contenedor,
        text="✅  Procesar TODAS automáticamente",
        command=lambda: _elegir("procesar_todas"),
        bootstyle="info-outline",
        width=35,
    ).pack(pady=5)

    ttk.Label(
        contenedor,
        text="Llena el formulario, guarda y adjunta XML+PDF automáticamente",
        font=("Segoe UI", 8),
        foreground="gray",
    ).pack(pady=(0, 10))

    # Botón: Solo guardar
    ttk.Button(
        contenedor,
        text="📁  Solo guardar los archivos",
        command=lambda: _elegir("solo_guardar"),
        bootstyle="info-outline",
        width=35,
    ).pack(pady=5)

    ttk.Label(
        contenedor,
        text="Los archivos quedan en disco para procesarlos después con '📥 Leer factura'",
        font=("Segoe UI", 8),
        foreground="gray",
    ).pack(pady=(0, 10))

    # Cerrar con X = cancelar
    ventana.protocol("WM_DELETE_WINDOW", lambda: _elegir("cancelar"))
    ventana.bind("<Escape>", lambda e: _elegir("cancelar"))

    ventana.wait_window()
    return resultado["accion"]