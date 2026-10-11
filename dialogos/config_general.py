# -*- coding: utf-8 -*-
"""
dialogos/config_general.py
Configuración general: Apariencia + Veterinaria.
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
from core.geocoding import geocodificar


def abrir_dialogo_config_general(app):
    DialogoConfigGeneral(app)


class DialogoConfigGeneral(ttk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("⚙️ Configuración")
        from ui.utils import configurar_ventana
        configurar_ventana(master, self, ancho=700, alto=550,
                           min_ancho=650, min_alto=500,
                           centrar_en_padre=True)

        ttk.Label(self, text="⚙️ Configuración general",
                  font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=True, padx=15, pady=10)

        self.tab_apariencia = ttk.Frame(self.notebook, padding=15)
        self.tab_veterinaria = ttk.Frame(self.notebook, padding=15)

        self.notebook.add(self.tab_apariencia, text="🎨 Apariencia")
        self.notebook.add(self.tab_veterinaria, text="🏥 Veterinaria")

        self._construir_tab_apariencia()
        self._construir_tab_veterinaria()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())

    # ---------- Apariencia ----------

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

    # ---------- Veterinaria ----------

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

    # NOTA: se eliminó `destroy()` personalizado que referenciaba
    # `self.var_nombre` (ya no existe ese campo). El JSON se guarda
    # directamente en cada acción (marcar activa, guardar sucursal, etc.),
    # no hace falta guardar nada al cerrar.


# ============================================================
# Diálogo de detalle de sucursal
# ============================================================

class DialogoSucursalDetalle(ttk.Toplevel):
    def __init__(self, master, sucursal: dict, on_guardar):
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
        import re
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