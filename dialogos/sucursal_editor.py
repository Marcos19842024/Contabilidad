# dialogos/sucursal_editor.py
"""
Diálogo para editar el catálogo de sucursales.
Permite agregar, editar, activar/desactivar sucursales.
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.utils import configurar_ventana

from core.recordatorios.sucursales import (
    cargar_sucursales,
    guardar_sucursales,
)


class DialogoSucursalEditor(ttk.Toplevel):
    def __init__(self, master, on_guardar=None):
        super().__init__(master)
        self.title("Configurar sucursales")
        configurar_ventana(master, self, ancho=760, alto=520,
                           min_ancho=650, min_alto=450, centrar_en_padre=True)

        self.on_guardar = on_guardar
        self.data = cargar_sucursales()

        self._construir_ui()
        self._refrescar_tabla()

    def _construir_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            frame,
            text="Sucursales disponibles",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            frame,
            text="Solo las sucursales activas aparecerán en el selector del módulo.",
            foreground="gray",
        ).pack(anchor="w", pady=(0, 8))

        # Tabla
        contenedor = ttk.Frame(frame)
        contenedor.pack(fill=BOTH, expand=True)

        cols = ("activa", "id", "nombre", "nombre_corto")
        self.tabla = ttk.Treeview(
            contenedor, columns=cols, show="headings",
            height=10, bootstyle="primary",
        )
        self.tabla.heading("activa", text="✔")
        self.tabla.heading("id", text="ID")
        self.tabla.heading("nombre", text="NOMBRE COMPLETO")
        self.tabla.heading("nombre_corto", text="NOMBRE CORTO")

        self.tabla.column("activa", width=40, anchor="center")
        self.tabla.column("id", width=130, anchor="center")
        self.tabla.column("nombre", width=300, anchor="w")
        self.tabla.column("nombre_corto", width=180, anchor="w")

        sb = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)

        self.tabla.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        self.tabla.bind("<Double-1>", self._editar)

        # Botones
        barra = ttk.Frame(frame)
        barra.pack(fill=X, pady=(10, 0))

        ttk.Button(barra, text="+ Nueva", command=self._nueva,
                   bootstyle="success-outline").pack(side=LEFT, padx=3)
        ttk.Button(barra, text="✏️ Editar", command=self._editar,
                   bootstyle="info-outline").pack(side=LEFT, padx=3)
        ttk.Button(barra, text="🗑️ Eliminar", command=self._eliminar,
                   bootstyle="danger-outline").pack(side=LEFT, padx=3)

        ttk.Button(barra, text="💾 Guardar", command=self._guardar_y_cerrar,
                   bootstyle="success").pack(side=RIGHT, padx=3)
        ttk.Button(barra, text="Cancelar", command=self.destroy,
                   bootstyle="secondary-outline").pack(side=RIGHT)

        self.protocol("WM_DELETE_WINDOW", self._guardar_y_cerrar)

    def _refrescar_tabla(self):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        for idx, s in enumerate(self.data["sucursales"]):
            activa = "✅" if s.get("activa", False) else "⬜"
            self.tabla.insert("", END, iid=str(idx), values=(
                activa, s.get("id", ""), s.get("nombre", ""),
                s.get("nombre_corto", ""),
            ))

    def _nueva(self):
        DialogoSucursalDetalle(self, None, on_guardar=self._recibir_sucursal)

    def _editar(self, event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        idx = int(sel[0])
        s = self.data["sucursales"][idx]
        DialogoSucursalDetalle(self, s, on_guardar=lambda s2: self._recibir_sucursal(s2, idx))

    def _recibir_sucursal(self, sucursal: dict, idx: int = None):
        if idx is None:
            self.data["sucursales"].append(sucursal)
        else:
            self.data["sucursales"][idx] = sucursal
        self._refrescar_tabla()

    def _eliminar(self):
        sel = self.tabla.selection()
        if not sel:
            return
        idx = int(sel[0])
        s = self.data["sucursales"][idx]
        if not messagebox.askyesno("Confirmar",
                                   f"¿Eliminar la sucursal '{s.get('nombre')}'?",
                                   parent=self):
            return
        # No permitir eliminar la activa
        if s["id"] == self.data.get("sucursal_activa"):
            messagebox.showwarning(
                "No se puede eliminar",
                "Es la sucursal activa. Cambia primero la activa.",
                parent=self,
            )
            return
        self.data["sucursales"].pop(idx)
        self._refrescar_tabla()

    def _guardar_y_cerrar(self):
        guardar_sucursales(self.data)
        if self.on_guardar:
            self.on_guardar()
        self.destroy()


# ============================================================
# Diálogo de detalle de sucursal
# ============================================================

class DialogoSucursalDetalle(ttk.Toplevel):
    def __init__(self, master, sucursal: dict, on_guardar):
        super().__init__(master)
        self.title("Sucursal")
        configurar_ventana(master, self, ancho=520, alto=460,
                           min_ancho=450, min_alto=400, centrar_en_padre=True)

        self.sucursal = dict(sucursal) if sucursal else {}
        self.es_nueva = sucursal is None
        self.on_guardar = on_guardar

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        # ID
        ttk.Label(frame, text="ID (mayúsculas, sin espacios):").grid(
            row=0, column=0, sticky="e", padx=6, pady=6)
        self.var_id = tk.StringVar(value=self.sucursal.get("id", ""))
        ttk.Entry(frame, textvariable=self.var_id, width=40).grid(
            row=0, column=1, sticky="w")

        # Nombre completo
        ttk.Label(frame, text="Nombre completo:").grid(
            row=1, column=0, sticky="e", padx=6, pady=6)
        self.var_nombre = tk.StringVar(value=self.sucursal.get("nombre", ""))
        ttk.Entry(frame, textvariable=self.var_nombre, width=40).grid(
            row=1, column=1, sticky="w")

        ttk.Label(frame, text="Ej: Clínica Veterinaria Baalak (Central)",
                  foreground="gray", font=("Segoe UI", 8)).grid(
            row=2, column=1, sticky="w", pady=(0, 4))

        # Nombre corto
        ttk.Label(frame, text="Nombre corto:").grid(
            row=3, column=0, sticky="e", padx=6, pady=6)
        self.var_corto = tk.StringVar(value=self.sucursal.get("nombre_corto", ""))
        ttk.Entry(frame, textvariable=self.var_corto, width=40).grid(
            row=3, column=1, sticky="w")

        ttk.Label(frame, text="Ej: Baalak (Central)",
                  foreground="gray", font=("Segoe UI", 8)).grid(
            row=4, column=1, sticky="w", pady=(0, 4))

        # Activa
        self.var_activa = tk.BooleanVar(value=self.sucursal.get("activa", True))
        ttk.Checkbutton(
            frame, text="Sucursal activa",
            variable=self.var_activa, bootstyle="round-toggle",
        ).grid(row=5, column=1, sticky="w", pady=10)

        # Coordenadas
        ttk.Label(frame, text="Latitud:").grid(
            row=6, column=0, sticky="e", padx=6, pady=6)
        coords = self.sucursal.get("coordenadas", {})
        self.var_lat = tk.StringVar(value=str(coords.get("lat", "")))
        ttk.Entry(frame, textvariable=self.var_lat, width=20).grid(
            row=6, column=1, sticky="w")

        ttk.Label(frame, text="Longitud:").grid(
            row=7, column=0, sticky="e", padx=6, pady=6)
        self.var_lng = tk.StringVar(value=str(coords.get("lng", "")))
        ttk.Entry(frame, textvariable=self.var_lng, width=20).grid(
            row=7, column=1, sticky="w")

        # Botones
        barra = ttk.Frame(frame)
        barra.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        ttk.Button(barra, text="💾 Guardar", command=self._guardar,
                   bootstyle="success").pack(side=RIGHT, padx=4)
        ttk.Button(barra, text="Cancelar", command=self.destroy,
                   bootstyle="secondary-outline").pack(side=RIGHT)

    def _guardar(self):
        sid = self.var_id.get().strip().upper().replace(" ", "_")
        nombre = self.var_nombre.get().strip()
        corto = self.var_corto.get().strip()

        if not sid or not nombre:
            messagebox.showwarning(
                "Faltan datos",
                "El ID y el nombre completo son obligatorios.",
                parent=self,
            )
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
            "activa": bool(self.var_activa.get()),
            "coordenadas": {"lat": lat, "lng": lng},
        }
        self.on_guardar(sucursal)
        self.destroy()