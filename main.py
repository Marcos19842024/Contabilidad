# -*- coding: utf-8 -*-
"""
Sistema de Ingresos - Contabilidad
Interfaz moderna con ttkbootstrap.
Registros por año (un archivo JSON por año).
"""
import os
import sys
import re
import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
import shutil
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ============================================================
# IMPORTS INTERNOS
# ============================================================
from config.ajustes import CONFIG, TEMA, cargar_config, guardar_config
from config.campos import (
    MESES_ES,
    CAMPOS,
    CAMPOS_DICT,
    REGLAS_AUTO,
    CATEGORIAS_PARA_TOTAL,
    CAMPOS_TIPO_PAGO,
)
from config.temas import (
    TEMAS_OSCUROS,
    tema_es_oscuro,
    COLORES,
    refrescar_colores,
    obtener_colores_sidebar,
)
from core.rutas import (
    BASE_DIR,
    HISTORIAL_FILE,
    _CARPETA_DATOS,
    ruta_registros,
    ruta_ingreso,
    ruta_deposito,
)
from core.utilidades import (
    parse_fecha,
    mes_anio_desde_fecha,
    formatear_moneda,
    limpiar_moneda,
    evaluar_expresion,
)
from core.persistencia import (
    cargar_db,
    guardar_db,
    cargar_historial,
    guardar_historial,
    actualizar_historial,
    existe_valor_unico,
    obtener_no_factura_numerico,
    obtener_consecutivo_esperado,
)
from core.adjuntos import (
    carpeta_de_registro,
    archivos_del_registro,
    eliminar_archivos_de_registro,
    eliminar_carpeta_si_vacia,
    carpeta_destino_factura,
    nombre_destino,
    adjuntar_archivos,
)
from excel.generador import (
    archivo_esta_bloqueado,
    escribir_excel,
    anexar_al_excel,
)
from lector_facturas import procesar_factura, agrupar_por_categoria
from core.correo_utils import agrupar_facturas_descargadas
from ui.widgets import EntryMoneda, EntryAutoComplete

