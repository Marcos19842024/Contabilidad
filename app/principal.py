# -*- coding: utf-8 -*-
"""
app/principal.py
Pantalla de inicio de Vet Suite.

Layout:
  ┌──────────────────────┬──────────────────────────────┐
  │  🩺 Vet Suite        │                              │
  │  ────────────        │                              │
  │  Operación           │      (área del módulo        │
  │      Ingresos        │       embebido, o bien       │
  │      Egresos         │       pantalla de bienvenida)│
  │  Clientes            │                              │
  │  Comunicación        │                              │
  │                      │                              │
  │  ────────────        │                              │
  │  Configuración       │                              │
  │  Ayuda               │                              │
  │  v2.1.4              │                              │
  └──────────────────────┴──────────────────────────────┘
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

VERSION = "v2.1.4"

# Colores del sidebar (estilo QVET)
COLOR_SIDEBAR_BG       = "#2b2b2b"
COLOR_CATEGORIA_BG     = "#333333"
COLOR_CATEGORIA_HOVER  = "#3d3d3d"
COLOR_CATEGORIA_FG     = "#e0e0e0"
COLOR_MODULO_BG        = "#2b2b2b"
COLOR_MODULO_FG        = "#c8c8c8"
COLOR_MODULO_BG_HOVER  = "#3a3a3a"
COLOR_MODULO_BG_ACTIVO = "#f0a500"
COLOR_MODULO_FG_ACTIVO = "#1a1a1a"


class AppPrincipal(ttk.Window):
    """Pantalla de inicio del sistema."""

    def __init__(self):
        super().__init__(themename=obtener_tema())

        from config.temas import guardar_tema
        from config.veterinaria import obtener_veterinaria, guardar_veterinaria
        guardar_tema(obtener_tema())
        guardar_veterinaria(obtener_veterinaria())

        self.title("Vet Suite")
        self.geometry("1040x720")
        self.minsize(920, 620)

        # Estado del sidebar (acordeón)
        self._categorias_expandidas = {}
        self._widgets_categoria = {}

        # Estado del embed
        self._panel_activo = None
        self._modulo_activo = None

        self._construir_ui()
        self.after(50, self._centrar_ventana)

    # ============================================================
    # Construcción general
    # ============================================================

    def _construir_ui(self):
        raiz = ttk.Frame(self)
        raiz.pack(fill="both", expand=True)

        self._construir_sidebar(raiz)
        self._construir_contenido(raiz)

        # Primera categoría expandida por defecto
        grupos = modulos_por_categoria()
        if grupos:
            primera = next(iter(grupos))
            self._categorias_expandidas[primera] = True
            self._mostrar_hijos(primera, True)

        self._registrar_atajos()

    # ------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------

    def _construir_sidebar(self, padre):
        sidebar = tk.Frame(padre, bg=COLOR_SIDEBAR_BG, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # ---- Marca ----
        marca = tk.Frame(sidebar, bg=COLOR_SIDEBAR_BG)
        marca.pack(fill="x", pady=(18, 6), padx=16)

        tk.Label(
            marca, text="🩺 Vet Suite",
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_SIDEBAR_BG, fg="#ffffff",
        ).pack(anchor="w")

        tk.Label(
            marca, text="Panel de inicio",
            font=("Segoe UI", 9),
            bg=COLOR_SIDEBAR_BG, fg="#999999",
        ).pack(anchor="w")

        tk.Frame(sidebar, bg="#444444", height=1).pack(
            fill="x", padx=12, pady=(10, 10)
        )

        # ---- Navegación por categorías ----
        self._nav = tk.Frame(sidebar, bg=COLOR_SIDEBAR_BG)
        self._nav.pack(fill="x")

        for cat_id, modulos in modulos_por_categoria().items():
            self._crear_categoria_sidebar(self._nav, cat_id, modulos)

        # ---- Footer ----
        footer = tk.Frame(sidebar, bg=COLOR_SIDEBAR_BG)
        footer.pack(side="bottom", fill="x", padx=10, pady=(10, 14))

        tk.Frame(footer, bg="#444444", height=1).pack(fill="x", pady=(0, 10))

        self._crear_boton_footer(footer, "Configuración", self._abrir_configuracion)
        self._crear_boton_footer(footer, "Ayuda", self._abrir_ayuda)

        tk.Label(
            footer, text=VERSION,
            font=("Segoe UI", 8),
            bg=COLOR_SIDEBAR_BG, fg="#777777",
        ).pack(anchor="e", pady=(8, 0))

    def _crear_boton_footer(self, padre, texto, comando):
        """Botón plano para el pie del sidebar."""
        lbl = tk.Label(
            padre, text=texto, anchor="w",
            font=("Segoe UI", 10),
            bg=COLOR_SIDEBAR_BG, fg=COLOR_MODULO_FG,
            padx=12, pady=8, cursor="hand2",
        )
        lbl.pack(fill="x", pady=1)
        lbl.bind("<Button-1>", lambda _e: comando())
        lbl.bind("<Enter>", lambda _e: lbl.configure(bg=COLOR_MODULO_BG_HOVER))
        lbl.bind("<Leave>", lambda _e: lbl.configure(bg=COLOR_SIDEBAR_BG))

    def _crear_categoria_sidebar(self, padre, cat_id, modulos):
        """
        Crea [cabecera de categoría + contenedor de hijos].
        Solo texto, sin flecha ni icono.
        El contenedor se ancla justo debajo de su categoría usando
        pack(before=<siguiente_widget>) para que no se vaya al final.
        """
        etiqueta = CATEGORIAS.get(cat_id, {}).get("nombre", cat_id.title())

        # --- Cabecera de la categoría (solo texto) ---
        fila_cat = tk.Frame(padre, bg=COLOR_CATEGORIA_BG, cursor="hand2")
        fila_cat.pack(fill="x", pady=(4, 1))

        lbl_cat = tk.Label(
            fila_cat, text=etiqueta,
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_CATEGORIA_BG, fg=COLOR_CATEGORIA_FG,
            anchor="w", padx=14, pady=8,
        )
        lbl_cat.pack(fill="x")

        # --- Contenedor de hijos (se crea pero NO se empaca aún) ---
        cont_mods = tk.Frame(padre, bg=COLOR_SIDEBAR_BG)

        botones_mods = []
        for modulo in modulos:
            fila_mod = self._crear_fila_modulo(cont_mods, modulo)
            botones_mods.append(fila_mod)

        # Guardar referencias (incluye el widget "siguiente" para el before)
        self._widgets_categoria[cat_id] = {
            "fila_cat": fila_cat,
            "label": lbl_cat,
            "cont": cont_mods,
            "modulos": botones_mods,
            "etiqueta": etiqueta,
        }

        # Click en la cabecera → toggle
        for w in (fila_cat, lbl_cat):
            w.bind("<Button-1>", lambda _e, c=cat_id: self._toggle_categoria(c))
            w.bind("<Enter>", lambda _e, f=fila_cat, l=lbl_cat: (
                f.configure(bg=COLOR_CATEGORIA_HOVER),
                l.configure(bg=COLOR_CATEGORIA_HOVER),
            ))
            w.bind("<Leave>", lambda _e, f=fila_cat, l=lbl_cat: (
                f.configure(bg=COLOR_CATEGORIA_BG),
                l.configure(bg=COLOR_CATEGORIA_BG),
            ))

        # Estado inicial
        self._categorias_expandidas.setdefault(cat_id, False)

    def _crear_fila_modulo(self, padre, modulo):
        """Fila plana clickeable para un módulo. Solo texto."""
        fila = tk.Frame(padre, bg=COLOR_MODULO_BG, cursor="hand2")
        fila.pack(fill="x")

        # Margen izquierdo para indentar
        tk.Frame(fila, bg=COLOR_MODULO_BG, width=28).pack(side="left")

        lbl_texto = tk.Label(
            fila, text=modulo.nombre, font=("Segoe UI", 10),
            bg=COLOR_MODULO_BG, fg=COLOR_MODULO_FG, anchor="w",
        )
        lbl_texto.pack(side="left", fill="x", expand=True, padx=(8, 10), pady=7)

        widgets = {
            "fila": fila,
            "texto": lbl_texto,
            "modulo": modulo,
        }

        def _click(_e, m=modulo):
            self._abrir_modulo(m)

        def _enter(_e, w=widgets):
            if self._modulo_activo is None or self._modulo_activo.id != w["modulo"].id:
                w["fila"].configure(bg=COLOR_MODULO_BG_HOVER)
                w["texto"].configure(bg=COLOR_MODULO_BG_HOVER)

        def _leave(_e, w=widgets):
            if self._modulo_activo is None or self._modulo_activo.id != w["modulo"].id:
                w["fila"].configure(bg=COLOR_MODULO_BG)
                w["texto"].configure(bg=COLOR_MODULO_BG)

        for w in (fila, lbl_texto):
            w.bind("<Button-1>", _click)
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

        return widgets

    def _mostrar_hijos(self, cat_id, visible):
        """
        Muestra u oculta los hijos de una categoría.
        Al mostrarlos, los ancla JUSTO DEBAJO de su cabecera usando
        'before' el siguiente widget del nav.
        """
        info = self._widgets_categoria.get(cat_id)
        if not info:
            return

        cont = info["cont"]

        if visible:
            # Buscar el siguiente widget del nav después de esta categoría
            siguiente = self._siguiente_widget_nav(cat_id)
            if siguiente is not None:
                cont.pack(fill="x", before=siguiente)
            else:
                cont.pack(fill="x")
        else:
            cont.pack_forget()

        # Refrescar el color de la cabecera (activo/inactivo)
        self._actualizar_color_categoria(cat_id)

    def _siguiente_widget_nav(self, cat_id):
        """
        Devuelve el widget del nav que va inmediatamente después de la
        categoría 'cat_id' (o None si es la última).
        Sirve para anclar el contenedor de hijos justo debajo de su
        categoría con pack(before=...).
        """
        orden = list(self._widgets_categoria.keys())
        try:
            idx = orden.index(cat_id)
        except ValueError:
            return None
        if idx + 1 < len(orden):
            siguiente_cat = orden[idx + 1]
            return self._widgets_categoria[siguiente_cat]["fila_cat"]
        return None

    def _actualizar_color_categoria(self, cat_id):
        """Pinta la cabecera como activa si está expandida."""
        info = self._widgets_categoria.get(cat_id)
        if not info:
            return
        expandida = self._categorias_expandidas.get(cat_id, False)
        bg = COLOR_CATEGORIA_HOVER if expandida else COLOR_CATEGORIA_BG
        info["fila_cat"].configure(bg=bg)
        info["label"].configure(bg=bg)

    def _toggle_categoria(self, cat_id):
        """Expande o colapsa la lista de módulos de una categoría."""
        info = self._widgets_categoria.get(cat_id)
        if not info:
            return

        nuevo = not self._categorias_expandidas.get(cat_id, False)
        self._categorias_expandidas[cat_id] = nuevo

        self._mostrar_hijos(cat_id, nuevo)

    def _resaltar_modulo_activo(self, modulo_activo):
        """Marca con fondo amarillo el módulo activo."""
        try:
            for cat_id, info in self._widgets_categoria.items():
                for w in info["modulos"]:
                    m = w["modulo"]
                    activo = (modulo_activo is not None and m.id == modulo_activo.id)

                    if activo:
                        # Fondo amarillo + texto negro
                        w["fila"].configure(bg=COLOR_MODULO_BG_ACTIVO)
                        w["texto"].configure(
                            bg=COLOR_MODULO_BG_ACTIVO,
                            fg=COLOR_MODULO_FG_ACTIVO,
                        )
                    else:
                        # Fondo normal + texto gris claro
                        w["fila"].configure(bg=COLOR_MODULO_BG)
                        w["texto"].configure(
                            bg=COLOR_MODULO_BG,
                            fg=COLOR_MODULO_FG,
                        )
        except Exception as e:
            print(f"[_resaltar_modulo_activo] Error: {e}")

    # ------------------------------------------------------------
    # Área central
    # ------------------------------------------------------------
    def _construir_contenido(self, padre):
        cont = ttk.Frame(padre, padding=(28, 24, 28, 24))
        cont.pack(side="left", fill="both", expand=True)
        self._cont = cont

        self._barra_embed = ttk.Frame(cont)
        self._area_embed = ttk.Frame(cont)

        self._pantalla_inicio = ttk.Frame(cont)
        self._pantalla_inicio.pack(fill="both", expand=True)
        self._construir_pantalla_inicio()

    def _construir_pantalla_inicio(self):
        """Home: solo bienvenida. Sin tarjetas de módulos."""
        pantalla = self._pantalla_inicio

        ttk.Label(
            pantalla, text="🩺  Bienvenido a Vet Suite",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w", pady=(20, 4))

        ttk.Label(
            pantalla, text="Selecciona un módulo desde el menú lateral.",
            font=("Segoe UI", 11), foreground="gray",
        ).pack(anchor="w", pady=(0, 24))

    def _crear_acceso_rapido(self, padre, modulo, fila, columna):
        card = ttk.LabelFrame(padre, text="", padding=14)
        card.grid(row=fila, column=columna, padx=6, pady=6, sticky="nsew")
        card.configure(height=130)
        card.grid_propagate(False)

        ttk.Label(
            card, text=modulo.icono,
            font=("Segoe UI Emoji", 24),
        ).pack(anchor="w")

        ttk.Label(
            card, text=modulo.nombre,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(2, 0))

        ttk.Button(
            card, text="Abrir",
            bootstyle="info-outline",
            width=8,
            command=lambda m=modulo: self._abrir_modulo(m),
        ).pack(anchor="w", pady=(8, 0))

    # ============================================================
    # Abrir / cerrar módulos
    # ============================================================

    def _abrir_modulo(self, modulo):
        """Si el módulo declara 'panel', lo embebe. Si no, Toplevel."""
        # Asegurar categoría expandida
        for cat_id in self._widgets_categoria:
            if any(m.id == modulo.id for m in modulos_por_categoria()[cat_id]):
                if not self._categorias_expandidas.get(cat_id, False):
                    self._categorias_expandidas[cat_id] = True
                    self._mostrar_hijos(cat_id, True)
                break

        self._resaltar_modulo_activo(modulo)

        if modulo.panel is not None:
            self._abrir_embed(modulo)
        else:
            self._abrir_toplevel(modulo)

    def _abrir_toplevel(self, modulo):
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
        try:
            # ---- Limpiar panel anterior si existe ----
            if getattr(self, "_panel_activo", None) is not None:
                try:
                    self._panel_activo.destroy()
                except Exception:
                    pass
                self._panel_activo = None

            # Por si quedara algún widget residual en el área embed
            for w in self._area_embed.winfo_children():
                try:
                    w.destroy()
                except Exception:
                    pass

            # Ocultar pantalla de inicio
            self._pantalla_inicio.pack_forget()

            # Barra superior
            for w in self._barra_embed.winfo_children():
                w.destroy()

            # Botón "volver": solo la flecha
            ttk.Button(
                self._barra_embed,
                text="←",
                bootstyle="link",
                width=3,
                command=self._cerrar_embed,
            ).pack(side="left")

            ttk.Label(
                self._barra_embed,
                text=f"{modulo.icono}  {modulo.nombre}",
                font=("Segoe UI", 13, "bold"),
            ).pack(side="left", padx=(14, 0))

            self._barra_embed.pack(fill="x", pady=(0, 10))
            self._area_embed.pack(fill="both", expand=True)

            # Crear panel nuevo
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
        try:
            if getattr(self, "_panel_activo", None) is not None:
                self._panel_activo.destroy()
                self._panel_activo = None
            self._modulo_activo = None
        except Exception:
            pass

        self._barra_embed.pack_forget()
        self._area_embed.pack_forget()
        self._pantalla_inicio.pack(fill="both", expand=True)

        self._resaltar_modulo_activo(None)

    def _cerrar_modulo(self, app):
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
        ancho = 1040
        alto = 720
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")