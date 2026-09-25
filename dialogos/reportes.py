# -*- coding: utf-8 -*-
"""
dialogos/reportes.py
Diálogo de reportes: árbol años → meses → centros.
Al hacer doble clic en cualquier nodo, cambia los selectores
del formulario principal para reflejar ese reporte.
"""

from collections import defaultdict

import ttkbootstrap as ttk

from tkinter import messagebox

from config.campos import MESES_ES
from core.persistencia import cargar_db
from core.rutas import _CARPETA_DATOS


def abrir_dialogo_reportes(app):
    """
    Abre el diálogo de reportes disponibles.

    Parámetros:
      app: instancia de AppIngresos. Se accede a:
           - app.var_anio, app.var_mes, app.var_centro
           - app.registros, app._anio_cargado
           - app._refrescar_tabla(), app._actualizar_titulo()
           - app._configurar_ventana()
    """
    # ============================================================
    # 1. Recolectar datos
    # ============================================================
    # Estructura: {anio: {mes: {centro: [registros]}}}
    datos = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    archivos = sorted(_CARPETA_DATOS.glob("registros_ingresos_*.json"))
    if not archivos:
        messagebox.showinfo("Reportes", "Todavía no hay registros guardados.")
        return

    for archivo in archivos:
        try:
            anio_str = archivo.stem.replace("registros_ingresos_", "")
            anio = int(anio_str)
        except Exception:
            continue
        regs = cargar_db(anio)
        for r in regs:
            mes = r.get("mes", "sin mes")
            centro = r.get("centro", "sin centro")
            datos[anio][mes][centro].append(r)

    if not datos:
        messagebox.showinfo("Reportes", "Todavía no hay registros guardados.")
        return

    # ============================================================
    # 2. Crear la ventana
    # ============================================================
    ventana = ttk.Toplevel(app)
    ventana.title("📊 Reportes disponibles")
    app._configurar_ventana(ventana, ancho=680, alto=480,
                            min_ancho=560, min_alto=380)

    # Encabezado
    header = ttk.Frame(ventana)
    header.pack(fill="x", padx=10, pady=8)
    ttk.Label(header,
              text="Doble clic (o selecciona + botón) para ir a un reporte:",
              font=("Segoe UI", 12, "bold")).pack(anchor="w")

    # Árbol
    frame_arbol = ttk.Frame(ventana)
    frame_arbol.pack(fill="both", expand=True, padx=10, pady=5)

    columnas = ("registros", "total", "ultimo_folio")
    arbol = ttk.Treeview(frame_arbol, columns=columnas,
                         show="tree headings", height=10)
    arbol.heading("#0", text="Año / Mes / Centro", anchor="w")
    arbol.heading("registros", text="Registros", anchor="center")
    arbol.heading("total", text="Total", anchor="e")
    arbol.heading("ultimo_folio", text="Último folio", anchor="center")

    arbol.column("#0", width=150, minwidth=150, anchor="w")
    arbol.column("registros", width=50, anchor="center")
    arbol.column("total", width=100, anchor="e")
    arbol.column("ultimo_folio", width=50, anchor="center")

    arbol.pack(fill="both", expand=True, side="left")

    sb = ttk.Scrollbar(frame_arbol, orient="vertical", command=arbol.yview)
    sb.pack(side="right", fill="y")
    arbol.configure(yscrollcommand=sb.set)

    # Panel de detalle
    panel = ttk.LabelFrame(ventana, text="Detalle del reporte seleccionado")
    panel.pack(fill="x", padx=10, pady=5)

    lbl_detalle = ttk.Label(panel, text="Selecciona un nodo del árbol",
                            font=("Segoe UI", 10), justify="left")
    lbl_detalle.pack(anchor="w", padx=10, pady=8)

    # Barra de botones
    fr = ttk.Frame(ventana)
    fr.pack(pady=8)

    # Mapa de metadatos: nodo → (anio, mes, centro)
    metadatos = {}

    def _ir_al_nodo(item):
        """Cambia los selectores del formulario al reporte del nodo."""
        md = metadatos.get(item)
        if not md:
            return
        anio, mes, centro = md

        # Cambiar año primero (esto recarga registros del año)
        app.var_anio.set(str(anio))
        if mes:
            app.var_mes.set(mes)
        if centro:
            app.var_centro.set(centro)

        # Recargar y refrescar
        app.registros = cargar_db(anio)
        app._anio_cargado = anio
        app._refrescar_tabla()
        app._actualizar_titulo()
        ventana.destroy()

    def _ir_a_seleccionado():
        sel = arbol.selection()
        if not sel:
            messagebox.showinfo("Reportes", "Selecciona un reporte.")
            return
        _ir_al_nodo(sel[0])

    # ============================================================
    # 3. Poblar árbol
    # ============================================================
    def _orden_mes(m):
        try:
            return MESES_ES.index(m)
        except ValueError:
            return 99

    for anio in sorted(datos.keys(), reverse=True):
        meses_dict = datos[anio]

        # Totales del año
        total_anio = sum(
            len(regs)
            for mes_dict in meses_dict.values()
            for regs in mes_dict.values()
        )
        monto_anio = sum(
            sum(r.get("total", 0) for r in regs)
            for mes_dict in meses_dict.values()
            for regs in mes_dict.values()
        )

        nodo_anio = arbol.insert(
            "", "end",
            text=f"📅 {anio}",
            values=(f"{total_anio} registros", f"${monto_anio:,.2f}", ""),
            open=False,
            tags=("anio",)
        )
        primer_mes = sorted(meses_dict.keys(), key=_orden_mes)[0]
        primer_centro = sorted(meses_dict[primer_mes].keys())[0]
        metadatos[nodo_anio] = (anio, primer_mes, primer_centro)

        # Meses
        for mes in sorted(meses_dict.keys(), key=_orden_mes):
            centros_dict = meses_dict[mes]
            total_mes = sum(len(r) for r in centros_dict.values())
            monto_mes = sum(
                sum(reg.get("total", 0) for reg in regs)
                for regs in centros_dict.values()
            )

            nodo_mes = arbol.insert(
                nodo_anio, "end",
                text=f"📆 {mes.capitalize()}",
                values=(f"{total_mes} registros", f"${monto_mes:,.2f}", ""),
                open=False,
                tags=("mes",)
            )
            primer_centro_mes = sorted(centros_dict.keys())[0]
            metadatos[nodo_mes] = (anio, mes, primer_centro_mes)

            # Centros
            for centro in sorted(centros_dict.keys()):
                regs = centros_dict[centro]
                n = len(regs)
                monto = sum(r.get("total", 0) for r in regs)
                ultimo_folio = ""
                if regs:
                    ultimo = max(regs, key=lambda x: x.get("id", 0))
                    ultimo_folio = str(ultimo.get("no_factura", ""))

                nodo_centro = arbol.insert(
                    nodo_mes, "end",
                    text=f"  🏢 {centro}",
                    values=(f"{n} facturas", f"${monto:,.2f}", ultimo_folio),
                    tags=("centro",)
                )
                metadatos[nodo_centro] = (anio, mes, centro)

    # ============================================================
    # 4. Eventos
    # ============================================================
    def _al_seleccionar(event=None):
        sel = arbol.selection()
        if not sel:
            return
        item = sel[0]
        tags = arbol.item(item, "tags")
        md = metadatos.get(item)
        if not md:
            return
        anio, mes, centro = md

        if "anio" in tags:
            lineas = [f"Año {anio}", ""]
            meses_dict = datos.get(anio, {})
            for m in sorted(meses_dict.keys(), key=_orden_mes):
                centros_dict = meses_dict[m]
                n = sum(len(r) for r in centros_dict.values())
                t = sum(sum(x.get("total", 0) for x in r)
                        for r in centros_dict.values())
                lineas.append(
                    f"  • {m.capitalize():<15} {n:>3} facturas   ${t:>12,.2f}"
                )
            lbl_detalle.configure(text="\n".join(lineas))

        elif "mes" in tags:
            lineas = [f"{mes.capitalize()} {anio}", ""]
            centros_dict = datos.get(anio, {}).get(mes, {})
            for c in sorted(centros_dict.keys()):
                regs = centros_dict[c]
                n = len(regs)
                t = sum(x.get("total", 0) for x in regs)
                lineas.append(
                    f"  • {c:<12} {n:>3} facturas   ${t:>12,.2f}"
                )
            lbl_detalle.configure(text="\n".join(lineas))

        elif "centro" in tags:
            lineas = [f"{centro} — {mes.capitalize()} {anio}", ""]
            regs = datos.get(anio, {}).get(mes, {}).get(centro, [])
            if regs:
                primeras = sorted(regs, key=lambda x: x.get("id", 0))[:5]
                for r in primeras:
                    lineas.append(
                        f"  • Factura {r.get('no_factura', '?'):<8} "
                        f"{r.get('fecha', ''):<12} "
                        f"${r.get('total', 0):>10,.2f}"
                    )
                if len(regs) > 5:
                    lineas.append(f"  ... y {len(regs) - 5} más")
            lbl_detalle.configure(text="\n".join(lineas))

    arbol.bind("<<TreeviewSelect>>", _al_seleccionar)
    arbol.bind("<Double-Button-1>", lambda e: _ir_a_seleccionado())
    arbol.bind("<Return>", lambda e: _ir_a_seleccionado())

    # Expandir el primer año al abrir
    hijos = arbol.get_children()
    if hijos:
        arbol.item(hijos[0], open=True)