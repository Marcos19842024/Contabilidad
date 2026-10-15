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
  │  v2.2.0              │                              │
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
from core import sesion
from shared.perfiles import perfil_por_id
from shared.registro_modulos import (
    modulos_por_categoria,
    modulos_visibles,
    CATEGORIAS,
)

VERSION = "v2.2.0"

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

        # Flag de cierre limpio
        self._app_cerrando = False

        self._construir_ui()
        self.protocol("WM_DELETE_WINDOW", self._cerrar_app)
        self.report_callback_exception = self._reportar_excepcion
        self.after(50, self._centrar_ventana)

    # ============================================================
    # Manejo global de excepciones
    # ============================================================

    def _reportar_excepcion(self, exc_type, exc_value, tb):
        """
        Manejador global de excepciones en callbacks de Tk.
        Ignora TclError por widgets destruidos (típico al cerrar ventanas).
        """
        import traceback
        from tkinter import TclError

        # Errores benignos de widgets destruidos: silencio total.
        if exc_type is TclError:
            msg = str(exc_value)
            if ("invalid command name" in msg
                    or "bad window path name" in msg
                    or "application has been destroyed" in msg):
                return

        # Cualquier otro: imprimir traceback y mostrar mensaje estándar.
        traceback.print_exception(exc_type, exc_value, tb)
        try:
            if not self._sigue_viva():
                return
            messagebox.showerror(
                "Error inesperado",
                f"{exc_type.__name__}: {exc_value}",
                parent=self,
            )
        except Exception:
            pass

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

        # ---- Bloque de sesión (arriba, junto a la marca) ----
        self._bloque_sesion = tk.Frame(sidebar, bg=COLOR_SIDEBAR_BG)
        self._bloque_sesion.pack(fill="x", padx=16, pady=(10, 6))
        self._actualizar_bloque_sesion()

        tk.Frame(sidebar, bg="#444444", height=1).pack(
            fill="x", padx=12, pady=(4, 10)
        )

        # ---- Navegación por categorías ----
        self._nav = tk.Frame(sidebar, bg=COLOR_SIDEBAR_BG)
        self._nav.pack(fill="x")

        for cat_id, modulos in modulos_por_categoria().items():
            self._crear_categoria_sidebar(self._nav, cat_id, modulos)

        # ---- Footer ----
        footer = tk.Frame(sidebar, bg=COLOR_SIDEBAR_BG)
        footer.pack(side="bottom", fill="x", padx=10, pady=(10, 14))
        self._footer = footer

        tk.Frame(footer, bg="#444444", height=1).pack(fill="x", pady=(0, 10))

        # Acciones del usuario: Configuración/Mi cuenta · Ayuda · Cerrar sesión
        texto_config = ("Configuración" if sesion.es_admin() else "Mi cuenta")
        self._lbl_config = self._crear_boton_footer(
            footer, texto_config, self._abrir_configuracion
        )
        self._lbl_ayuda = self._crear_boton_footer(
            footer, "Ayuda", self._abrir_ayuda
        )
        self._crear_boton_footer(footer, "🚪 Cerrar sesión",
                                  self._cerrar_sesion)

        # Versión al pie
        tk.Label(
            footer, text=VERSION,
            font=("Segoe UI", 8),
            bg=COLOR_SIDEBAR_BG, fg="#777777",
        ).pack(anchor="e", pady=(10, 0))

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
        return lbl

    def _actualizar_bloque_sesion(self):
        """
        Rellena el bloque de sesión de arriba con el usuario actual.
        Se llama al construir el sidebar y tras cada login.
        Solo muestra información: las acciones (Configuración / Mi cuenta,
        Ayuda, Cerrar sesión) viven en el footer.
        """
        bloque = self._bloque_sesion
        for w in bloque.winfo_children():
            w.destroy()

        s = sesion.actual()
        if s is None:
            return

        perfil = perfil_por_id(s.perfil_id)
        perfil_nombre = perfil.nombre if perfil else s.perfil_id
        primer_nombre = s.nombre.split()[0] if s.nombre.split() else s.nombre

        tk.Label(
            bloque,
            text=f"👤 {primer_nombre} ({perfil_nombre})",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_SIDEBAR_BG, fg="#e0e0e0",
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            bloque, text="Panel de inicio",
            font=("Segoe UI", 10),
            bg=COLOR_SIDEBAR_BG, fg="#999999",
        ).pack(anchor="w")

    def _cerrar_sesion(self):
        """
        Cierra la sesión activa y vuelve al login sin reiniciar el proceso.
        Si el usuario cancela el login, la app se cierra.
        """
        self._cerrar_embed()
        sesion.cerrar_sesion()

        self.withdraw()
        try:
            from dialogos.login import mostrar_login
            ok = mostrar_login(self)
        except Exception as e:
            if not self._sigue_viva():
                return
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el login:\n{e}",
                parent=self,
            )
            ok = False

        if not ok:
            try:
                self.destroy()
            except Exception:
                pass
            return

        # Si la app se destruyó durante el login, no seguimos.
        if not self._sigue_viva():
            return

        try:
            self._reconstruir_sidebar()
            self._verificar_modulo_activo()
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception as e:
            print(f"[_cerrar_sesion] Error al reconstruir: {e}",
                  file=sys.stderr)

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
            siguiente = self._siguiente_widget_nav(cat_id)
            if siguiente is not None:
                cont.pack(fill="x", before=siguiente)
            else:
                cont.pack(fill="x")
        else:
            cont.pack_forget()

        self._actualizar_color_categoria(cat_id)

    def _siguiente_widget_nav(self, cat_id):
        """
        Devuelve el widget del nav que va inmediatamente después de la
        categoría 'cat_id' (o None si es la última).
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

    def _reconstruir_sidebar(self):
        """
        Vuelve a construir el sidebar desde cero con el estado actual
        de config_ui.json. Preserva qué categorías estaban expandidas.
        """
        expandidas_previas = dict(self._categorias_expandidas)

        for w in self._nav.winfo_children():
            w.destroy()
        self._widgets_categoria = {}
        self._categorias_expandidas = {}

        for cat_id, modulos in modulos_por_categoria().items():
            self._crear_categoria_sidebar(self._nav, cat_id, modulos)

        for cat_id, estaba in expandidas_previas.items():
            if cat_id in self._widgets_categoria and estaba:
                self._categorias_expandidas[cat_id] = True
                self._mostrar_hijos(cat_id, True)

        if not any(self._categorias_expandidas.values()) and self._widgets_categoria:
            primera = next(iter(self._widgets_categoria))
            self._categorias_expandidas[primera] = True
            self._mostrar_hijos(primera, True)

        # Refrescar texto del botón "Configuración" / "Mi cuenta"
        if getattr(self, "_lbl_config", None) is not None:
            try:
                self._lbl_config.configure(
                    text=("Configuración" if sesion.es_admin()
                          else "Mi cuenta")
                )
            except Exception:
                pass

        self._resaltar_modulo_activo(self._modulo_activo)
        self._actualizar_bloque_sesion()

    def _verificar_modulo_activo(self):
        """
        Si el módulo abierto dejó de ser visible (lo desactivaron o el
        perfil actual ya no lo permite), se cierra el embed.
        """
        if self._modulo_activo is None:
            return
        from core import config_ui
        from shared.perfiles import modulo_permitido

        activo = config_ui.modulo_esta_activo(
            self._modulo_activo.id, default=self._modulo_activo.activo
        )
        permitido = modulo_permitido(self._modulo_activo.id)
        if not (activo and permitido):
            self._cerrar_embed()

    def _resaltar_modulo_activo(self, modulo_activo):
        """Marca con fondo amarillo el módulo activo."""
        try:
            for cat_id, info in self._widgets_categoria.items():
                for w in info["modulos"]:
                    m = w["modulo"]
                    activo = (modulo_activo is not None and m.id == modulo_activo.id)

                    if activo:
                        w["fila"].configure(bg=COLOR_MODULO_BG_ACTIVO)
                        w["texto"].configure(
                            bg=COLOR_MODULO_BG_ACTIVO,
                            fg=COLOR_MODULO_FG_ACTIVO,
                        )
                    else:
                        w["fila"].configure(bg=COLOR_MODULO_BG)
                        w["texto"].configure(
                            bg=COLOR_MODULO_BG,
                            fg=COLOR_MODULO_FG,
                        )
        except Exception as e:
            print(f"[_resaltar_modulo_activo] Error: {e}", file=sys.stderr)

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
        from core import config_ui
        from shared.perfiles import modulo_permitido
        if not config_ui.modulo_esta_activo(modulo.id, default=modulo.activo):
            return
        if not modulo_permitido(modulo.id):
            return

        for cat_id, info in self._widgets_categoria.items():
            if any(w["modulo"].id == modulo.id for w in info["modulos"]):
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
            if not self._sigue_viva():
                return
            messagebox.showerror(
                "Error",
                f"No se pudo abrir {modulo.nombre}:\n{e}",
                parent=self,
            )

    def _abrir_embed(self, modulo):
        try:
            if getattr(self, "_panel_activo", None) is not None:
                try:
                    self._panel_activo.destroy()
                except Exception:
                    pass
                self._panel_activo = None

            for w in self._area_embed.winfo_children():
                try:
                    w.destroy()
                except Exception:
                    pass

            self._pantalla_inicio.pack_forget()

            for w in self._barra_embed.winfo_children():
                w.destroy()

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

            self._panel_activo = modulo.panel(
                master=self._area_embed,
                on_volver=self._cerrar_embed,
            )
            self._panel_activo.pack(fill="both", expand=True)
            self._modulo_activo = modulo

        except Exception as e:
            if not self._sigue_viva():
                return
            messagebox.showerror(
                "Error",
                f"No se pudo abrir {modulo.nombre} embebido:\n{e}",
                parent=self,
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

        try:
            self._barra_embed.pack_forget()
            self._area_embed.pack_forget()
            self._pantalla_inicio.pack(fill="both", expand=True)
            self._resaltar_modulo_activo(None)
        except Exception:
            pass

    def _cerrar_modulo(self, app):
        try:
            app.destroy()
        except Exception:
            pass
        if not self._sigue_viva():
            return
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _registrar_atajos(self):
        for m in modulos_visibles():
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
            dlg = abrir_dialogo_config_general(self)
            self.wait_window(dlg)
        except Exception as e:
            if not self._sigue_viva():
                return
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la configuración:\n{e}",
                parent=self,
            )
            return

        # Después del wait_window, la app puede haberse destruido si el
        # usuario cerró la ventana principal mientras Config estaba abierta.
        if not self._sigue_viva():
            return

        try:
            self._reconstruir_sidebar()
            self._verificar_modulo_activo()
        except Exception as e:
            print(f"[_abrir_configuracion] Error al reconstruir: {e}",
                  file=sys.stderr)

    def _abrir_ayuda(self):
        try:
            from dialogos.manual import abrir_manual
            abrir_manual(self)
        except Exception as e:
            if not self._sigue_viva():
                return
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el manual:\n{e}",
                parent=self,
            )

    # ============================================================
    # Ciclo de vida
    # ============================================================

    def _sigue_viva(self) -> bool:
        """True si la ventana raíz sigue existiendo y es usable."""
        try:
            return bool(self.winfo_exists())
        except Exception:
            return False

    def _cerrar_app(self):
        """
        Cierra la app limpiamente: destruye los Toplevel hijos antes de
        destruir la raíz, para evitar callbacks diferidos contra widgets
        ya muertos.
        """
        self._app_cerrando = True

        try:
            self._destruir_toplevels_recursivo(self)
        except Exception:
            pass

        try:
            self._cerrar_embed()
        except Exception:
            pass

        try:
            self.destroy()
        except Exception:
            pass

    def _destruir_toplevels_recursivo(self, padre):
        """Destruye recursivamente todos los Toplevel descendientes."""
        for w in list(padre.winfo_children()):
            if isinstance(w, tk.Toplevel):
                try:
                    self._destruir_toplevels_recursivo(w)
                except Exception:
                    pass
                try:
                    w.destroy()
                except Exception:
                    pass

    def _centrar_ventana(self):
        try:
            self.update_idletasks()
            ancho = 1040
            alto = 720
            x = (self.winfo_screenwidth() - ancho) // 2
            y = (self.winfo_screenheight() - alto) // 2
            self.geometry(f"{ancho}x{alto}+{x}+{y}")
        except Exception:
            pass