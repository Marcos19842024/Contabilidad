# -*- coding: utf-8 -*-
"""
dialogos/usuario_editar.py
Alta y edición de usuarios. Solo admin.

Uso:
    DialogoUsuarioEditar(master, usuario=None, on_guardar=callback)   # alta
    DialogoUsuarioEditar(master, usuario=dict, on_guardar=callback)   # edición

Al crear: el callback recibe (usuario_creado, password_inicial).
Al editar: el callback recibe (usuario_actualizado, None).
           La contraseña solo se cambia si el usuario escribió una nueva
           (y su confirmación). Si ambos campos están vacíos, no se toca.

Este diálogo NO toca usuarios.json: construye el dict y llama al callback.
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from core import usuarios
from core.auth import hashear_password, generar_password_temporal
from shared.perfiles import perfiles, perfil_por_id


class DialogoUsuarioEditar(ttk.Toplevel):
    def __init__(self, master, usuario: dict | None = None, on_guardar=None):
        super().__init__(master)
        self.es_nueva = usuario is None
        self.usuario_original = dict(usuario) if usuario else {}
        self.on_guardar = on_guardar

        self.title("Nuevo usuario" if self.es_nueva else "Editar usuario")
        self.resizable(False, False)

        from ui.utils import configurar_ventana
        configurar_ventana(master, self, ancho=460, alto=550,
                           min_ancho=440, min_alto=500,
                           centrar_en_padre=True)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        fila = 0

        # ---- ID ----
        ttk.Label(frame, text="Usuario (login)",
                  font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(0, 4)); fila += 1
        self.var_id = tk.StringVar(value=self.usuario_original.get("id", ""))
        self.entry_id = ttk.Entry(frame, textvariable=self.var_id, width=32)
        self.entry_id.grid(row=fila, column=0, sticky="we", pady=(0, 4)); fila += 1
        if not self.es_nueva:
            self.entry_id.configure(state="disabled")
        ttk.Label(frame,
                  text="Minúsculas, sin espacios. Empieza con letra. "
                       "Solo a-z, 0-9, _ (3–32).",
                  foreground="gray", font=("Segoe UI", 8),
                  wraplength=400, justify="left").grid(
            row=fila, column=0, sticky="w", pady=(0, 12)); fila += 1

        # ---- Nombre ----
        ttk.Label(frame, text="Nombre completo",
                  font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(0, 4)); fila += 1
        self.var_nombre = tk.StringVar(value=self.usuario_original.get("nombre", ""))
        ttk.Entry(frame, textvariable=self.var_nombre, width=32).grid(
            row=fila, column=0, sticky="we", pady=(0, 12)); fila += 1

        # ---- Perfil ----
        ttk.Label(frame, text="Perfil",
            font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(0, 4)); fila += 1
        lista_perfiles = perfiles()
        default_perfil = (self.usuario_original.get("perfil")
            or (lista_perfiles[0].id if lista_perfiles else ""))
        self.var_perfil = tk.StringVar(value=default_perfil)
        combo = ttk.Combobox(
            frame, textvariable=self.var_perfil,
            values=[p.id for p in lista_perfiles],
            state="readonly", width=30,
        )
        combo.grid(row=fila, column=0, sticky="we", pady=(0, 4)); fila += 1

        self.lbl_desc_perfil = ttk.Label(
            frame, text="", foreground="gray",
            font=("Segoe UI", 8), wraplength=400, justify="left",
        )
        self.lbl_desc_perfil.grid(row=fila, column=0, sticky="w",
                                   pady=(0, 12)); fila += 1
        self.var_perfil.trace_add("write", self._actualizar_desc_perfil)
        self._actualizar_desc_perfil()

        # ---- Activo ----
        self.var_activo = tk.BooleanVar(
            value=self.usuario_original.get("activo", True))
        ttk.Checkbutton(
            frame, text="Usuario activo (puede iniciar sesión)",
            variable=self.var_activo,
        ).grid(row=fila, column=0, sticky="w", pady=(0, 16)); fila += 1

        # ---- Contraseña ----
        # Al crear: obligatoria, con valor generado por default.
        # Al editar: opcional; si se deja vacía, no se cambia.
        if self.es_nueva:
            titulo_pwd = "Contraseña inicial"
        else:
            titulo_pwd = "Nueva contraseña (dejar vacío para no cambiar)"

        ttk.Label(frame, text=titulo_pwd,
                  font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(0, 4)); fila += 1

        fila_pwd = ttk.Frame(frame)
        fila_pwd.grid(row=fila, column=0, sticky="we", pady=(0, 4)); fila += 1
        self.var_pwd = tk.StringVar(
            value=generar_password_temporal() if self.es_nueva else "")
        self.entry_pwd = ttk.Entry(
            fila_pwd, textvariable=self.var_pwd, show="•",
            font=("Consolas", 11), width=24,
        )
        self.entry_pwd.pack(side=LEFT, fill=X, expand=True)
        ttk.Button(fila_pwd, text="↻",
                   command=self._regenerar_pwd,
                   bootstyle="secondary-outline", width=3).pack(
            side=LEFT, padx=(6, 0))
        ttk.Button(fila_pwd, text="👁",
                   command=self._toggle_ver_pwd,
                   bootstyle="secondary-outline", width=3).pack(
            side=LEFT, padx=(4, 0))

        fila_pwd2 = ttk.Frame(frame)
        fila_pwd2.grid(row=fila, column=0, sticky="w", pady=(2, 8)); fila += 1
        ttk.Button(fila_pwd2, text="📋 Copiar",
                   command=self._copiar_pwd,
                   bootstyle="secondary-outline").pack(side=LEFT)

        # Confirmación
        ttk.Label(frame, text="Confirmar contraseña",
                  font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(8, 4)); fila += 1
        self.var_conf = tk.StringVar()
        self.entry_conf = ttk.Entry(
            frame, textvariable=self.var_conf, show="•",
            font=("Consolas", 11), width=32,
        )
        self.entry_conf.grid(row=fila, column=0, sticky="we", pady=(0, 4)); fila += 1

        if self.es_nueva:
            ttk.Label(frame,
                      text="Anota la contraseña: se mostrará al guardar.",
                      foreground="gray", font=("Segoe UI", 8)).grid(
                row=fila, column=0, sticky="w", pady=(0, 12)); fila += 1

        # ---- Botón Guardar (sin Cancelar; X o Escape cierran sin guardar) ----
        barra = ttk.Frame(frame)
        barra.grid(row=fila, column=0, sticky="ew", pady=(20, 0))
        ttk.Button(barra, text="💾 Guardar",
                   command=self._guardar,
                   bootstyle="success").pack(side=RIGHT)

        frame.columnconfigure(0, weight=1)
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", lambda _e: self._guardar())
        self.after(50, self._foco_inicial)

    # ------------------------------------------------------------

    def _foco_inicial(self):
        if self.es_nueva:
            self.entry_id.focus_set()
        else:
            self.entry_pwd.focus_set()

    def _actualizar_desc_perfil(self, *_args):
        p = perfil_por_id(self.var_perfil.get())
        self.lbl_desc_perfil.configure(text=p.descripcion if p else "")

    def _regenerar_pwd(self):
        self.var_pwd.set(generar_password_temporal())
        self.var_conf.set(self.var_pwd.get())

    def _toggle_ver_pwd(self):
        actual = self.entry_pwd.cget("show")
        nuevo = "" if actual else "•"
        self.entry_pwd.configure(show=nuevo)
        self.entry_conf.configure(show=nuevo)

    def _copiar_pwd(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.var_pwd.get())
            self.update()
        except Exception:
            pass

    # ------------------------------------------------------------

    def _guardar(self):
        uid = self.var_id.get().strip().lower()
        nombre = self.var_nombre.get().strip()
        perfil_id = self.var_perfil.get()
        activo = self.var_activo.get()

        if not uid or not nombre:
            messagebox.showwarning("Faltan datos",
                                    "Usuario y nombre son obligatorios.",
                                    parent=self)
            return
        if self.es_nueva and not usuarios.id_es_valido(uid):
            messagebox.showwarning(
                "Usuario inválido",
                "El nombre de usuario debe empezar con letra y usar solo "
                "a-z, 0-9, _ (3–32 caracteres).",
                parent=self)
            return
        if perfil_por_id(perfil_id) is None:
            messagebox.showwarning("Perfil inválido",
                                    "Selecciona un perfil válido.",
                                    parent=self)
            return

        # Regla del último admin
        if not self.es_nueva:
            uid_orig = self.usuario_original["id"]
            era_admin = self.usuario_original.get("perfil") == "admin"
            era_activo = self.usuario_original.get("activo", True)
            sigue_admin_activo = (perfil_id == "admin" and activo)
            if era_admin and era_activo and not sigue_admin_activo:
                if usuarios.quedarian_admins_sin(uid_orig) == 0:
                    messagebox.showwarning(
                        "No se puede",
                        "Es el único administrador activo. Debe quedar al "
                        "menos uno.",
                        parent=self)
                    return

        # Validación de contraseña
        pwd = self.var_pwd.get()
        conf = self.var_conf.get()

        if self.es_nueva:
            # Al crear, la contraseña es obligatoria y debe coincidir
            if not pwd:
                messagebox.showwarning("Falta contraseña",
                                        "Escribe una contraseña inicial.",
                                        parent=self)
                return
            if pwd != conf:
                messagebox.showwarning("No coinciden",
                                        "La contraseña y su confirmación "
                                        "no coinciden.", parent=self)
                self.var_conf.set("")
                self.entry_conf.focus_set()
                return
            if len(pwd) < 8:
                messagebox.showwarning("Contraseña corta",
                                        "Debe tener al menos 8 caracteres.",
                                        parent=self)
                return
        else:
            # Al editar, la contraseña es opcional.
            # Si ambos campos están vacíos, no se cambia.
            # Si solo uno está relleno, error.
            if not pwd and not conf:
                pwd = None
            elif pwd and not conf:
                messagebox.showwarning(
                    "Falta confirmar",
                    "Escribe la confirmación de la nueva contraseña.",
                    parent=self)
                self.entry_conf.focus_set()
                return
            elif conf and not pwd:
                messagebox.showwarning(
                    "Falta contraseña",
                    "Escribe la nueva contraseña.",
                    parent=self)
                self.entry_pwd.focus_set()
                return
            else:
                if pwd != conf:
                    messagebox.showwarning(
                        "No coinciden",
                        "La contraseña y su confirmación no coinciden.",
                        parent=self)
                    self.var_conf.set("")
                    self.entry_conf.focus_set()
                    return
                if len(pwd) < 8:
                    messagebox.showwarning(
                        "Contraseña corta",
                        "Debe tener al menos 8 caracteres.",
                        parent=self)
                    return

        # Persistir
        if self.es_nueva:
            try:
                u = usuarios.crear(uid, nombre, perfil_id,
                                    hashear_password(pwd))
                if not activo:
                    usuarios.actualizar(uid, activo=False)
            except Exception as e:
                messagebox.showerror("Error al crear", str(e), parent=self)
                return
            if self.on_guardar:
                self.on_guardar(u, pwd)
        else:
            uid_orig = self.usuario_original["id"]
            campos = {"nombre": nombre, "perfil": perfil_id, "activo": activo}
            if pwd is not None:
                campos["password_hash"] = hashear_password(pwd)
            try:
                u = usuarios.actualizar(uid_orig, **campos)
            except Exception as e:
                messagebox.showerror("Error al guardar", str(e), parent=self)
                return
            if self.on_guardar:
                self.on_guardar(u, None)

        self.destroy()