# dialogos/cliente_detalle.py
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.utils import configurar_ventana

from core.rutas_estetica import (
    CLIENTES_MAESTRO, MASCOTAS_FILE, TRANSPORTES_CLIENTE,
    TARIFAS_TRANSPORTE,
)
from modulos.estetica_transportes import (
    _cargar_json, _guardar_json,
    normalizar_nombre, calcular_ruta_haversine, clave_busqueda,
)
from core.geocoding import geocodificar


class DialogoClienteDetalle(ttk.Toplevel):
    """
    Detalle del cliente con 4 pestañas:
      - Datos (nombre, población, dirección, notas cliente)
      - Transporte (coords, distancia, tiempo, tarifa, notas transporte)
      - Estética / Mascotas (mascotas + notas estética)
      - (implícito) el ⚠️ sale si hay notas en cualquier pestaña

    Autoguardado: guarda al cerrar con la X.
    """

    def __init__(self, master, cliente: dict, on_guardar=None):
        super().__init__(master)
        self.title(f"Cliente: {cliente.get('cliente') or '(nuevo)'}")
        configurar_ventana(master, self, ancho=880, alto=680,
                           min_ancho=760, min_alto=560, centrar_en_padre=True)

        self.cliente = cliente
        self.on_guardar = on_guardar
        self.es_nuevo = cliente.get("nuevo", False)

        self.mascotas = _cargar_json(MASCOTAS_FILE, {})
        self.transportes = _cargar_json(TRANSPORTES_CLIENTE, {})
        self.nombre_original = cliente.get("cliente", "")

        self._construir_ui()
        self._cargar_datos()

        # Autoguardado al cerrar con la X
        self.protocol("WM_DELETE_WINDOW", self._cerrar_y_guardar)

    # ---------- UI ----------

    def _construir_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=True, padx=8, pady=8)

        self.tab_datos = ttk.Frame(self.notebook, padding=12)
        self.tab_transporte = ttk.Frame(self.notebook, padding=12)
        self.tab_estetica = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.tab_datos, text="Datos")
        self.notebook.add(self.tab_transporte, text="Transporte")
        self.notebook.add(self.tab_estetica, text="Estética / Mascotas")

        self._construir_tab_datos()
        self._construir_tab_transporte()
        self._construir_tab_estetica()

    def _construir_tab_datos(self):
        f = self.tab_datos
        ttk.Label(f, text="Nombre:").grid(row=0, column=0, sticky="e", pady=6, padx=4)
        self.var_nombre = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_nombre, width=55).grid(row=0, column=1, sticky="w")

        ttk.Label(f, text="Población:").grid(row=1, column=0, sticky="e", pady=6, padx=4)
        self.var_pob = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_pob, width=55).grid(row=1, column=1, sticky="w")

        ttk.Label(f, text="Dirección:").grid(row=2, column=0, sticky="e", pady=6, padx=4)
        self.var_dir = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_dir, width=55).grid(row=2, column=1, sticky="w")

        ttk.Label(f, text="Notas del cliente:").grid(row=3, column=0, sticky="ne", pady=6, padx=4)
        self.txt_notas_cliente = tk.Text(f, width=55, height=6)
        self.txt_notas_cliente.grid(row=3, column=1, sticky="w")

        ttk.Label(
            f, text="(cualquier nota en cualquier pestaña mostrará ⚠️ en la tabla principal)",
            foreground="gray",
        ).grid(row=4, column=1, sticky="w", pady=(10, 0))

    def _construir_tab_transporte(self):
        f = self.tab_transporte
        ttk.Label(f, text="Latitud:").grid(row=0, column=0, sticky="e", pady=6, padx=4)
        self.var_lat = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_lat, width=18).grid(row=0, column=1, sticky="w")

        ttk.Label(f, text="Longitud:").grid(row=1, column=0, sticky="e", pady=6, padx=4)
        self.var_lng = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_lng, width=18).grid(row=1, column=1, sticky="w")

        ttk.Button(
            f, text="🔎 Buscar coords (por dirección)",
            command=self._buscar_coords,
            bootstyle="info-outline",
        ).grid(row=2, column=1, sticky="w", pady=(2, 12))

        ttk.Label(f, text="Distancia (km):").grid(row=3, column=0, sticky="e", pady=6, padx=4)
        self.var_dist = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_dist, width=18).grid(row=3, column=1, sticky="w")

        ttk.Label(f, text="Tiempo (min):").grid(row=4, column=0, sticky="e", pady=6, padx=4)
        self.var_tiempo = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_tiempo, width=18).grid(row=4, column=1, sticky="w")

        ttk.Button(
            f, text="🧭 Calcular ruta (Haversine)",
            command=self._calcular_ruta,
            bootstyle="info-outline",
        ).grid(row=5, column=1, sticky="w", pady=(2, 12))

        ttk.Label(f, text="Tarifa:").grid(row=6, column=0, sticky="e", pady=6, padx=4)
        self.var_tarifa = tk.StringVar()
        self.combo_tarifa = ttk.Combobox(f, textvariable=self.var_tarifa,
                                         width=32, state="readonly")
        self.combo_tarifa.grid(row=6, column=1, sticky="w")
        self._cargar_tarifas()

        ttk.Label(f, text="Notas de transporte:").grid(row=7, column=0, sticky="ne",
                                                       pady=6, padx=4)
        self.txt_notas_transporte = tk.Text(f, width=55, height=6)
        self.txt_notas_transporte.grid(row=7, column=1, sticky="w", pady=(10, 0))

    def _construir_tab_estetica(self):
        f = self.tab_estetica

        ttk.Label(
            f, text="Mascotas (doble clic para editar, + para agregar)",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        barra = ttk.Frame(f)
        barra.pack(fill=X, pady=(4, 6))
        ttk.Button(barra, text="+ Agregar mascota",
                   command=self._agregar_mascota,
                   bootstyle="success-outline").pack(side=LEFT)

        cols = ("nombre", "raza", "caracter", "precauciones", "servicio", "duracion")
        self.tabla_mascotas = ttk.Treeview(f, columns=cols, show="headings",
                                           height=10, bootstyle="primary")
        for c, t, w in [
            ("nombre", "Mascota", 130),
            ("raza", "Raza", 110),
            ("caracter", "Carácter", 110),
            ("precauciones", "Precauciones", 180),
            ("servicio", "Servicio", 110),
            ("duracion", "Duración (min)", 90),
        ]:
            self.tabla_mascotas.heading(c, text=t)
            self.tabla_mascotas.column(c, width=w)
        self.tabla_mascotas.pack(fill=BOTH, expand=True)
        self.tabla_mascotas.bind("<Double-1>", self._editar_mascota)

        ttk.Label(f, text="Notas de estética:").pack(anchor="w", pady=(10, 4))
        self.txt_notas_estetica = tk.Text(f, width=80, height=5)
        self.txt_notas_estetica.pack(fill=X)

    # ---------- Carga ----------

    def _cargar_datos(self):
        c = self.cliente
        self.var_nombre.set(c.get("cliente", ""))
        self.var_pob.set(c.get("poblacion", ""))
        self.var_dir.set(c.get("direccion", ""))
        self.txt_notas_cliente.delete("1.0", "end")
        self.txt_notas_cliente.insert("1.0", c.get("notas_cliente", ""))

        nombre = c.get("cliente", "")
        trans = self.transportes.get(nombre, {})
        self.var_lat.set(str(trans.get("lat", "") or ""))
        self.var_lng.set(str(trans.get("lng", "") or ""))
        self.var_dist.set(str(trans.get("distancia_km", "") or ""))
        self.var_tiempo.set(str(trans.get("tiempo_min", "") or ""))
        self.var_tarifa.set(str(trans.get("tarifa", "") or ""))
        self.txt_notas_transporte.delete("1.0", "end")
        self.txt_notas_transporte.insert("1.0", trans.get("notas", ""))

        # Notas de estética (a nivel cliente, no por mascota)
        self.txt_notas_estetica.delete("1.0", "end")
        self.txt_notas_estetica.insert("1.0", self.mascotas.get(f"__notas__{nombre}", ""))

        self._refrescar_mascotas()

    def _refrescar_mascotas(self):
        for i in self.tabla_mascotas.get_children():
            self.tabla_mascotas.delete(i)
        for idx, m in enumerate(self.mascotas.get(self.var_nombre.get(), [])):
            self.tabla_mascotas.insert("", END, iid=str(idx), values=(
                m.get("nombre", ""),
                m.get("raza", ""),
                m.get("caracter", ""),
                m.get("precauciones", ""),
                m.get("servicio", ""),
                m.get("duracion_min", ""),
            ))

    def _cargar_tarifas(self):
        tarifas = _cargar_json(TARIFAS_TRANSPORTE, [])
        opciones = [f"{t['codigo']} — ${t['precio']}"
                    for t in tarifas if t.get("activo", True)]
        self.combo_tarifa["values"] = opciones

    # ---------- Geocodificación ----------

    def _buscar_coords(self):
        direccion = self.var_dir.get().strip()
        poblacion = self.var_pob.get().strip()
        if not direccion:
            messagebox.showinfo("Falta dirección",
                                "Escribe primero la dirección.", parent=self)
            return
        try:
            resultado = geocodificar(direccion, poblacion)
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar coordenadas:\n{e}",
                                 parent=self)
            return
        if not resultado:
            messagebox.showinfo(
                "Sin coincidencia exacta",
                "No se encontró una coincidencia precisa para esta dirección.\n\n"
                "Puedes copiar las coordenadas manualmente desde Google Maps.",
                parent=self,
            )
            return
        lat, lng = resultado
        self.var_lat.set(f"{lat:.6f}")
        self.var_lng.set(f"{lng:.6f}")

    def _calcular_ruta(self):
        try:
            lat = float(self.var_lat.get())
            lng = float(self.var_lng.get())
        except ValueError:
            messagebox.showwarning("Faltan coords",
                                   "Ingresa latitud y longitud primero.", parent=self)
            return
        dist, tiempo = calcular_ruta_haversine(lat, lng)
        if dist is None:
            messagebox.showwarning("Sin datos", "No se pudo calcular.", parent=self)
            return
        self.var_dist.set(str(dist))
        self.var_tiempo.set(str(tiempo))

    # ---------- Mascotas ----------

    def _agregar_mascota(self):
        nombre_cliente = self.var_nombre.get().strip()
        if not nombre_cliente:
            messagebox.showinfo("Falta nombre",
                                "Primero asigna un nombre al cliente.", parent=self)
            return
        from dialogos.mascota_editar import DialogoMascota
        DialogoMascota(self, None,
                       existentes=self.mascotas.get(nombre_cliente, []),
                       on_guardar=self._recibir_mascota)

    def _editar_mascota(self, event=None):
        sel = self.tabla_mascotas.selection()
        if not sel:
            return
        idx = int(sel[0])
        lista = self.mascotas.get(self.var_nombre.get(), [])
        if idx >= len(lista):
            return
        from dialogos.mascota_editar import DialogoMascota
        DialogoMascota(
            self, lista[idx],
            existentes=[m for i, m in enumerate(lista) if i != idx],
            on_guardar=lambda m: self._recibir_mascota(m, idx),
            on_eliminar=lambda: self._eliminar_mascota(idx),
        )

    def _recibir_mascota(self, mascota, idx=None):
        nombre = self.var_nombre.get()
        lista = self.mascotas.setdefault(nombre, [])
        if idx is None:
            lista.append(mascota)
        else:
            lista[idx] = mascota
        _guardar_json(MASCOTAS_FILE, self.mascotas)
        self._refrescar_mascotas()

    def _eliminar_mascota(self, idx):
        nombre = self.var_nombre.get()
        lista = self.mascotas.get(nombre, [])
        if idx < len(lista):
            lista.pop(idx)
            self.mascotas[nombre] = lista
            _guardar_json(MASCOTAS_FILE, self.mascotas)
            self._refrescar_mascotas()

    # ---------- Guardar al cerrar ----------

    def _cerrar_y_guardar(self):
        nuevo_nombre = normalizar_nombre(self.var_nombre.get())
        if not nuevo_nombre:
            if self.es_nuevo:
                if messagebox.askyesno(
                    "Nombre vacío",
                    "El cliente no tiene nombre. ¿Cerrar sin guardar?",
                    parent=self,
                ):
                    self.destroy()
                return
            else:
                self.destroy()
                return

        # Validar duplicado si es nuevo o cambió de nombre
        if self.es_nuevo or nuevo_nombre != self.nombre_original:
            clientes = _cargar_json(CLIENTES_MAESTRO, [])
            clave_nueva = clave_busqueda(nuevo_nombre)
            for c in clientes:
                if c.get("id") == self.cliente.get("id"):
                    continue
                if clave_busqueda(c.get("cliente", "")) == clave_nueva:
                    messagebox.showwarning(
                        "Cliente duplicado",
                        f"Ya existe un cliente llamado:\n{c.get('cliente')}\n\n"
                        f"No se guardó el cambio.",
                        parent=self,
                    )
                    return

        # Guardar cliente
        clientes = _cargar_json(CLIENTES_MAESTRO, [])
        for c in clientes:
            if c.get("id") == self.cliente.get("id"):
                c["cliente"] = nuevo_nombre
                c["poblacion"] = self.var_pob.get().strip()
                c["direccion"] = self.var_dir.get().strip()
                c["notas_cliente"] = self.txt_notas_cliente.get("1.0", "end").strip()
                break
        else:
            clientes.append({
                "id": max((c.get("id", 0) for c in clientes), default=0) + 1,
                "cliente": nuevo_nombre,
                "cliente_raw": self.var_nombre.get(),
                "poblacion": self.var_pob.get().strip(),
                "direccion": self.var_dir.get().strip(),
                "notas_cliente": self.txt_notas_cliente.get("1.0", "end").strip(),
                "duplicado": False,
            })
        _guardar_json(CLIENTES_MAESTRO, clientes)

        # Guardar transporte
        try:
            lat = float(self.var_lat.get()) if self.var_lat.get() else None
        except ValueError:
            lat = None
        try:
            lng = float(self.var_lng.get()) if self.var_lng.get() else None
        except ValueError:
            lng = None

        trans = self.transportes.setdefault(nuevo_nombre, {})
        trans.update({
            "lat": lat,
            "lng": lng,
            "distancia_km": self.var_dist.get(),
            "tiempo_min": self.var_tiempo.get(),
            "tarifa": self.var_tarifa.get(),
            "notas": self.txt_notas_transporte.get("1.0", "end").strip(),
        })
        _guardar_json(TRANSPORTES_CLIENTE, self.transportes)

        # Notas de estética
        notas_est = self.txt_notas_estetica.get("1.0", "end").strip()
        clave_notas = f"__notas__{nuevo_nombre}"
        if notas_est:
            self.mascotas[clave_notas] = notas_est
        else:
            self.mascotas.pop(clave_notas, None)

        # Migrar mascotas si cambió el nombre
        if self.nombre_original and self.nombre_original != nuevo_nombre:
            if self.nombre_original in self.mascotas:
                self.mascotas[nuevo_nombre] = self.mascotas.pop(self.nombre_original)
            # Migrar notas de estética
            clave_vieja = f"__notas__{self.nombre_original}"
            if clave_vieja in self.mascotas:
                self.mascotas[clave_notas] = self.mascotas.pop(clave_vieja)

        _guardar_json(MASCOTAS_FILE, self.mascotas)

        if self.on_guardar:
            self.on_guardar()
        self.destroy()