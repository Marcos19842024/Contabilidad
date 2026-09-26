# -*- coding: utf-8 -*-
"""
dialogos/gmail_config.py
Diálogo para configurar las credenciales de Gmail y filtros
de descarga de facturas.
"""

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from config.ajustes import CONFIG, guardar_config


def pedir_credenciales_correo(app):
    """
    Pide las credenciales de Gmail y opciones de filtrado.
    Devuelve (usuario, password, etiqueta) o (None, None, None).
    """
    print("[DEBUG gmail] inicio")
    ventana = ttk.Toplevel(app)
    print(f"[DEBUG gmail] Toplevel creado: {ventana}")

    try:
        ventana.title("Configuración de Gmail")
        print("[DEBUG gmail] title ok")
    except Exception as e:
        print(f"[DEBUG gmail] error en title: {e}")

    try:
        app._configurar_ventana(ventana, ancho=620, alto=580,
                                min_ancho=520, min_alto=460)
        print("[DEBUG gmail] _configurar_ventana ok")
    except Exception as e:
        print(f"[DEBUG gmail] error en _configurar_ventana: {e}")
        import traceback
        traceback.print_exc()

    # ---- Contenedor con padding ----
    contenedor = ttk.Frame(ventana, padding=20)
    contenedor.pack(fill="both", expand=True)

    # ---- Encabezado ----
    ttk.Label(contenedor,
              text="Configuración de Gmail",
              font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))

    ttk.Label(contenedor,
              text="Necesitas una 'Contraseña de aplicación' de Google.\n"
                   "Genérala en: myaccount.google.com/apppasswords",
              justify="center", foreground="gray",
              font=("Segoe UI", 9)).pack(pady=(0, 20))

    # ---- Formulario ----
    form = ttk.Frame(contenedor)
    form.pack(fill="x", expand=False)
    form.columnconfigure(0, weight=0)
    form.columnconfigure(1, weight=1)

    cfg_actual = CONFIG.get("correo", {})
    fila = 0

    # Correo
    ttk.Label(form, text="Correo de Gmail:").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    var_usuario = tk.StringVar(value=cfg_actual.get("usuario", ""))
    ttk.Entry(form, textvariable=var_usuario).grid(
        row=fila, column=1, sticky="ew", pady=8)
    fila += 1

    # Contraseña
    ttk.Label(form, text="Contraseña de app:").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    var_password = tk.StringVar(value=cfg_actual.get("password_app", ""))
    ttk.Entry(form, textvariable=var_password, show="•").grid(
        row=fila, column=1, sticky="ew", pady=8)
    fila += 1

    # Etiqueta
    ttk.Label(form, text="Etiqueta de Gmail:").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    var_etiqueta = tk.StringVar(
        value=cfg_actual.get("etiqueta", "FACTURAS BAALAK"))
    ttk.Entry(form, textvariable=var_etiqueta).grid(
        row=fila, column=1, sticky="ew", pady=8)
    fila += 1

    ttk.Label(form,
              text="Ejemplo: 'Facturas QVET' o 'Facturas/QVET' (con subcarpeta)",
              foreground="gray", font=("Segoe UI", 8)).grid(
        row=fila, column=1, sticky="w", pady=(0, 5))
    fila += 1

    # Filtro de remitente
    ttk.Label(form, text="Filtrar por remitente:").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    var_remitente = tk.StringVar(
        value=cfg_actual.get("filtro_remitente", ""))
    ttk.Entry(form, textvariable=var_remitente).grid(
        row=fila, column=1, sticky="ew", pady=8)
    fila += 1

    ttk.Label(form,
              text="Opcional. Ejemplo: 'qvet' o 'facturacion'. Déjalo vacío para descargar todos.",
              foreground="gray", font=("Segoe UI", 8), wraplength=400).grid(
        row=fila, column=1, sticky="w", pady=(0, 5))
    fila += 1

    # Días atrás
    ttk.Label(form, text="Correos de los últimos (días):").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    var_dias = tk.StringVar(value=str(cfg_actual.get("dias_atras", 30)))
    ttk.Entry(form, textvariable=var_dias, width=10).grid(
        row=fila, column=1, sticky="w", pady=8)
    fila += 1

    ttk.Label(form,
              text="Escribe 0 para descargar todos los correos sin límite de fecha.",
              foreground="gray", font=("Segoe UI", 8)).grid(
        row=fila, column=1, sticky="w", pady=(0, 5))
    fila += 1

    # Espacio flexible
    ttk.Frame(contenedor).pack(fill="y", expand=True)

    resultado = {"ok": False}

    def _guardar():
        u = var_usuario.get().strip()
        p = var_password.get().strip().replace(" ", "")
        e = var_etiqueta.get().strip() or "Facturas QVET"
        r = var_remitente.get().strip()
        try:
            d = int(var_dias.get().strip() or "0")
        except ValueError:
            d = 0

        if not u or not p:
            messagebox.showwarning(
                "Faltan datos",
                "Correo y contraseña son obligatorios.",
                parent=ventana
            )
            return

        CONFIG["correo"] = {
            "usuario": u,
            "password_app": p,
            "etiqueta": e,
            "filtro_remitente": r,
            "dias_atras": d,
        }
        guardar_config(CONFIG)
        resultado["ok"] = True
        ventana.destroy()

    # Botones
    fr = ttk.Frame(contenedor)
    fr.pack(fill="x", pady=(15, 0))

    ttk.Button(fr, text="💾 Guardar",
               command=_guardar,
               bootstyle="info-outline").pack(side="right", padx=5)

    ventana.wait_window()

    if resultado["ok"]:
        return (CONFIG["correo"]["usuario"],
                CONFIG["correo"]["password_app"],
                CONFIG["correo"]["etiqueta"])
    return None, None, None