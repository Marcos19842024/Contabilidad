# -*- coding: utf-8 -*-
"""
main.py
Punto de entrada del Sistema de Contabilidad QVET.
"""

from app.principal import AppPrincipal
import sys

# DPI awareness en Windows
if sys.platform.startswith("win"):
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            windll.user32.SetProcessDPIAware()
        except Exception:
            pass

if __name__ == "__main__":
    app = AppPrincipal()
    app.mainloop()