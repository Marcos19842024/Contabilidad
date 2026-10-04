# -*- coding: utf-8 -*-
"""
app/principal.py
Pantalla de inicio del Sistema de Contabilidad QVET.
Permite elegir entre:
  - Reporte de Ingresos
  - Reporte de Egresos (próximamente)
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
        self.title("Sistema de Contabilidad")
        self.geometry("800x600")
        self.minsize(700, 500)

        self._construir_ui()
        self.after(50, self._centrar_ventana)

    def _construir_ui(self):
        """Construye la pantalla de inicio."""
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)

        # ---- Encabezado ----
        ttk.Label(
            frame,
            text="📊 Sistema de Contabilidad",
            font=("Segoe UI", 24, "bold"),
            bootstyle="info"
        ).pack(pady=(20, 10))

        ttk.Label(
            frame,
            text="¿Qué quieres hacer hoy?",
            font=("Segoe UI", 14),
            foreground="gray"
        ).pack(pady=(0, 40))

        # ---- Botones ----
        botones_frame = ttk.Frame(frame)
        botones_frame.pack(expand=True)

        botones_frame.columnconfigure(0, weight=1)
        botones_frame.columnconfigure(1, weight=1)

        self._crear_boton_modulo(
            botones_frame,
            icono="💰",
            titulo="INGRESOS",
            descripcion="Facturas de venta\n(descarga del Qvet o Gmail)",
            comando=self._abrir_ingresos,
            habilitado=True,
            columna=0
        )

        self._crear_boton_modulo(
            botones_frame,
            icono="💸",
            titulo="EGRESOS",
            descripcion="Facturas de compra\n(descarga del SAT)",
            comando=self._abrir_egresos,
            habilitado=True,
            columna=1
        )

        # ---- Pie ----
        pie = ttk.Frame(frame)
        pie.pack(side="bottom", fill="x", pady=(40, 0))

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

        ttk.Button(
            pie,
            text="❌ Salir",
            command=self.destroy,
            bootstyle="danger-outline"
        ).pack(side="right", padx=5)

        ttk.Label(
            pie,
            text="v1.0.1",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(side="right", padx=10)

    def _crear_boton_modulo(self, parent, icono, titulo, descripcion,
                            comando, habilitado=True, columna=0):
        """Crea un botón grande para un módulo."""
        frame = ttk.LabelFrame(parent, text="", padding=20)
        frame.grid(row=0, column=columna, padx=20, pady=10, sticky="nsew")

        ttk.Label(
            frame,
            text=icono,
            font=("Segoe UI Emoji", 48)
        ).pack(pady=(0, 10))

        ttk.Label(
            frame,
            text=titulo,
            font=("Segoe UI", 18, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            frame,
            text=descripcion,
            font=("Segoe UI", 11),
            justify="center",
            foreground="gray"
        ).pack(pady=(0, 20))

        if habilitado:
            ttk.Button(
                frame,
                text="Abrir",
                command=comando,
                bootstyle="info",
                width=15
            ).pack()
        else:
            ttk.Button(
                frame,
                text="Próximamente",
                state="disabled",
                bootstyle="secondary",
                width=15
            ).pack()

    def _abrir_ingresos(self):
        """Abre el módulo de Ingresos."""
        try:
            from modulos.ingresos import AppIngresos
            app = AppIngresos(master=self)
            app.protocol("WM_DELETE_WINDOW", lambda: self._cerrar_modulo(app))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Ingresos:\n{e}")

    def _abrir_egresos(self):
        """Abre el módulo de Egresos."""
        try:
            from modulos.egresos import AppEgresos
            app = AppEgresos(master=self)
            app.protocol("WM_DELETE_WINDOW", lambda: self._cerrar_modulo(app))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Egresos:\n{e}")

    def _abrir_configuracion(self):
        """Abre el diálogo de configuración general."""
        try:
            from dialogos.config_general import abrir_dialogo_config_general
            abrir_dialogo_config_general(self)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la configuración:\n{e}"
            )

    def _abrir_ayuda(self):
        """Abre el manual de usuario."""
        try:
            from dialogos.manual import abrir_manual
            abrir_manual(self)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el manual:\n{e}"
            )

    def _cerrar_modulo(self, app):
        """Se llama al cerrar un módulo. Vuelve a mostrar la pantalla de inicio."""
        try:
            app.destroy()
        except Exception:
            pass
        self.deiconify()

    def _centrar_ventana(self):
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        ancho = 800
        alto = 600
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")