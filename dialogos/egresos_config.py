# -*- coding: utf-8 -*-
"""
dialogos/egresos_config.py
Diálogo de configuración del módulo de Egresos.
Permite configurar:
  - RFC del receptor
  - Archivos de la e.firma (.cer y .key)
  - Contraseña de la e.firma
  - Rango de fechas por defecto
"""

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox, filedialog
from pathlib import Path

from config.config_egresos import (
    cargar_config_egresos,
    guardar_config_egresos,
)


def abrir_dialogo_config_egresos(app):
    """
    Abre el diálogo de configuración del módulo de Egresos.
    Devuelve True si se guardó la configuración.
    """
    cfg = cargar_config_egresos()

    from ui.utils import configurar_ventana

    ventana = ttk.Toplevel(app)
    ventana.title("⚙️ Configuración de Egresos")
    configurar_ventana(app, ventana, ancho=500, alto=500,
                       min_ancho=450, min_alto=450)

    # ---- Encabezado ----
    ttk.Label(ventana,
              text="⚙️ Configuración del módulo de Egresos",
              font=("Segoe UI", 14, "bold")).pack(pady=(15, 5))

    ttk.Label(ventana,
              text="Configura las credenciales de tu e.firma (FIEL)\n"
                   "para descargar las facturas del SAT.",
              font=("Segoe UI", 9),
              foreground="gray",
              justify="center").pack(pady=(0, 15))

    # ---- Formulario ----
    form = ttk.Frame(ventana)
    form.pack(fill="x", padx=20, pady=10)
    form.columnconfigure(0, weight=0)
    form.columnconfigure(1, weight=1)

    fila = 0

    # RFC del receptor
    ttk.Label(form, text="RFC del receptor:").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    
    var_rfc = tk.StringVar(value=cfg.get("rfc_receptor", ""))
    ttk.Entry(form, textvariable=var_rfc).grid(
        row=fila, column=1, sticky="ew", pady=8)
    fila += 1

    # Forzar mayúsculas en vivo
    def _force_upper_rfc(*args):
        texto = var_rfc.get()
        upper = texto.upper()
        if texto != upper:
            var_rfc.set(upper)
    var_rfc.trace_add("write", _force_upper_rfc)
    
    ttk.Label(form,
              text="El RFC de la empresa (Animalia/Baalak).",
              foreground="gray", font=("Segoe UI", 8)).grid(
        row=fila, column=1, sticky="w", pady=(0, 5))
    fila += 1

    # Archivo .cer
    ttk.Label(form, text="Certificado (.cer):").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    frame_cer = ttk.Frame(form)
    frame_cer.grid(row=fila, column=1, sticky="ew", pady=8)
    frame_cer.columnconfigure(0, weight=1)
    var_cer = tk.StringVar(value=cfg.get("certificado_cer", ""))
    ttk.Entry(frame_cer, textvariable=var_cer).grid(
        row=0, column=0, sticky="ew")
    ttk.Button(frame_cer, text="📁",
               command=lambda: _seleccionar_archivo(var_cer, "*.cer"),
               bootstyle="secondary-outline").grid(
        row=0, column=1, padx=(5, 0))
    fila += 1

    # Archivo .key
    ttk.Label(form, text="Llave privada (.key):").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    frame_key = ttk.Frame(form)
    frame_key.grid(row=fila, column=1, sticky="ew", pady=8)
    frame_key.columnconfigure(0, weight=1)
    var_key = tk.StringVar(value=cfg.get("certificado_key", ""))
    ttk.Entry(frame_key, textvariable=var_key).grid(
        row=0, column=0, sticky="ew")
    ttk.Button(frame_key, text="📁",
               command=lambda: _seleccionar_archivo(var_key, "*.key"),
               bootstyle="secondary-outline").grid(
        row=0, column=1, padx=(5, 0))
    fila += 1

    # Contraseña de la e.firma
    ttk.Label(form, text="Contraseña de la e.firma:").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    var_password = tk.StringVar(value=cfg.get("password_fiel", ""))
    ttk.Entry(form, textvariable=var_password, show="•").grid(
        row=fila, column=1, sticky="ew", pady=8)
    fila += 1

    ttk.Label(form,
              text="La contraseña que usas para firmar con tu e.firma.",
              foreground="gray", font=("Segoe UI", 8)).grid(
        row=fila, column=1, sticky="w", pady=(0, 5))
    fila += 1

    # Última descarga
    ttk.Label(form, text="Última descarga:").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
    ttk.Label(form, text=cfg.get("ultima_descarga", "Nunca"),
              foreground="gray").grid(
        row=fila, column=1, sticky="w", pady=8)
    fila += 1

    # ---- Separador ----
    ttk.Separator(ventana).pack(fill="x", padx=20, pady=15)

    # ---- Nota ----
    ttk.Label(ventana,
              text="ℹ️ Esta información se guarda localmente en tu computadora.\n"
                   "La contraseña se guarda en texto plano. No la compartas.",
              font=("Segoe UI", 8),
              foreground="gray",
              justify="center").pack(pady=(0, 15))

    # ---- Botones ----
    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(fill="x", padx=20, pady=(0, 15))

    resultado = {"ok": False}

    def _guardar():
        rfc = var_rfc.get().strip().upper()
        cer = var_cer.get().strip()
        key = var_key.get().strip()
        pwd = var_password.get().strip()

        if not rfc:
            messagebox.showwarning(
                "Faltan datos",
                "El RFC del receptor es obligatorio.",
                parent=ventana)
            return

        if not cer or not Path(cer).exists():
            messagebox.showwarning(
                "Faltan datos",
                "Selecciona el archivo .cer de tu e.firma.",
                parent=ventana)
            return

        if not key or not Path(key).exists():
            messagebox.showwarning(
                "Faltan datos",
                "Selecciona el archivo .key de tu e.firma.",
                parent=ventana)
            return

        if not pwd:
            messagebox.showwarning(
                "Faltan datos",
                "La contraseña de la e.firma es obligatoria.",
                parent=ventana)
            return

        cfg["rfc_receptor"] = rfc
        cfg["certificado_cer"] = cer
        cfg["certificado_key"] = key
        cfg["password_fiel"] = pwd

        guardar_config_egresos(cfg)
        resultado["ok"] = True

        messagebox.showinfo(
            "Configuración guardada",
            "✅ Los datos se guardaron correctamente.\n\n"
            "Ahora puedes descargar las facturas del SAT.",
            parent=ventana)

        ventana.destroy()

    def _cancelar():
        ventana.destroy()

    ttk.Button(fr_btn, text="💾 Guardar",
               command=_guardar,
               bootstyle="info-outline").pack(side="right", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", _cancelar)
    ventana.bind("<Escape>", lambda e: _cancelar())

    ventana.wait_window()
    return resultado["ok"]


def _seleccionar_archivo(var, patron):
    """Abre el diálogo para seleccionar un archivo."""
    ruta = filedialog.askopenfilename(
        title="Selecciona el archivo",
        filetypes=[("Archivos", patron), ("Todos", "*.*")]
    )
    if ruta:
        var.set(ruta)