# -*- coding: utf-8 -*-
"""
dialogos/config_general.py
Configuración general de Vet Suite.

Tabs:
  - 🔒 Mi cuenta   (todos los perfiles)
  - 🎨 Apariencia  (admin)
  - 🏥 Veterinaria (admin)
  - 🧩 Módulos     (admin)
  - 🧑 Perfiles    (admin)
  - 👥 Usuarios    (admin)

El diálogo se autofiltra según el perfil de la sesión activa.
No hace falta ocultar tabs desde fuera.

Los diálogos de detalle de sucursal viven en dialogos/sucursal_detalle.py.
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.temas import obtener_tema
from config.veterinaria import (
    obtener_veterinaria, guardar_veterinaria,
    cambiar_sucursal_activa,
)
from core import sesion


# ============================================================
# API pública
# ============================================================

def abrir_dialogo_config_general(app):
    """Abre el diálogo. Devuelve el Toplevel para poder hacer wait_window."""
    return DialogoConfigGeneral(app)


# ============================================================
# Diálogo principal
# ============================================================

class DialogoConfigGeneral(ttk.Toplevel):
    def __init__(self, master):
        super().__init__(master)

        # Flag de vida útil (lo usa _enfocar_seguro)
        self._vivo = True

        es_admin = sesion.es_admin()
        titulo = "⚙️ Configuración" if es_admin else "🔒 Mi cuenta"
        subtitulo = ("⚙️ Configuración general"
                     if es_admin else "🔒 Mi cuenta")

        self.title(titulo)
        from ui.utils import configurar_ventana
        configurar_ventana(master, self, ancho=700, alto=550,
                           min_ancho=650, min_alto=500,
                           centrar_en_padre=True)

        ttk.Label(self, text=subtitulo,
                  font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=True, padx=15, pady=10)

        # ---- Tabs comunes (todos los perfiles) ----
        self.tab_mi_cuenta = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_mi_cuenta, text="🔒 Mi cuenta")
        self._construir_tab_mi_cuenta()

        # ---- Tabs solo admin ----
        if es_admin:
            self.tab_apariencia = ttk.Frame(self.notebook, padding=15)
            self.tab_veterinaria = ttk.Frame(self.notebook, padding=15)
            self.tab_modulos = ttk.Frame(self.notebook, padding=15)
            self.tab_perfiles = ttk.Frame(self.notebook, padding=15)
            self.tab_usuarios = ttk.Frame(self.notebook, padding=15)

            self.notebook.add(self.tab_apariencia, text="🎨 Apariencia")
            self.notebook.add(self.tab_veterinaria, text="🏥 Veterinaria")
            self.notebook.add(self.tab_modulos, text="🧩 Módulos")
            self.notebook.add(self.tab_perfiles, text="🧑 Perfiles")
            self.notebook.add(self.tab_usuarios, text="👥 Usuarios")

            self._construir_tab_apariencia()
            self._construir_tab_veterinaria()
            self._construir_tab_modulos()
            self._construir_tab_perfiles()
            self._construir_tab_usuarios()

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.bind("<Escape>", lambda _e: self._cerrar())

    # ------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------

    def _cerrar(self):
        self._vivo = False
        self.destroy()

    def destroy(self):
        # Idempotente: si ya se destruyó, no hacemos nada.
        self._vivo = False
        try:
            super().destroy()
        except Exception:
            pass

    def _enfocar_seguro(self, widget):
        """Enfoca un widget solo si el diálogo sigue vivo."""
        try:
            if self._vivo and widget.winfo_exists():
                widget.focus_set()
        except Exception:
            pass

    # ============================================================
    # Tab: Mi cuenta
    # ============================================================

    def _construir_tab_mi_cuenta(self):
        """
        Formulario para cambiar la propia contraseña.
        No permite cambiar el usuario ni el perfil: eso es admin-only
        y va en el tab 👥 Usuarios.
        """
        from core import usuarios
        from core.auth import verificar_password, hashear_password

        f = self.tab_mi_cuenta

        s = sesion.actual()
        if s is None:
            ttk.Label(f, text="No hay sesión activa.",
                      foreground="red").pack(anchor="w")
            return

        u = usuarios.obtener(s.usuario_id)
        if u is None:
            ttk.Label(f, text="No se encontró tu usuario en la base.",
                      foreground="red").pack(anchor="w")
            return

        # ---- Info de sesión ----
        info = ttk.LabelFrame(f, text="Sesión activa", padding=12)
        info.pack(fill=X, pady=(0, 14))

        ttk.Label(info, text=f"👤 {u['nombre']}",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(info, text=f"Usuario: {u['id']}  ·  Perfil: {s.perfil_id}",
                  foreground="gray", font=("Segoe UI", 9)).pack(anchor="w",
                                                                 pady=(2, 0))

        # ---- Formulario ----
        form = ttk.LabelFrame(f, text="Cambiar contraseña", padding=12)
        form.pack(fill=X)

        ttk.Label(form, text="Contraseña actual").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        var_actual = tk.StringVar()
        e_actual = ttk.Entry(form, textvariable=var_actual, show="•", width=32)
        e_actual.grid(row=1, column=0, sticky="we", pady=(0, 10))

        ttk.Label(form, text="Nueva contraseña (mínimo 8 caracteres)").grid(
            row=2, column=0, sticky="w", pady=(0, 4))
        var_nueva = tk.StringVar()
        e_nueva = ttk.Entry(form, textvariable=var_nueva, show="•", width=32)
        e_nueva.grid(row=3, column=0, sticky="we", pady=(0, 10))

        ttk.Label(form, text="Confirmar nueva contraseña").grid(
            row=4, column=0, sticky="w", pady=(0, 4))
        var_conf = tk.StringVar()
        e_conf = ttk.Entry(form, textvariable=var_conf, show="•", width=32)
        e_conf.grid(row=5, column=0, sticky="we", pady=(0, 14))

        form.columnconfigure(0, weight=1)

        # ---- Mensaje ----
        lbl_msg = ttk.Label(form, text="", font=("Segoe UI", 9))
        lbl_msg.grid(row=6, column=0, sticky="w", pady=(0, 10))

        def _limpiar_msg(*_args):
            lbl_msg.configure(text="")

        var_actual.trace_add("write", _limpiar_msg)
        var_nueva.trace_add("write", _limpiar_msg)
        var_conf.trace_add("write", _limpiar_msg)

        def _mostrar(msg: str, ok: bool):
            lbl_msg.configure(
                text=msg,
                foreground=("#0a7c2f" if ok else "#c0392b"),
            )

        def _guardar():
            actual = var_actual.get()
            nueva = var_nueva.get()
            conf = var_conf.get()

            if not actual or not nueva or not conf:
                _mostrar("Completa los tres campos.", ok=False)
                return
            if not verificar_password(actual, u.get("password_hash", "")):
                _mostrar("La contraseña actual no es correcta.", ok=False)
                var_actual.set("")
                e_actual.focus_set()
                return
            if nueva != conf:
                _mostrar("La nueva contraseña y su confirmación no coinciden.",
                         ok=False)
                var_conf.set("")
                e_conf.focus_set()
                return
            if len(nueva) < 8:
                _mostrar("La nueva contraseña debe tener al menos 8 caracteres.",
                         ok=False)
                e_nueva.focus_set()
                return
            if nueva == actual:
                _mostrar("La nueva contraseña debe ser distinta a la actual.",
                         ok=False)
                e_nueva.focus_set()
                return

            try:
                usuarios.actualizar(u["id"], password_hash=hashear_password(nueva))
            except Exception as e:
                _mostrar(f"No se pudo guardar: {e}", ok=False)
                return

            # Éxito: limpiar todo y avisar
            var_actual.set("")
            var_nueva.set("")
            var_conf.set("")
            _mostrar("✅ Contraseña actualizada.", ok=True)
            self._enfocar_seguro(e_actual)

        botones = ttk.Frame(form)
        botones.grid(row=7, column=0, sticky="e")
        ttk.Button(botones, text="Cambiar contraseña",
                   command=_guardar, bootstyle="success").pack(side=RIGHT)

        # Enter dispara guardar desde cualquier campo
        for e in (e_actual, e_nueva, e_conf):
            e.bind("<Return>", lambda _e: _guardar())

        self.after(50, lambda: self._enfocar_seguro(e_actual))

    # ============================================================
    # Tab: Apariencia
    # ============================================================

    def _construir_tab_apariencia(self):
        f = self.tab_apariencia
        frame = ttk.LabelFrame(f, text="🎨 Tema visual", padding=15)
        frame.pack(fill=X)

        fila = ttk.Frame(frame)
        fila.pack(fill=X, pady=5)

        ttk.Label(fila, text="Tema actual:",
                  font=("Segoe UI", 10, "bold"),
                  width=15, anchor="w").pack(side=LEFT)
        self.lbl_tema = ttk.Label(fila, text=obtener_tema(),
                                   font=("Segoe UI", 10), foreground="gray")
        self.lbl_tema.pack(side=LEFT, padx=(5, 15))

        def _cambiar_tema():
            from dialogos.temas import abrir_dialogo_temas
            abrir_dialogo_temas(self)
            try:
                self.lbl_tema.configure(text=obtener_tema())
            except Exception:
                pass

        ttk.Button(fila, text="Cambiar tema",
                   command=_cambiar_tema,
                   bootstyle="info-outline").pack(side=RIGHT)

    # ============================================================
    # Tab: Veterinaria
    # ============================================================

    def _construir_tab_veterinaria(self):
        f = self.tab_veterinaria

        # Tabla sucursales
        frame_sucs = ttk.LabelFrame(f, text="🏢 Sucursales", padding=10)
        frame_sucs.pack(fill=BOTH, expand=True)

        ttk.Label(frame_sucs,
                  text="Doble clic para editar. La sucursal activa (●) es el "
                       "origen de rutas en Estética y el emisor en Recordatorios.",
                  foreground="gray", font=("Segoe UI", 8)).pack(anchor="w",
                                                                  pady=(0, 8))

        contenedor = ttk.Frame(frame_sucs)
        contenedor.pack(fill=BOTH, expand=True)

        cols = ("activa", "id", "nombre", "coords")
        self.tabla = ttk.Treeview(contenedor, columns=cols, show="headings",
                                   height=8, bootstyle="primary")
        self.tabla.heading("activa", text="●")
        self.tabla.heading("id", text="ID")
        self.tabla.heading("nombre", text="NOMBRE")
        self.tabla.heading("coords", text="COORDENADAS")
        self.tabla.column("activa", width=40, anchor="center")
        self.tabla.column("id", width=140, anchor="w")
        self.tabla.column("nombre", width=280, anchor="w")
        self.tabla.column("coords", width=150, anchor="w")

        sb = ttk.Scrollbar(contenedor, orient="vertical",
                            command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        self.tabla.bind("<Double-1>", self._editar_sucursal)

        barra = ttk.Frame(frame_sucs)
        barra.pack(fill=X, pady=(10, 0))
        ttk.Button(barra, text="+ Nueva", command=self._nueva_sucursal,
                   bootstyle="success-outline").pack(side=LEFT, padx=3)
        ttk.Button(barra, text="✏️ Editar",
                   command=self._editar_sucursal_sel,
                   bootstyle="info-outline").pack(side=LEFT, padx=3)
        ttk.Button(barra, text="🗑️ Eliminar",
                   command=self._eliminar_sucursal,
                   bootstyle="danger-outline").pack(side=LEFT, padx=3)
        ttk.Button(barra, text="● Marcar como activa",
                   command=self._marcar_activa,
                   bootstyle="warning-outline").pack(side=LEFT, padx=3)

        self._refrescar_tabla_sucursales()

    def _refrescar_tabla_sucursales(self):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        vet = obtener_veterinaria()
        activa_id = vet.get("sucursal_activa", "")
        for idx, s in enumerate(vet.get("sucursales", [])):
            marca = "●" if s.get("id") == activa_id else ""
            coords = s.get("coordenadas", {})
            lat, lng = coords.get("lat"), coords.get("lng")
            coords_txt = f"{lat:.5f}, {lng:.5f}" if lat and lng else "—"
            self.tabla.insert("", END, iid=str(idx), values=(
                marca, s.get("id", ""), s.get("nombre", ""), coords_txt,
            ))

    def _nueva_sucursal(self):
        from dialogos.sucursal_detalle import DialogoSucursalDetalle
        DialogoSucursalDetalle(self, None,
                                on_guardar=self._recibir_sucursal)

    def _editar_sucursal(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        idx = int(sel[0])
        sucs = obtener_veterinaria().get("sucursales", [])
        if idx >= len(sucs):
            return
        from dialogos.sucursal_detalle import DialogoSucursalDetalle
        DialogoSucursalDetalle(self, sucs[idx],
                                on_guardar=lambda s: self._recibir_sucursal(s, idx))

    def _editar_sucursal_sel(self):
        self._editar_sucursal()

    def _recibir_sucursal(self, sucursal: dict, idx: int = None):
        vet = obtener_veterinaria()
        sucs = vet.get("sucursales", [])
        if idx is None:
            if any(s.get("id") == sucursal["id"] for s in sucs):
                messagebox.showwarning(
                    "ID duplicado",
                    f"Ya existe una sucursal con ID '{sucursal['id']}'.",
                    parent=self)
                return
            sucs.append(sucursal)
        else:
            sucs[idx] = sucursal
        vet["sucursales"] = sucs
        guardar_veterinaria(vet)
        self._refrescar_tabla_sucursales()

    def _eliminar_sucursal(self):
        sel = self.tabla.selection()
        if not sel:
            return
        idx = int(sel[0])
        vet = obtener_veterinaria()
        sucs = vet.get("sucursales", [])
        if idx >= len(sucs):
            return
        s = sucs[idx]
        if s.get("id") == vet.get("sucursal_activa"):
            messagebox.showwarning(
                "No se puede eliminar",
                "Es la sucursal activa. Marca otra como activa primero.",
                parent=self)
            return
        if not messagebox.askyesno("Confirmar",
                                    f"¿Eliminar '{s.get('nombre')}'?",
                                    parent=self):
            return
        sucs.pop(idx)
        vet["sucursales"] = sucs
        guardar_veterinaria(vet)
        self._refrescar_tabla_sucursales()

    def _marcar_activa(self):
        sel = self.tabla.selection()
        if not sel:
            return
        idx = int(sel[0])
        sucs = obtener_veterinaria().get("sucursales", [])
        if idx >= len(sucs):
            return
        cambiar_sucursal_activa(sucs[idx]["id"])
        self._refrescar_tabla_sucursales()
        messagebox.showinfo(
            "Sucursal activa",
            f"Ahora la sucursal activa es:\n{sucs[idx]['nombre']}",
            parent=self)

    # ============================================================
    # Tab: Módulos
    # ============================================================

    def _construir_tab_modulos(self):
        """
        Checkboxes para activar/desactivar módulos.
        Se agrupan por categoría. Si una categoría se queda sin módulos
        visibles, desaparece del sidebar (no de aquí).
        """
        from shared.registro_modulos import MODULOS, CATEGORIAS
        from core import config_ui

        f = self.tab_modulos

        ttk.Label(
            f,
            text="Activa o desactiva módulos. Los desactivados no aparecen "
                 "en el menú lateral. Las categorías sin módulos visibles "
                 "también se ocultan.",
            foreground="gray", font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(0, 12))

        # Agrupar por categoría respetando el orden
        por_cat: dict[str, list] = {}
        for m in MODULOS:
            por_cat.setdefault(m.categoria, []).append(m)

        for cat_id, modulos in sorted(
            por_cat.items(),
            key=lambda kv: CATEGORIAS.get(kv[0], {}).get("orden", 99),
        ):
            etiqueta = CATEGORIAS.get(cat_id, {}).get("nombre", cat_id.title())
            frame_cat = ttk.LabelFrame(f, text=etiqueta, padding=10)
            frame_cat.pack(fill="x", pady=6)

            for m in modulos:
                # Default = m.activo (lo que declara el registro)
                actual = config_ui.modulo_esta_activo(m.id, default=m.activo)
                var = tk.BooleanVar(value=actual)

                def _toggle(mod_id=m.id, v=var):
                    config_ui.set_modulo_activo(mod_id, v.get())

                chk = ttk.Checkbutton(
                    frame_cat,
                    text=f"{m.icono}  {m.nombre}",
                    variable=var,
                    command=_toggle,
                    bootstyle="success-round-toggle",
                )
                chk.pack(anchor="w", pady=2)

                ttk.Label(
                    frame_cat,
                    text=m.descripcion.replace("\n", " "),
                    foreground="gray", font=("Segoe UI", 8),
                ).pack(anchor="w", padx=(28, 0), pady=(0, 6))

    # ============================================================
    # Tab: Perfiles
    # ============================================================

    def _construir_tab_perfiles(self):
        """
        Tabla de perfiles y qué módulos ve cada uno.
        El perfil admin es intocable.
        """
        f = self.tab_perfiles

        ttk.Label(
            f,
            text="Los perfiles definen qué módulos ve cada tipo de usuario. "
                 "El perfil Administrador es intocable y siempre ve todo.",
            foreground="gray", font=("Segoe UI", 8),
            wraplength=620, justify="left",
        ).pack(anchor="w", pady=(0, 10))

        contenedor = ttk.Frame(f)
        contenedor.pack(fill=BOTH, expand=True)

        cols = ("id", "nombre", "modulos")
        self.tabla_perfiles = ttk.Treeview(
            contenedor, columns=cols, show="headings",
            height=10, bootstyle="primary",
        )
        self.tabla_perfiles.heading("id", text="ID")
        self.tabla_perfiles.heading("nombre", text="NOMBRE")
        self.tabla_perfiles.heading("modulos", text="MÓDULOS VISIBLES")

        self.tabla_perfiles.column("id", width=130, anchor="w")
        self.tabla_perfiles.column("nombre", width=160, anchor="w")
        self.tabla_perfiles.column("modulos", width=440, anchor="w")

        sb = ttk.Scrollbar(contenedor, orient="vertical",
                            command=self.tabla_perfiles.yview)
        self.tabla_perfiles.configure(yscrollcommand=sb.set)
        self.tabla_perfiles.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        self.tabla_perfiles.bind("<Double-1>", lambda _e: self._editar_perfil())

        barra = ttk.Frame(f)
        barra.pack(fill=X, pady=(10, 0))
        ttk.Button(barra, text="+ Nuevo perfil",
                   command=self._nuevo_perfil,
                   bootstyle="success-outline").pack(side=LEFT, padx=3)
        ttk.Button(barra, text="🗑️ Eliminar",
                   command=self._eliminar_perfil,
                   bootstyle="danger-outline").pack(side=LEFT, padx=3)

        ttk.Label(barra,
                  text="Doble clic en una fila para editar. El perfil "
                       "Administrador es intocable.",
                  foreground="gray", font=("Segoe UI", 8)).pack(
            side=LEFT, padx=(12, 0))

        self._refrescar_tabla_perfiles()

    def _refrescar_tabla_perfiles(self):
        from shared.perfiles import perfiles
        from shared.registro_modulos import MODULOS

        nombres_modulos = {m.id: m.nombre for m in MODULOS}

        for i in self.tabla_perfiles.get_children():
            self.tabla_perfiles.delete(i)

        for p in perfiles():
            if p.modulos == "*":
                mods_txt = "Todos los módulos"
            else:
                if not p.modulos:
                    mods_txt = "— sin módulos —"
                else:
                    mods_txt = ", ".join(
                        nombres_modulos.get(mid, mid) for mid in p.modulos
                    )
            self.tabla_perfiles.insert(
                "", END, iid=p.id,
                values=(p.id, p.nombre, mods_txt),
            )

    def _perfil_seleccionado(self):
        sel = self.tabla_perfiles.selection()
        if not sel:
            return None
        from shared.perfiles import perfil_por_id
        return perfil_por_id(sel[0])

    def _nuevo_perfil(self):
        from dialogos.perfil_editar import DialogoPerfilEditar
        from shared import perfiles as perfiles_mod

        def _recibir(perfil, es_nuevo):
            if es_nuevo:
                perfiles_mod.agregar_perfil(perfil)
            else:
                perfiles_mod.actualizar_perfil(
                    perfil.id,
                    nombre=perfil.nombre,
                    descripcion=perfil.descripcion,
                    modulos=perfil.modulos,
                )
            self._refrescar_tabla_perfiles()

        DialogoPerfilEditar(self, None, on_guardar=_recibir)

    def _editar_perfil(self):
        p = self._perfil_seleccionado()
        if p is None:
            return
        if p.id == "admin":
            messagebox.showinfo(
                "Perfil intocable",
                "El perfil Administrador no se puede editar. Siempre ve "
                "todos los módulos y es el único que puede configurar.",
                parent=self)
            return

        from dialogos.perfil_editar import DialogoPerfilEditar
        from shared import perfiles as perfiles_mod

        def _recibir(perfil, _es_nuevo):
            perfiles_mod.actualizar_perfil(
                perfil.id,
                nombre=perfil.nombre,
                descripcion=perfil.descripcion,
                modulos=perfil.modulos,
            )
            self._refrescar_tabla_perfiles()

        DialogoPerfilEditar(self, p, on_guardar=_recibir)

    def _eliminar_perfil(self):
        p = self._perfil_seleccionado()
        if p is None:
            return
        if p.id == "admin":
            messagebox.showwarning(
                "No se puede",
                "El perfil Administrador no se puede eliminar.",
                parent=self)
            return

        from shared import perfiles as perfiles_mod

        usuarios_asignados = perfiles_mod.usuarios_con_perfil(p.id)
        if usuarios_asignados:
            nombres = ", ".join(u["id"] for u in usuarios_asignados[:5])
            extra = (f" (y {len(usuarios_asignados) - 5} más)"
                     if len(usuarios_asignados) > 5 else "")
            messagebox.showwarning(
                "Perfil en uso",
                f"El perfil '{p.nombre}' tiene {len(usuarios_asignados)} "
                f"usuario(s) asignado(s): {nombres}{extra}.\n\n"
                "Reasígnalos a otro perfil antes de eliminarlo.",
                parent=self)
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar el perfil '{p.nombre}' ({p.id})?\n\n"
            "Esta acción no se puede deshacer.",
            parent=self,
        ):
            return

        try:
            perfiles_mod.eliminar_perfil(p.id)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        self._refrescar_tabla_perfiles()

    # ============================================================
    # Tab: Usuarios
    # ============================================================

    def _construir_tab_usuarios(self):
        """Tabla de usuarios + CRUD. Solo visible para admin."""
        from shared.perfiles import perfil_por_id  # noqa: F401

        f = self.tab_usuarios

        ttk.Label(f,
                  text="Administra las cuentas y sus perfiles. El perfil "
                       "define qué módulos ve cada usuario.",
                  foreground="gray", font=("Segoe UI", 8),
                  wraplength=620, justify="left").pack(anchor="w",
                                                        pady=(0, 10))

        contenedor = ttk.Frame(f)
        contenedor.pack(fill=BOTH, expand=True)

        cols = ("id", "nombre", "perfil", "activo", "ultimo_login")
        self.tabla_usuarios = ttk.Treeview(
            contenedor, columns=cols, show="headings",
            height=10, bootstyle="primary",
        )
        self.tabla_usuarios.heading("id", text="USUARIO")
        self.tabla_usuarios.heading("nombre", text="NOMBRE")
        self.tabla_usuarios.heading("perfil", text="PERFIL")
        self.tabla_usuarios.heading("activo", text="●")
        self.tabla_usuarios.heading("ultimo_login", text="ÚLTIMO LOGIN")

        self.tabla_usuarios.column("id", width=100, anchor="w")
        self.tabla_usuarios.column("nombre", width=180, anchor="w")
        self.tabla_usuarios.column("perfil", width=120, anchor="w")
        self.tabla_usuarios.column("activo", width=40, anchor="center")
        self.tabla_usuarios.column("ultimo_login", width=140, anchor="w")

        sb = ttk.Scrollbar(contenedor, orient="vertical",
                            command=self.tabla_usuarios.yview)
        self.tabla_usuarios.configure(yscrollcommand=sb.set)
        self.tabla_usuarios.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        self.tabla_usuarios.bind("<Double-1>", lambda _e: self._editar_usuario())

        barra = ttk.Frame(f)
        barra.pack(fill=X, pady=(10, 0))
        ttk.Button(barra, text="+ Nuevo usuario",
                   command=self._nuevo_usuario,
                   bootstyle="success-outline").pack(side=LEFT, padx=3)
        ttk.Button(barra, text="🗑️ Eliminar",
                   command=self._eliminar_usuario,
                   bootstyle="danger-outline").pack(side=LEFT, padx=3)

        ttk.Label(barra,
                  text="Doble clic en una fila para editar.",
                  foreground="gray", font=("Segoe UI", 8)).pack(
            side=LEFT, padx=(12, 0))

        self._refrescar_tabla_usuarios()

    def _refrescar_tabla_usuarios(self):
        from core import usuarios as _usuarios
        from shared.perfiles import perfil_por_id

        for i in self.tabla_usuarios.get_children():
            self.tabla_usuarios.delete(i)

        for u in sorted(_usuarios.listar(), key=lambda x: x.get("id", "")):
            marca = "●" if u.get("activo", True) else "○"
            perfil = perfil_por_id(u.get("perfil", ""))
            perfil_nombre = perfil.nombre if perfil else u.get("perfil", "")
            ultimo = u.get("ultimo_login") or "—"
            self.tabla_usuarios.insert("", END, iid=u["id"], values=(
                u.get("id", ""),
                u.get("nombre", ""),
                perfil_nombre,
                marca,
                ultimo,
            ))

    def _usuario_seleccionado(self):
        sel = self.tabla_usuarios.selection()
        if not sel:
            return None
        from core import usuarios as _usuarios
        return _usuarios.obtener(sel[0])

    def _nuevo_usuario(self):
        from dialogos.usuario_editar import DialogoUsuarioEditar

        def _recibir(u, password):
            self._refrescar_tabla_usuarios()
            messagebox.showinfo(
                "Usuario creado",
                f"Usuario: {u['id']}\n"
                f"Contraseña inicial: {password}\n\n"
                "Anótala: no se volverá a mostrar.",
                parent=self,
            )

        DialogoUsuarioEditar(self, None, on_guardar=_recibir)

    def _editar_usuario(self):
        u = self._usuario_seleccionado()
        if u is None:
            return
        from dialogos.usuario_editar import DialogoUsuarioEditar

        def _recibir(_u, _pwd):
            self._refrescar_tabla_usuarios()

        DialogoUsuarioEditar(self, u, on_guardar=_recibir)

    def _eliminar_usuario(self):
        from core import usuarios as _usuarios

        u = self._usuario_seleccionado()
        if u is None:
            return

        # No permitir eliminarse a sí mismo
        s = sesion.actual()
        if s is not None and s.usuario_id == u["id"]:
            messagebox.showwarning(
                "No se puede",
                "No puedes eliminar tu propia cuenta.",
                parent=self)
            return

        # No dejar el sistema sin admins
        if u.get("perfil") == "admin" and u.get("activo", True):
            if _usuarios.quedarian_admins_sin(u["id"]) == 0:
                messagebox.showwarning(
                    "No se puede",
                    "Es el único administrador activo. Debe quedar "
                    "al menos uno.",
                    parent=self)
                return

        if not messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar al usuario '{u['id']}' ({u['nombre']})?\n\n"
            "Esta acción no se puede deshacer.",
            parent=self,
        ):
            return

        try:
            _usuarios.eliminar(u["id"])
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        self._refrescar_tabla_usuarios()