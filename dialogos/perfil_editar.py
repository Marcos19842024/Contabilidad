# -*- coding: utf-8 -*-
"""
dialogos/perfil_editar.py
Alta y edición de perfiles. Solo admin.

Uso:
    DialogoPerfilEditar(master, perfil=None, on_guardar=callback)  # alta
    DialogoPerfilEditar(master, perfil=Perfil, on_guardar=callback)  # edición

Al guardar, el callback recibe el Perfil construido. NO persiste: eso
es responsabilidad del caller (que usa shared.perfiles.agregar_perfil
o actualizar_perfil).

Reglas:
  - El id es estable. Al editar no se puede cambiar.
  - El perfil admin nunca se edita desde aquí (el caller no debe abrir
    el diálogo con admin).
  - Módulos: checkboxes explícitos. Sin botón "Todos".
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from shared.perfiles import Perfil, id_perfil_es_valido
from shared.registro_modulos import MODULOS, CATEGORIAS


class DialogoPerfilEditar(ttk.Toplevel):
    def __init__(self, master, perfil: Perfil | None = None, on_guardar=None):
        super().__init__(master)
        self.es_nuevo = perfil is None
        self.perfil_original = perfil
        self.on_guardar = on_guardar

        self.title("Nuevo perfil" if self.es_nuevo else "Editar perfil")
        self.resizable(False, False)

        from ui.utils import configurar_ventana
        configurar_ventana(master, self, ancho=520, alto=550,
                           min_ancho=480, min_alto=500,
                           centrar_en_padre=True)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        fila = 0

        # ---- ID ----
        ttk.Label(frame, text="ID del perfil",
                  font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(0, 4)); fila += 1
        self.var_id = tk.StringVar(
            value=perfil.id if perfil else "")
        self.entry_id = ttk.Entry(frame, textvariable=self.var_id, width=32)
        self.entry_id.grid(row=fila, column=0, sticky="we", pady=(0, 4)); fila += 1
        if not self.es_nuevo:
            self.entry_id.configure(state="disabled")
        ttk.Label(frame,
                  text="Minúsculas, sin espacios. Empieza con letra. "
                       "Solo a-z, 0-9, _ (3–32). No se puede cambiar después.",
                  foreground="gray", font=("Segoe UI", 8),
                  wraplength=460, justify="left").grid(
            row=fila, column=0, sticky="w", pady=(0, 12)); fila += 1

        # ---- Nombre ----
        ttk.Label(frame, text="Nombre visible",
                  font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(0, 4)); fila += 1
        self.var_nombre = tk.StringVar(
            value=perfil.nombre if perfil else "")
        ttk.Entry(frame, textvariable=self.var_nombre, width=32).grid(
            row=fila, column=0, sticky="we", pady=(0, 12)); fila += 1

        # ---- Descripción ----
        ttk.Label(frame, text="Descripción (opcional)",
                  font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(0, 4)); fila += 1
        self.var_desc = tk.StringVar(
            value=perfil.descripcion if perfil else "")
        ttk.Entry(frame, textvariable=self.var_desc, width=32).grid(
            row=fila, column=0, sticky="we", pady=(0, 12)); fila += 1

        # ---- Módulos ----
        ttk.Label(frame, text="Módulos visibles",
                  font=("Segoe UI", 10, "bold")).grid(
            row=fila, column=0, sticky="w", pady=(0, 4)); fila += 1
        ttk.Label(frame,
                  text="Marca los módulos que este perfil podrá ver. "
                       "Si un módulo está desactivado globalmente, no se "
                       "mostrará aunque esté marcado aquí.",
                  foreground="gray", font=("Segoe UI", 8),
                  wraplength=460, justify="left").grid(
            row=fila, column=0, sticky="w", pady=(0, 8)); fila += 1

        # Frame con borde para los checkboxes
        mods_frame = ttk.LabelFrame(frame, text="", padding=10)
        mods_frame.grid(row=fila, column=0, sticky="we", pady=(0, 12)); fila += 1

        # Determinar qué módulos están marcados
        if perfil and perfil.modulos == "*":
            modulos_marcados = {m.id for m in MODULOS}
        elif perfil:
            modulos_marcados = set(perfil.modulos)
        else:
            modulos_marcados = set()

        self.vars_modulos: dict[str, tk.BooleanVar] = {}

        # Agrupar por categoría respetando orden
        por_cat: dict[str, list] = {}
        for m in MODULOS:
            por_cat.setdefault(m.categoria, []).append(m)

        for cat_id, mods in sorted(
            por_cat.items(),
            key=lambda kv: CATEGORIAS.get(kv[0], {}).get("orden", 99),
        ):
            etiqueta = CATEGORIAS.get(cat_id, {}).get("nombre", cat_id.title())
            ttk.Label(mods_frame, text=etiqueta,
                      font=("Segoe UI", 9, "bold")).pack(
                anchor="w", pady=(6, 2))
            for m in mods:
                var = tk.BooleanVar(value=m.id in modulos_marcados)
                self.vars_modulos[m.id] = var
                ttk.Checkbutton(
                    mods_frame,
                    text=f"{m.icono}  {m.nombre}",
                    variable=var,
                ).pack(anchor="w", padx=(16, 0), pady=1)

        # ---- Botón Guardar ----
        barra = ttk.Frame(frame)
        barra.grid(row=fila, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(barra, text="💾 Guardar",
                   command=self._guardar,
                   bootstyle="success").pack(side=RIGHT)

        frame.columnconfigure(0, weight=1)
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", lambda _e: self._guardar())
        self.after(50, self._foco_inicial)

    def _foco_inicial(self):
        if self.es_nuevo:
            self.entry_id.focus_set()
        else:
            self.entry_id.focus_set() if self.es_nuevo else None

    def _guardar(self):
        pid = self.var_id.get().strip().lower()
        nombre = self.var_nombre.get().strip()
        desc = self.var_desc.get().strip()

        if not pid or not nombre:
            messagebox.showwarning("Faltan datos",
                                    "ID y nombre son obligatorios.",
                                    parent=self)
            return
        if self.es_nuevo and not id_perfil_es_valido(pid):
            messagebox.showwarning(
                "ID inválido",
                "El ID debe empezar con letra y usar solo a-z, 0-9, _ "
                "(3–32 caracteres).",
                parent=self)
            return

        modulos = tuple(mid for mid, var in self.vars_modulos.items() if var.get())

        perfil = Perfil(
            id=pid,
            nombre=nombre,
            descripcion=desc,
            modulos=modulos,
            puede_configurar=False,
        )
        if self.on_guardar:
            try:
                self.on_guardar(perfil, self.es_nuevo)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)
                return
        self.destroy()