# -*- coding: utf-8 -*-
"""
main.py
Punto de entrada de Vet Suite.

Flujo:
  1. DPI awareness (Windows).
  2. Crear AppPrincipal (oculta de inmediato).
  3. Mostrar login modal. Bootstrap de admin si es el primer arranque.
  4. Si no hay sesión al cerrar el login → salir limpio.
  5. Reconstruir sidebar con la sesión activa.
  6. Mostrar la ventana y entrar al mainloop.
"""

import sys

# DPI awareness en Windows — DEBE ir antes de crear cualquier Tk()
if sys.platform.startswith("win"):
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    from app.principal import AppPrincipal
    from dialogos.login import mostrar_login

    # 1. Crear la ventana principal y ocultarla de inmediato.
    #    Así el login aparece como diálogo modal sobre una raíz ya lista.
    app = AppPrincipal()
    app.withdraw()

    # 2. Login (o bootstrap de primer arranque).
    if not mostrar_login(app):
        # El usuario canceló: cerramos sin arrancar la UI.
        try:
            app.destroy()
        except Exception:
            pass
        sys.exit(0)

    # 3. Reconstruir sidebar con la sesión activa.
    #    En Fase 1, AppPrincipal construye el sidebar vacío porque
    #    modulos_visibles() exige sesión. Ahora que hay una, lo
    #    volvemos a construir.
    try:
        app._reconstruir_sidebar()
    except Exception as e:
        # Fallback: si falla, al menos avisamos por consola y seguimos.
        print(f"[main] No se pudo reconstruir el sidebar: {e}", file=sys.stderr)

    # 4. Mostrar la ventana y entrar al mainloop.
    app.deiconify()
    app.lift()
    app.focus_force()
    app.mainloop()


if __name__ == "__main__":
    main()