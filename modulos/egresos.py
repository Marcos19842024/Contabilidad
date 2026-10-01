# -*- coding: utf-8 -*-
"""
modulos/egresos.py
Módulo de Egresos.

Permite:
  - Descargar facturas de compra del SAT.
  - Procesar los XML automáticamente.
  - Generar el reporte de egresos en Excel (PUE y PPD).
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


class AppEgresos(ttk.Toplevel):
    """Módulo de Egresos."""

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Sistema de Egresos - Contabilidad")
        self.geometry("1250x880")
        self.minsize(1000, 700)

        self._construir_ui()

    def _construir_ui(self):
        """Construye la UI básica."""
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


if __name__ == "__main__":
    import ttkbootstrap as ttk_local
    from config.ajustes import TEMA

    raiz = ttk_local.Window(themename=TEMA)
    raiz.withdraw()
    app = AppEgresos(master=raiz)
    app.protocol("WM_DELETE_WINDOW", raiz.destroy)
    raiz.mainloop()