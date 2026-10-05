# -*- coding: utf-8 -*-
"""
dialogos/adjuntos.py
Dialogo para ver los datos de una factura de Ingresos
y sus adjuntos (XML, PDF).

Permite:
  - Abrir los archivos si existen.
  - Adjuntarlos (copiarlos) si no existen.
  - Eliminar el registro.
"""

import sys
import shutil
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox, filedialog
from pathlib import Path

from core.adjuntos import (
    archivos_del_registro,
    carpeta_de_registro,
    eliminar_archivos_de_registro,
    eliminar_carpeta_si_vacia,
)


def abrir_dialogo_adjuntos(app, reg):
    """
    Muestra una ventana con los datos del registro y sus adjuntos.

    Devuelve True si el registro fue eliminado, False si solo se cerro.
    """
    from ui.utils import configurar_ventana

    ventana = ttk.Toplevel(app)
    no_factura = reg.get("no_factura", "?")
    ventana.title(f"Factura {no_factura}")
    configurar_ventana(app, ventana, ancho=380, alto=400,
                       min_ancho=300, min_alto=350)

    # ---- Encabezado ----
    ttk.Label(
        ventana,
        text=f"Factura {no_factura}",
        font=("Segoe UI", 15, "bold"),
    ).pack(pady=(15, 10))

    # ==================================================
    # DATOS DE LA FACTURA
    # ==================================================
    frame_datos = ttk.LabelFrame(ventana, text="Datos de la factura", padding=10)
    frame_datos.pack(fill="x", padx=15, pady=5)

    campos_mostrar = [
        ("Fecha", reg.get("fecha", "")),
        ("No. Factura", reg.get("no_factura", "")),
        ("QVET", reg.get("qvet", "")),
        ("Centro", reg.get("centro", "")),
        ("Nombre", reg.get("nombre", "")),
        ("RFC", reg.get("rfc", "")),
        ("Folio Fiscal", reg.get("folio_fiscal", "")),
        ("Total", f"${reg.get('total', 0):,.2f}"),
    ]

    for i, (lbl, valor) in enumerate(campos_mostrar):
        ttk.Label(
            frame_datos, text=f"{lbl}:",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=i, column=0, sticky="e", padx=(0, 8), pady=2)

        v = str(valor)
        if len(v) > 60:
            v = v[:57] + "..."
        ttk.Label(
            frame_datos, text=v,
            font=("Segoe UI", 9),
        ).grid(row=i, column=1, sticky="w", pady=2)

    # ==================================================
    # ARCHIVOS ADJUNTOS
    # ==================================================
    frame_adj = ttk.LabelFrame(ventana, text="📎 Archivos adjuntos",
                                padding=10)
    frame_adj.pack(fill="x", padx=15, pady=10)

    # Detectar XML y PDF actuales
    adjuntos = archivos_del_registro(reg)

    # Buscar XML y PDF dentro de los adjuntos
    def _buscar_por_extension(ext):
        for a in adjuntos:
            if a.suffix.lower() == ext.lower():
                return a
        return None

    rutas = {
        "xml": str(_buscar_por_extension(".xml") or ""),
        "pdf": str(_buscar_por_extension(".pdf") or ""),
    }

    frame_botones_adj = ttk.Frame(frame_adj)
    frame_botones_adj.pack(fill="x")

    def _abrir_o_adjuntar(tipo):
        """
        Si el archivo existe → lo abre.
        Si no existe → pide uno nuevo y lo copia a la carpeta del registro.
        """
        ruta_actual = rutas.get(tipo, "")
        etiqueta = "XML" if tipo == "xml" else "PDF"

        # Caso 1: ya existe → abrir
        if ruta_actual and Path(ruta_actual).exists():
            _abrir_archivo(ruta_actual)
            return

        # Caso 2: no existe → adjuntar
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

        # Carpeta destino del registro
        carpeta_destino = carpeta_de_registro(reg)
        if not carpeta_destino:
            messagebox.showwarning(
                "Sin carpeta",
                "El registro no tiene una carpeta asignada.",
                parent=ventana,
            )
            return

        carpeta_destino.mkdir(parents=True, exist_ok=True)

        # Nombre destino: mismo que el no_factura + extensión
        extension = ".xml" if tipo == "xml" else ".PDF"
        nombre_destino = f"{no_factura}{extension}"
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
                width=15,
            ).pack(side="left", padx=3, pady=2)

    _refrescar_botones()

    # ==================================================
    # BOTONES
    # ==================================================
    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(fill="x", padx=15, pady=(5, 15))

    resultado = {"eliminado": False}

    def _eliminar():
        archivos_txt = ""
        if adjuntos:
            archivos_txt = (
                f"\n\nSe eliminaran {len(adjuntos)} archivo(s):\n"
                + "\n".join(f"   - {a.name}" for a in adjuntos[:5])
            )
            if len(adjuntos) > 5:
                archivos_txt += f"\n   ... y {len(adjuntos) - 5} mas"

        msg = (
            f"Eliminar el registro de la factura {no_factura}?"
            f"{archivos_txt}\n\n"
            "Esta accion no se puede deshacer."
        )

        if not messagebox.askyesno("Confirmar eliminacion", msg, parent=ventana):
            return

        eliminados, errores = eliminar_archivos_de_registro(reg)

        try:
            carpeta = carpeta_de_registro(reg)
            if carpeta and carpeta.exists():
                eliminar_carpeta_si_vacia(reg)
        except Exception:
            pass

        resultado["eliminado"] = True

        partes = ["Registro eliminado."]
        if eliminados:
            partes.append(f"\nArchivos eliminados: {len(eliminados)}")
        if errores:
            partes.append(f"\nErrores: {len(errores)}")
        messagebox.showinfo("Eliminado", "\n".join(partes), parent=ventana)
        ventana.destroy()

    def _cerrar():
        ventana.destroy()

    ttk.Button(
        fr_btn, text="Eliminar registro",
        command=_eliminar,
        bootstyle="danger-outline",
    ).pack(side="right", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", _cerrar)
    ventana.bind("<Escape>", lambda e: _cerrar())

    ventana.wait_window()
    return resultado["eliminado"]


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