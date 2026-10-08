# -*- coding: utf-8 -*-
"""
app/principal.py
Pantalla de inicio del Sistema de Contabilidad QVET.
Permite elegir entre:
  - Reporte de Ingresos
  - Reporte de Egresos
  - Estética y Transportes
  - Recordatorios
"""

import sys
from pathlib import Path

# Agregar la raíz del proyecto al path
_raiz = Path(__file__).parent.parent
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from config.ajustes import TEMA


class AppPrincipal(ttk.Window):
    """Pantalla de inicio del sistema."""

    def __init__(self):
        super().__init__(themename=TEMA)
        self.title("Vet Suite")
        self.geometry("720x820")
        self.minsize(680, 760)

        self._construir_ui()
        self.after(50, self._centrar_ventana)

    def _construir_ui(self):
        """Construye la pantalla de inicio."""
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        # ---- Encabezado ----
        ttk.Label(
            frame,
            text="🩺 Vet Suite",
            font=("Segoe UI", 24, "bold"),
            bootstyle="info"
        ).pack(pady=(10, 8))

        ttk.Label(
            frame,
            text="¿Qué quieres hacer hoy?",
            font=("Segoe UI", 13),
            foreground="gray"
        ).pack(pady=(0, 25))

        # ---- Botones en grid 2x2 ----
        botones_frame = ttk.Frame(frame)
        botones_frame.pack(expand=True)

        botones_frame.columnconfigure(0, weight=1)
        botones_frame.columnconfigure(1, weight=1)
        botones_frame.rowconfigure(0, weight=1)
        botones_frame.rowconfigure(1, weight=1)

        self._crear_boton_modulo(
            botones_frame,
            icono="💰",
            titulo="INGRESOS",
            descripcion="Facturas de venta\n(descarga del Qvet o Gmail)",
            comando=self._abrir_ingresos,
            habilitado=True,
            fila=0, columna=0
        )

        self._crear_boton_modulo(
            botones_frame,
            icono="💸",
            titulo="EGRESOS",
            descripcion="Facturas de compra\n(descarga del SAT)",
            comando=self._abrir_egresos,
            habilitado=True,
            fila=0, columna=1
        )

        self._crear_boton_modulo(
            botones_frame,
            icono="🐾",
            titulo="ESTÉTICA\nTRANSPORTES",
            descripcion="Clientes, mascotas,\nrutas y tarifas",
            comando=self._abrir_estetica_transportes,
            habilitado=True,
            fila=1, columna=0
        )

        self._crear_boton_modulo(
            botones_frame,
            icono="📅",
            titulo="RECORDATORIOS",
            descripcion="Citas y vacunas\npor WhatsApp",
            comando=self._abrir_recordatorios,
            habilitado=True,
            fila=1, columna=1
        )

        # ---- Pie ----
        pie = ttk.Frame(frame)
        pie.pack(side="bottom", fill="x", pady=(15, 0))

        ttk.Button(
            pie,
            text="⚙️ Configuración",
            command=self._abrir_configuracion,
            bootstyle="secondary-outline"
        ).pack(side="left", padx=5)

        ttk.Button(
            pie,
            text="📖 Ayuda",
            command=self._abrir_ayuda,
            bootstyle="secondary-outline"
        ).pack(side="left", padx=5)

        ttk.Label(
            pie,
            text="v2.0.0",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(side="right", padx=10)

    def _crear_boton_modulo(self, parent, icono, titulo, descripcion,
                            comando, habilitado=True, fila=0, columna=0):
        """
        Crea un botón grande para un módulo.
        Tamaño fijo 280x260 en grid 2x2.
        """
        frame = ttk.LabelFrame(parent, text="", padding=20,
                               width=280, height=260)
        frame.grid(row=fila, column=columna, padx=10, pady=10, sticky="nsew")
        frame.grid_propagate(False)

        contenedor = ttk.Frame(frame)
        contenedor.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(
            contenedor,
            text=icono,
            font=("Segoe UI Emoji", 42)
        ).pack(pady=(0, 8))

        ttk.Label(
            contenedor,
            text=titulo,
            font=("Segoe UI", 15, "bold"),
            justify="center",
            anchor="center"
        ).pack(pady=(0, 8))

        ttk.Label(
            contenedor,
            text=descripcion,
            font=("Segoe UI", 10),
            justify="center",
            foreground="gray",
            anchor="center"
        ).pack(pady=(0, 14))

        if habilitado:
            ttk.Button(
                contenedor,
                text="Abrir",
                command=comando,
                bootstyle="info",
                width=14
            ).pack()
        else:
            ttk.Button(
                contenedor,
                text="Próximamente",
                state="disabled",
                bootstyle="secondary",
                width=14
            ).pack()

    # ============================================================
    # Abrir módulos
    # ============================================================

    def _abrir_ingresos(self):
        try:
            from modulos.ingresos import AppIngresos
            app = AppIngresos(master=self)
            app.protocol("WM_DELETE_WINDOW", lambda: self._cerrar_modulo(app))
            app.lift()
            app.focus_force()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Ingresos:\n{e}")

    def _abrir_egresos(self):
        try:
            from modulos.egresos import AppEgresos
            app = AppEgresos(master=self)
            app.protocol("WM_DELETE_WINDOW", lambda: self._cerrar_modulo(app))
            app.lift()
            app.focus_force()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Egresos:\n{e}")

    def _abrir_estetica_transportes(self):
        try:
            from modulos.estetica_transportes import AppEsteticaTransportes
            app = AppEsteticaTransportes(master=self)
            app.protocol("WM_DELETE_WINDOW", lambda: self._cerrar_modulo(app))
            app.lift()
            app.focus_force()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir Estética y Transportes:\n{e}"
            )

    def _abrir_recordatorios(self):
        try:
            from modulos.recordatorios import AppRecordatorios
            app = AppRecordatorios(master=self)
            app.protocol("WM_DELETE_WINDOW", lambda: self._cerrar_modulo(app))
            app.lift()
            app.focus_force()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir Recordatorios:\n{e}"
            )

    def _cerrar_modulo(self, app):
        try:
            app.destroy()
        except Exception:
            pass
        self.lift()
        self.focus_force()

    def _abrir_configuracion(self):
        try:
            from dialogos.config_general import abrir_dialogo_config_general
            abrir_dialogo_config_general(self)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la configuración:\n{e}"
            )

    def _abrir_ayuda(self):
        try:
            from dialogos.manual import abrir_manual
            abrir_manual(self)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el manual:\n{e}"
            )

    def _centrar_ventana(self):
        self.update_idletasks()
        ancho = 720
        alto = 820
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")