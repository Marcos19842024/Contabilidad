# dialogos/catalogo_editor.py
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.utils import configurar_ventana

from core.rutas_estetica import SERVICIOS_ESTETICA, TARIFAS_TRANSPORTE
from modulos.estetica_transportes import _cargar_json, _guardar_json


# ============================================================
# Diálogo de edición de un servicio de estética
# ============================================================
class DialogoServicioEstetica(ttk.Toplevel):
    def __init__(self, master, servicio, on_guardar, on_eliminar):
        super().__init__(master)
        self.title("Editar servicio de estética")
        configurar_ventana(master, self, ancho=520, alto=200, centrar_en_padre=True)

        self.servicio = dict(servicio)  # copia
        self.on_guardar = on_guardar
        self.on_eliminar = on_eliminar

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        # Código
        ttk.Label(frame, text="Código:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.var_codigo = tk.StringVar(value=self.servicio.get("codigo", ""))
        ttk.Entry(frame, textvariable=self.var_codigo, width=40).grid(row=0, column=1, sticky="w")

        # Descripción
        ttk.Label(frame, text="Descripción:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.var_desc = tk.StringVar(value=self.servicio.get("descripcion", ""))
        ttk.Entry(frame, textvariable=self.var_desc, width=40).grid(row=1, column=1, sticky="w")

        # Precio
        ttk.Label(frame, text="Precio:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.var_precio = tk.StringVar(value=str(self.servicio.get("precio", "")))
        ttk.Entry(frame, textvariable=self.var_precio, width=15).grid(row=2, column=1, sticky="w")

        # Duración
        ttk.Label(frame, text="Duración (min):").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.var_dur = tk.StringVar(value=str(self.servicio.get("duracion_min", "")))
        ttk.Entry(frame, textvariable=self.var_dur, width=15).grid(row=3, column=1, sticky="w")

        # Botonera
        barra = ttk.Frame(frame)
        barra.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        ttk.Button(barra, text="🗑️ Eliminar", command=self._eliminar,
                   bootstyle="danger-outline").pack(side=LEFT)
        ttk.Button(barra, text="💾 Guardar cambios", command=self._guardar,
                   bootstyle="success").pack(side=RIGHT)

        # Al cerrar con la X → guardar
        self.protocol("WM_DELETE_WINDOW", self._guardar_y_cerrar)

    def _guardar(self):
        try:
            precio = float(self.var_precio.get() or 0)
        except ValueError:
            messagebox.showwarning("Precio inválido", "El precio debe ser numérico.", parent=self)
            return False
        try:
            dur = int(self.var_dur.get() or 0)
        except ValueError:
            messagebox.showwarning("Duración inválida", "La duración debe ser un número entero.", parent=self)
            return False

        self.servicio["codigo"] = self.var_codigo.get().strip()
        self.servicio["descripcion"] = self.var_desc.get().strip()
        self.servicio["precio"] = precio
        self.servicio["duracion_min"] = dur
        self.on_guardar(self.servicio)
        return True

    def _guardar_y_cerrar(self):
        if self._guardar():
            self.destroy()

    def _eliminar(self):
        if not messagebox.askyesno("Confirmar",
                                   f"¿Eliminar '{self.servicio.get('codigo')}'?",
                                   parent=self):
            return
        self.on_eliminar(self.servicio)
        self.destroy()


# ============================================================
# Diálogo de edición de una tarifa de transporte
# ============================================================
class DialogoTarifaTransporte(ttk.Toplevel):
    def __init__(self, master, tarifa, on_guardar, on_eliminar):
        super().__init__(master)
        self.title("Editar tarifa de transporte")
        configurar_ventana(master, self, ancho=520, alto=150, centrar_en_padre=True)

        self.tarifa = dict(tarifa)
        self.on_guardar = on_guardar
        self.on_eliminar = on_eliminar

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="Código:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.var_codigo = tk.StringVar(value=self.tarifa.get("codigo", ""))
        ttk.Entry(frame, textvariable=self.var_codigo, width=40).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Precio:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.var_precio = tk.StringVar(value=str(self.tarifa.get("precio", "")))
        ttk.Entry(frame, textvariable=self.var_precio, width=15).grid(row=1, column=1, sticky="w")

        barra = ttk.Frame(frame)
        barra.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        ttk.Button(barra, text="🗑️ Eliminar", command=self._eliminar,
                   bootstyle="danger-outline").pack(side=LEFT)
        ttk.Button(barra, text="💾 Guardar cambios", command=self._guardar,
                   bootstyle="success").pack(side=RIGHT)

        self.protocol("WM_DELETE_WINDOW", self._guardar_y_cerrar)

    def _guardar(self):
        try:
            precio = float(self.var_precio.get() or 0)
        except ValueError:
            messagebox.showwarning("Precio inválido", "El precio debe ser numérico.", parent=self)
            return False
        self.tarifa["codigo"] = self.var_codigo.get().strip()
        self.tarifa["precio"] = precio
        self.on_guardar(self.tarifa)
        return True

    def _guardar_y_cerrar(self):
        if self._guardar():
            self.destroy()

    def _eliminar(self):
        if not messagebox.askyesno("Confirmar",
                                   f"¿Eliminar '{self.tarifa.get('codigo')}'?",
                                   parent=self):
            return
        self.on_eliminar(self.tarifa)
        self.destroy()


# ============================================================
# Ventana principal del catálogo
# ============================================================
class DialogoCatalogo(ttk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Catálogos editables")
        configurar_ventana(master, self, ancho=820, alto=620,
                           min_ancho=700, min_alto=500, centrar_en_padre=True)

        self.servicios = _cargar_json(SERVICIOS_ESTETICA, [])
        self.tarifas = _cargar_json(TARIFAS_TRANSPORTE, [])

        nb = ttk.Notebook(self)
        nb.pack(fill=BOTH, expand=True, padx=8, pady=8)

        self.tab_serv = ttk.Frame(nb, padding=8)
        self.tab_tar = ttk.Frame(nb, padding=8)
        nb.add(self.tab_serv, text="Servicios de estética")
        nb.add(self.tab_tar, text="Tarifas de transporte")

        self._construir_servicios()
        self._construir_tarifas()

        # Al cerrar, persistir todo
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    # ---------- Servicios ----------

    def _construir_servicios(self):
        f = self.tab_serv
        cols = ("codigo", "descripcion", "precio", "duracion")
        self.tabla_serv = ttk.Treeview(f, columns=cols, show="headings",
                                       bootstyle="primary")
        for c, t, w in [
            ("codigo", "Código", 180),
            ("descripcion", "Descripción", 320),
            ("precio", "Precio", 100),
            ("duracion", "Duración (min)", 120),
        ]:
            self.tabla_serv.heading(c, text=t)
            self.tabla_serv.column(c, width=w,
                                   anchor="center" if c != "descripcion" else "w")
        self.tabla_serv.pack(fill=BOTH, expand=True)
        self.tabla_serv.bind("<Double-1>", self._editar_servicio)
        self._refrescar_servicios()

    def _refrescar_servicios(self):
        for i in self.tabla_serv.get_children():
            self.tabla_serv.delete(i)
        for s in self.servicios:
            self.tabla_serv.insert("", END, iid=str(s["id"]), values=(
                s.get("codigo", ""),
                s.get("descripcion", ""),
                f"${s.get('precio', 0):,.2f}",
                s.get("duracion_min", ""),
            ))

    def _editar_servicio(self, event=None):
        sel = self.tabla_serv.selection()
        if not sel:
            return
        sid = int(sel[0])
        servicio = next((s for s in self.servicios if s["id"] == sid), None)
        if not servicio:
            return

        def _guardar(srv):
            _guardar_json(SERVICIOS_ESTETICA, self.servicios)
            self._refrescar_servicios()

        def _eliminar(srv):
            self.servicios = [s for s in self.servicios if s["id"] != srv["id"]]
            _guardar_json(SERVICIOS_ESTETICA, self.servicios)
            self._refrescar_servicios()

        DialogoServicioEstetica(self, servicio, _guardar, _eliminar)

    # ---------- Tarifas ----------

    def _construir_tarifas(self):
        f = self.tab_tar
        cols = ("codigo", "precio")
        self.tabla_tar = ttk.Treeview(f, columns=cols, show="headings",
                                      bootstyle="primary")
        for c, t, w in [("codigo", "Código", 400), ("precio", "Precio", 120)]:
            self.tabla_tar.heading(c, text=t)
            self.tabla_tar.column(c, width=w, anchor="w" if c == "codigo" else "center")
        self.tabla_tar.pack(fill=BOTH, expand=True)
        self.tabla_tar.bind("<Double-1>", self._editar_tarifa)
        self._refrescar_tarifas()

    def _refrescar_tarifas(self):
        for i in self.tabla_tar.get_children():
            self.tabla_tar.delete(i)
        for t in self.tarifas:
            self.tabla_tar.insert("", END, iid=str(t["id"]), values=(
                t.get("codigo", ""),
                f"${t.get('precio', 0):,.2f}",
            ))

    def _editar_tarifa(self, event=None):
        sel = self.tabla_tar.selection()
        if not sel:
            return
        tid = int(sel[0])
        tarifa = next((t for t in self.tarifas if t["id"] == tid), None)
        if not tarifa:
            return

        def _guardar(t):
            _guardar_json(TARIFAS_TRANSPORTE, self.tarifas)
            self._refrescar_tarifas()

        def _eliminar(t):
            self.tarifas = [x for x in self.tarifas if x["id"] != t["id"]]
            _guardar_json(TARIFAS_TRANSPORTE, self.tarifas)
            self._refrescar_tarifas()

        DialogoTarifaTransporte(self, tarifa, _guardar, _eliminar)

    # ---------- Cierre ----------

    def _cerrar(self):
        _guardar_json(SERVICIOS_ESTETICA, self.servicios)
        _guardar_json(TARIFAS_TRANSPORTE, self.tarifas)
        self.destroy()