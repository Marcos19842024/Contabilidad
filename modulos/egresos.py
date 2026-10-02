# -*- coding: utf-8 -*-
"""
modulos/egresos.py
Módulo de Egresos.
"""

from ui.utils import configurar_ventana
import sys
from pathlib import Path

_raiz = Path(__file__).parent.parent
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox


class AppEgresos(ttk.Toplevel):
    """Módulo de Egresos."""

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Sistema de Egresos - Contabilidad")

        # Configurar tamaño y centrar
        configurar_ventana(
            master, self,
            ancho=1250, alto=880,
            min_ancho=1000, min_alto=700,
            centrar_en_padre=True
        )

        self._construir_ui()

    def _construir_ui(self):
        """Construye la UI básica."""
        # Barra superior
        top = ttk.LabelFrame(self, text="Configuración", padding=10)
        top.pack(fill="x", padx=10, pady=5)

        # Centro / Sucursal
        ttk.Label(top, text="Sucursal:").grid(row=0, column=0, padx=5, sticky="e")
        self.var_sucursal = ttk.StringVar(value="Baalak")
        ttk.Combobox(
            top, textvariable=self.var_sucursal,
            values=["Baalak", "Animalia"],
            width=12, state="readonly", bootstyle="primary"
        ).grid(row=0, column=1, padx=5)

        # Año
        ttk.Label(top, text="Año:").grid(row=0, column=2, padx=5, sticky="e")
        from datetime import datetime
        self.var_anio = ttk.StringVar(value=str(datetime.now().year))
        ttk.Entry(top, textvariable=self.var_anio, width=6,
                  style="Custom.TEntry").grid(row=0, column=3, padx=5)

        # Mes
        from config.campos import MESES_ES
        ttk.Label(top, text="Mes:").grid(row=0, column=4, padx=5, sticky="e")
        self.var_mes = ttk.StringVar(value=MESES_ES[datetime.now().month - 1])
        ttk.Combobox(top, textvariable=self.var_mes, values=MESES_ES,
                     width=11, state="readonly", bootstyle="primary").grid(
            row=0, column=5, padx=5)

        # Botones
        ttk.Button(top, text="⚙️ Configuración SAT",
                   command=self._abrir_configuracion,
                   bootstyle="info-outline").grid(row=0, column=7, padx=10)

        ttk.Button(top, text="📥 Descargar del SAT",
                   command=self._descargar_sat,
                   bootstyle="info-outline").grid(row=0, column=8, padx=10)

        # Contenido principal
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="💸 Módulo de Egresos",
            font=("Segoe UI", 24, "bold"),
            bootstyle="info"
        ).pack(pady=(40, 20))

        ttk.Label(
            frame,
            text="Próximamente disponible",
            font=("Segoe UI", 14),
            foreground="gray"
        ).pack(pady=(0, 40))

        ttk.Label(
            frame,
            text=(
                "Este módulo permitirá:\n\n"
                "• Descargar facturas de compra del SAT.\n"
                "• Procesar los XML automáticamente.\n"
                "• Separar facturas por sucursal (Animalia / Baalak).\n"
                "• Generar el reporte de egresos en Excel (PUE y PPD)."
            ),
            font=("Segoe UI", 11),
            justify="left"
        ).pack(pady=20)

    def _abrir_configuracion(self):
        """Abre el diálogo de configuración de Egresos."""
        from dialogos.egresos_config import abrir_dialogo_config_egresos
        abrir_dialogo_config_egresos(self)

    def _descargar_sat(self):
        """Inicia el flujo de descarga del SAT (próximamente)."""
        messagebox.showinfo(
            "Próximamente",
            "La descarga del SAT estará disponible en una futura versión."
        )


if __name__ == "__main__":
    import ttkbootstrap as ttk_local
    from config.ajustes import TEMA

    raiz = ttk_local.Window(themename=TEMA)
    raiz.withdraw()
    app = AppEgresos(master=raiz)
    app.protocol("WM_DELETE_WINDOW", raiz.destroy)
    raiz.mainloop()