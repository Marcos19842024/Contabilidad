# -*- coding: utf-8 -*-
"""
app/principal.py
Pantalla de inicio de Vet Suite.

Layout:
  ┌──────────────┬────────────────────────────────────┐
  │  SIDEBAR     │  HEADER (categoría activa)         │
  │  ─────────   │  ────────────────────────────────  │
  │  Operación   │  Lista de módulos (filas)          │
  │   💰 Ingr.   │                                    │
  │   💸 Egr.    │                                    │
  │  Clientes    │                                    │
  │   🐾 Estét.  │  ← o, si es embed:                 │
  │  Comunicac.  │    [← Volver] Nombre               │
  │   📅 Record. │    ┌───────────────────────┐       │
  │              │    │ Panel del módulo      │       │
  │  ─────────   │    └───────────────────────┘       │
  │  ⚙ Config    │                                    │
  │  📖 Ayuda    │                                    │
  │  v2.1.3      │                                    │
  └──────────────┴────────────────────────────────────┘
"""

import sys
from pathlib import Path

_raiz = Path(__file__).parent.parent
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox

from config.temas import obtener_tema
from shared.registro_modulos import (
    modulos_por_categoria,
    modulos_activos,
    CATEGORIAS,
)

VERSION = "v2.1.3"


class AppPrincipal(ttk.Window):
    """Pantalla de inicio del sistema."""

    def __init__(self):
        super().__init__(themename=obtener_tema())
        from config.temas import guardar_tema
        from config.veterinaria import obtener_veterinaria, guardar_veterinaria
        guardar_tema(obtener_tema())
        guardar_veterinaria(obtener_veterinaria())

        self.title("Vet Suite")
        self.geometry("980x720")
        self.minsize(880, 620)

        self._categoria_activa = None
        self._botones_sidebar = {}

        # Estado del embed
        self._panel_activo = None
        self._modulo_activo = None

        self._construir_ui()
        self.after(50, self._centrar_ventana)

    # ============================================================
    # Construcción
    # ============================================================

    def _construir_ui(self):
        raiz = ttk.Frame(self)
        raiz.pack(fill="both", expand=True)

        self._construir_sidebar(raiz)
        self._construir_contenido(raiz)

        grupos = modulos_por_categoria()
        if grupos:
            self._mostrar_categoria(next(iter(grupos)))

        self._registrar_atajos()

    # ------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------
    def _construir_sidebar(self, padre):
        sidebar = ttk.Frame(padre, width=230, bootstyle="dark")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        marca = ttk.Frame(sidebar, bootstyle="dark")
        marca.pack(fill="x", pady=(18, 6), padx=16)

        ttk.Label(
            marca, text="🩺 Vet Suite",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-dark",
        ).pack(anchor="w")

        ttk.Label(
            marca, text="Panel de inicio",
            font=("Segoe UI", 9),
            bootstyle="inverse-dark",
        ).pack(anchor="w")

        ttk.Separator(sidebar, orient="horizontal").pack(
            fill="x", padx=12, pady=(10, 12)
        )

        nav = ttk.Frame(sidebar, bootstyle="dark")
        nav.pack(fill="x")

        for cat_id, modulos in modulos_por_categoria().items():
            etiqueta = CATEGORIAS.get(cat_id, {}).get("nombre", cat_id.title())
            icono = self._icono_categoria(cat_id)
            btn = ttk.Button(
                nav,
                text=f"  {icono}  {etiqueta}",
                bootstyle="dark",
                width=22,
                command=lambda c=cat_id: self._mostrar_categoria(c),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._botones_sidebar[cat_id] = btn

        footer = ttk.Frame(sidebar, bootstyle="dark")
        footer.pack(side="bottom", fill="x", padx=10, pady=(10, 14))

        ttk.Separator(footer, orient="horizontal").pack(fill="x", pady=(0, 10))

        ttk.Button(
            footer, text="  ⚙️  Configuración",
            bootstyle="secondary-outline",
            width=22,
            command=self._abrir_configuracion,
        ).pack(fill="x", pady=2)

        ttk.Button(
            footer, text="  📖  Ayuda",
            bootstyle="secondary-outline",
            width=22,
            command=self._abrir_ayuda,
        ).pack(fill="x", pady=2)

        ttk.Label(
            footer, text=VERSION,
            font=("Segoe UI", 8),
            bootstyle="inverse-dark",
        ).pack(anchor="e", pady=(8, 0))

    def _icono_categoria(self, cat_id):
        return {
            "operacion": "💼",
            "clientes": "🐾",
            "comunicacion": "💬",
            "reportes": "📊",
            "admin": "⚙️",
        }.get(cat_id, "•")

    # ------------------------------------------------------------
    # Contenido central
    # ------------------------------------------------------------
    def _construir_contenido(self, padre):
        cont = ttk.Frame(padre, padding=(28, 24, 28, 24))
        cont.pack(side="left", fill="both", expand=True)
        self._cont = cont

        header = ttk.Frame(cont)
        header.pack(fill="x", pady=(0, 16))

        self._lbl_titulo = ttk.Label(
            header, text="", font=("Segoe UI", 20, "bold"),
        )
        self._lbl_titulo.pack(anchor="w")

        self._lbl_subtitulo = ttk.Label(
            header, text="", font=("Segoe UI", 10), foreground="gray",
        )
        self._lbl_subtitulo.pack(anchor="w", pady=(2, 0))

        ttk.Separator(cont, orient="horizontal").pack(fill="x", pady=(0, 14))

        # Lista de módulos
        self._lista = ttk.Frame(cont)
        self._lista.pack(fill="both", expand=True)

        # Barra del embed (oculta hasta usarse)
        self._barra_embed = ttk.Frame(cont)

        # Área del embed (oculta hasta usarse)
        self._area_embed = ttk.Frame(cont)

    def _limpiar_lista(self):
        for w in self._lista.winfo_children():
            w.destroy()

    def _mostrar_categoria(self, cat_id):
        # Si estamos en embed, salir primero
        if self._panel_activo is not None:
            self._cerrar_embed()

        self._categoria_activa = cat_id

        for cid, btn in self._botones_sidebar.items():
            btn.configure(bootstyle="info" if cid == cat_id else "dark")

        grupos = modulos_por_categoria()
        modulos = grupos.get(cat_id, [])

        etiqueta = CATEGORIAS.get(cat_id, {}).get("nombre", cat_id.title())
        self._lbl_titulo.configure(text=etiqueta)
        n = len(modulos)
        self._lbl_subtitulo.configure(
            text=f"{n} módulo{'s' if n != 1 else ''}"
        )

        self._renderizar_lista(modulos)

    def _renderizar_lista(self, modulos):
        self._limpiar_lista()

        for modulo in modulos:
            self._crear_fila_modulo(modulo)

    def _crear_fila_modulo(self, modulo):
        """Fila compacta: icono | nombre+desc | atajo | botón."""
        fila = ttk.Frame(self._lista, padding=(12, 10))
        fila.pack(fill="x", pady=4)

        sep = ttk.Separator(self._lista, orient="horizontal")
        sep.pack(fill="x")

        ttk.Label(
            fila, text=modulo.icono,
            font=("Segoe UI Emoji", 22),
            width=3,
            anchor="center",
        ).pack(side="left", padx=(4, 12))

        bloque = ttk.Frame(fila)
        bloque.pack(side="left", fill="x", expand=True)

        ttk.Label(
            bloque, text=modulo.nombre,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            bloque, text=modulo.descripcion.replace("\n", " "),
            font=("Segoe UI", 9),
            foreground="gray",
        ).pack(anchor="w")

        if modulo.atajo:
            atajo_legible = (
                modulo.atajo
                .replace("Control-Key-", "Ctrl+")
                .replace("Control-", "Ctrl+")
            )
            ttk.Label(
                fila, text=atajo_legible,
                font=("Consolas", 9),
                foreground="gray",
            ).pack(side="right", padx=(0, 14))

        ttk.Button(
            fila, text="Abrir",
            bootstyle="info",
            width=9,
            command=lambda m=modulo: self._abrir_modulo(m),
        ).pack(side="right")

    # ============================================================
    # Abrir / cerrar módulos
    # ============================================================

    def _abrir_modulo(self, modulo):
        """Si el módulo declara 'panel', lo embebe. Si no, Toplevel."""
        if modulo.panel is not None:
            self._abrir_embed(modulo)
        else:
            self._abrir_toplevel(modulo)

    def _abrir_toplevel(self, modulo):
        """Abre el módulo como ventana independiente (legacy)."""
        try:
            app = modulo.factory(master=self)
            if app is None:
                return
            app.protocol(
                "WM_DELETE_WINDOW",
                lambda a=app: self._cerrar_modulo(a),
            )
            app.lift()
            app.focus_force()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir {modulo.nombre}:\n{e}",
            )

    def _abrir_embed(self, modulo):
        """Embebe el panel del módulo en el área central."""
        try:
            # Ocultar lista, mostrar barra + área embed
            self._lista.pack_forget()

            # Barra superior con "Volver"
            for w in self._barra_embed.winfo_children():
                w.destroy()

            ttk.Button(
                self._barra_embed,
                text="←  Volver al inicio",
                bootstyle="secondary-outline",
                command=self._cerrar_embed,
            ).pack(side="left")

            ttk.Label(
                self._barra_embed,
                text=f"{modulo.icono}  {modulo.nombre}",
                font=("Segoe UI", 13, "bold"),
            ).pack(side="left", padx=(14, 0))

            self._barra_embed.pack(fill="x", pady=(0, 10))
            self._area_embed.pack(fill="both", expand=True)

            # Instanciar el panel
            self._panel_activo = modulo.panel(
                master=self._area_embed,
                on_volver=self._cerrar_embed,
            )
            self._panel_activo.pack(fill="both", expand=True)
            self._modulo_activo = modulo

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir {modulo.nombre} embebido:\n{e}",
            )
            self._cerrar_embed()

    def _cerrar_embed(self):
        """Cierra el panel embebido y vuelve a la lista."""
        try:
            if getattr(self, "_panel_activo", None) is not None:
                self._panel_activo.destroy()
                self._panel_activo = None
            self._modulo_activo = None
        except Exception:
            pass

        self._barra_embed.pack_forget()
        self._area_embed.pack_forget()
        self._lista.pack(fill="both", expand=True)

        if self._categoria_activa:
            self._mostrar_categoria(self._categoria_activa)

    def _cerrar_modulo(self, app):
        """Cierra un Toplevel legacy."""
        try:
            app.destroy()
        except Exception:
            pass
        self.lift()
        self.focus_force()

    def _registrar_atajos(self):
        for m in modulos_activos():
            if not m.atajo:
                continue
            self.bind_all(
                f"<{m.atajo}>",
                lambda _e, mod=m: self._abrir_modulo(mod),
            )

    # ============================================================
    # Configuración y Ayuda
    # ============================================================

    def _abrir_configuracion(self):
        try:
            from dialogos.config_general import abrir_dialogo_config_general
            abrir_dialogo_config_general(self)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la configuración:\n{e}",
            )

    def _abrir_ayuda(self):
        try:
            from dialogos.manual import abrir_manual
            abrir_manual(self)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el manual:\n{e}",
            )

    def _centrar_ventana(self):
        self.update_idletasks()
        ancho = 980
        alto = 720
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")