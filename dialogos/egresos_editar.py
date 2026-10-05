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

import shutil
import sys
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox, filedialog
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

    rutas = {
        "xml": registro.get("ruta_xml") or registro.get("ruta_xml_destino", ""),
        "pdf": registro.get("ruta_pdf", ""),
    }

    # Frame contenedor de botones (horizontal)
    frame_botones_adj = ttk.Frame(frame_adj)
    frame_botones_adj.pack(fill="x")

    def _abrir_o_adjuntar(tipo):
        """
        Si el archivo existe → lo abre.
        Si no existe → pide uno nuevo y lo copia a la carpeta del XML.
        """
        ruta_actual = rutas.get(tipo, "")
        extension = ".xml" if tipo == "xml" else ".PDF"
        etiqueta = "XML" if tipo == "xml" else "PDF"

        # --- Caso 1: ya existe → abrir ---
        if ruta_actual and Path(ruta_actual).exists():
            _abrir_archivo(ruta_actual)
            return

        # --- Caso 2: no existe → adjuntar ---
        filtros = (
            [("XML CFDI", "*.xml"), ("Todos", "*.*")]
            if tipo == "xml"
            else [("PDF", "*.pdf *.PDF"), ("Todos", "*.*")]
        )
        ruta_origen = filedialog.askopenfilename(
            title=f"Selecciona el {etiqueta} de la factura",
            filetypes=filtros,
        )
        if not ruta_origen:
            return

        origen = Path(ruta_origen)

        # Determinar carpeta destino (junto al XML)
        ruta_xml = rutas.get("xml", "")
        if not ruta_xml:
            messagebox.showwarning(
                "Sin ubicacion",
                f"No se puede adjuntar el {etiqueta} porque el registro "
                "no tiene un XML en disco.\n\n"
                "Asegurate de haber descargado la factura primero.",
                parent=ventana,
            )
            return

        carpeta_destino = Path(ruta_xml).parent
        carpeta_destino.mkdir(parents=True, exist_ok=True)

        # Nombre destino: mismo que el XML pero con la extensión correcta
        nombre_xml = Path(ruta_xml).stem  # "1-A-1234"
        nombre_destino = f"{nombre_xml}{extension}"
        destino = carpeta_destino / nombre_destino

        try:
            if destino.exists():
                respuesta = messagebox.askyesno(
                    "Ya existe",
                    f"Ya existe un archivo:\n{destino.name}\n\n"
                    "¿Reemplazarlo?",
                    parent=ventana,
                )
                if not respuesta:
                    return
                destino.unlink()

            shutil.copy2(origen, destino)
            rutas[tipo] = str(destino)

            messagebox.showinfo(
                f"{etiqueta} adjuntado",
                f"✅ {etiqueta} copiado a:\n{destino}",
                parent=ventana,
            )

            # Refrescar botones
            _refrescar_botones()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo copiar el {etiqueta}:\n{e}",
                parent=ventana,
            )

    def _refrescar_botones():
        """Recrea los botones según el estado actual."""
        for w in frame_botones_adj.winfo_children():
            w.destroy()

        for tipo in ("xml", "pdf"):
            ruta_str = rutas.get(tipo, "")
            existe = ruta_str and Path(ruta_str).exists()

            if existe:
                icono = "📋" if tipo == "xml" else "📄"
                texto = f"{icono}  {Path(ruta_str).name}"
                estilo = "secondary-outline"
            else:
                icono = "📋" if tipo == "xml" else "📄"
                etiqueta = "XML" if tipo == "xml" else "PDF"
                texto = f"{icono}  Adjuntar {etiqueta}"
                estilo = "info-outline"

            ttk.Button(
                frame_botones_adj,
                text=texto,
                command=lambda t=tipo: _abrir_o_adjuntar(t),
                bootstyle=estilo,
                width=20,
            ).pack(side="left", padx=3, pady=2)

    _refrescar_botones()

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

        # Guardar rutas actualizadas
        if rutas.get("xml"):
            registro["ruta_xml"] = rutas["xml"]
            registro["ruta_xml_destino"] = rutas["xml"]
        if rutas.get("pdf"):
            registro["ruta_pdf"] = rutas["pdf"]

        resultado["guardado"] = True
        ventana.destroy()

    def _eliminar():
        msg = (
            f"¿Eliminar el registro de la factura {folio}?\n\n"
            "Se eliminarán los archivos adjuntos y no se puede deshacer."
        )
        if not messagebox.askyesno("Confirmar", msg, parent=ventana):
            return

        # Eliminar archivos (XML y PDF)
        eliminados = 0
        errores = []
        for tipo_key in ("xml", "pdf"):
            ruta_str = rutas.get(tipo_key, "")
            if ruta_str:
                p = Path(ruta_str)
                if p.exists():
                    try:
                        p.unlink()
                        eliminados += 1
                    except Exception as e:
                        errores.append(f"{p.name}: {e}")

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