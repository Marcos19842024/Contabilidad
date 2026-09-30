# -*- coding: utf-8 -*-
"""
main.py
Punto de entrada del Sistema de Contabilidad QVET.
"""

from app.principal import AppPrincipal


if __name__ == "__main__":
    app = AppPrincipal()
    app.mainloop()