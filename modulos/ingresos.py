# -*- coding: utf-8 -*-
"""
Sistema de Ingresos - Contabilidad
Interfaz moderna con ttkbootstrap.
Registros por año (un archivo JSON por año).
"""
import sys
from pathlib import Path

# Agregar la raíz del proyecto al path
_raiz = Path(__file__).parent.parent
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))
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
class AppIngresos(ttk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
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
                w = DateEntry(frame_grupo, width=15, dateformat="%d/%m/%Y",bootstyle="primary")
            elif tipo == "number":
                if clave == "total":
                    w = EntryMoneda(frame_grupo, callback=None, width=20,style="Custom.TEntry")
                    w.configure(state="readonly")
                elif clave in REGLAS_AUTO:
                    w = EntryMoneda(frame_grupo, callback=None, width=20,style="Custom.TEntry")
                    w.configure(state="readonly")
                else:
                    w = EntryMoneda(frame_grupo, callback=self._recalcular_total,width=20, style="Custom.TEntry")
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
            if dif > 0.02:
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
        self._recalcular_total()

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
                self._recalcular_total()
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

        resumen, _, avisos_reclasificacion = self._llenar_desde_factura(datos)

        if avisos_reclasificacion:
            self._avisar_reclasificacion(avisos_reclasificacion)

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

    def _editar_config_correo(self):
        """
        Abre el diálogo de configuración de Gmail para editar los datos
        ya guardados (correo, contraseña, etiqueta, filtros).
        """
        from dialogos.gmail_config import pedir_credenciales_correo

        usuario, password, etiqueta = pedir_credenciales_correo(self)
        if usuario:
            messagebox.showinfo(
                "Configuración actualizada",
                f"✅ Datos guardados correctamente\n\n"
                f"📧 Correo: {usuario or '(vacío)'}\n"
                f"🏷️ Etiqueta: {etiqueta or '(vacía)'}\n\n"
                f"Ya puedes sincronizar con el botón ⚡ Sincronizar."
            )

    def _sincronizar(self):
        """Abre el flujo de sincronización con el correo."""
        from dialogos.sincronizar import sincronizar_facturas
        sincronizar_facturas(self)

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
        agrupado, detalle, avisos_reclasificacion = agrupar_por_categoria(datos)

        mapa_campos = {
            "U": {"importe": "u_importe", "iva": "u_iva"},
            "ACCESORIOS": {"importe": "ac_importe", "iva": "ac_iva"},
            "ESTETICA": {"importe": "est_importe", "iva": "est_iva"},
            "TRANSPORTE": {"importe": "tra_importe", "iva": "tra_iva"},
            "VACUNA": {"importe": "vac_importe"},
            "CLINICA": {"importe": "cli_importe"},
            "PENSION": {"importe": "pen_importe", "iva": "pen_iva"},
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
                    # Para IMPORTE: usar la expresión con operaciones
                    # Para IVA: usar solo el VALOR (evitar expresiones largas que fallen)
                    if subclave == "iva":
                        # El IVA se calcula automáticamente por _auto_iva
                        # Solo asignamos el valor, sin expresión
                        w.set_valor(round(valor, 2))
                    else:
                        # Importe y otros: usar la expresión
                        clave_det = f"{cat}__{subclave}"
                        terminos = detalle.get(clave_det, [])
                        if terminos:
                            expresion = "+".join(terminos)
                        else:
                            expresion = f"{valor:.2f}"
                        w.set_valor(round(valor, 2), expresion=expresion)

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
        self.after(100, self._recalcular_total)

        # 6. Leer TODOS los campos del formulario para tener el dict completo
        datos_completos = self._leer_form()

        # Preservar los pagos del XML
        datos_completos["pagos"] = pagos

        return resumen, datos_completos, avisos_reclasificacion

    def _avisar_reclasificacion(self, avisos):
        """
        Muestra un aviso con los productos que tienen IVA pero están en
        categorías que no lo manejan (VACUNA, CLINICA).
        Ofrece un botón para registrarlos en el catálogo.
        """
        if not avisos:
            return

        # Encabezado con datos de la factura
        primer_aviso = avisos[0]
        no_factura = primer_aviso.get("no_factura", "?")
        nombre_cliente = primer_aviso.get("nombre", "?")
        fecha = primer_aviso.get("fecha", "?")
        folio_fiscal = primer_aviso.get("folio_fiscal", "")

        lineas = [
            "⚠️ Se detectaron productos con IVA en categorías que no lo manejan.",
            "",
            f"📄 Factura: {no_factura}",
            f"👤 Cliente: {nombre_cliente}",
            f"📅 Fecha:   {fecha}",
        ]
        if folio_fiscal:
            lineas.append(f"🔑 UUID:    {folio_fiscal[:8]}…")
        lineas.append("")
        lineas.append("Productos detectados:")
        lineas.append("")

        # Agrupar por categoría
        por_categoria = {}
        for a in avisos:
            cat = a["categoria_actual"]
            por_categoria.setdefault(cat, []).append(a)

        for cat, items in sorted(por_categoria.items()):
            lineas.append(f"📂 {cat}:")
            for a in items:
                lineas.append(
                    f"   • {a['producto']} "
                    f"(remisión {a['remision']}) — ${a['importe']:,.2f}"
                )
            lineas.append("")

        lineas.append("¿Qué quieres hacer?")

        # ---- Diálogo personalizado ----
        ventana = ttk.Toplevel(self)
        ventana.title("Reclasificación sugerida")
        self._configurar_ventana(ventana, ancho=700, alto=500,
                                 min_ancho=600, min_alto=400)

        # Encabezado
        ttk.Label(ventana,
                  text="⚠️ Productos en categorías incorrectas",
                  font=("Segoe UI", 14, "bold")).pack(pady=(15, 5))

        ttk.Label(ventana,
                  text=f"Factura {no_factura} — {nombre_cliente}",
                  font=("Segoe UI", 10),
                  foreground="gray").pack(pady=(0, 15))

        # Frame de productos con scroll
        frame_prod = ttk.LabelFrame(ventana, text="Productos detectados", padding=10)
        frame_prod.pack(fill="both", expand=True, padx=15, pady=5)

        txt = tk.Text(frame_prod, wrap="word", font=("Consolas", 10),
                      height=12, borderwidth=0)
        txt.pack(fill="both", expand=True, side="left")

        sb = ttk.Scrollbar(frame_prod, orient="vertical", command=txt.yview)
        sb.pack(side="right", fill="y")
        txt.configure(yscrollcommand=sb.set)

        for linea in lineas:
            txt.insert(tk.END, linea + "\n")
        txt.configure(state="disabled")

        # ---- Botones ----
        fr_btn = ttk.Frame(ventana)
        fr_btn.pack(fill="x", padx=15, pady=15)

        resultado = {"accion": "cerrar"}

        def _registrar():
            resultado["accion"] = "registrar"
            ventana.destroy()

        def _cerrar():
            resultado["accion"] = "cerrar"
            ventana.destroy()

        ttk.Button(fr_btn, text="➕ Registrar en catálogo",
                   command=_registrar,
                   bootstyle="info-outline").pack(side="left", padx=5)
        ttk.Button(fr_btn, text="Cerrar",
                   command=_cerrar,
                   bootstyle="secondary-outline").pack(side="right", padx=5)

        ventana.protocol("WM_DELETE_WINDOW", _cerrar)
        ventana.bind("<Escape>", lambda e: _cerrar())

        ventana.wait_window()

        # ---- Si el usuario decidió registrar ----
        if resultado["accion"] == "registrar":
            from dialogos.registrar_productos import abrir_dialogo_registrar_productos
            abrir_dialogo_registrar_productos(self, avisos)

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
        """..."""
        # Liberar cualquier grab previo (por si otra ventana lo tenía)
        try:
            self.grab_release()
        except Exception:
            pass

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

    @staticmethod
    def _backup_excel(ruta_xlsx):
        """
        Crea un backup del archivo Excel antes de borrarlo.
        
        El backup se guarda en la misma carpeta con el nombre:
            <nombre_archivo>_backup_YYYY-MM-DD_HH-MM-SS.xlsx
        
        Devuelve la ruta del backup creado, o None si no se pudo crear.
        """
        if not ruta_xlsx.exists():
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_base = ruta_xlsx.stem
            nombre_backup = f"{nombre_base}_backup_{timestamp}{ruta_xlsx.suffix}"
            ruta_backup = ruta_xlsx.parent / nombre_backup
            
            shutil.copy2(ruta_xlsx, ruta_backup)
            return ruta_backup
        except Exception as e:
            print(f"[_backup_excel] Error al crear backup: {e}")
            return None

    @staticmethod
    def _contar_backups(ruta_xlsx):
        """
        Cuenta los backups que existen para un Excel dado.
        Los backups tienen el nombre:
            <nombre_base>_backup_YYYY-MM-DD_HH-MM-SS.xlsx
        """
        if not ruta_xlsx.parent.exists():
            return 0

        nombre_base = ruta_xlsx.stem
        patron = f"{nombre_base}_backup_*.xlsx"
        return len(list(ruta_xlsx.parent.glob(patron)))

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
        # Ordenar por FECHA ascendente y luego por No. factura ascendente
        from datetime import datetime

        def _clave_orden(r):
            fecha_str = r.get("fecha", "")
            try:
                fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y")
            except Exception:
                fecha_dt = datetime.min
            no_factura = obtener_no_factura_numerico(r.get("no_factura", "")) or 0
            return (fecha_dt, no_factura)

        filtrados.sort(key=_clave_orden)

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
                # Preguntar al usuario qué hacer
                respuesta = messagebox.askyesnocancel(
                    "Archivo existente",
                    f"El archivo Excel ya existe:\n{ruta_xlsx}\n\n"
                    f"¿Qué quieres hacer?\n\n"
                    f"• Sí → Anexar solo los registros NUEVOS (más rápido)\n"
                    f"• No → Reordenar TODO (borra y regenera completo)\n"
                    f"• Cancelar → No hacer nada",
                    icon="question"
                )
                if respuesta is None:
                    # Cancelar
                    return
                elif respuesta is True:
                    # Anexar solo nuevos
                    nuevos, omitidos = anexar_al_excel(ruta_xlsx, filtrados)
                    n_backups = self._contar_backups(ruta_xlsx)
                    if nuevos == 0:
                        msg_sin = (
                            f"El archivo ya contiene todos los registros.\n\n"
                            f"Archivo:\n{ruta_xlsx}\n\n"
                            f"Ya presentes: {omitidos}"
                        )
                        if n_backups > 0:
                            msg_sin += f"\n\n💾 Backups existentes: {n_backups}"
                        messagebox.showinfo("Sin novedades", msg_sin)
                        self._abrir_carpeta(carpeta)
                        return
                    msg = (
                        f"Archivo ACTUALIZADO (no sobrescrito):\n{ruta_xlsx}\n\n"
                        f"➕ Nuevos agregados: {nuevos}\n"
                        f"⏭️ Ya existían:      {omitidos}"
                    )
                    if n_backups > 0:
                        msg += f"\n\n💾 Backups existentes: {n_backups}"
                else:
                    # Reordenar todo: backup, borrar y regenerar
                    ruta_backup = self._backup_excel(ruta_xlsx)

                    try:
                        ruta_xlsx.unlink()
                    except Exception as e:
                        messagebox.showerror(
                            "Error al borrar",
                            f"No se pudo borrar el archivo original:\n{e}"
                        )
                        return

                    escribir_excel(
                        ruta_xlsx, filtrados,
                        var_mes=mes_nombre, var_anio=anio
                    )

                    n_backups = self._contar_backups(ruta_xlsx)
                    if ruta_backup:
                        msg = (
                            f"Archivo REORDENADO (borrado y regenerado):\n"
                            f"{ruta_xlsx}\n\n"
                            f"Registros: {len(filtrados)}\n\n"
                            f"💾 Backup recién creado:\n"
                            f"{ruta_backup.name}"
                        )
                    else:
                        msg = (
                            f"Archivo REORDENADO (borrado y regenerado):\n"
                            f"{ruta_xlsx}\n\n"
                            f"Registros: {len(filtrados)}\n\n"
                            f"⚠️ No se pudo crear el backup."
                        )

                    if n_backups > 0:
                        msg += (
                            f"\n\n📦 Total de backups de este Excel: {n_backups}\n"
                            f"(Guárdalos o elimínalos manualmente desde la carpeta)"
                        )
            else:
                escribir_excel(
                    ruta_xlsx, filtrados,
                    var_mes=mes_nombre, var_anio=anio
                )
                n_backups = self._contar_backups(ruta_xlsx)
                msg = (
                    f"Archivo creado:\n{ruta_xlsx}\n\n"
                    f"Registros: {len(filtrados)}"
                )
                if n_backups > 0:
                    msg += f"\n\n💾 Backups existentes: {n_backups}"
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
    import ttkbootstrap as ttk_local

    # Para ejecutarlo directamente, hay que crear una raíz antes
    raiz = ttk_local.Window(themename=TEMA)
    raiz.withdraw()  # Ocultar la raíz vacía

    app = AppIngresos(master=raiz)
    app.protocol("WM_DELETE_WINDOW", raiz.destroy)

    raiz.mainloop()