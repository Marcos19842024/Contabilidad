# -*- coding: utf-8 -*-
"""
dialogos/egresos_editar.py
Dialogo para editar un registro de Egresos.

Campos editables:
  - sucursal
  - observacion
  - forma_pago_texto
  - folio (por si el SAT no lo trajo)
  - metodo_pago (PUE/PPD)

Campos de solo lectura (no editables):
  - UUID, RFC emisor, nombre emisor, fecha, total, subtotal, iva, ieps
"""

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox


# Valores disponibles para los campos editables
SUCURSALES = ["Baalak", "Animalia"]

METODOS = ["PUE", "PPD"]

FORMAS_PAGO = [
    "EFVO", "CHEQUE", "TRANSF", "TC", "TD", "PPD",
]

OBSERVACIONES = [
    "GASTOS EN GENERAL",
    "ADQUISICION DE MERCANCIA",
    "GASOLINA",
    "INTERNET",
    "CELULAR",
    "ESCUELA",
    "MEMBRESIA",
    "TRANSPORTE",
    "HONORARIOS",
    "SEGUROS",
    "PUBLICIDAD",
    "DEVOLUCIONES",
    "CONSTRUCCIONES",
    "MOBILIARIO",
    "EQUIPO DE TRANSPORTE",
    "EQUIPO DE COMPUTO",
    "MAQUINARIA Y EQUIPO",
    "COMPLEMENTO DE PAGO",
    "POR DEFINIR",
    "SIN EFECTOS FISCALES",
]


def abrir_dialogo_editar_egreso(app, registro):
    """
    Abre el dialogo para editar un registro de Egresos.

    Parametros:
      - app: instancia de AppEgresos.
      - registro: dict del registro a editar.

    Devuelve True si se guardaron cambios, False si se cancelo.
    """
    from ui.utils import configurar_ventana

    ventana = ttk.Toplevel(app)
    ventana.title("✏️ Editar registro de Egreso")
    configurar_ventana(app, ventana, ancho=650, alto=680,
                       min_ancho=580, min_alto=600)

    # Encabezado
    ttk.Label(
        ventana,
        text="✏️ Editar registro",
        font=("Segoe UI", 15, "bold"),
    ).pack(pady=(15, 5))

    folio = registro.get("folio", "?")
    uuid_corto = str(registro.get("uuid", ""))[:8]
    ttk.Label(
        ventana,
        text=f"Factura: {folio}   |   UUID: {uuid_corto}…",
        font=("Segoe UI", 9),
        foreground="gray",
    ).pack(pady=(0, 15))

    # ==================================================
    # CAMPOS DE SOLO LECTURA (info del SAT)
    # ==================================================
    frame_ro = ttk.LabelFrame(ventana, text="📄 Datos del SAT (solo lectura)",
                              padding=10)
    frame_ro.pack(fill="x", padx=20, pady=5)

    info_ro = [
        ("RFC Emisor:", registro.get("rfc_emisor", "")),
        ("Nombre Emisor:", registro.get("nombre_emisor", "")),
        ("Fecha:", registro.get("fecha", "")),
        ("Subtotal:", f"${registro.get('subtotal', 0):,.2f}"),
        ("IVA:", f"${registro.get('iva', 0):,.2f}"),
        ("IEPS:", f"${registro.get('ieps', 0):,.2f}"),
        ("Total:", f"${registro.get('total', 0):,.2f}"),
    ]

    for i, (lbl, valor) in enumerate(info_ro):
        ttk.Label(frame_ro, text=lbl, font=("Segoe UI", 9, "bold")).grid(
            row=i, column=0, sticky="e", padx=(0, 8), pady=2)
        ttk.Label(frame_ro, text=valor, font=("Segoe UI", 9)).grid(
            row=i, column=1, sticky="w", pady=2)

    # ==================================================
    # CAMPOS EDITABLES
    # ==================================================
    frame_edit = ttk.LabelFrame(ventana, text="✏️ Campos editables", padding=10)
    frame_edit.pack(fill="x", padx=20, pady=10)

    # Sucursal
    ttk.Label(frame_edit, text="Sucursal:").grid(
        row=0, column=0, sticky="e", padx=(0, 8), pady=6)
    var_sucursal = tk.StringVar(value=registro.get("sucursal", "Baalak"))
    ttk.Combobox(
        frame_edit, textvariable=var_sucursal,
        values=SUCURSALES, width=15, state="readonly",
    ).grid(row=0, column=1, sticky="w", pady=6)

    # Metodo de pago
    ttk.Label(frame_edit, text="Método de pago:").grid(
        row=1, column=0, sticky="e", padx=(0, 8), pady=6)
    var_metodo = tk.StringVar(value=registro.get("metodo_pago", "PUE"))
    ttk.Combobox(
        frame_edit, textvariable=var_metodo,
        values=METODOS, width=15, state="readonly",
    ).grid(row=1, column=1, sticky="w", pady=6)

    # Forma de pago
    ttk.Label(frame_edit, text="Forma de pago:").grid(
        row=2, column=0, sticky="e", padx=(0, 8), pady=6)
    var_forma = tk.StringVar(value=registro.get("forma_pago_texto", ""))
    ttk.Combobox(
        frame_edit, textvariable=var_forma,
        values=FORMAS_PAGO, width=15, state="readonly",
    ).grid(row=2, column=1, sticky="w", pady=6)

    # Observacion
    ttk.Label(frame_edit, text="Observación:").grid(
        row=3, column=0, sticky="e", padx=(0, 8), pady=6)
    var_obs = tk.StringVar(value=registro.get("observacion", ""))
    ttk.Combobox(
        frame_edit, textvariable=var_obs,
        values=OBSERVACIONES, width=35,
    ).grid(row=3, column=1, sticky="w", pady=6)

    # Folio (por si el SAT no lo trajo)
    ttk.Label(frame_edit, text="Folio:").grid(
        row=4, column=0, sticky="e", padx=(0, 8), pady=6)
    var_folio = tk.StringVar(value=registro.get("folio", ""))
    ttk.Entry(frame_edit, textvariable=var_folio, width=25).grid(
        row=4, column=1, sticky="w", pady=6)

    # ==================================================
    # BOTONES
    # ==================================================
    resultado = {"guardado": False}

    def _guardar():
        # Actualizar el dict del registro
        registro["sucursal"] = var_sucursal.get()
        registro["metodo_pago"] = var_metodo.get()
        registro["forma_pago_texto"] = var_forma.get()
        registro["observacion"] = var_obs.get().strip().upper()
        registro["folio"] = var_folio.get().strip()

        resultado["guardado"] = True
        ventana.destroy()

    def _cancelar():
        ventana.destroy()

    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(fill="x", padx=20, pady=(10, 20))

    ttk.Button(
        fr_btn, text="💾 Guardar cambios",
        command=_guardar, bootstyle="success-outline",
    ).pack(side="right", padx=5)

    ttk.Button(
        fr_btn, text="❌ Cancelar",
        command=_cancelar, bootstyle="secondary-outline",
    ).pack(side="right", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", _cancelar)
    ventana.bind("<Escape>", lambda e: _cancelar())

    ventana.wait_window()
    return resultado["guardado"]