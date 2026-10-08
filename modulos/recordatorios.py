# modulos/recordatorios.py
"""
Módulo de Recordatorios.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui.utils import configurar_ventana

from core.rutas_recordatorios import _cargar_json, _guardar_json, CARPETA_DATOS
from core.recordatorios.sucursales import (
    cargar_sucursales,
    sucursal_activa,
    nombre_clinica_activa,
    sucursales_activas,
    cambiar_sucursal_activa,
)
from core.recordatorios.procesar_excel import (
    procesar_excel,
    detectar_tipo_excel,
    regenerar_mensajes_cliente,
)
from core.recordatorios import historial
from core.recordatorios import envio


CITAS_CACHE = CARPETA_DATOS / "agenda_importada.json"
VACUNAS_CACHE = CARPETA_DATOS / "vacunas_importada.json"


class AppRecordatorios(ttk.Toplevel):
    """Ventana principal del módulo de Recordatorios."""

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Vet Suite — Recordatorios")

        configurar_ventana(
            master, self,
            ancho=1150, alto=880,
            min_ancho=1000, min_alto=720,
            centrar_en_padre=True,
        )

        self.sucursales = cargar_sucursales()
        self.clientes_citas = _cargar_json(CITAS_CACHE, [])
        self.clientes_vacunas = _cargar_json(VACUNAS_CACHE, [])
        self.tab_activo = "citas"

        self._construir_ui()
        self._refrescar_tabs()
        self._actualizar_estadisticas()

    # ============================================================
    # UI
    # ============================================================

    def _construir_ui(self):
        # ---- Barra superior ----
        top = ttk.LabelFrame(self, text="Configuración", padding=10)
        top.pack(fill=X, padx=10, pady=5)

        ttk.Label(top, text="Sucursal:").pack(side=LEFT, padx=(0, 6))
        self.var_sucursal = tk.StringVar(value=sucursal_activa()["nombre"])
        self.combo_sucursal = ttk.Combobox(
            top, textvariable=self.var_sucursal,
            values=[s["nombre"] for s in sucursales_activas()],
            width=40, state="readonly", bootstyle="primary",
        )
        self.combo_sucursal.pack(side=LEFT, padx=(0, 8))
        self.combo_sucursal.bind("<<ComboboxSelected>>", self._al_cambiar_sucursal)

        ttk.Button(
            top, text="⚙️ Sucursales",
            command=self._abrir_sucursales,
            bootstyle="secondary-outline",
        ).pack(side=LEFT, padx=4)

        ttk.Button(
            top, text="📥 Importar Excel",
            command=self._importar_excel,
            bootstyle="info-outline",
        ).pack(side=LEFT, padx=4)

        ttk.Button(
            top, text="🧹 Limpiar todo",
            command=self._limpiar_todo,
            bootstyle="danger-outline",
        ).pack(side=LEFT, padx=4)

        # ---- Notebook ----
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=(0, 5))

        self.tab_citas = ttk.Frame(self.notebook, padding=8)
        self.tab_vacunas = ttk.Frame(self.notebook, padding=8)

        self.notebook.add(self.tab_citas, text="📅 Citas (0)")
        self.notebook.add(self.tab_vacunas, text="💉 Vacunas (0)")
        self.notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_tab)

        self._construir_tab_citas(self.tab_citas)
        self._construir_tab_vacunas(self.tab_vacunas)

        # ---- Estadísticas ----
        self.lbl_stats = ttk.Label(
            self, text="", font=("Segoe UI", 10, "bold"),
        )
        self.lbl_stats.pack(fill=X, padx=15, pady=(0, 8))

    def _construir_tab_citas(self, parent):
        # ---- Tabla de clientes ----
        frame_clientes = ttk.LabelFrame(parent, text="Clientes", padding=5)
        frame_clientes.pack(fill=BOTH, expand=True, pady=(0, 6))

        columnas = ("estado", "cliente", "telefono", "mascotas",
                    "hora", "asunto", "agenda", "estado_cita")
        tabla = ttk.Treeview(
            frame_clientes, columns=columnas, show="headings",
            height=10, bootstyle="primary",
        )
        tabla.heading("estado", text="✔")
        tabla.heading("cliente", text="CLIENTE")
        tabla.heading("telefono", text="TELÉFONO")
        tabla.heading("mascotas", text="MASCOTAS")
        tabla.heading("hora", text="HORA")
        tabla.heading("asunto", text="ASUNTO")
        tabla.heading("agenda", text="AGENDA")
        tabla.heading("estado_cita", text="ESTADO")

        tabla.column("estado", width=40, anchor="center")
        tabla.column("cliente", width=220, anchor="w")
        tabla.column("telefono", width=120, anchor="center")
        tabla.column("mascotas", width=180, anchor="w")
        tabla.column("hora", width=70, anchor="center")
        tabla.column("asunto", width=150, anchor="w")
        tabla.column("agenda", width=110, anchor="center")
        tabla.column("estado_cita", width=130, anchor="center")

        sb = ttk.Scrollbar(frame_clientes, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        self.tabla_citas = tabla
        tabla.bind("<<TreeviewSelect>>", lambda e: self._al_seleccionar("citas"))

        # ---- Panel de mensaje (reducido) ----
        frame_msg = ttk.LabelFrame(parent, text="Mensaje", padding=5)
        frame_msg.pack(fill=X, expand=False)

        txt_msg = tk.Text(
            frame_msg, height=7, wrap="word",
            font=("Segoe UI", 11), relief="flat",
        )
        sb_msg = ttk.Scrollbar(frame_msg, orient="vertical", command=txt_msg.yview)
        txt_msg.configure(yscrollcommand=sb_msg.set)
        txt_msg.pack(side=LEFT, fill=BOTH, expand=True)
        sb_msg.pack(side=RIGHT, fill=Y)

        self.txt_msg_citas = txt_msg

        # ---- Botones ----
        frame_btn = ttk.Frame(parent)
        frame_btn.pack(fill=X, pady=(6, 0))

        botones = [
            ("📤 Enviar por WhatsApp", lambda: self._enviar("citas"), "success"),
            ("✅ Marcar como enviado", lambda: self._marcar("citas"), "primary-outline"),
            ("↩️ Desmarcar", lambda: self._desmarcar("citas"), "secondary-outline"),
        ]
        for txt, cmd, estilo in botones:
            ttk.Button(frame_btn, text=txt, command=cmd,
                       bootstyle=estilo).pack(side=LEFT, padx=4)

    def _construir_tab_vacunas(self, parent):
        # ---- Tabla de clientes ----
        frame_clientes = ttk.LabelFrame(parent, text="Clientes", padding=5)
        frame_clientes.pack(fill=BOTH, expand=True, pady=(0, 6))

        columnas = ("estado", "cliente", "telefono", "mascotas",
                    "tipo_recordatorio", "vacuna", "proxima_fecha")
        tabla = ttk.Treeview(
            frame_clientes, columns=columnas, show="headings",
            height=10, bootstyle="primary",
        )
        tabla.heading("estado", text="✔")
        tabla.heading("cliente", text="CLIENTE")
        tabla.heading("telefono", text="TELÉFONO")
        tabla.heading("mascotas", text="MASCOTAS")
        tabla.heading("tipo_recordatorio", text="TIPO RECORDATORIO")
        tabla.heading("vacuna", text="VACUNA")
        tabla.heading("proxima_fecha", text="PRÓXIMA FECHA")

        tabla.column("estado", width=40, anchor="center")
        tabla.column("cliente", width=200, anchor="w")
        tabla.column("telefono", width=120, anchor="center")
        tabla.column("mascotas", width=150, anchor="w")
        tabla.column("tipo_recordatorio", width=150, anchor="w")
        tabla.column("vacuna", width=200, anchor="w")
        tabla.column("proxima_fecha", width=140, anchor="center")

        sb = ttk.Scrollbar(frame_clientes, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        self.tabla_vacunas = tabla
        tabla.bind("<<TreeviewSelect>>", lambda e: self._al_seleccionar("vacunas"))

        # ---- Panel de mensaje (reducido) ----
        frame_msg = ttk.LabelFrame(parent, text="Mensaje", padding=5)
        frame_msg.pack(fill=X, expand=False)

        txt_msg = tk.Text(
            frame_msg, height=7, wrap="word",
            font=("Segoe UI", 11), relief="flat",
        )
        sb_msg = ttk.Scrollbar(frame_msg, orient="vertical", command=txt_msg.yview)
        txt_msg.configure(yscrollcommand=sb_msg.set)
        txt_msg.pack(side=LEFT, fill=BOTH, expand=True)
        sb_msg.pack(side=RIGHT, fill=Y)

        self.txt_msg_vacunas = txt_msg

        # ---- Botones ----
        frame_btn = ttk.Frame(parent)
        frame_btn.pack(fill=X, pady=(6, 0))

        botones = [
            ("📤 Enviar por WhatsApp", lambda: self._enviar("vacunas"), "success"),
            ("✅ Marcar como enviado", lambda: self._marcar("vacunas"), "primary-outline"),
            ("↩️ Desmarcar", lambda: self._desmarcar("vacunas"), "secondary-outline"),
        ]
        for txt, cmd, estilo in botones:
            ttk.Button(frame_btn, text=txt, command=cmd,
                       bootstyle=estilo).pack(side=LEFT, padx=4)

    # ============================================================
    # Navegación
    # ============================================================

    def _al_cambiar_tab(self, event=None):
        idx = self.notebook.index(self.notebook.select())
        self.tab_activo = "citas" if idx == 0 else "vacunas"

    def _al_cambiar_sucursal(self, event=None):
        """Al cambiar sucursal, regenera mensajes de los clientes NO enviados."""
        nombre = self.var_sucursal.get()

        for s in self.sucursales["sucursales"]:
            if s["nombre"] == nombre:
                cambiar_sucursal_activa(s["id"])
                break

        nombre_clinica = nombre_clinica_activa()
        regenerados = 0

        # Regenerar mensajes de clientes no enviados
        for lista, tipo in ((self.clientes_citas, "citas"),
                            (self.clientes_vacunas, "vacunas")):
            for c in lista:
                if historial.ya_fue_enviado(c["telefono"], tipo, self._mensaje_de(c)):
                    continue  # Ya enviado → no tocar
                regenerar_mensajes_cliente(c, nombre_clinica)
                regenerados += 1

        # Guardar caché actualizado
        _guardar_json(CITAS_CACHE, self.clientes_citas)
        _guardar_json(VACUNAS_CACHE, self.clientes_vacunas)

        self._refrescar_tabs()

        # Limpiar panel de mensaje si el cliente seleccionado cambió
        self.txt_msg_citas.delete("1.0", END)
        self.txt_msg_vacunas.delete("1.0", END)

    def _abrir_sucursales(self):
        from dialogos.sucursal_editor import DialogoSucursalEditor
        DialogoSucursalEditor(self, on_guardar=self._recargar_sucursales)

    def _recargar_sucursales(self):
        self.sucursales = cargar_sucursales()
        activas = [s["nombre"] for s in sucursales_activas()]
        self.combo_sucursal["values"] = activas
        self.var_sucursal.set(sucursal_activa()["nombre"])

    # ============================================================
    # Importar / Limpiar
    # ============================================================

    def _importar_excel(self):
        rutas = filedialog.askopenfilenames(
            title="Selecciona uno o más Excel (Agendas, Vacunas, etc.)",
            filetypes=[("Excel", "*.xlsx *.xls")],
        )
        if not rutas:
            return

        nombre_clinica = nombre_clinica_activa()
        resumen = []
        nuevas_citas = 0
        nuevas_vacunas = 0

        for r in rutas:
            nombre = os.path.basename(r)
            try:
                tipo = detectar_tipo_excel(r)
                if not tipo:
                    resumen.append(f"❌ {nombre}: no reconocido")
                    continue

                resultado = procesar_excel(r, nombre_clinica)
                clientes = resultado["clientes"]

                if tipo == "citas":
                    claves = {c["telefono"] for c in self.clientes_citas}
                    for c in clientes:
                        if c["telefono"] not in claves:
                            self.clientes_citas.append(c)
                            nuevas_citas += 1
                    resumen.append(f"✅ {nombre}: {len(clientes)} clientes ({nuevas_citas} nuevos)")
                else:
                    claves = {c["telefono"] for c in self.clientes_vacunas}
                    for c in clientes:
                        if c["telefono"] not in claves:
                            self.clientes_vacunas.append(c)
                            nuevas_vacunas += 1
                    resumen.append(f"✅ {nombre}: {len(clientes)} clientes ({nuevas_vacunas} nuevos)")

            except Exception as e:
                resumen.append(f"❌ {nombre}: {e}")

        _guardar_json(CITAS_CACHE, self.clientes_citas)
        _guardar_json(VACUNAS_CACHE, self.clientes_vacunas)

        self._refrescar_tabs()
        self._actualizar_estadisticas()
        messagebox.showinfo("Importación", "\n".join(resumen), parent=self)

    def _limpiar_todo(self):
        if not messagebox.askyesno(
            "Limpiar",
            "¿Borrar todos los clientes importados?",
            parent=self,
        ):
            return
        self.clientes_citas = []
        self.clientes_vacunas = []
        _guardar_json(CITAS_CACHE, [])
        _guardar_json(VACUNAS_CACHE, [])
        self._refrescar_tabs()
        self._actualizar_estadisticas()
        # Limpiar cuadros de mensaje
        self.txt_msg_citas.delete("1.0", END)
        self.txt_msg_vacunas.delete("1.0", END)

    # ============================================================
    # Tablas
    # ============================================================

    def _refrescar_tabs(self):
        self._refrescar_tabla("citas")
        self._refrescar_tabla("vacunas")
        self.notebook.tab(0, text=f"📅 Citas ({len(self.clientes_citas)})")
        self.notebook.tab(1, text=f"💉 Vacunas ({len(self.clientes_vacunas)})")

    def _refrescar_tabla(self, tipo: str):
        if tipo == "citas":
            tabla = self.tabla_citas
            clientes = self.clientes_citas
        else:
            tabla = self.tabla_vacunas
            clientes = self.clientes_vacunas

        for i in tabla.get_children():
            tabla.delete(i)

        for idx, c in enumerate(clientes):
            enviado = historial.ya_fue_enviado(
                c["telefono"], tipo, self._mensaje_de(c)
            )
            estado = "✅" if enviado else "⬜"
            mascotas = self._nombres_mascotas(c)

            if tipo == "citas":
                primera_cita = c["citas"][0] if c.get("citas") else {}
                tabla.insert("", END, iid=str(idx), values=(
                    estado,
                    c["nombre"],
                    c["telefono_display"],
                    mascotas,
                    primera_cita.get("hora", ""),
                    primera_cita.get("asunto", ""),
                    primera_cita.get("agenda", ""),
                    primera_cita.get("estado", ""),
                ))
            else:
                # Vacunas: concatenar tipo recordatorio + vacuna + fecha de todas
                tipos_record = []
                vacunas = []
                fechas = []
                for m in c.get("mascotas", []):
                    if not isinstance(m, dict):
                        continue
                    for r in m.get("recordatorios", []):
                        tipos_record.append(r.get("nombre", ""))
                        for t in r.get("tipos", []):
                            vacunas.append(t.get("nombre", ""))
                            f = t.get("fecha", "")
                            if f:
                                fechas.append(f)

                tabla.insert("", END, iid=str(idx), values=(
                    estado,
                    c["nombre"],
                    c["telefono_display"],
                    mascotas,
                    ", ".join(t for t in tipos_record if t),
                    ", ".join(v for v in vacunas if v),
                    ", ".join(f for f in fechas if f),
                ))

    def _nombres_mascotas(self, cliente: dict) -> str:
        mascotas = cliente.get("mascotas", [])
        if not mascotas:
            return ""
        nombres = []
        for m in mascotas:
            if isinstance(m, str):
                nombres.append(m)
            elif isinstance(m, dict):
                nombres.append(m.get("nombre", ""))
        return ", ".join(n for n in nombres if n)

    def _al_seleccionar(self, tipo: str):
        cliente = self._cliente_seleccionado(tipo)
        if not cliente:
            return
        mensaje = self._mensaje_de(cliente)
        txt = self.txt_msg_citas if tipo == "citas" else self.txt_msg_vacunas
        txt.delete("1.0", END)
        txt.insert("1.0", mensaje)

    # ============================================================
    # Acciones
    # ============================================================

    def _mensaje_de(self, cliente: dict) -> str:
        mensajes = cliente.get("mensajes", [])
        return "\n\n".join(mensajes)

    def _cliente_seleccionado(self, tipo: str) -> dict | None:
        if tipo == "citas":
            tabla = self.tabla_citas
            clientes = self.clientes_citas
        else:
            tabla = self.tabla_vacunas
            clientes = self.clientes_vacunas

        sel = tabla.selection()
        if not sel:
            return None
        idx = int(sel[0])
        if 0 <= idx < len(clientes):
            return clientes[idx]
        return None

    def _enviar(self, tipo: str):
        cliente = self._cliente_seleccionado(tipo)
        if not cliente:
            messagebox.showinfo("Selecciona", "Selecciona un cliente.", parent=self)
            return

        mensaje = self._mensaje_de(cliente)  # CON emojis

        # 1. Copiar al portapapeles
        if not envio.copiar_al_portapapeles(mensaje):
            messagebox.showerror(
                "Error",
                "No se pudo copiar el mensaje al portapapeles.",
                parent=self,
            )
            return

        # 2. Abrir WhatsApp SIN texto (para que el usuario pegue)
        ok = envio.abrir_whatsapp_solo_chat(cliente["telefono"])

        if not ok:
            messagebox.showerror("Error", "No se pudo abrir WhatsApp.", parent=self)
            return

        # 3. Confirmar
        self.after(500, lambda: self._confirmar_envio(tipo, cliente, mensaje))

    def _confirmar_envio(self, tipo: str, cliente: dict, mensaje: str):
        respuesta = messagebox.askyesno(
            "Confirmar envío",
            f"El mensaje está en el portapapeles.\n\n"
            f"Pégalo en WhatsApp (Cmd+V) y envíalo a:\n"
            f"{cliente['nombre']}\n\n"
            f"¿Ya lo enviaste?",
            parent=self,
        )
        if respuesta:
            historial.marcar_enviado(
                cliente["telefono"], tipo, mensaje, cliente["nombre"]
            )
            self._refrescar_tabla(tipo)
            self._actualizar_estadisticas()

    def _marcar(self, tipo: str):
        cliente = self._cliente_seleccionado(tipo)
        if not cliente:
            return
        mensaje = self._mensaje_de(cliente)
        historial.marcar_enviado(cliente["telefono"], tipo, mensaje, cliente["nombre"])
        self._refrescar_tabla(tipo)
        self._actualizar_estadisticas()

    def _desmarcar(self, tipo: str):
        cliente = self._cliente_seleccionado(tipo)
        if not cliente:
            return
        historial.desmarcar_enviado(cliente["telefono"], tipo)
        self._refrescar_tabla(tipo)
        self._actualizar_estadisticas()

    # ============================================================
    # Estadísticas
    # ============================================================

    def _actualizar_estadisticas(self):
        total_citas = len(self.clientes_citas)
        total_vacunas = len(self.clientes_vacunas)

        enviados_citas = 0
        for c in self.clientes_citas:
            if historial.ya_fue_enviado(c["telefono"], "citas", self._mensaje_de(c)):
                enviados_citas += 1

        enviados_vacunas = 0
        for c in self.clientes_vacunas:
            if historial.ya_fue_enviado(c["telefono"], "vacunas", self._mensaje_de(c)):
                enviados_vacunas += 1

        self.lbl_stats.configure(
            text=(
                f"📅 Citas: {total_citas} (Enviados: {enviados_citas} | "
                f"Pendientes: {total_citas - enviados_citas})   "
                f"💉 Vacunas: {total_vacunas} (Enviados: {enviados_vacunas} | "
                f"Pendientes: {total_vacunas - enviados_vacunas})"
            )
        )