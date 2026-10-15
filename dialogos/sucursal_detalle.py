# -*- coding: utf-8 -*-
"""
dialogos/sucursal_detalle.py
Diálogo de alta/edición de sucursal.

Se usa desde Config General → tab 🏥 Veterinaria.
Vive en su propio archivo para no mezclar responsabilidades con
dialogos/config_general.py.
"""

import re
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from core.geocoding import geocodificar


class DialogoSucursalDetalle(ttk.Toplevel):
    def __init__(self, master, sucursal: dict | None, on_guardar):
        super().__init__(master)
        self.title("Sucursal")
        from ui.utils import configurar_ventana
        configurar_ventana(master, self, ancho=400, alto=380,
                           min_ancho=350, min_alto=350,
                           centrar_en_padre=True)

        self.sucursal = dict(sucursal) if sucursal else {}
        self.es_nueva = sucursal is None
        self.on_guardar = on_guardar

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="ID:").grid(row=0, column=0, sticky="e",
                                            padx=6, pady=6)
        self.var_id = tk.StringVar(value=self.sucursal.get("id", ""))
        ttk.Entry(frame, textvariable=self.var_id, width=25).grid(
            row=0, column=1, columnspan=2, sticky="w")

        ttk.Label(frame, text="Nombre completo:").grid(row=1, column=0,
                                                        sticky="e",
                                                        padx=6, pady=6)
        self.var_nombre = tk.StringVar(value=self.sucursal.get("nombre", ""))
        ttk.Entry(frame, textvariable=self.var_nombre, width=25).grid(
            row=1, column=1, columnspan=2, sticky="w")

        ttk.Label(frame, text="Nombre corto:").grid(row=2, column=0,
                                                     sticky="e",
                                                     padx=6, pady=6)
        self.var_corto = tk.StringVar(value=self.sucursal.get("nombre_corto", ""))
        ttk.Entry(frame, textvariable=self.var_corto, width=25).grid(
            row=2, column=1, columnspan=2, sticky="w")

        ttk.Label(frame, text="Dirección:").grid(row=3, column=0,
                                                   sticky="e", padx=6, pady=6)
        self.var_dir = tk.StringVar(value=self.sucursal.get("direccion", ""))
        ttk.Entry(frame, textvariable=self.var_dir, width=25).grid(
            row=3, column=1, columnspan=2, sticky="w")

        ttk.Label(frame, text="Teléfono:").grid(row=4, column=0,
                                                  sticky="e", padx=6, pady=6)
        self.var_tel = tk.StringVar(value=self.sucursal.get("telefono", ""))
        ttk.Entry(frame, textvariable=self.var_tel, width=25).grid(
            row=4, column=1, columnspan=2, sticky="w")

        ttk.Label(frame, text="Coordenadas",
                  font=("Segoe UI", 10, "bold")).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(10, 4))

        coords = self.sucursal.get("coordenadas", {})
        ttk.Label(frame, text="Latitud:").grid(row=6, column=0, sticky="e",
                                                 padx=6, pady=6)
        self.var_lat = tk.StringVar(value=str(coords.get("lat", "") or ""))
        ttk.Entry(frame, textvariable=self.var_lat, width=25).grid(
            row=6, column=1, sticky="w")

        ttk.Label(frame, text="Longitud:").grid(row=7, column=0, sticky="e",
                                                  padx=6, pady=6)
        self.var_lng = tk.StringVar(value=str(coords.get("lng", "") or ""))
        ttk.Entry(frame, textvariable=self.var_lng, width=25).grid(
            row=7, column=1, sticky="w")

        barra_coords = ttk.Frame(frame)
        barra_coords.grid(row=8, column=0, columnspan=3, sticky="w", pady=4)
        ttk.Button(barra_coords, text="📋 Pegar del portapapeles",
                   command=self._pegar_coords,
                   bootstyle="secondary-outline").pack(side=LEFT, padx=(0, 6))
        ttk.Button(barra_coords, text="🔎 Buscar por dirección",
                   command=self._buscar_coords,
                   bootstyle="info-outline").pack(side=LEFT)

        barra = ttk.Frame(frame)
        barra.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        ttk.Button(barra, text="💾 Guardar", command=self._guardar,
                   bootstyle="success").pack(side=LEFT)

    def _pegar_coords(self):
        try:
            texto = self.clipboard_get()
        except tk.TclError:
            texto = ""
        patron = r"(-?\d{1,3}\.\d{4,})\s*,\s*(-?\d{1,3}\.\d{4,})"
        match = re.search(patron, texto) if texto else None
        if not match:
            messagebox.showwarning(
                "Sin coordenadas",
                "El portapapeles no tiene coordenadas.\n\n"
                "Formatos aceptados:\n"
                "  • 19.8421, -90.5189\n"
                "  • https://maps.google.com/?q=19.8421,-90.5189",
                parent=self)
            return
        self.var_lat.set(f"{float(match.group(1)):.6f}")
        self.var_lng.set(f"{float(match.group(2)):.6f}")

    def _buscar_coords(self):
        direccion = self.var_dir.get().strip()
        if not direccion:
            messagebox.showinfo("Falta dirección",
                                "Escribe primero la dirección.", parent=self)
            return
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            r = geocodificar(direccion)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Error", str(e), parent=self)
            return
        self.config(cursor="")
        if not r:
            messagebox.showinfo("Sin coincidencia",
                                "No se encontró. Pega las coords a mano.",
                                parent=self)
            return
        self.var_lat.set(f"{r[0]:.6f}")
        self.var_lng.set(f"{r[1]:.6f}")

    def _guardar(self):
        sid = self.var_id.get().strip().upper().replace(" ", "_")
        nombre = self.var_nombre.get().strip()
        corto = self.var_corto.get().strip()
        if not sid or not nombre:
            messagebox.showwarning("Faltan datos",
                                    "ID y nombre completo son obligatorios.",
                                    parent=self)
            return
        try:
            lat = float(self.var_lat.get()) if self.var_lat.get() else None
            lng = float(self.var_lng.get()) if self.var_lng.get() else None
        except ValueError:
            messagebox.showwarning("Coordenadas inválidas",
                                    "Lat/Lng deben ser números.",
                                    parent=self)
            return
        sucursal = {
            "id": sid,
            "nombre": nombre,
            "nombre_corto": corto or nombre,
            "direccion": self.var_dir.get().strip(),
            "telefono": self.var_tel.get().strip(),
            "activa": self.sucursal.get("activa", True),
            "coordenadas": {"lat": lat, "lng": lng},
        }
        self.on_guardar(sucursal)
        self.destroy()