# dialogos/mascota_editar.py
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.utils import configurar_ventana
from modulos.estetica_transportes import clave_busqueda


class DialogoMascota(ttk.Toplevel):
    """
    Alta / edición de mascota.
    - Autoguardado al cerrar con la X.
    - Valida que no exista otra mascota con el mismo nombre
      para el mismo cliente.
    - on_guardar(mascota) o on_guardar(mascota, idx) si es edición
    - on_eliminar() opcional (solo en edición)
    """

    def __init__(self, master, mascota, existentes=None,
                 on_guardar=None, on_eliminar=None):
        super().__init__(master)
        self.title("Mascota")
        configurar_ventana(master, self, ancho=560, alto=520, centrar_en_padre=True)

        self.mascota = dict(mascota or {})
        self.existentes = existentes or []
        self.on_guardar = on_guardar
        self.on_eliminar = on_eliminar
        self.es_edicion = mascota is not None

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        campos = [
            ("nombre", "Nombre mascota"),
            ("raza", "Raza"),
            ("caracter", "Carácter"),
            ("precauciones", "Precauciones"),
            ("servicio", "Servicio habitual"),
            ("duracion_min", "Duración (min)"),
        ]
        self.vars = {}
        for i, (key, label) in enumerate(campos):
            ttk.Label(frame, text=label + ":").grid(row=i, column=0, sticky="e",
                                                    padx=6, pady=6)
            v = tk.StringVar(value=str(self.mascota.get(key, "")))
            self.vars[key] = v
            ttk.Entry(frame, textvariable=v, width=42).grid(row=i, column=1, sticky="w")

        ttk.Label(frame, text="Notas:").grid(row=len(campos), column=0,
                                             sticky="ne", padx=6, pady=6)
        self.txt_notas = tk.Text(frame, width=42, height=5)
        self.txt_notas.grid(row=len(campos), column=1, sticky="w")
        self.txt_notas.insert("1.0", self.mascota.get("notas", ""))

        if self.es_edicion and self.on_eliminar:
            ttk.Button(frame, text="🗑️ Eliminar mascota",
                       command=self._eliminar,
                       bootstyle="danger-outline").grid(
                row=len(campos) + 1, column=0, columnspan=2,
                sticky="w", pady=(15, 0)
            )

        self.protocol("WM_DELETE_WINDOW", self._cerrar_y_guardar)

    def _validar(self):
        nombre = self.vars["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("Falta nombre",
                                   "El nombre de la mascota es obligatorio.",
                                   parent=self)
            return False
        clave = clave_busqueda(nombre)
        for m in self.existentes:
            if clave_busqueda(m.get("nombre", "")) == clave:
                messagebox.showwarning(
                    "Mascota duplicada",
                    f"Ya existe una mascota llamada '{m.get('nombre')}' "
                    f"para este cliente.",
                    parent=self,
                )
                return False
        return True

    def _cerrar_y_guardar(self):
        # Si el usuario no escribió nada y no es edición, simplemente cerrar
        if not any(v.get().strip() for v in self.vars.values()) \
                and not self.txt_notas.get("1.0", "end").strip() \
                and not self.es_edicion:
            self.destroy()
            return

        if not self._validar():
            return

        m = dict(self.mascota)
        for k, v in self.vars.items():
            m[k] = v.get().strip()
        m["notas"] = self.txt_notas.get("1.0", "end").strip()
        self.on_guardar(m)
        self.destroy()

    def _eliminar(self):
        if not messagebox.askyesno("Confirmar",
                                   f"¿Eliminar a '{self.mascota.get('nombre')}'?",
                                   parent=self):
            return
        self.on_eliminar()
        self.destroy()