# ============================================================
# MAPEO DE SERIES A CENTROS
# ============================================================
# Cada serie del XML corresponde a un centro específico.
# Ajusta este diccionario si agregas más series o centros.
def centro_desde_serie(serie):
    """
    Devuelve el nombre del centro según la serie del XML.
    Acepta variantes como 'S1', 'S1/', 's1', 'S-1'.
    """
    if not serie:
        return None
    # Limpiar: quitar '/', espacios, guiones, y pasar a mayúsculas
    s = str(serie).strip().upper()
    s = s.replace("/", "").replace("-", "").replace(" ", "")
    # Mapear con las variantes limpias
    mapeo = {
        "S1": "Central",
        "PRADOS": "Prado",
        "PRADO": "Prado",
    }
    return mapeo.get(s)

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
class AppIngresos(ttk.Window):
    def __init__(self):
        super().__init__(themename=TEMA)
        self.title("Sistema de Ingresos - Contabilidad")
        self.geometry("1250x880")
        self.minsize(1000, 700)

        # Año del archivo de registros cargado actualmente
        try:
            self._anio_cargado = int(datetime.now().year)
        except Exception:
            self._anio_cargado = datetime.now().year

        self.registros = cargar_db(self._anio_cargado)
        self.id_actual = None
        self.entradas = {}
        self.widgets_ordenados = []
        self.historial = actualizar_historial(self.registros)
        self._configurar_estilos()
        self._construir_ui()
        self._refrescar_tabla()
        self._recalcular_total()
        self._actualizar_titulo()
        self._ultima_factura_xml = None
        self._ultima_factura_pdf = None

    # ------------------------------------------------------------
    def _construir_ui(self):
        # ============================================================
        # BARRA LATERAL (colores según tema)
        # ============================================================
        self.colores_sidebar = obtener_colores_sidebar()

        # Estado del sidebar: True = expandido, False = colapsado
        self.sidebar_expandido = True
        self.sidebar_ancho_expandido = 220
        self.sidebar_ancho_colapsado = 60

        # Contenedor principal
        self.contenedor_principal = ttk.Frame(self)
        self.contenedor_principal.pack(fill="both", expand=True)

        # ---------- Barra lateral ----------
        self.sidebar = tk.Frame(
            self.contenedor_principal,
            bg=self.colores_sidebar["bg"],
            width=self.sidebar_ancho_expandido,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ---------- Encabezado del sidebar ----------
        self.header_sidebar = tk.Frame(
            self.sidebar,
            bg=self.colores_sidebar["bg"],
            height=80
        )
        self.header_sidebar.pack(fill="x", side="top")
        self.header_sidebar.pack_propagate(False)

        # Texto del logo (solo visible cuando expandido)
        self.lbl_logo_texto = tk.Label(
            self.header_sidebar,
            text="Sistema de\nIngresos",
            font=("Segoe UI", 15, "bold"),
            bg=self.colores_sidebar["bg"],
            fg=self.colores_sidebar["fg"],
            justify="left",
        )
        self.lbl_logo_texto.pack(side="left", padx=15, pady=10)

        # Botón de hamburguesa del header (visible SOLO cuando expandido)
        self.btn_hamburguesa_header = tk.Label(
            self.header_sidebar,
            text="☰",
            font=("Segoe UI", 18),
            bg=self.colores_sidebar["bg"],
            fg=self.colores_sidebar["fg"],
            cursor="hand2",
        )
        self.btn_hamburguesa_header.pack(side="right", padx=12, pady=10)
        self.btn_hamburguesa_header.bind("<Button-1>", lambda e: self._toggle_sidebar())

        # ---------- Separador ----------
        self.separador_sidebar = tk.Frame(
            self.sidebar,
            bg=self.colores_sidebar["separador"],
            height=1
        )
        self.separador_sidebar.pack(fill="x", pady=(0, 10))

        # ---------- Botones del menú ----------
        menu_items = [
            ("⚡", "Sincronizar",   self._sincronizar),
            ("📥", "Leer factura",  self._leer_factura),
            ("🏷️", "Reclasificar",  self._abrir_reclasificador),
            ("📊", "Generar Excel", self._generar_excel),
            ("📈", "Reportes",      self._ver_reportes),
            ("🎨", "Cambiar tema",  self._elegir_tema),
            ("📜", "Ver logs",      self._ver_logs),
            ("🔧", "Reset caché",   self._reset_cache),
        ]

        self._botones_menu = []
        for icono, texto, comando in menu_items:
            btn_frame = tk.Frame(
                self.sidebar,
                bg=self.colores_sidebar["bg"],
                cursor="hand2",
                height=50,
            )
            btn_frame.pack(fill="x", padx=0, pady=0)
            btn_frame.pack_propagate(False)

            lbl_icono = tk.Label(
                btn_frame,
                text=icono,
                font=("Segoe UI Emoji", 16),
                bg=self.colores_sidebar["bg"],
                fg=self.colores_sidebar["fg"],
                width=3,
            )
            lbl_icono.pack(side="left", padx=(12, 0), pady=10)

            lbl_texto = tk.Label(
                btn_frame,
                text=texto,
                font=("Segoe UI", 12),
                bg=self.colores_sidebar["bg"],
                fg=self.colores_sidebar["fg_suave"],
                anchor="w",
            )
            lbl_texto.pack(side="left", padx=(8, 10), pady=10, fill="x", expand=True)

            # Hover + click
            def _on_enter(e, frame=btn_frame, ic=lbl_icono, tx=lbl_texto):
                if not self.sidebar_expandido:
                    return
                c = self.colores_sidebar
                frame.configure(bg=c["hover"])
                ic.configure(bg=c["hover"])
                tx.configure(bg=c["hover"], fg=c["fg"])

            def _on_leave(e, frame=btn_frame, ic=lbl_icono, tx=lbl_texto):
                c = self.colores_sidebar
                frame.configure(bg=c["bg"])
                ic.configure(bg=c["bg"])
                tx.configure(bg=c["bg"], fg=c["fg_suave"])

            def _on_click(e, cmd=comando):
                cmd()

            for widget in (btn_frame, lbl_icono, lbl_texto):
                widget.bind("<Enter>", _on_enter)
                widget.bind("<Leave>", _on_leave)
                widget.bind("<Button-1>", _on_click)

            self._botones_menu.append({
                "frame": btn_frame,
                "icono": lbl_icono,
                "texto": lbl_texto,
            })

        # ---------- Versión al pie ----------
        self.lbl_version = tk.Label(
            self.sidebar,
            text="v1.0",
            font=("Segoe UI", 8),
            bg=self.colores_sidebar["bg"],
            fg=self.colores_sidebar["version"],
        )
        self.lbl_version.pack(side="bottom", pady=10)

        # ---------- Contenido principal ----------
        self.contenido = ttk.Frame(self.contenedor_principal)
        self.contenido.pack(side="left", fill="both", expand=True)

        # ============================================================
        # BARRA SUPERIOR DE CONFIGURACIÓN + BOTONES PRINCIPALES
        # ============================================================
        top = ttk.LabelFrame(self.contenido, text="Configuración", padding=10)
        top.pack(fill="x", padx=10, pady=5)

        # --- Fila única con todo ---
        # Selector: Centro
        ttk.Label(top, text="Centro:").grid(row=0, column=1, padx=5, sticky="e")
        self.var_centro = ttk.StringVar(value="Central")
        ttk.Combobox(top, textvariable=self.var_centro, values=["Central", "Prado"],
                     width=12, state="readonly", bootstyle="primary").grid(
            row=0, column=2, padx=5)

        # Selector: Año
        ttk.Label(top, text="Año:").grid(row=0, column=3, padx=5, sticky="e")
        self.var_anio = ttk.StringVar(value=str(datetime.now().year))
        ttk.Entry(top, textvariable=self.var_anio, width=6,
                  style="Custom.TEntry").grid(row=0, column=4, padx=5)

        # Selector: Mes
        ttk.Label(top, text="Mes:").grid(row=0, column=5, padx=5, sticky="e")
        self.var_mes = ttk.StringVar(value=MESES_ES[datetime.now().month-1])
        ttk.Combobox(top, textvariable=self.var_mes, values=MESES_ES,
                     width=11, state="readonly", bootstyle="primary").grid(
            row=0, column=6, padx=5)

        # Botón: Abrir carpeta
        ttk.Button(top, text="📁 Abrir carpeta",
                   command=self._abrir_carpeta_ingreso,
                   bootstyle="info-outline").grid(row=0, column=7, padx=10)

        # Botones principales (a la derecha)
        ttk.Button(top, text="🆕 Nuevo", command=self._nuevo,
                   bootstyle="info-outline").grid(row=0, column=10, padx=3)

        self.btn_guardar = ttk.Button(top, text="💾 Guardar", command=self._guardar,
                                      bootstyle="info-outline")
        self.btn_guardar.grid(row=0, column=11, padx=3)

        self.btn_toggle_tabla = ttk.Button(
            top, text="👁️ Ocultar tabla", command=self._toggle_tabla,
            bootstyle="info-outline")
        self.btn_toggle_tabla.grid(row=0, column=12, padx=3)

        # Espacio flexible: empuja los botones de la derecha hacia el borde
        top.columnconfigure(8, weight=1)
        top.columnconfigure(9, weight=0)

        # ============================================================
        # FORMULARIO CON SCROLL
        # ============================================================
        cont = ttk.Frame(self.contenido)
        cont.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas_form = tk.Canvas(cont, borderwidth=0, highlightthickness=0)
        scroll = ttk.Scrollbar(cont, orient="vertical", command=self.canvas_form.yview)
        self.frame_form = ttk.Frame(self.canvas_form)

        self.frame_form.bind("<Configure>",
                             lambda e: self.canvas_form.configure(
                                 scrollregion=self.canvas_form.bbox("all")))
        self.canvas_window = self.canvas_form.create_window(
            (0, 0), window=self.frame_form, anchor="nw")
        self.canvas_form.configure(yscrollcommand=scroll.set)
        self.canvas_form.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.canvas_form.bind("<Configure>", self._on_canvas_configure)

        # Construir grupos de campos
        grupo_actual = None
        frame_grupo = None
        col = 0
        for clave, etiqueta, grupo, tipo in CAMPOS:
            if grupo != grupo_actual:
                grupo_actual = grupo
                frame_grupo = ttk.LabelFrame(self.frame_form, text=grupo, padding=8)
                frame_grupo.pack(fill="x", padx=5, pady=4)
                col = 0
            fila = col // 3
            columnas = (col % 3) * 2
            ttk.Label(frame_grupo, text=etiqueta + ":").grid(
                row=fila, column=columnas, padx=5, pady=3, sticky="e")

            if tipo == "date":
                w = DateEntry(frame_grupo, width=15, dateformat="%d/%m/%Y",
                              bootstyle="primary")
            elif tipo == "number":
                if clave == "total":
                    w = EntryMoneda(frame_grupo, callback=None, width=20,
                                    style="Custom.TEntry")
                    w.configure(state="readonly")
                elif clave in REGLAS_AUTO:
                    w = EntryMoneda(frame_grupo, callback=None, width=20,
                                    style="Custom.TEntry")
                else:
                    w = EntryMoneda(frame_grupo, callback=self._recalcular_total,
                                    width=20, style="Custom.TEntry")
            else:
                if clave in ("nombre", "rfc"):
                    w = EntryAutoComplete(frame_grupo,
                                          opciones=self.historial.get(clave, []),
                                          width=35 if clave == "nombre" else 20,
                                          style="Custom.TEntry")
                else:
                    w = ttk.Entry(frame_grupo, width=20, style="Custom.TEntry")
                # Forzar mayúsculas al escribir manualmente
                self._forzar_mayusculas(w)

            w.grid(row=fila, column=columnas + 1, padx=5, pady=3, sticky="w")
            self.entradas[clave] = w
            self.widgets_ordenados.append(w)
            col += 1

        # Conectar auto-cálculo de IVA
        for clave_iva, (clave_base, tasa) in REGLAS_AUTO.items():
            base = self.entradas[clave_base]
            iva = self.entradas[clave_iva]
            base.bind("<FocusOut>",
                      lambda e, b=base, i=iva, t=tasa: self._auto_iva(b, i, t), add="+")

        # --- Label de alerta de total ---
        self.lbl_alerta_total = ttk.Label(self.contenido, text="", bootstyle="danger")
        self.lbl_alerta_total.pack(fill="x", padx=15, pady=(0, 5))

        # ============================================================
        # TABLA
        # ============================================================
        self.frame_tabla = ttk.LabelFrame(self.contenido, text="Registros guardados", padding=5)
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)
        cols_vis = ["no_factura", "fecha", "nombre", "rfc", "total",
            "efectivo", "tc", "td", "cheque", "transfer",
            "folio_fiscal", "adjuntos"]
        self.tabla = ttk.Treeview(self.frame_tabla, columns=cols_vis,
            show="headings", height=8,
            bootstyle="primary")
        for c in cols_vis:
            if c == "adjuntos":
                self.tabla.heading(c, text="📎")
                self.tabla.column(c, width=45, anchor="center")
            else:
                self.tabla.heading(c, text=CAMPOS_DICT[c][1])
                self.tabla.column(c, width=100, anchor="center")
        self.tabla.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(self.frame_tabla, orient="vertical",
                           command=self.tabla.yview)
        sb.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=sb.set)

        # ---- MENÚ CONTEXTUAL para la tabla ----
        self._crear_menu_contextual_tabla()

        # ---- Enter salta al siguiente campo ----
        for w in self.widgets_ordenados:
            w.bind("<Return>", self._enter_siguiente, add="+")
            w.bind("<KP_Enter>", self._enter_siguiente, add="+")

        # ---- Validación visual No. Factura y QVET ----
        w_nf = self.entradas.get("no_factura")
        if w_nf:
            w_nf.bind("<KeyRelease>", self._validar_no_factura_visual, add="+")
            w_nf.bind("<FocusOut>", self._validar_no_factura_visual, add="+")
        w_qv = self.entradas.get("qvet")
        if w_qv:
            w_qv.bind("<KeyRelease>", self._validar_qvet_visual, add="+")
            w_qv.bind("<FocusOut>", self._validar_qvet_visual, add="+")

        # ---- Scroll con rueda del mouse ----
        self._bind_mousewheel(self.frame_form)

        # ---- Atajo Ctrl+T / Cmd+T ----
        self.bind("<Control-t>", lambda e: self._toggle_tabla())
        self.bind("<Command-t>", lambda e: self._toggle_tabla())
        self.bind("<Control-b>", lambda e: self._toggle_sidebar())
        self.bind("<Command-b>", lambda e: self._toggle_sidebar())

        # Validación inicial
        self._validar_no_factura_visual()
        self._validar_qvet_visual()

        # ---- Refrescar tabla y título al cambiar centro/año/mes ----
        def _on_cambio_anio(*args):
            try:
                anio = int(self.var_anio.get())
            except Exception:
                return
            if self._anio_cargado != anio:
                self.registros = cargar_db(anio)
                self._anio_cargado = anio
            self._refrescar_tabla()
            self._actualizar_titulo()

        def _on_cambio_reporte_otros(*args):
            self._refrescar_tabla()
            self._actualizar_titulo()

        self.var_anio.trace_add("write", _on_cambio_anio)
        self.var_centro.trace_add("write", _on_cambio_reporte_otros)
        self.var_mes.trace_add("write", _on_cambio_reporte_otros)
        # ---- Iniciar con el sidebar cerrado ----
        self.after(50, self._toggle_sidebar)

    # ---------------- BARRA LATERAL ----------------
    def _toggle_sidebar(self):
        """Expande o colapsa la barra lateral."""
        if self.sidebar_expandido:
            # ---- Colapsar ----
            self.sidebar.configure(width=self.sidebar_ancho_colapsado)

            # Ocultar el texto "Sistema de Ingresos" y dejar solo el ☰
            self.lbl_logo_texto.pack_forget()

            # Mover el ☰ al centro del header
            self.btn_hamburguesa_header.pack_forget()
            self.btn_hamburguesa_header.pack(side="top", pady=20)

            # Ocultar los textos de todos los botones de la lista
            for btn in self._botones_menu:
                btn["texto"].pack_forget()

            # Centrar los íconos
            for btn in self._botones_menu:
                btn["icono"].pack_configure(padx=(18, 0))

            self.sidebar_expandido = False

        else:
            # ---- Expandir ----
            self.sidebar.configure(width=self.sidebar_ancho_expandido)

            # Reponer el texto del header
            self.lbl_logo_texto.pack(side="left", padx=15, pady=10)

            # Mover el ☰ de vuelta a la derecha del header
            self.btn_hamburguesa_header.pack_forget()
            self.btn_hamburguesa_header.pack(side="right", padx=12, pady=10)

            # Reponer los textos de la lista
            for btn in self._botones_menu:
                btn["icono"].pack_configure(padx=(12, 0))
                btn["texto"].pack(side="left", padx=(8, 10), pady=10,
                                  fill="x", expand=True)

            self.sidebar_expandido = True

    # ---------------- MENÚ CONTEXTUAL DE LA TABLA ----------------
    def _crear_menu_contextual_tabla(self):
        """Crea el menú que aparece al hacer clic derecho en un registro."""
        self.menu_contextual = tk.Menu(self, tearoff=0)

        self.menu_contextual.add_command(
            label="✏️  Editar",
            command=self._editar
        )
        self.menu_contextual.add_command(
            label="🗑️  Eliminar",
            command=self._eliminar
        )
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(
            label="📎  Adjuntar factura",
            command=self._adjuntar_factura
        )
        self.menu_contextual.add_command(
            label="📂  Ver adjuntos",
            command=self._ver_adjuntos
        )

        # Bindings: clic derecho en Mac es Button-2 y Control+Click
        self.tabla.bind("<Button-3>", self._mostrar_menu_contextual)   # Windows/Linux
        self.tabla.bind("<Button-2>", self._mostrar_menu_contextual)   # Mac
        self.tabla.bind("<Control-Button-1>", self._mostrar_menu_contextual)  # Mac

    def _mostrar_menu_contextual(self, event):
        """Muestra el menú contextual en la posición del cursor."""
        # Identificar el registro bajo el cursor
        item = self.tabla.identify_row(event.y)
        if not item:
            return
        # Seleccionar el registro antes de mostrar el menú
        self.tabla.selection_set(item)
        # Mostrar el menú
        try:
            self.menu_contextual.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_contextual.grab_release()

    # ---------------- SCROLL ----------------
    def _on_mousewheel(self, event):
        if sys.platform == "darwin":
            delta = -1 * event.delta
        elif sys.platform.startswith("win"):
            delta = -1 * (event.delta // 120)
        else:
            delta = -1 if event.num == 5 else 1
        self.canvas_form.yview_scroll(int(delta), "units")

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")
        for hijo in widget.winfo_children():
            self._bind_mousewheel(hijo)

    def _on_canvas_configure(self, event):
        self.canvas_form.itemconfigure(self.canvas_window, width=event.width)

    # ---------------- ENTER ----------------
    def _enter_siguiente(self, event):
        widget_actual = event.widget

        if isinstance(widget_actual, EntryAutoComplete) and widget_actual._lista:
            widget_actual._seleccionar()
            return "break"

        if isinstance(widget_actual, EntryMoneda):
            texto = widget_actual.get().strip()
            if widget_actual._tiene_operacion(texto):
                widget_actual._ultima_expresion = texto.replace(",", "").replace("$", "").strip()
                widget_actual._ultimo_valor = evaluar_expresion(texto)
            else:
                widget_actual._ultima_expresion = ""
                widget_actual._ultimo_valor = limpiar_moneda(texto)
            widget_actual.delete(0, tk.END)
            widget_actual.insert(0, formatear_moneda(widget_actual._ultimo_valor))
            widget_actual._pintar()
            if widget_actual.callback:
                widget_actual.callback()

        try:
            idx = self.widgets_ordenados.index(widget_actual)
        except ValueError:
            return
        if idx + 1 < len(self.widgets_ordenados):
            siguiente = self.widgets_ordenados[idx + 1]
            siguiente.focus_set()
            try:
                siguiente.selection_range(0, tk.END)
            except Exception:
                pass
        else:
            self.btn_guardar.focus_set()
        return "break"

    # ---------------- CÁLCULOS AUTOMÁTICOS ----------------
    def _auto_iva(self, entrada_base, entrada_iva, tasa):
        base = entrada_base.get_valor()
        if base != 0:
            entrada_iva.set_valor(round(base * tasa, 2))
            self._recalcular_total()

    def _recalcular_total(self, *args):
        """
        TOTAL muestra la suma de tipo de pago.
        Compara con la suma de categorías y alerta si hay diferencia > $0.01.
        """
        total_pago = 0.0
        for clave in CAMPOS_TIPO_PAGO:
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                total_pago += w.get_valor()

        total_categorias = 0.0
        for clave in CATEGORIAS_PARA_TOTAL:
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                total_categorias += w.get_valor()

        w_total = self.entradas.get("total")
        if isinstance(w_total, EntryMoneda):
            w_total.configure(state="normal")
            w_total.set_valor(round(total_pago, 2))
            w_total.configure(state="readonly")

        if total_pago > 0 and total_categorias > 0:
            dif = abs(total_pago - total_categorias)
            if dif > 0.01:
                try:
                    w_total.configure(foreground="red")
                    self.lbl_alerta_total.configure(
                        text=f"⚠️ Diferencia: ${dif:,.2f} "
                             f"(pago: ${total_pago:,.2f} / "
                             f"categorías: ${total_categorias:,.2f})"
                    )
                except Exception:
                    pass
            else:
                try:
                    w_total.configure(foreground=COLORES["texto_normal"])
                    self.lbl_alerta_total.configure(text="")
                except Exception:
                    pass
        else:
            try:
                w_total.configure(foreground=COLORES["texto_normal"])
                self.lbl_alerta_total.configure(text="")
            except Exception:
                pass

    # ---------------- VALIDACIÓN VISUAL ----------------
    def _validar_campo_unico(self, clave, event=None):
        w = self.entradas.get(clave)
        if not w:
            return
        valor = w.get().strip()
        if not valor:
            self._pintar_entry(w, None)
            return
        duplicado = existe_valor_unico(self.registros, clave, valor,
                                       ignorar_id=self.id_actual)
        color = COLORES["campo_error"] if duplicado else COLORES["campo_ok"]
        self._pintar_entry(w, color)

    def _validar_no_factura_visual(self, event=None):
        self._validar_campo_unico("no_factura", event)

    def _validar_qvet_visual(self, event=None):
        self._validar_campo_unico("qvet", event)

    @staticmethod
    def _pintar_entry(widget, color_fondo):
        try:
            if color_fondo:
                widget.configure(background=color_fondo)
            else:
                widget.configure(background="")
        except Exception:
            pass

    @staticmethod
    def _forzar_mayusculas(widget):
        """Convierte automáticamente a mayúsculas lo que se escriba en el widget."""
        def _convertir(event):
            # Ignorar teclas especiales
            if event.keysym in ("BackSpace", "Delete", "Left", "Right",
                                "Up", "Down", "Home", "End", "Tab",
                                "Shift_L", "Shift_R", "Control_L", "Control_R",
                                "Alt_L", "Alt_R"):
                return
            texto_actual = widget.get()
            texto_mayus = texto_actual.upper()
            if texto_actual != texto_mayus:
                pos = widget.index(tk.INSERT)
                widget.delete(0, tk.END)
                widget.insert(0, texto_mayus)
                try:
                    widget.icursor(pos)
                except Exception:
                    pass

        widget.bind("<KeyRelease>", _convertir, add="+")

    # ---------------- CRUD ----------------
    def _leer_form(self):
        d = {}
        for clave, _, _, tipo in CAMPOS:
            w = self.entradas[clave]
            if tipo == "number":
                if isinstance(w, EntryMoneda):
                    texto = w.get().strip()
                    if w._tiene_operacion(texto):
                        w._ultima_expresion = texto.replace(",", "").replace("$", "").strip()
                        w._ultimo_valor = evaluar_expresion(texto)
                        w.delete(0, tk.END)
                        w.insert(0, formatear_moneda(w._ultimo_valor))
                    else:
                        w._ultimo_valor = limpiar_moneda(texto)

                    d[clave] = w._ultimo_valor
                    d[f"{clave}__expr"] = w._ultima_expresion
                else:
                    d[clave] = limpiar_moneda(w.get())
            elif tipo == "date":
                if isinstance(w, DateEntry):
                    d[clave] = w.entry.get()
                else:
                    d[clave] = w.get()
            else:
                d[clave] = w.get().strip().upper()
        d["centro"] = self.var_centro.get()
        d["anio"] = int(self.var_anio.get())
        d["mes"] = self.var_mes.get()
        return d

    def _escribir_form(self, r):
        for clave, _, _, tipo in CAMPOS:
            w = self.entradas[clave]
            valor = r.get(clave, "")
            if tipo == "number":
                if isinstance(w, EntryMoneda):
                    expr = r.get(f"{clave}__expr", "")
                    w.set_valor(float(valor or 0), expresion=expr)
            elif tipo == "date":
                if isinstance(w, DateEntry):
                    try:
                        w.entry.delete(0, tk.END)
                        w.entry.insert(0, str(valor))
                    except Exception:
                        pass
                else:
                    w.delete(0, tk.END)
                    w.insert(0, str(valor))
            else:
                w.delete(0, tk.END)
                w.insert(0, str(valor))

    def _nuevo(self):
        self.id_actual = None
        self._ultima_factura_xml = None
        self._ultima_factura_pdf = None
        hoy = datetime.now().strftime("%d/%m/%Y")
        for clave, _, _, tipo in CAMPOS:
            w = self.entradas[clave]
            if tipo == "number" and isinstance(w, EntryMoneda):
                w.set_valor(0, expresion="")
            elif tipo == "date":
                if isinstance(w, DateEntry):
                    try:
                        w.entry.delete(0, tk.END)
                        w.entry.insert(0, hoy)
                    except Exception:
                        pass
            else:
                w.delete(0, tk.END)
        for clave in ("nombre", "rfc"):
            w = self.entradas[clave]
            if isinstance(w, EntryAutoComplete):
                w.set_opciones(self.historial.get(clave, []))

        try:
            anio_actual = int(self.var_anio.get())
        except Exception:
            anio_actual = datetime.now().year
        esperado = obtener_consecutivo_esperado(
            self.registros,
            centro=self.var_centro.get(),
            anio=anio_actual,
            mes=self.var_mes.get()
        )
        if esperado is not None:
            self.entradas["no_factura"].insert(0, str(esperado))

        self._recalcular_total()
        self._validar_no_factura_visual()
        self._validar_qvet_visual()
        self.entradas["no_factura"].focus_set()

    def _guardar(self):
        w_foco = self.focus_get()
        if w_foco is not None:
            try:
                w_foco.event_generate("<FocusOut>")
            except Exception:
                pass
            self.update_idletasks()

        datos = self._leer_form()

        if not datos["no_factura"]:
            messagebox.showwarning("Falta info", "El No. de Factura es obligatorio.")
            return
        if not datos["qvet"]:
            messagebox.showwarning("Falta info", "El QVET es obligatorio.")
            return

        if self.id_actual is None:
            if existe_valor_unico(self.registros, "no_factura", datos["no_factura"]):
                messagebox.showerror("Duplicado",
                                     f"Ya existe el No. de Factura {datos['no_factura']}.")
                return
            if existe_valor_unico(self.registros, "qvet", datos["qvet"]):
                messagebox.showerror("Duplicado",
                                     f"Ya existe el QVET {datos['qvet']}.")
                return
        else:
            if existe_valor_unico(self.registros, "no_factura",
                                  datos["no_factura"], ignorar_id=self.id_actual):
                messagebox.showerror("Duplicado",
                                     f"Ya existe OTRO registro con No. Factura {datos['no_factura']}.")
                return
            if existe_valor_unico(self.registros, "qvet",
                                  datos["qvet"], ignorar_id=self.id_actual):
                messagebox.showerror("Duplicado",
                                     f"Ya existe OTRO registro con QVET {datos['qvet']}.")
                return

        if self.id_actual is None:
            esperado = obtener_consecutivo_esperado(
                self.registros,
                centro=datos["centro"],
                anio=datos["anio"],
                mes=datos["mes"]
            )
            actual = obtener_no_factura_numerico(datos["no_factura"])
            if esperado is not None and actual is not None and actual != esperado:
                respuesta = messagebox.askyesno(
                    "No. de Factura no consecutivo",
                    f"El último No. de Factura registrado es "
                    f"{esperado - 1}.\n\n"
                    f"El siguiente debería ser: {esperado}\n"
                    f"Pero estás ingresando: {actual}\n\n"
                    "¿Estás seguro de continuar?"
                )
                if not respuesta:
                    return

        for clave, _, _, tipo in CAMPOS:
            if tipo == "date":
                datos[clave] = parse_fecha(datos[clave]).replace("-", "/")

        es_edicion = self.id_actual is not None
        reg_viejo = None
        if es_edicion:
            reg_viejo = next((r for r in self.registros if r["id"] == self.id_actual), None)

        if not es_edicion:
            datos["id"] = int(datetime.now().timestamp() * 1000)
            self.registros.append(datos)
            msg = "Registro guardado."
        else:
            for i, r in enumerate(self.registros):
                if r["id"] == self.id_actual:
                    datos["id"] = self.id_actual
                    self.registros[i] = datos
                    break
            msg = "Registro actualizado."

        # Guardar en el archivo del año que corresponde
        try:
            anio_datos = int(datos.get("anio", self._anio_cargado))
        except Exception:
            anio_datos = self._anio_cargado
        guardar_db(self.registros, anio_datos)

        self.historial = actualizar_historial(self.registros)
        for clave in ("nombre", "rfc"):
            w = self.entradas[clave]
            if isinstance(w, EntryAutoComplete):
                w.set_opciones(self.historial.get(clave, []))

        fecha_carpeta = parse_fecha(datos.get("fecha", ""))
        ruta = ruta_ingreso(datos["centro"], datos["anio"],
                            MESES_ES.index(datos["mes"]) + 1) / fecha_carpeta
        try:
            ruta.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error carpeta", str(e))

        msgs_archivos = []
        if es_edicion and reg_viejo:
            msgs_archivos = self._gestionar_adjuntos_al_editar(reg_viejo, datos)

        if not es_edicion and (self._ultima_factura_xml or self._ultima_factura_pdf):
            rutas_adjuntar = []
            if self._ultima_factura_xml and Path(self._ultima_factura_xml).exists():
                rutas_adjuntar.append(self._ultima_factura_xml)
            if self._ultima_factura_pdf and Path(self._ultima_factura_pdf).exists():
                rutas_adjuntar.append(self._ultima_factura_pdf)

            if rutas_adjuntar:
                try:
                    copiados, errores = adjuntar_archivos(datos, rutas_adjuntar)
                    if copiados:
                        nombres = ", ".join(d.name for _, d in copiados)
                        msgs_archivos.append(f"\n📎 Adjuntados: {nombres}")
                    if errores:
                        for origen, err in errores:
                            msgs_archivos.append(f"⚠️ Error al adjuntar {origen}: {err}")
                except Exception as e:
                    msgs_archivos.append(f"⚠️ Error al adjuntar: {e}")

            self._ultima_factura_xml = None
            self._ultima_factura_pdf = None

        partes = [msg, f"Carpeta: {ruta}"]
        if msgs_archivos:
            partes.append("")
            partes.extend(msgs_archivos)
        messagebox.showinfo("OK", "\n".join(partes))

        self._refrescar_tabla()
        self._nuevo()

    def _gestionar_adjuntos_al_editar(self, reg_viejo, datos_nuevos):
        msgs = []
        no_viejo = str(reg_viejo.get("no_factura", "")).strip()
        no_nuevo = str(datos_nuevos.get("no_factura", "")).strip()
        carpeta_vieja = carpeta_de_registro(reg_viejo)
        carpeta_nueva = carpeta_de_registro(datos_nuevos)
        cambio_no = no_viejo and no_nuevo and no_viejo != no_nuevo
        cambio_carpeta = (carpeta_vieja and carpeta_nueva
                          and carpeta_vieja != carpeta_nueva)
        if not cambio_no and not cambio_carpeta:
            return msgs
        if not carpeta_vieja or not carpeta_vieja.exists():
            return msgs
        adjuntos = archivos_del_registro(reg_viejo)
        if not adjuntos:
            return msgs
        if cambio_carpeta:
            try:
                carpeta_nueva.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                msgs.append(f"⚠️ No se pudo crear la carpeta destino: {e}")
                return msgs
        for archivo in adjuntos:
            try:
                ext = archivo.suffix
                nombre_final = f"{no_nuevo}{ext}" if cambio_no else archivo.name
                carpeta_final = carpeta_nueva if cambio_carpeta else archivo.parent
                destino = carpeta_final / nombre_final
                if destino.resolve() == archivo.resolve():
                    continue
                if destino.exists():
                    msgs.append(f"⚠️ {archivo.name}: ya existe {nombre_final}, no se movió.")
                    continue
                archivo.rename(destino)
                if cambio_no and cambio_carpeta:
                    msgs.append(f"📝➡️ {archivo.name} → {carpeta_final.name}/{nombre_final}")
                elif cambio_no:
                    msgs.append(f"📝 {archivo.name} → {nombre_final}")
                else:
                    msgs.append(f"➡️ {archivo.name} movido a {carpeta_final.name}/")
            except Exception as e:
                msgs.append(f"⚠️ {archivo.name}: {e}")
        if cambio_carpeta and carpeta_vieja.exists():
            try:
                if not any(carpeta_vieja.iterdir()):
                    carpeta_vieja.rmdir()
                    msgs.append(f"🗑️ Carpeta vacía eliminada: {carpeta_vieja.name}/")
            except Exception:
                pass
        return msgs

    def _editar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Editar", "Selecciona un registro.")
            return
        id_sel = int(sel[0])
        for r in self.registros:
            if r["id"] == id_sel:
                self.id_actual = id_sel
                self._escribir_form(r)
                self.var_centro.set(r.get("centro", "Central"))
                self.var_anio.set(str(r.get("anio", datetime.now().year)))
                self.var_mes.set(r.get("mes", MESES_ES[datetime.now().month-1]))
                self._validar_no_factura_visual()
                self._validar_qvet_visual()
                break

    def _eliminar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Eliminar", "Selecciona un registro.")
            return
        id_sel = int(sel[0])
        reg = next((r for r in self.registros if r["id"] == id_sel), None)
        if not reg:
            return
        no_factura = str(reg.get("no_factura", "")).strip()
        fecha_str = reg.get("fecha", "")
        centro = reg.get("centro", "Central")
        archivos = archivos_del_registro(reg)
        carpeta = carpeta_de_registro(reg)
        lineas = [f"¿Eliminar el registro de la factura {no_factura}?",
                  "", f"Centro: {centro}", f"Fecha:  {fecha_str}", ""]
        if carpeta:
            lineas.append(f"Carpeta: {carpeta}")
        if archivos:
            lineas.append("")
            lineas.append(f"Se eliminarán {len(archivos)} archivo(s):")
            for a in archivos:
                lineas.append(f"   • {a.name}")
        lineas.append("")
        lineas.append("¿Continuar?")
        if not messagebox.askyesno("Confirmar", "\n".join(lineas)):
            return
        eliminados, errores = eliminar_archivos_de_registro(reg)
        self.registros = [r for r in self.registros if r["id"] != id_sel]
        guardar_db(self.registros, self._anio_cargado)
        self.historial = actualizar_historial(self.registros)
        carpeta_borrada = False
        motivo_carpeta = ""
        if carpeta and carpeta.exists():
            carpeta_borrada, motivo_carpeta = eliminar_carpeta_si_vacia(reg)
        self._refrescar_tabla()
        self._nuevo()
        partes = ["Registro eliminado."]
        if eliminados:
            partes.append(f"\nArchivos eliminados ({len(eliminados)}):")
            for a in eliminados:
                partes.append(f"   • {a.name}")
        if carpeta_borrada:
            partes.append(f"\nCarpeta eliminada:\n   {motivo_carpeta}")
        elif carpeta and carpeta.exists():
            partes.append(f"\nCarpeta NO eliminada:\n   {motivo_carpeta}")
        if errores:
            partes.append("\n⚠️ Errores:")
            for a, e in errores:
                partes.append(f"   • {a.name}: {e}")
        messagebox.showinfo("Resultado", "\n".join(partes))

    def _leer_factura(self):
        """Lee un XML (y opcionalmente un PDF) y llena el formulario."""
        ruta_xml = filedialog.askopenfilename(
            title="Selecciona el XML de la factura",
            filetypes=[("XML CFDI", "*.xml"), ("Todos", "*.*")]
        )
        if not ruta_xml:
            return

        ruta_pdf = filedialog.askopenfilename(
            title="Selecciona el PDF de la factura (opcional, cancelar para omitir)",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")]
        )

        try:
            datos = procesar_factura(ruta_xml, ruta_pdf or None)
        except Exception as e:
            messagebox.showerror("Error al leer factura",
                                 f"No se pudo procesar la factura:\n{e}")
            return

        resumen, _ = self._llenar_desde_factura(datos)

        self._ultima_factura_xml = ruta_xml
        self._ultima_factura_pdf = ruta_pdf or None

        serie = datos.get("serie", "").strip()
        centro_detectado = centro_desde_serie(serie)
        centro_txt = centro_detectado if centro_detectado else "sin cambios"

        # Recalcular los valores actuales de los combos (ya se cambiaron antes)
        centro_final = self.var_centro.get()
        mes_final = self.var_mes.get()
        anio_final = self.var_anio.get()

        lineas = [
            f"Factura leída: {datos['no_factura']}",
            f"Serie: {serie}",
            f"Centro: {centro_final}",
            f"Año: {anio_final} | Mes: {mes_final.capitalize()}",
            f"Nombre: {datos['nombre']}",
            f"Total: ${datos['total']:,.2f}",
            "",
            "Campos llenados:",
        ]
        lineas.extend(resumen)
        messagebox.showinfo("Factura leída", "\n".join(lineas))

        if not centro_detectado:
            messagebox.showwarning(
                "Serie no reconocida",
                f"La serie '{serie}' no está mapeada a ningún centro.\n\n"
                "Verifica manualmente el Centro antes de guardar.\n\n"
                "Si quieres agregarla, abre el código de ingresos.py "
                "y añade la serie al diccionario 'SERIES_A_CENTRO'."
            )

    def _pedir_credenciales_correo(self):
        """
        Pide las credenciales de Gmail y opciones de filtrado.
        Devuelve (usuario, password, etiqueta) o (None, None, None).
        """
        ventana = ttk.Toplevel(self)
        ventana.title("Configuración de Gmail")
        ventana.geometry("550x450")
        ventana.resizable(False, False)
        ventana.minsize(550, 450)
        ventana.transient(self)
        ventana.grab_set()

        # ---- Contenedor con padding ----
        contenedor = ttk.Frame(ventana, padding=20)
        contenedor.pack(fill="both", expand=True)

        # ---- Encabezado ----
        ttk.Label(contenedor,
                  text="Configuración de Gmail",
                  font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))

        ttk.Label(contenedor,
                  text="Necesitas una 'Contraseña de aplicación' de Google.\n"
                       "Genérala en: myaccount.google.com/apppasswords",
                  justify="center", foreground="gray",
                  font=("Segoe UI", 9)).pack(pady=(0, 20))

        # ---- Formulario (una fila por campo) ----
        form = ttk.Frame(contenedor)
        form.pack(fill="x", expand=False)

        # Columna 0: etiquetas | Columna 1: campos
        form.columnconfigure(0, weight=0)
        form.columnconfigure(1, weight=1)

        cfg_actual = CONFIG.get("correo", {})

        fila = 0

        # ---------- Correo de Gmail ----------
        ttk.Label(form, text="Correo de Gmail:").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_usuario = tk.StringVar(value=cfg_actual.get("usuario", ""))
        ttk.Entry(form, textvariable=var_usuario).grid(
            row=fila, column=1, sticky="ew", pady=8)
        fila += 1

        # ---------- Contraseña de app ----------
        ttk.Label(form, text="Contraseña de app:").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_password = tk.StringVar(value=cfg_actual.get("password_app", ""))
        ttk.Entry(form, textvariable=var_password, show="•").grid(
            row=fila, column=1, sticky="ew", pady=8)
        fila += 1

        # ---------- Etiqueta ----------
        ttk.Label(form, text="Etiqueta de Gmail:").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_etiqueta = tk.StringVar(
            value=cfg_actual.get("etiqueta", "FACTURAS BAALAK"))
        ttk.Entry(form, textvariable=var_etiqueta).grid(
            row=fila, column=1, sticky="ew", pady=8)
        fila += 1

        # Texto de ayuda de la etiqueta
        ttk.Label(form,
                  text="Ejemplo: 'Facturas QVET' o 'Facturas/QVET' (con subcarpeta)",
                  foreground="gray", font=("Segoe UI", 8)).grid(
            row=fila, column=1, sticky="w", pady=(0, 5))
        fila += 1

        # ---------- Filtro de remitente ----------
        ttk.Label(form, text="Filtrar por remitente:").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_remitente = tk.StringVar(
            value=cfg_actual.get("filtro_remitente", ""))
        ttk.Entry(form, textvariable=var_remitente).grid(
            row=fila, column=1, sticky="ew", pady=8)
        fila += 1

        ttk.Label(form,
                  text="Opcional. Ejemplo: 'qvet' o 'facturacion'. Déjalo vacío para descargar todos.",
                  foreground="gray", font=("Segoe UI", 8), wraplength=400).grid(
            row=fila, column=1, sticky="w", pady=(0, 5))
        fila += 1

        # ---------- Días atrás ----------
        ttk.Label(form, text="Correos de los últimos (días):").grid(
            row=fila, column=0, sticky="w", padx=(0, 10), pady=8)
        var_dias = tk.StringVar(value=str(cfg_actual.get("dias_atras", 30)))
        ttk.Entry(form, textvariable=var_dias, width=10).grid(
            row=fila, column=1, sticky="w", pady=8)
        fila += 1

        ttk.Label(form,
                  text="Escribe 0 para descargar todos los correos sin límite de fecha.",
                  foreground="gray", font=("Segoe UI", 8)).grid(
            row=fila, column=1, sticky="w", pady=(0, 5))
        fila += 1

        # ---- Espacio flexible para centrar botones abajo ----
        ttk.Frame(contenedor).pack(fill="y", expand=True)

        resultado = {"ok": False}

        def _guardar():
            u = var_usuario.get().strip()
            p = var_password.get().strip().replace(" ", "")
            e = var_etiqueta.get().strip() or "Facturas QVET"
            r = var_remitente.get().strip()
            try:
                d = int(var_dias.get().strip() or "0")
            except ValueError:
                d = 0

            if not u or not p:
                messagebox.showwarning(
                    "Faltan datos",
                    "Correo y contraseña son obligatorios.",
                    parent=ventana
                )
                return

            CONFIG["correo"] = {
                "usuario": u,
                "password_app": p,
                "etiqueta": e,
                "filtro_remitente": r,
                "dias_atras": d,
            }
            guardar_config(CONFIG)
            resultado["ok"] = True
            ventana.destroy()

        # ---- Botones ----
        fr = ttk.Frame(contenedor)
        fr.pack(fill="x", pady=(15, 0))

        ttk.Button(fr, text="💾 Guardar",
                   command=_guardar,
                   bootstyle="info-outline").pack(side="right", padx=5)

        ventana.wait_window()

        if resultado["ok"]:
            return (CONFIG["correo"]["usuario"],
                    CONFIG["correo"]["password_app"],
                    CONFIG["correo"]["etiqueta"])
        return None, None, None

    def _editar_config_correo(self):
        """
        Abre el diálogo de configuración de Gmail para editar los datos
        ya guardados (correo, contraseña, etiqueta, filtros).
        """
        # Abrir el diálogo (ya carga los valores actuales desde CONFIG)
        usuario, password, etiqueta = self._pedir_credenciales_correo()
        if usuario:
            messagebox.showinfo(
                "Configuración actualizada",
                f"Datos guardados correctamente.\n\n"
                f"Correo: {usuario}\n"
                f"Etiqueta: {etiqueta}\n\n"
                "Ahora puedes sincronizar con ⚡ Sincronizar."
            )

    def _sincronizar(self):
        """
        Flujo unificado: descarga facturas del correo y pregunta al usuario
        qué hacer con ellas.
        Ofrece la opción de editar la configuración si hay errores.
        """
        from correo_facturas import descargar_adjuntos_gmail

        # ---- Bucle: permite reintentar tras editar credenciales ----
        while True:
            # ---- 1. Verificar/obtener configuración ----
            cfg_correo = CONFIG.get("correo", {})
            usuario = cfg_correo.get("usuario", "")
            password = cfg_correo.get("password_app", "")
            etiqueta = cfg_correo.get("etiqueta", "FACTURAS BAALAK")
            filtro_remitente = cfg_correo.get("filtro_remitente", "")
            dias_atras = cfg_correo.get("dias_atras", 30)

            # Si no hay configuración, pedirla
            if not usuario or not password:
                usuario, password, etiqueta = self._pedir_credenciales_correo()
                if not usuario:
                    return
                cfg_correo = CONFIG.get("correo", {})
                filtro_remitente = cfg_correo.get("filtro_remitente", "")
                dias_atras = cfg_correo.get("dias_atras", 30)

            # ---- 2. Preguntar modo con opción de editar ----
            modo = self._preguntar_modo_descarga(dias_atras)
            if modo == "cancelar":
                return
            elif modo == "editar":
                # Abrir el diálogo de configuración
                u, p, e = self._pedir_credenciales_correo()
                if u:
                    messagebox.showinfo(
                        "Configuración actualizada",
                        f"Datos guardados correctamente.\n\n"
                        f"Correo: {u}\n"
                        f"Etiqueta: {e}"
                    )
                # Volver al inicio del bucle para preguntar de nuevo
                continue
            else:
                solo_no_leidos = (modo == "no_leidos")
                break

        # ---- 3. Ventana de progreso ----
        ventana_prog = ttk.Toplevel(self)
        ventana_prog.title("⚡ Sincronizando facturas...")
        ventana_prog.geometry("900x700")
        ventana_prog.transient(self)
        # Flag para saber si el usuario quiere cancelar la descarga
        # ---- Estado de cancelación ----
        estado = {"cancelar": False}

        def _al_intentar_cerrar():
            """Se ejecuta cuando el usuario hace clic en la X."""
            if estado["cancelar"]:
                return
            respuesta = messagebox.askyesno(
                "Cancelar descarga",
                "La descarga está en curso.\n\n"
                "¿Quieres cancelarla?\n\n"
                "Los correos ya descargados quedarán guardados.\n"
                "El proceso se detendrá en el próximo correo.",
                parent=ventana_prog
            )
            if respuesta:
                estado["cancelar"] = True
                log("⚠️ Cancelación solicitada. Esperando a que termine el correo actual...")
                try:
                    self.barra_progreso.stop()
                    self.lbl_progreso.configure(text="⚠️ Cancelando...")
                except Exception:
                    pass

        ventana_prog.protocol("WM_DELETE_WINDOW", _al_intentar_cerrar)

        def debe_cancelar():
            """Devuelve True si el usuario canceló la operación."""
            return estado["cancelar"]

        # Centrar la ventana
        ventana_prog.update_idletasks()
        x = (ventana_prog.winfo_screenwidth() - 900) // 2
        y = (ventana_prog.winfo_screenheight() - 700) // 2
        ventana_prog.geometry(f"900x700+{x}+{y}")

        # ---- Título ----
        ttk.Label(ventana_prog,
                  text="⚡ Sincronizando facturas del correo",
                  font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))

        # ---- Contador grande de progreso ----
        self.lbl_progreso = ttk.Label(
            ventana_prog,
            text="⏳ Preparando...",
            font=("Segoe UI", 11),
            bootstyle="info"
        )
        self.lbl_progreso.pack(pady=5)

        # ---- Barra de progreso indeterminada (para la fase de descarga) ----
        self.barra_progreso = ttk.Progressbar(
            ventana_prog,
            mode="indeterminate",
            bootstyle="info-striped",
            length=600
        )
        self.barra_progreso.pack(pady=5, padx=20, fill="x")
        self.barra_progreso.start(15)  # animación continua

        # ---- Log ----
        frame_log = ttk.LabelFrame(ventana_prog, text="Detalle", padding=5)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        txt_log = tk.Text(frame_log, height=22, width=100,
                          font=("Consolas", 9), wrap="word")
        txt_log.pack(fill="both", expand=True, side="left")

        sb = ttk.Scrollbar(frame_log, orient="vertical", command=txt_log.yview)
        sb.pack(side="right", fill="y")
        txt_log.configure(yscrollcommand=sb.set)

        def log(msg):
            txt_log.insert(tk.END, msg + "\n")
            txt_log.see(tk.END)
            try:
                ventana_prog.update()
            except Exception:
                pass

        def actualizar_progreso(texto):
            """Actualiza el texto grande de progreso."""
            try:
                self.lbl_progreso.configure(text=texto)
                ventana_prog.update()
            except Exception:
                pass

        # ---- 4. Descargar del correo ----
        log("=" * 80)
        log("PASO 1: Descargando adjuntos del correo")
        log("=" * 80)

        carpeta_descargas = _CARPETA_DATOS / "facturas_descargadas"
        if carpeta_descargas.exists():
            for f in carpeta_descargas.iterdir():
                if f.is_file():
                    try:
                        f.unlink()
                    except Exception:
                        pass

        # ---- Detener la animación de la barra ----
        try:
            self.barra_progreso.stop()
            self.barra_progreso.configure(mode="determinate")
            self.barra_progreso["value"] = 100
        except Exception:
            pass

        descargados, errores, info = descargar_adjuntos_gmail(
            usuario=usuario,
            password_app=password,
            etiqueta=etiqueta,
            carpeta_destino=carpeta_descargas,
            solo_no_leidos=solo_no_leidos,
            filtro_remitente=filtro_remitente if filtro_remitente else None,
            dias_atras=dias_atras if dias_atras else None,
            usar_cache=True,
            callback_log=log,
            callback_progreso=actualizar_progreso,
            callback_cancelado=debe_cancelar,
        )

        # ---- 5. Verificar si hubo errores de autenticación ----
        if errores and any("AUTHENTICATIONFAILED" in str(e).upper() or
                            "LOGIN" in str(e).upper() or
                            "IMAP" in str(e).upper() or
                            "authentication" in str(e).lower()
                            for e in errores):
            log("\n" + "=" * 80)
            log("❌ ERROR DE AUTENTICACIÓN")
            log("=" * 80)
            log("Los datos de conexión al correo son incorrectos.")
            log("\nRevisa la configuración.")

            ventana_prog.update_idletasks()

            editar = messagebox.askyesno(
                "Error de autenticación",
                "No se pudo conectar al correo.\n\n"
                "Los datos de conexión son incorrectos (usuario, contraseña "
                "de aplicación, o etiqueta).\n\n"
                "¿Quieres editar la configuración ahora?"
            )
            if editar:
                u, p, e = self._pedir_credenciales_correo()
                if u:
                    messagebox.showinfo(
                        "Configuración actualizada",
                        f"Datos guardados correctamente.\n\n"
                        "Vuelve a intentar con ⚡ Sincronizar."
                    )
            return

        log(f"\n📊 Resumen de descarga:")
        log(f"   Correos encontrados: {info.get('total_correos', 0)}")
        log(f"   Correos procesados:  {info.get('procesados', 0)}")
        log(f"   Omitidos por caché:  {info.get('omitidos_cache', 0)}")
        log(f"   Omitidos por filtro: {info.get('omitidos_filtros', 0)}")
        log(f"   Archivos descargados: {len(descargados)}")
        log(f"   Log completo: {info.get('log', '')}")

        # ---- Si el usuario canceló, salir limpiamente ----
        if estado["cancelar"]:
            log("\n" + "=" * 80)
            log("⚠️ DESCARGA CANCELADA POR EL USUARIO")
            log("=" * 80)
            log(f"Se descargaron {len(descargados)} archivos antes de cancelar.")
            if descargados:
                log(f"Los archivos están en: {carpeta_descargas}")
                log("Puedes procesarlos con '📥 Leer factura' cuando quieras.")
            ventana_prog.protocol("WM_DELETE_WINDOW",
                lambda: ventana_prog.destroy())
            return

        if not descargados:
            log("\n⚠️ No se descargó ningún archivo nuevo.")
            if errores:
                log("Errores:")
                for e in errores:
                    log(f"  • {e}")
            ventana_prog.protocol("WM_DELETE_WINDOW",
                lambda: ventana_prog.destroy())
            return

        # ---- 6. Agrupar por No. de factura ----
        log("\n" + "=" * 80)
        log("PASO 2: Agrupando por No. de factura")
        log("=" * 80)

        archivos_por_correo = info.get("archivos_por_correo", {})
        grupos = agrupar_facturas_descargadas(
            carpeta_descargas,
            archivos_por_correo=archivos_por_correo
        )
        log(f"Facturas únicas detectadas: {len(grupos)}")

        # ---- 7. Preguntar qué hacer ----
        ventana_prog.grab_release()
        respuesta_procesar = self._preguntar_accion_facturas(
            len(descargados), len(grupos), carpeta_descargas
        )
        ventana_prog.grab_set()

        if respuesta_procesar == "cancelar":
            log("\n⏸️ Los archivos quedan en disco. Puedes procesarlos con '📥 Leer factura'.")
            log(f"   Carpeta: {carpeta_descargas}")
            return

        if respuesta_procesar == "solo_guardar":
            log("\n📁 Archivos guardados (sin procesar).")
            log(f"   Carpeta: {carpeta_descargas}")
            messagebox.showinfo(
                "Archivos descargados",
                f"Se descargaron {len(descargados)} archivos.\n\n"
                f"Carpeta: {carpeta_descargas}\n\n"
                "Puedes procesarlos con '📥 Leer factura'."
            )
            return

        # Preparar la barra para mostrar progreso de procesamiento
        try:
            self.barra_progreso.configure(mode="determinate", maximum=len(grupos))
            self.barra_progreso["value"] = 0
        except Exception:
            pass

        # ---- 8. Procesar todas automáticamente ----
        log("\n" + "=" * 80)
        log("PASO 3: Procesando facturas")
        log("=" * 80)

        uuids_existentes = set()
        for r in self.registros:
            ff = str(r.get("folio_fiscal", "")).strip()
            if ff:
                uuids_existentes.add(ff)

        facturas_procesadas = []
        facturas_duplicadas = []
        facturas_sin_xml = []
        facturas_con_error = []

        def _orden_grupo(item):
            clave = item[0]
            try:
                return int(str(clave).replace("grupo_", ""))
            except Exception:
                return 0

        for i, (_, files) in enumerate(sorted(grupos.items(), key=_orden_grupo), 1):
            no_factura = files.get("no_factura", "?")
            log(f"\n[{i}/{len(grupos)}] Procesando factura {no_factura}...")
            try:
                self.barra_progreso["value"] = i
                self.lbl_progreso.configure(
                    text=f"⚙️ Procesando factura {i} de {len(grupos)}: {no_factura}"
                )
                ventana_prog.update()
            except Exception:
                pass

            if not files["xml"]:
                log(f"  ⚠️ No hay XML. Se omite.")
                facturas_sin_xml.append(no_factura)
                continue

            try:
                datos = procesar_factura(
                    str(files["xml"]),
                    str(files["pdf"]) if files["pdf"] else None
                )

                if existe_valor_unico(self.registros, "no_factura",
                                       datos["no_factura"]):
                    log(f"  ⏭️ Ya existe No. de Factura {datos['no_factura']}. Se omite.")
                    facturas_duplicadas.append(datos["no_factura"])
                    continue

                ff = str(datos.get("folio_fiscal", "")).strip()
                if ff and ff in uuids_existentes:
                    log(f"  ⏭️ Ya existe Folio Fiscal {ff[:8]}... Se omite.")
                    facturas_duplicadas.append(datos["no_factura"])
                    continue

                try:
                    anio_factura = int(datos.get("anio", self._anio_cargado))
                except Exception:
                    anio_factura = self._anio_cargado

                if anio_factura != self._anio_cargado:
                    regs_anio = cargar_db(anio_factura)
                else:
                    regs_anio = self.registros

                if existe_valor_unico(regs_anio, "no_factura", datos["no_factura"]):
                    log(f"  ⏭️ Ya existe (en año {anio_factura}). Se omite.")
                    facturas_duplicadas.append(datos["no_factura"])
                    continue

                _, datos_completos = self._llenar_desde_factura(datos)

                # Aplicar QVET desde el asunto del correo (si está disponible)
                qvet_por_archivo = info.get("qvet_por_archivo", {})
                nombre_xml = Path(files["xml"]).name
                qvet_email = qvet_por_archivo.get(nombre_xml, "")
                if qvet_email:
                    self.entradas["qvet"].delete(0, tk.END)
                    self.entradas["qvet"].insert(0, qvet_email.upper())
                    datos_completos["qvet"] = qvet_email.upper()
                    log(f"  🔖 QVET asignado desde el correo: {qvet_email}")
                self._ultima_factura_xml = str(files["xml"])
                self._ultima_factura_pdf = str(files["pdf"]) if files["pdf"] else None

                self._guardar_silencioso(datos_completos)

                if ff:
                    uuids_existentes.add(ff)

                log(f"  ✅ Guardado: No. {datos['no_factura']} | "
                    f"{datos.get('centro', '?')} | "
                    f"{datos.get('mes', '?')} {datos.get('anio', '?')} | "
                    f"Total: ${datos['total']:,.2f}")
                facturas_procesadas.append(datos)

            except Exception as e:
                log(f"  ❌ Error: {e}")
                facturas_con_error.append((no_factura, str(e)))

        # ---- 9. Resumen final ----
        log("\n" + "=" * 80)
        log("RESUMEN FINAL")
        log("=" * 80)
        log(f"✅ Facturas guardadas:  {len(facturas_procesadas)}")
        log(f"⏭️ Facturas duplicadas: {len(facturas_duplicadas)}")
        log(f"⚠️ Facturas sin XML:    {len(facturas_sin_xml)}")
        log(f"❌ Facturas con error:  {len(facturas_con_error)}")

        if facturas_procesadas:
            total_procesado = sum(f.get("total", 0) for f in facturas_procesadas)
            log(f"\n💰 Total procesado: ${total_procesado:,.2f}")

            from collections import defaultdict
            resumen = defaultdict(lambda: {"n": 0, "total": 0.0})
            for f in facturas_procesadas:
                key = (f.get("centro", "?"),
                       f.get("mes", "?"),
                       f.get("anio", "?"))
                resumen[key]["n"] += 1
                resumen[key]["total"] += f.get("total", 0)

            log("\n📊 Desglose:")
            for (centro, mes, anio), data in sorted(resumen.items()):
                log(f"   • {centro:<10} {mes:<12} {anio}   "
                    f"{data['n']:>3} facturas   ${data['total']:>12,.2f}")

        if facturas_duplicadas:
            log(f"\n⏭️ Facturas duplicadas (omitidas):")
            for nf in facturas_duplicadas:
                log(f"   • {nf}")

        if facturas_sin_xml:
            log(f"\n⚠️ Facturas sin XML:")
            for nf in facturas_sin_xml:
                log(f"   • {nf}")

        if facturas_con_error:
            log(f"\n❌ Errores:")
            for nf, err in facturas_con_error:
                log(f"   • {nf}: {err}")

        log(f"\n📄 Log completo guardado en: {info.get('log', '')}")

        self._refrescar_tabla()
        self._nuevo()

        messagebox.showinfo(
            "Sincronización completa",
            f"✅ {len(facturas_procesadas)} facturas guardadas\n"
            f"⏭️ {len(facturas_duplicadas)} duplicadas\n"
            f"⚠️ {len(facturas_sin_xml)} sin XML\n"
            f"❌ {len(facturas_con_error)} con error\n\n"
            f"Log: {info.get('log', '')}"
        )

        # Reponer el comportamiento normal de la X
        try:
            ventana_prog.protocol("WM_DELETE_WINDOW", ventana_prog.destroy)
        except Exception:
            pass

    def _preguntar_accion_facturas(self, num_archivos, num_facturas, carpeta):
        """
        Muestra un diálogo personalizado preguntando qué hacer con las
        facturas descargadas.
        
        Devuelve:
          - "procesar_todas" → procesar automáticamente
          - "solo_guardar"   → solo guardar en disco
        """
        ventana = ttk.Toplevel(self)
        ventana.title("Facturas descargadas")
        ventana.transient(self)
        ventana.grab_set()
        ventana.resizable(False, False)

        # ---- Centrar la ventana ----
        ventana.update_idletasks()
        ancho = 450
        alto = 300
        x = (ventana.winfo_screenwidth() - ancho) // 2
        y = (ventana.winfo_screenheight() - alto) // 2
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

        # ---- Contenedor con padding ----
        contenedor = ttk.Frame(ventana, padding=25)
        contenedor.pack(fill="both", expand=True)

        # ---- Encabezado ----
        ttk.Label(
            contenedor,
            text="📬 Facturas descargadas",
            font=("Segoe UI", 15, "bold"),
        ).pack(pady=(0, 10))

        # ---- Resumen ----
        resumen = (
            f"Se descargaron {num_archivos} archivo(s),\n"
            f"correspondientes a {num_facturas} factura(s) única(s)."
        )
        ttk.Label(
            contenedor,
            text=resumen,
            font=("Segoe UI", 11),
            justify="center",
        ).pack(pady=(0, 5))

        # ---- Ruta de la carpeta ----
        ttk.Label(
            contenedor,
            text=f"📁 {carpeta}",
            font=("Segoe UI", 9),
            foreground="gray",
            wraplength=460,
            justify="center",
        ).pack(pady=(0, 20))

        # ---- Pregunta ----
        ttk.Label(
            contenedor,
            text="¿Qué quieres hacer?",
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(0, 15))

        # ---- Resultado ----
        resultado = {"accion": "cancelar"}

        def _elegir(accion):
            resultado["accion"] = accion
            ventana.destroy()

        # ---- Botón: Procesar todas ----
        ttk.Button(
            contenedor,
            text="✅  Procesar TODAS automáticamente",
            command=lambda: _elegir("procesar_todas"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        # Descripción del botón
        ttk.Label(
            contenedor,
            text="Llena el formulario, guarda y adjunta XML+PDF automáticamente",
            font=("Segoe UI", 8),
            foreground="gray",
        ).pack(pady=(0, 10))

        # ---- Botón: Solo guardar ----
        ttk.Button(
            contenedor,
            text="📁  Solo guardar los archivos",
            command=lambda: _elegir("solo_guardar"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        # Descripción del botón
        ttk.Label(
            contenedor,
            text="Los archivos quedan en disco para procesarlos después con '📥 Leer factura'",
            font=("Segoe UI", 8),
            foreground="gray",
        ).pack(pady=(0, 10))

        # ---- Cerrar con X = Cancelar ----
        ventana.protocol("WM_DELETE_WINDOW", lambda: _elegir("cancelar"))

        # ---- Atajos de teclado ----
        ventana.bind("<Escape>", lambda e: _elegir("cancelar"))

        ventana.wait_window()
        return resultado["accion"]

    def _preguntar_modo_descarga(self, dias_atras):
        """
        Muestra un diálogo personalizado para elegir cómo descargar.
        Devuelve:
          - "no_leidos" → solo correos no leídos
          - "todos"     → todos los correos
          - "editar"    → abrir configuración
        """
        ventana = ttk.Toplevel(self)
        ventana.title("Sincronizar facturas")
        ventana.geometry("450x250")
        ventana.resizable(False, False)
        ventana.transient(self)
        ventana.grab_set()

        # Centrar la ventana
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 450) // 2
        y = (ventana.winfo_screenheight() - 250) // 2
        ventana.geometry(f"450x250+{x}+{y}")

        # ---- Encabezado ----
        ttk.Label(ventana, text="⚡ Sincronizar facturas",
                  font=("Segoe UI", 14, "bold")).pack(pady=(20, 5))

        ttk.Label(ventana, text="¿Cómo quieres descargar?",
                  font=("Segoe UI", 10), foreground="gray").pack(pady=(0, 20))

        # ---- Botones de opción ----
        resultado = {"modo": "cancelar"}

        def _elegir(modo):
            resultado["modo"] = modo
            ventana.destroy()

        # Botón: Solo no leídos
        ttk.Button(
            ventana,
            text="📥  Solo correos NO leídos  (más rápido)",
            command=lambda: _elegir("no_leidos"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        # Botón: Todos los correos
        texto_todos = "📨  Todos los correos"
        if dias_atras:
            texto_todos += f"  (últimos {dias_atras} días)"
        else:
            texto_todos += "  (sin límite de fecha)"
        ttk.Button(
            ventana,
            text=texto_todos,
            command=lambda: _elegir("todos"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        # Separador
        ttk.Separator(ventana).pack(fill="x", padx=20, pady=10)

        # Botón: Editar configuración
        ttk.Button(
            ventana,
            text="⚙️  Editar configuración del correo",
            command=lambda: _elegir("editar"),
            bootstyle="info-outline",
            width=35,
        ).pack(pady=5)

        ventana.wait_window()
        return resultado["modo"]

    def _guardar_silencioso(self, datos):
        """
        Guarda un registro en el archivo correspondiente SIN mostrar
        diálogos de confirmación. Usado por el flujo automático.
        """
        # Normalizar fechas
        for clave, _, _, tipo in CAMPOS:
            if tipo == "date":
                datos[clave] = parse_fecha(datos[clave]).replace("-", "/")

        # Asignar ID
        datos["id"] = int(datetime.now().timestamp() * 1000)

        # Año del registro
        try:
            anio_datos = int(datos.get("anio", self._anio_cargado))
        except Exception:
            anio_datos = self._anio_cargado

        # Cargar los registros del año destino (por si el año es distinto al activo)
        if anio_datos != self._anio_cargado:
            regs_destino = cargar_db(anio_datos)
        else:
            regs_destino = self.registros

        regs_destino.append(datos)
        guardar_db(regs_destino, anio_datos)

        # Actualizar historial
        self.historial = actualizar_historial(regs_destino)

        # Crear carpeta del registro
        fecha_carpeta = parse_fecha(datos.get("fecha", ""))
        ruta = ruta_ingreso(datos["centro"], datos["anio"],
                            MESES_ES.index(datos["mes"]) + 1) / fecha_carpeta
        try:
            ruta.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # Auto-adjuntar XML y PDF
        rutas_adjuntar = []
        if self._ultima_factura_xml and Path(self._ultima_factura_xml).exists():
            rutas_adjuntar.append(self._ultima_factura_xml)
        if self._ultima_factura_pdf and Path(self._ultima_factura_pdf).exists():
            rutas_adjuntar.append(self._ultima_factura_pdf)

        if rutas_adjuntar:
            try:
                copiados, errores = adjuntar_archivos(datos, rutas_adjuntar)
                # LOG para diagnosticar
                print(f"[GUARDAR-SILENCIOSO] Copiados: {copiados}")
                if errores:
                    print(f"[GUARDAR-SILENCIOSO] Errores: {errores}")
            except Exception as e:
                print(f"[GUARDAR-SILENCIOSO] Excepción al adjuntar: {e}")

        # ---- Eliminar los archivos originales de facturas_descargadas ----
        carpeta_descargas = _CARPETA_DATOS / "facturas_descargadas"
        for ruta in rutas_adjuntar:
            try:
                p = Path(ruta)
                if p.exists() and p.parent == carpeta_descargas:
                    p.unlink()
                    print(f"[GUARDAR-SILENCIOSO] Eliminado de descargas: {p.name}")
            except Exception as e:
                print(f"[GUARDAR-SILENCIOSO] No se pudo eliminar {ruta}: {e}")

        self._ultima_factura_xml = None
        self._ultima_factura_pdf = None

        # Refrescar registros en memoria si es el mismo año
        if anio_datos == self._anio_cargado:
            self.registros = regs_destino

    def _llenar_desde_factura(self, datos):
        """
        Llena el formulario con los datos de la factura.
        Devuelve:
          - resumen (lista de strings)
          - datos_completos (dict con TODOS los campos del formulario)
        """
        # 0. Detectar centro, año y mes según la factura
        serie = datos.get("serie", "").strip()
        centro_detectado = centro_desde_serie(serie)
        if centro_detectado:
            self.var_centro.set(centro_detectado)

        fecha_factura = datos.get("fecha", "")
        mes_detectado, anio_detectado = mes_anio_desde_fecha(fecha_factura)
        if anio_detectado:
            self.var_anio.set(str(anio_detectado))
        if mes_detectado:
            self.var_mes.set(mes_detectado)

        try:
            anio_actual = int(self.var_anio.get())
        except Exception:
            anio_actual = self._anio_cargado
        if self._anio_cargado != anio_actual:
            self.registros = cargar_db(anio_actual)
            self._anio_cargado = anio_actual

        # 1. Limpiar formulario
        self._nuevo()

        # 2. Datos generales
        self.entradas["no_factura"].delete(0, tk.END)
        self.entradas["no_factura"].insert(0, str(datos["no_factura"]).upper())

        self.entradas["qvet"].delete(0, tk.END)
        self.entradas["qvet"].insert(0, str(datos.get("qvet", "")).upper())

        self.entradas["nombre"].delete(0, tk.END)
        self.entradas["nombre"].insert(0, str(datos["nombre"]).upper())

        self.entradas["rfc"].delete(0, tk.END)
        self.entradas["rfc"].insert(0, str(datos["rfc"]).upper())

        self.entradas["folio_fiscal"].delete(0, tk.END)
        self.entradas["folio_fiscal"].insert(0, datos["folio_fiscal"])

        if isinstance(self.entradas["fecha"], DateEntry):
            try:
                self.entradas["fecha"].entry.delete(0, tk.END)
                self.entradas["fecha"].entry.insert(0, datos["fecha"])
            except Exception:
                pass

        if isinstance(self.entradas["fecha_impresion"], DateEntry):
            try:
                self.entradas["fecha_impresion"].entry.delete(0, tk.END)
                self.entradas["fecha_impresion"].entry.insert(0, datos.get("fecha_impresion", ""))
            except Exception:
                pass

        # 3. Agrupar conceptos
        agrupado, detalle = agrupar_por_categoria(datos)

        mapa_campos = {
            "U": {"importe": "u_importe", "iva": "u_iva"},
            "ACCESORIOS": {"importe": "ac_importe", "iva": "ac_iva"},
            "ESTETICA": {"importe": "est_importe", "iva": "est_iva"},
            "TRANSPORTE": {"importe": "tra_importe", "iva": "tra_iva"},
            "VACUNA": {"importe": "vac_importe"},
            "CLINICA": {"importe": "cli_importe"},
            "MEDICAMENTOS": {
                "importe": "med_importe",
                "sin_iva": "med_sin_iva",
                "iva": "med_iva",
            },
            "HIGIENE": {
                "importe": "hig_importe",
                "sin_iva": "hig_sin_iva",
                "iva": "hig_iva",
                "sin_ieps_6": "hig_sin_ieps_6",
                "ieps_6": "hig_ieps_6",
                "sin_ieps_7": "hig_sin_ieps_7",
                "ieps_7": "hig_ieps_7",
            },
        }

        resumen = []
        for cat, valores in agrupado.items():
            if cat not in mapa_campos:
                continue
            for subclave, campo in mapa_campos[cat].items():
                valor = valores.get(subclave, 0.0)
                if valor == 0:
                    continue
                w = self.entradas.get(campo)
                if isinstance(w, EntryMoneda):
                    clave_det = f"{cat}__{subclave}"
                    terminos = detalle.get(clave_det, [])
                    if terminos:
                        expresion = "+".join(terminos)
                    else:
                        expresion = f"{valor:.2f}"
                    w.set_valor(round(valor, 2), expresion=expresion)
                    resumen.append(f"  {cat} → {campo}: ${valor:,.2f}")

        # 4. Tipo de pago
        pagos = datos.get("pagos", {})
        for clave in ("efectivo", "tc", "td", "cheque", "transfer", "vale"):
            valor = pagos.get(clave, 0)
            if valor <= 0:
                continue
            w = self.entradas.get(clave)
            if isinstance(w, EntryMoneda):
                w.set_valor(round(valor, 2), expresion=f"{valor:.2f}")
                resumen.append(f"  {clave.upper()}: ${valor:,.2f}")

        # 5. Recalcular
        self._recalcular_total()

        # 6. Leer TODOS los campos del formulario para tener el dict completo
        datos_completos = self._leer_form()
        # Preservar los pagos del XML
        datos_completos["pagos"] = pagos

        return resumen, datos_completos

    def _actualizar_titulo(self):
        try:
            self.title(
                f"Sistema de Ingresos — {self.var_centro.get()} "
                f"{self.var_mes.get()} {self.var_anio.get()}"
            )
        except Exception:
            pass

    # ---------------- TABLA ----------------
    def _ver_reportes(self):
        """Abre el diálogo de reportes disponibles."""
        from dialogos.reportes import abrir_dialogo_reportes
        abrir_dialogo_reportes(self)

    def _refrescar_tabla(self):
        """Carga los registros del año activo y filtra por centro/mes."""
        try:
            anio_activo = int(self.var_anio.get())
        except Exception:
            anio_activo = datetime.now().year

        # Si cambió el año, recargar desde el archivo correspondiente
        if self._anio_cargado != anio_activo:
            self.registros = cargar_db(anio_activo)
            self._anio_cargado = anio_activo

        # ---- Limpiar tabla ----
        for i in self.tabla.get_children():
            self.tabla.delete(i)

        # ---- Filtrar y mostrar (SIN autoajuste) ----
        mes_activo = self.var_mes.get()
        centro_activo = self.var_centro.get()

        filtrados = [
            r for r in self.registros
            if r.get("centro") == centro_activo
            and r.get("anio") == anio_activo
            and r.get("mes") == mes_activo
        ]

        def clave_orden(r):
            n = obtener_no_factura_numerico(r.get("no_factura", ""))
            return (n is None, n or 0, str(r.get("no_factura", "")))
        filtrados.sort(key=clave_orden)

        for r in filtrados:
            try:
                n_adj = len(archivos_del_registro(r))
            except Exception:
                n_adj = 0
            self.tabla.insert("", "end", iid=r["id"],
                values=(r.get("no_factura", ""), r.get("fecha", ""),
                    r.get("nombre", ""), r.get("rfc", ""),
                    formatear_moneda(r.get("total", 0)),
                    formatear_moneda(r.get("efectivo", 0)),
                    formatear_moneda(r.get("tc", 0)),
                    formatear_moneda(r.get("td", 0)),
                    formatear_moneda(r.get("cheque", 0)),
                    formatear_moneda(r.get("transfer", 0)),
                    r.get("folio_fiscal", ""),
                    f"📎 {n_adj}" if n_adj else ""))

    # ---------------- ADJUNTOS ----------------
    def _adjuntar_factura(self):
        reg = None
        if self.id_actual is not None:
            reg = next((r for r in self.registros if r["id"] == self.id_actual), None)
        if reg is None:
            sel = self.tabla.selection()
            if sel:
                reg = next((r for r in self.registros if r["id"] == int(sel[0])), None)
        if reg is None:
            messagebox.showinfo("Adjuntar", "Guarda primero el registro o selecciona uno.")
            return
        no_factura = str(reg.get("no_factura", "")).strip()
        if not no_factura:
            messagebox.showwarning("Falta info", "El registro no tiene No. de Factura.")
            return
        rutas = filedialog.askopenfilenames(
            title=f"Seleccionar factura para {no_factura}",
            filetypes=[("Facturas", "*.pdf *.xml *.PDF *.XML"),
                       ("PDF", "*.pdf"), ("XML", "*.xml"),
                       ("Todos", "*.*")])
        if not rutas:
            return
        carpeta = carpeta_destino_factura(reg)
        existentes = []
        for ruta in rutas:
            destino = carpeta / nombre_destino(no_factura, ruta)
            if destino.exists():
                existentes.append(destino.name)
        if existentes:
            if not messagebox.askyesno("Reemplazar",
                                       "Ya existen:\n" + "\n".join(existentes) +
                                       "\n\n¿Reemplazar?"):
                return
        copiados, errores = adjuntar_archivos(reg, rutas)
        lineas = []
        if copiados:
            lineas.append(f"✅ {len(copiados)} archivo(s) adjuntado(s):")
            for _, d in copiados:
                lineas.append(f"   • {d.name}")
            lineas.append(f"\nCarpeta:\n{carpeta}")
        if errores:
            lineas.append(f"\n⚠️ Errores:")
            for o, e in errores:
                lineas.append(f"   • {o}: {e}")
        messagebox.showinfo("Adjuntar", "\n".join(lineas))
        self._refrescar_tabla()

    def _ver_adjuntos(self):
        """Abre el diálogo para ver los adjuntos de un registro."""
        from dialogos.adjuntos import abrir_dialogo_adjuntos

        reg = None
        if self.id_actual is not None:
            reg = next((r for r in self.registros if r["id"] == self.id_actual), None)
        if reg is None:
            sel = self.tabla.selection()
            if sel:
                reg = next((r for r in self.registros if r["id"] == int(sel[0])), None)
        if reg is None:
            messagebox.showinfo("Ver adjuntos", "Selecciona un registro.")
            return

        abrir_dialogo_adjuntos(self, reg)

    @staticmethod
    def _abrir_archivo(ruta):
        try:
            if sys.platform.startswith("win"):
                os.startfile(ruta)
            elif sys.platform == "darwin":
                os.system(f'open "{ruta}"')
            else:
                os.system(f'xdg-open "{ruta}"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir:\n{e}")

    def _abrir_carpeta_ingreso(self):
        anio = int(self.var_anio.get())
        mes = MESES_ES.index(self.var_mes.get()) + 1
        ruta = ruta_ingreso(self.var_centro.get(), anio, mes)
        ruta.mkdir(parents=True, exist_ok=True)
        self._abrir_carpeta(ruta)

    @staticmethod
    def _abrir_carpeta(ruta):
        if sys.platform.startswith("win"):
            os.startfile(ruta)
        elif sys.platform == "darwin":
            os.system(f'open "{ruta}"')
        else:
            os.system(f'xdg-open "{ruta}"')

    def _toggle_tabla(self):
        if self.frame_tabla.winfo_ismapped():
            self.frame_tabla.pack_forget()
            self.btn_toggle_tabla.configure(text="👁️ Mostrar tabla")
        else:
            self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)
            self.btn_toggle_tabla.configure(text="👁️ Ocultar tabla")

    def _configurar_estilos(self):
        style = ttk.Style()
        oscuro = tema_es_oscuro()
        color_texto = "#ffffff" if oscuro else "#000000"
        color_fondo = "#2b2b2b" if oscuro else "#ffffff"

        try:
            style.configure("Custom.TEntry",
                            foreground=color_texto,
                            fieldbackground=color_fondo,
                            background=color_fondo)
            style.map("Custom.TEntry",
                      foreground=[("disabled", "#888888"),
                                  ("readonly", color_texto)],
                      fieldbackground=[("readonly", color_fondo),
                                       ("disabled", color_fondo)],
                      background=[("readonly", color_fondo)])
        except Exception as e:
            print(f"[_configurar_estilos] Error: {e}")

    def _elegir_tema(self):
        """Abre el diálogo para elegir el tema visual."""
        from dialogos.temas import abrir_dialogo_temas
        abrir_dialogo_temas(self)

    def _configurar_ventana(self, ventana, ancho=500, alto=400,
        min_ancho=400, min_alto=320,
        centrar_en_padre=True):
        """
        Configura tamaño, minsize y centrado de un Toplevel.
        - En vez de bloquear el resize, permite agrandar.
        - Centra la ventana respecto a la principal.
        """
        ventana.geometry(f"{ancho}x{alto}")
        ventana.minsize(min_ancho, min_alto)
        ventana.transient(self)
        ventana.grab_set()
        ventana.update_idletasks()

        if centrar_en_padre:
            x = self.winfo_rootx() + (self.winfo_width() - ancho) // 2
            y = self.winfo_rooty() + (self.winfo_height() - alto) // 2
            x = max(0, x)
            y = max(0, y)
            ventana.geometry(f"+{x}+{y}")

    def _repintar_sidebar(self):
        """Aplica los colores del tema actual a todos los widgets del sidebar."""
        self.colores_sidebar = obtener_colores_sidebar()
        c = self.colores_sidebar

        # Contenedores principales
        self.sidebar.configure(bg=c["bg"])
        self.header_sidebar.configure(bg=c["bg"])
        self.separador_sidebar.configure(bg=c["separador"])
        self.lbl_version.configure(bg=c["bg"], fg=c["version"])

        # Encabezado y hamburguesa del header
        self.lbl_logo_texto.configure(bg=c["bg"], fg=c["fg"])
        self.btn_hamburguesa_header.configure(bg=c["bg"], fg=c["fg"])

        # Botones del menú
        for btn in self._botones_menu:
            btn["frame"].configure(bg=c["bg"])
            btn["icono"].configure(bg=c["bg"], fg=c["fg"])
            btn["texto"].configure(bg=c["bg"], fg=c["fg_suave"])

    def _repintar_todo(self):
        for w in self.entradas.values():
            if isinstance(w, EntryMoneda):
                w._pintar()

        color_texto = COLORES["texto_normal"]
        color_fondo = COLORES["fondo_entry"]

        for w in self.entradas.values():
            if isinstance(w, EntryAutoComplete):
                try:
                    w.configure(foreground=color_texto, background=color_fondo)
                except Exception:
                    pass

        self._validar_no_factura_visual()
        self._validar_qvet_visual()
        self.update_idletasks()

    # -----------------EXCEL--------------------------
    def _generar_excel(self):
        """Genera (o anexa a) el Excel de resumen del centro/mes/año activo."""
        from tkinter import messagebox

        if not self.registros:
            messagebox.showwarning("Sin datos", "No hay registros.")
            return

        anio = int(self.var_anio.get())
        mes_idx = MESES_ES.index(self.var_mes.get()) + 1
        mes_nombre = self.var_mes.get()
        centro = self.var_centro.get()

        filtrados = [
            r for r in self.registros
            if r.get("anio") == anio
            and r.get("mes") == mes_nombre
            and r.get("centro") == centro
        ]

        if not filtrados:
            messagebox.showwarning(
                "Sin datos",
                f"No hay registros para {centro} - {mes_nombre} {anio}.")
            return

        carpeta = ruta_deposito(anio, mes_idx)
        carpeta.mkdir(parents=True, exist_ok=True)

        nombre = f"Resumen {centro} - {mes_nombre} {anio}.xlsx"
        ruta_xlsx = carpeta / nombre
        existe = ruta_xlsx.exists()

        if archivo_esta_bloqueado(ruta_xlsx):
            messagebox.showerror(
                "Archivo en uso",
                f"El archivo Excel ya existe y está abierto en otro programa.\n\n"
                f"Archivo:\n{ruta_xlsx}\n\n"
                f"👉 Ciérralo y vuelve a intentarlo para poder anexar los datos nuevos."
            )
            return

        try:
            if existe:
                nuevos, omitidos = anexar_al_excel(ruta_xlsx, filtrados)
                if nuevos == 0:
                    messagebox.showinfo(
                        "Sin novedades",
                        f"El archivo ya contiene todos los registros.\n\n"
                        f"Archivo:\n{ruta_xlsx}\n\n"
                        f"Ya presentes: {omitidos}"
                    )
                    self._abrir_carpeta(carpeta)
                    return
                msg = (
                    f"Archivo ACTUALIZADO (no sobrescrito):\n{ruta_xlsx}\n\n"
                    f"➕ Nuevos agregados: {nuevos}\n"
                    f"⏭️ Ya existían:      {omitidos}"
                )
            else:
                escribir_excel(
                    ruta_xlsx, filtrados,
                    var_mes=mes_nombre, var_anio=anio
                )
                msg = (
                    f"Archivo creado:\n{ruta_xlsx}\n\n"
                    f"Registros: {len(filtrados)}"
                )
        except PermissionError:
            messagebox.showerror(
                "Archivo en uso",
                f"No se pudo guardar el Excel porque el archivo está "
                f"abierto en otro programa (probablemente Excel).\n\n"
                f"Archivo:\n{ruta_xlsx}\n\n"
                f"👉 Cierra el archivo y vuelve a intentarlo."
            )
            return
        except OSError as e:
            if getattr(e, "errno", None) in (13, 11):
                messagebox.showerror(
                    "Archivo bloqueado",
                    f"No se pudo acceder al archivo.\n\n"
                    f"Archivo:\n{ruta_xlsx}\n\n"
                    f"👉 Verifica que no esté abierto en Excel ni en otro "
                    f"programa, y que tengas permisos de escritura.\n\n"
                    f"Detalle: {e}"
                )
            else:
                messagebox.showerror("Error al crear Excel", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error al crear Excel", str(e))
            return

        messagebox.showinfo("Excel generado", msg)
        self._abrir_carpeta(carpeta)

    # ---------------- RECLASIFICADOR ----------------
    def _abrir_reclasificador(self):
        """Abre el diálogo del reclasificador de productos."""
        from dialogos.reclasificador import abrir_dialogo_reclasificador
        abrir_dialogo_reclasificador(self)

    def _ver_logs(self):
        """Abre la carpeta de logs."""
        carpeta = _CARPETA_DATOS / "logs"
        carpeta.mkdir(parents=True, exist_ok=True)
        self._abrir_carpeta(carpeta)

    def _reset_cache(self):
        """Resetea la caché de correos procesados."""
        ruta = _CARPETA_DATOS / "correos_procesados.json"
        if ruta.exists():
            if not messagebox.askyesno(
                "Reset caché",
                "Esto hará que la próxima sincronización descargue TODOS los correos "
                "de la etiqueta (incluso los ya procesados).\n\n"
                "Los duplicados se detectarán igual, pero se descargarán de nuevo.\n\n"
                "¿Continuar?"
            ):
                return
            try:
                ruta.unlink()
                messagebox.showinfo("Reset caché",
                                     "Caché eliminada correctamente.")
            except Exception as e:
                messagebox.showerror("Error",
                                      f"No se pudo eliminar la caché:\n{e}")
        else:
            messagebox.showinfo("Reset caché",
                                 "No hay caché para eliminar.")
# ============================================================
if __name__ == "__main__":
    app = AppIngresos()
    app.mainloop()