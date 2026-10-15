# -*- coding: utf-8 -*-
"""
dialogos/login.py
Diálogo modal de inicio de sesión + asistente de primer arranque.

Uso:
    ok = mostrar_login(master)
    if not ok:
        sys.exit(0)

El diálogo:
  1. Verifica si hay usuarios. Si no, corre el bootstrap (crea admin,
     muestra la contraseña temporal en un diálogo previo).
  2. Pide usuario y contraseña.
  3. Al acertar, llama a sesion.iniciar_sesion() y devuelve True.
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from core import auth
from core import sesion
from core import usuarios


# ---------------------------------------------------------------
# API pública
# ---------------------------------------------------------------

def mostrar_login(master) -> bool:
    """
    Muestra el login (y el bootstrap si hace falta).
    Devuelve True si hay sesión iniciada al cerrar, False si se canceló.
    """
    if not usuarios.existe():
        _bootstrap_primer_arranque(master)
        if not usuarios.existe():
            # El usuario canceló el bootstrap
            return False

    dlg = DialogoLogin(master)
    master.wait_window(dlg)
    return sesion.hay_sesion()


# ---------------------------------------------------------------
# Bootstrap de primera ejecución
# ---------------------------------------------------------------

def _bootstrap_primer_arranque(master) -> None:
    """
    Crea usuarios.json con un admin y muestra la contraseña temporal
    UNA VEZ. Bloquea hasta que el usuario marque el checkbox y continúe.
    Si cancela, borra el usuario recién creado y no deja arrancar.
    """
    try:
        usuario, password = usuarios.crear_admin_inicial("Administrador")
    except Exception as e:
        messagebox.showerror(
            "Error de arranque",
            f"No se pudo crear el administrador inicial:\n{e}",
            parent=master,
        )
        return

    dlg = DialogoPrimerArranque(master, usuario, password)
    master.wait_window(dlg)

    # Si el usuario canceló, deshacemos la creación del admin.
    # (Si no, quedaría un usuarios.json con un admin cuya contraseña
    #  nadie anotó, y no podría entrar nunca.)
    if not dlg.confirmo:
        try:
            usuarios.eliminar(usuario["id"])
        except Exception:
            pass
        # Si el archivo quedó vacío, lo borramos para forzar bootstrap limpio.
        try:
            if not usuarios.listar():
                usuarios.USUARIOS_FILE.unlink()
        except Exception:
            pass


class DialogoPrimerArranque(ttk.Toplevel):
    """Muestra las credenciales del admin recién creado. Bloqueante."""

    def __init__(self, master, usuario: dict, password: str):
        super().__init__(master)
        self.title("Primer arranque")
        self.resizable(False, False)
        # Nota: NO usamos transient() ni grab_set() cuando el master está
        # withdrawn. En macOS eso deja el diálogo sin foco ni input.
        # En su lugar, forzamos el foco explícitamente al final del __init__.

        self.confirmo = False
        self._password = password

        frame = ttk.Frame(self, padding=24)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            frame, text="🩺  Bienvenido a Vet Suite",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            frame,
            text="Se ha creado un usuario administrador.\n"
                 "Anota la contraseña: no se volverá a mostrar.",
            font=("Segoe UI", 10), foreground="gray",
            justify="left",
        ).pack(anchor="w", pady=(6, 18))

        # Credenciales en un frame monoespaciado
        cred = ttk.LabelFrame(frame, text="Credenciales", padding=14)
        cred.pack(fill=X)

        ttk.Label(cred, text="Usuario:",
                  font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Label(cred, text=usuario["id"],
                  font=("Consolas", 12)).grid(
            row=0, column=1, sticky="w", pady=4)

        ttk.Label(cred, text="Contraseña:",
                  font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=4)
        self._lbl_pwd = ttk.Label(cred, text=password,
                                   font=("Consolas", 14, "bold"),
                                   foreground="#0a7c2f")
        self._lbl_pwd.grid(row=1, column=1, sticky="w", pady=4)

        # Botón copiar
        barra_cred = ttk.Frame(cred)
        barra_cred.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(
            barra_cred, text="📋 Copiar contraseña",
            command=self._copiar, bootstyle="secondary-outline",
        ).pack(side=LEFT)

        # Checkbox de confirmación
        self._var_ok = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(
            frame,
            text="Ya anoté la contraseña en un lugar seguro.",
            variable=self._var_ok,
            command=self._toggle_continuar,
        )
        chk.pack(anchor="w", pady=(18, 8))

        # Botón continuar
        self._btn_continuar = ttk.Button(
            frame, text="Continuar →",
            command=self._continuar_click,
            bootstyle="success", state="disabled",
        )
        self._btn_continuar.pack(anchor="e", pady=(4, 0))

        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        self._centrar(master)
        self._traer_al_frente()

    def _traer_al_frente(self):
        """En macOS, un diálogo hijo de una ventana withdrawn no recibe foco
        solo. Hay que forzarlo después de que el WM lo haya mapeado."""
        try:
            self.lift()
            self.attributes("-topmost", True)
            self.after(200, lambda: self.attributes("-topmost", False))
            self.focus_force()
            self.after(50, self._enfocar_continuar)
        except Exception:
            pass

    def _enfocar_continuar(self):
        try:
            self.focus_force()
        except Exception:
            pass

    def _centrar(self, master):
        self.update_idletasks()
        ancho = 480
        alto = self.winfo_reqheight()
        try:
            master.update_idletasks()
            x = master.winfo_rootx() + (master.winfo_width() - ancho) // 2
            y = master.winfo_rooty() + (master.winfo_height() - alto) // 2
        except Exception:
            x = (self.winfo_screenwidth() - ancho) // 2
            y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(x, 0)}+{max(y, 0)}")

    def _copiar(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self._password)
            self.update()
            self._lbl_pwd.configure(foreground="#0a7c2f")
        except Exception:
            pass

    def _toggle_continuar(self):
        estado = "normal" if self._var_ok.get() else "disabled"
        self._btn_continuar.configure(state=estado)

    def _continuar_click(self):
        self.confirmo = True
        self.destroy()

    def _cancelar(self):
        self.confirmo = False
        self.destroy()


# ---------------------------------------------------------------
# Login
# ---------------------------------------------------------------

class DialogoLogin(ttk.Toplevel):
    """Login modal. Al acertar, inicia la sesión y se cierra."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Iniciar sesión — Vet Suite")
        self.resizable(False, False)
        # Ver nota en DialogoPrimerArranque sobre transient/grab_set.

        frame = ttk.Frame(self, padding=28)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            frame, text="🩺  Vet Suite",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            frame, text="Inicia sesión para continuar.",
            font=("Segoe UI", 10), foreground="gray",
        ).pack(anchor="w", pady=(4, 20))

        # Usuario
        ttk.Label(frame, text="Usuario",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.var_usuario = tk.StringVar()
        self.entry_usuario = ttk.Entry(
            frame, textvariable=self.var_usuario, width=32,
            font=("Segoe UI", 11),
        )
        self.entry_usuario.pack(fill=X, pady=(2, 12))

        # Contraseña
        ttk.Label(frame, text="Contraseña",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.var_password = tk.StringVar()
        self.entry_password = ttk.Entry(
            frame, textvariable=self.var_password, width=32,
            show="•", font=("Segoe UI", 11),
        )
        self.entry_password.pack(fill=X, pady=(2, 8))

        # Mensaje de error
        self.lbl_error = ttk.Label(
            frame, text="", foreground="#c0392b",
            font=("Segoe UI", 9),
        )
        self.lbl_error.pack(anchor="w", pady=(0, 12))

        # Botones
        barra = ttk.Frame(frame)
        barra.pack(fill=X, pady=(4, 0))
        
        self.btn_entrar = ttk.Button(
            barra, text="Entrar",
            command=self._intentar, bootstyle="success",
        )
        self.btn_entrar.pack(side=RIGHT)

        # Atajos
        for w in (self.entry_usuario, self.entry_password):
            w.bind("<Return>", lambda _e: self._intentar())
        self.bind("<Escape>", lambda _e: self._cancelar())

        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        self._centrar(master)
        self._traer_al_frente()

    def _traer_al_frente(self):
        """Fuerza el diálogo al frente y le da foco.
        Necesario en macOS cuando el master está withdrawn."""
        try:
            self.lift()
            self.attributes("-topmost", True)
            self.after(200, lambda: self.attributes("-topmost", False))
            self.focus_force()
            self.after(50, self.entry_usuario.focus_set)
        except Exception:
            pass

        # Foco inicial
        self.after(50, self.entry_usuario.focus_set)

    def _centrar(self, master):
        self.update_idletasks()
        ancho = 380
        alto = self.winfo_reqheight()
        try:
            master.update_idletasks()
            x = master.winfo_rootx() + (master.winfo_width() - ancho) // 2
            y = master.winfo_rooty() + (master.winfo_height() - alto) // 2
        except Exception:
            x = (self.winfo_screenwidth() - ancho) // 2
            y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(x, 0)}+{max(y, 0)}")

    def _intentar(self):
        uid = self.var_usuario.get().strip().lower()
        pwd = self.var_password.get()

        if not uid or not pwd:
            self._mostrar_error("Escribe usuario y contraseña.")
            return

        # Buscar usuario
        u = usuarios.obtener(uid)

        # Validaciones (mensaje genérico, no revelamos cuál falló)
        valido = (
            u is not None
            and u.get("activo", True)
            and auth.verificar_password(pwd, u.get("password_hash", ""))
        )

        if not valido:
            self._mostrar_error("Usuario o contraseña incorrectos.")
            self.var_password.set("")
            self.entry_password.focus_set()
            return

        # Éxito
        try:
            usuarios.marcar_login(uid)
        except Exception:
            pass   # no bloqueamos el login por un fallo al sellar la fecha

        sesion.iniciar_sesion(u)
        self.destroy()

    def _mostrar_error(self, msg: str):
        self.lbl_error.configure(text=msg)

    def _cancelar(self):
        sesion.cerrar_sesion()
        self.destroy()