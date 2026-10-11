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
    normalizar_nombre, calcular_ruta_completa, clave_busqueda,
)
from core.geocoding import geocodificar


class DialogoClienteDetalle(ttk.Toplevel):
    """
    Detalle del cliente con 4 pestañas:
      - Datos (nombre, población, dirección, notas cliente)
      - Transporte (coords, distancia, tiempo, tarifa, notas transporte)
      - Estética / Mascotas (mascotas + notas estética)
    """

    def __init__(self, master, cliente: dict, on_guardar=None):
        super().__init__(master)
        self.title(f"Cliente: {cliente.get('cliente') or '(nuevo)'}")
        configurar_ventana(master, self, ancho=920, alto=540,
                           min_ancho=800, min_alto=400, centrar_en_padre=True)

        self.cliente = cliente
        self.on_guardar = on_guardar
        self.es_nuevo = cliente.get("nuevo", False)

        self.mascotas = _cargar_json(MASCOTAS_FILE, {})
        self.transportes = _cargar_json(TRANSPORTES_CLIENTE, {})
        self.nombre_original = cliente.get("cliente", "")

        self._construir_ui()
        self._cargar_datos()

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

    # ---------- Transporte ----------

    def _construir_tab_transporte(self):
        f = self.tab_transporte

        # --- Dirección de servicio (opcional, para clientes empresa) ---
        ttk.Label(f, text="Dirección de servicio:",
                  font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=3,
                                                      sticky="w", pady=(0, 4))
        ttk.Label(f, text="(si es distinta a la del registro)",
                  foreground="gray").grid(row=1, column=0, columnspan=3,
                                          sticky="w", pady=(0, 6))
        self.var_dir_servicio = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_dir_servicio, width=60).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )

        # --- Coordenadas ---
        ttk.Label(f, text="Latitud:").grid(row=3, column=0, sticky="e", pady=6, padx=4)
        self.var_lat = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_lat, width=20).grid(row=3, column=1, sticky="w")

        ttk.Label(f, text="Longitud:").grid(row=4, column=0, sticky="e", pady=6, padx=4)
        self.var_lng = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_lng, width=20).grid(row=4, column=1, sticky="w")

        # Botones de coordenadas
        barra_coords = ttk.Frame(f)
        barra_coords.grid(row=5, column=0, columnspan=3, sticky="w", pady=(2, 12))
        ttk.Button(barra_coords, text="📋 Pegar del portapapeles",
                   command=self._pegar_coords_portapapeles,
                   bootstyle="secondary-outline").pack(side=LEFT, padx=(0, 6))
        ttk.Button(barra_coords, text="🔎 Buscar por dirección",
                   command=self._buscar_coords,
                   bootstyle="info-outline").pack(side=LEFT, padx=(0, 6))
        ttk.Button(barra_coords, text="🗑️ Limpiar coords",
                   command=self._limpiar_coords,
                   bootstyle="danger-outline").pack(side=LEFT)

        # --- Resultado de ruta ---
        self.frame_ruta = ttk.LabelFrame(f, text="Ruta desde Maps", padding=10)
        self.frame_ruta.grid(row=6, column=0, columnspan=3, sticky="ew",
                             pady=(6, 12), padx=4)

        self.lbl_ruta = ttk.Label(self.frame_ruta, text="Sin calcular",
                                   font=("Segoe UI", 10), justify="left")
        self.lbl_ruta.pack(anchor="w")

        barra_ruta = ttk.Frame(self.frame_ruta)
        barra_ruta.pack(anchor="w", pady=(8, 0))
        ttk.Button(barra_ruta, text="🧮 Calcular ruta",
                   command=self._calcular_ruta,
                   bootstyle="success-outline").pack(side=LEFT)

        # --- Tarifa y notas ---
        ttk.Label(f, text="Tarifa:").grid(row=7, column=0, sticky="e", pady=6, padx=4)
        self.var_tarifa = tk.StringVar()
        self.combo_tarifa = ttk.Combobox(f, textvariable=self.var_tarifa,
                                         width=32, state="readonly")
        self.combo_tarifa.grid(row=7, column=1, sticky="w")
        self._cargar_tarifas()

        ttk.Label(f, text="Notas de transporte:").grid(row=8, column=0, sticky="ne",
                                                       pady=6, padx=4)
        self.txt_notas_transporte = tk.Text(f, width=55, height=5)
        self.txt_notas_transporte.grid(row=8, column=1, columnspan=2,
                                       sticky="w", pady=(10, 0))

    # ---------- Estética ----------

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

        cols = ("alerta", "nombre", "especie", "raza", "caracter", "precauciones", "servicio", "duracion")
        self.tabla_mascotas = ttk.Treeview(f, columns=cols, show="headings",
                                           height=10, bootstyle="primary")
        for c, t, w in [
            ("alerta", "", 30),
            ("nombre", "Mascota", 130),
            ("especie", "Especie", 100),
            ("raza", "Raza", 110),
            ("caracter", "Carácter", 100),
            ("precauciones", "Precauciones", 160),
            ("servicio", "Servicio", 100),
            ("duracion", "Duración (min)", 90),
        ]:
            self.tabla_mascotas.heading(c, text=t)
            self.tabla_mascotas.column(c, width=w,
                                       anchor="center" if c in ("alerta", "duracion") else "w")
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
        self.var_dir_servicio.set(trans.get("direccion_servicio", ""))
        self.var_lat.set(str(trans.get("lat", "") or ""))
        self.var_lng.set(str(trans.get("lng", "") or ""))
        self.var_tarifa.set(str(trans.get("tarifa", "") or ""))
        self.txt_notas_transporte.delete("1.0", "end")
        self.txt_notas_transporte.insert("1.0", trans.get("notas", ""))

        # Notas de estética
        self.txt_notas_estetica.delete("1.0", "end")
        self.txt_notas_estetica.insert("1.0", self.mascotas.get(f"__notas__{nombre}", ""))

        self._refrescar_mascotas()
        self._actualizar_label_ruta()

    def _refrescar_mascotas(self):
        for i in self.tabla_mascotas.get_children():
            self.tabla_mascotas.delete(i)
        for idx, m in enumerate(self.mascotas.get(self.var_nombre.get(), [])):
            tiene_nota = (
                m.get("notas", "").strip()
                or m.get("caracter", "").strip()
                or m.get("precauciones", "").strip()
            )
            alerta = "⚠️" if tiene_nota else ""
            self.tabla_mascotas.insert("", END, iid=str(idx), values=(
                alerta,
                m.get("nombre", "[sin nombre]"),
                m.get("especie", ""),
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

    # ---------- Coordenadas ----------

    def _pegar_coords_portapapeles(self):
        import re
        try:
            texto = self.clipboard_get()
        except tk.TclError:
            texto = ""

        if not texto:
            messagebox.showinfo("Portapapeles vacío",
                                "Copia primero un link de Google Maps o "
                                "un par de coordenadas.", parent=self)
            return

        # Busca "lat, lng" en cualquier parte del texto
        patron = r"(-?\d{1,3}\.\d{4,})\s*,\s*(-?\d{1,3}\.\d{4,})"
        match = re.search(patron, texto)
        if not match:
            messagebox.showwarning(
                "Sin coordenadas",
                "El texto no contiene coordenadas.\n\n"
                "Formatos aceptados:\n"
                "  • 19.8421, -90.5189\n"
                "  • https://maps.google.com/?q=19.8421,-90.5189\n"
                "  • https://www.google.com/maps/place/19.8421,-90.5189,17z/...",
                parent=self,
            )
            return

        lat = float(match.group(1))
        lng = float(match.group(2))
        self.var_lat.set(f"{lat:.6f}")
        self.var_lng.set(f"{lng:.6f}")
        self._actualizar_label_ruta()

    def _limpiar_coords(self):
        self.var_lat.set("")
        self.var_lng.set("")
        self._actualizar_label_ruta()

    def _buscar_coords(self):
        # Prioriza dirección de servicio, si no, la del registro
        direccion = (self.var_dir_servicio.get().strip()
                     or self.var_dir.get().strip())
        poblacion = self.var_pob.get().strip()
        if not direccion:
            messagebox.showinfo("Falta dirección",
                                "Escribe primero una dirección.", parent=self)
            return

        self.config(cursor="watch")
        self.update_idletasks()
        try:
            resultado = geocodificar(direccion, poblacion)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Error",
                                 f"Error al buscar coordenadas:\n{e}",
                                 parent=self)
            return
        self.config(cursor="")

        if not resultado:
            messagebox.showinfo(
                "Sin coincidencia",
                "No se encontró una coincidencia precisa.\n\n"
                "Puedes pegar las coordenadas manualmente desde Google Maps.",
                parent=self,
            )
            return

        lat, lng = resultado
        self.var_lat.set(f"{lat:.6f}")
        self.var_lng.set(f"{lng:.6f}")
        self._actualizar_label_ruta()

    # ---------- Ruta ----------

    def _actualizar_label_ruta(self):
        try:
            lat = float(self.var_lat.get()) if self.var_lat.get() else None
            lng = float(self.var_lng.get()) if self.var_lng.get() else None
        except ValueError:
            lat = lng = None

        if lat is None or lng is None:
            self.lbl_ruta.config(text="Sin coordenadas. Pega o busca las coords primero.")
            return

        dist, t_ida, t_total = calcular_ruta_completa(lat, lng)
        if dist is None:
            self.lbl_ruta.config(text="No se pudo calcular.")
            return

        texto = (
            f"Distancia (ida):     {dist} km\n"
            f"Tiempo (ida):        {t_ida} min\n"
            f"Tiempo (vuelta):     {t_ida} min\n"
            f"Recolección:         5 min\n"
            f"─────────────────────────\n"
            f"⏱️  TOTAL:            {t_total} min"
        )
        self.lbl_ruta.config(text=texto)

    def _calcular_ruta(self):
        self._actualizar_label_ruta()

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

    # ---------- Guardar ----------

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

        # Validar duplicado
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

        # Coordenadas
        try:
            lat = float(self.var_lat.get()) if self.var_lat.get() else None
        except ValueError:
            lat = None
        try:
            lng = float(self.var_lng.get()) if self.var_lng.get() else None
        except ValueError:
            lng = None

        # Recalcular tiempos para guardarlos
        dist = t_ida = t_total = None
        if lat is not None and lng is not None:
            dist, t_ida, t_total = calcular_ruta_completa(lat, lng)

        trans = self.transportes.setdefault(nuevo_nombre, {})
        trans.update({
            "direccion_servicio": self.var_dir_servicio.get().strip(),
            "lat": lat,
            "lng": lng,
            "distancia_km": dist,
            "tiempo_ida_min": t_ida,
            "tiempo_total_min": t_total,
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
            clave_vieja = f"__notas__{self.nombre_original}"
            if clave_vieja in self.mascotas:
                self.mascotas[clave_notas] = self.mascotas.pop(clave_vieja)

        _guardar_json(MASCOTAS_FILE, self.mascotas)

        if self.on_guardar:
            self.on_guardar()
        self.destroy()