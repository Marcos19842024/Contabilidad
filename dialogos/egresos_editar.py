# -*- coding: utf-8 -*-
"""
dialogos/egresos_editar.py
Dialogo para ver y editar un registro de Egresos.

Incluye:
  - Datos del SAT (solo lectura)
  - Campos editables
  - Archivos adjuntos (XML / PDF)
  - Botón Eliminar
"""

import sys
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox
from pathlib import Path


# Valores disponibles para los campos editables
SUCURSALES = ["Baalak", "Animalia"]
METODOS = ["PUE", "PPD"]
FORMAS_PAGO = ["Efectivo", "Transferencia", "TC", "TD", "PPD"]

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
    Abre el dialogo para ver y editar un registro de Egresos.

    Devuelve un dict:
      {"guardado": bool, "eliminado": bool}
    """
    from ui.utils import configurar_ventana

    ventana = ttk.Toplevel(app)
    ventana.title(f"Factura {registro.get('folio', '?')}")
    configurar_ventana(app, ventana, ancho=450, alto=700,
                       min_ancho=350, min_alto=450)

    # Encabezado
    folio = registro.get("folio", "?")
    uuid_corto = str(registro.get("uuid", ""))[:8]

    ttk.Label(
        ventana,
        text=f"Factura {folio}",
        font=("Segoe UI", 15, "bold"),
    ).pack(pady=(15, 5))

    ttk.Label(
        ventana,
        text=f"UUID: {uuid_corto}...",
        font=("Segoe UI", 9),
        foreground="gray",
    ).pack(pady=(0, 12))

    # ==================================================
    # DATOS DEL SAT (SOLO LECTURA)
    # ==================================================
    frame_ro = ttk.LabelFrame(ventana, text="📄 Datos del SAT (solo lectura)",
                              padding=10)
    frame_ro.pack(fill="x", padx=20, pady=5)

    info_ro = [
        ("RFC Emisor:", registro.get("rfc_emisor", "")),
        ("Nombre Emisor:", registro.get("nombre_emisor", "")),
        ("CP:", registro.get("cp", "")),
        ("Fecha:", registro.get("fecha", "")),
        ("Subtotal:", f"${registro.get('subtotal', 0):,.2f}"),
        ("IVA:", f"${registro.get('iva', 0):,.2f}"),
        ("IEPS:", f"${registro.get('ieps', 0):,.2f}"),
        ("Total:", f"${registro.get('total', 0):,.2f}"),
    ]

    for i, (lbl, valor) in enumerate(info_ro):
        ttk.Label(frame_ro, text=lbl, font=("Segoe UI", 9, "bold")).grid(
            row=i, column=0, sticky="e", padx=(0, 8), pady=2)
        v = str(valor)
        if len(v) > 55:
            v = v[:52] + "..."
        ttk.Label(frame_ro, text=v, font=("Segoe UI", 9)).grid(
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
    var_forma = tk.StringVar(value=registro.get("forma_pago_texto", "Efectivo"))
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
        values=OBSERVACIONES, width=20,
    ).grid(row=3, column=1, sticky="w", pady=6)

    # Folio
    ttk.Label(frame_edit, text="Folio:").grid(
        row=4, column=0, sticky="e", padx=(0, 8), pady=6)
    var_folio = tk.StringVar(value=registro.get("folio", ""))
    ttk.Entry(frame_edit, textvariable=var_folio, width=28).grid(
        row=4, column=1, sticky="w", pady=6)

    # ==================================================
    # ARCHIVOS ADJUNTOS
    # ==================================================
    frame_adj = ttk.LabelFrame(ventana, text="📎 Archivos adjuntos",
                                padding=10)
    frame_adj.pack(fill="x", padx=15, pady=10)

    ruta_xml = registro.get("ruta_xml") or registro.get("ruta_xml_destino", "")
    ruta_pdf = registro.get("ruta_pdf", "")

    archivos = []
    if ruta_xml:
        p = Path(ruta_xml)
        archivos.append(("XML", p, p.exists()))
    if ruta_pdf:
        p = Path(ruta_pdf)
        archivos.append(("PDF", p, p.exists()))

    if not archivos:
        ttk.Label(
            frame_adj,
            text="No hay archivos adjuntos.",
            font=("Segoe UI", 9),
            foreground="gray",
        ).pack(pady=5)
    else:
        for tipo, ruta, existe in archivos:
            icono = "📋" if tipo == "XML" else "📄"
            nombre = ruta.name if ruta.name else f"({tipo})"
            estado = "" if existe else "  (no existe)"

            btn = ttk.Button(
                frame_adj,
                text=f"{icono}  {nombre}{estado}",
                command=lambda r=ruta: _abrir_archivo(r),
                bootstyle="secondary-outline",
                width=58,
            )
            btn.pack(fill="x", pady=2)
            if not existe:
                btn.configure(state="disabled")

    # ==================================================
    # BOTONES
    # ==================================================
    resultado = {"guardado": False, "eliminado": False}

    def _guardar():
        # Actualizar el dict del registro
        registro["sucursal"] = var_sucursal.get()
        registro["metodo_pago"] = var_metodo.get()
        registro["forma_pago_texto"] = var_forma.get()
        registro["observacion"] = var_obs.get().strip().upper()
        registro["folio"] = var_folio.get().strip()

        # Si el método es PPD, forzar forma de pago PPD
        if registro["metodo_pago"] == "PPD":
            registro["forma_pago_texto"] = "PPD"

        resultado["guardado"] = True
        ventana.destroy()

    def _eliminar():
        msg = (
            f"¿Eliminar el registro de la factura {folio}?\n\n"
            "Se eliminarán los archivos adjuntos y no se puede deshacer."
        )
        if not messagebox.askyesno("Confirmar", msg, parent=ventana):
            return

        # Eliminar archivos
        eliminados = 0
        errores = []
        for tipo, ruta, existe in archivos:
            if existe:
                try:
                    ruta.unlink()
                    eliminados += 1
                except Exception as e:
                    errores.append(f"{ruta.name}: {e}")

        resultado["eliminado"] = True

        partes = ["Registro eliminado."]
        if eliminados:
            partes.append(f"\nArchivos eliminados: {eliminados}")
        if errores:
            partes.append(f"\nErrores: {len(errores)}")
        messagebox.showinfo("Eliminado", "\n".join(partes), parent=ventana)
        ventana.destroy()

    def _cancelar():
        ventana.destroy()

    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(fill="x", padx=20, pady=(10, 15))

    ttk.Button(
        fr_btn, text="💾 Guardar cambios",
        command=_guardar, bootstyle="success-outline",
    ).pack(side="right", padx=5)

    ttk.Button(
        fr_btn, text="🗑️ Eliminar",
        command=_eliminar, bootstyle="danger-outline",
    ).pack(side="left", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", _cancelar)
    ventana.bind("<Escape>", lambda e: _cancelar())

    ventana.wait_window()
    return resultado


def _abrir_archivo(ruta):
    """Abre un archivo con el visor por defecto."""
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