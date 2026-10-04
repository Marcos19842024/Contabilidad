# -*- coding: utf-8 -*-
"""
dialogos/reportes_egresos.py
Dialogo de reportes de Egresos: arbol anios -> meses -> sucursales.
Al hacer doble clic en cualquier nodo, cambia los selectores
del modulo de Egresos para reflejar ese reporte.
"""

from collections import defaultdict

import ttkbootstrap as ttk

from tkinter import messagebox

from config.campos import MESES_ES


def abrir_dialogo_reportes_egresos(app):
    """
    Abre el dialogo de reportes disponibles de Egresos.

    Parametros:
      - app: instancia de AppEgresos. Se accede a:
           - app.var_anio, app.var_mes, app.var_sucursal
           - app.registros, app._anio_cargado
           - app._refrescar_tabla()
    """
    from config.config_egresos import _CARPETA_DATOS
    from sat.guardar_egresos import cargar_db_egresos

    # ============================================================
    # 1. Recolectar datos
    # ============================================================
    # Estructura: {anio: {mes: {sucursal: [registros]}}}
    datos = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    archivos = sorted(_CARPETA_DATOS.glob("registros_egresos_*.json"))
    if not archivos:
        messagebox.showinfo("Reportes", "Todavia no hay registros de Egresos.")
        return

    for archivo in archivos:
        try:
            anio_str = archivo.stem.replace("registros_egresos_", "")
            anio = int(anio_str)
        except Exception:
            continue

        regs = cargar_db_egresos(anio)
        for r in regs:
            mes = r.get("mes", "sin mes")
            sucursal = r.get("sucursal", "Baalak")
            datos[anio][mes][sucursal].append(r)

    if not datos:
        messagebox.showinfo("Reportes", "Todavia no hay registros de Egresos.")
        return

    # ============================================================
    # 2. Crear la ventana
    # ============================================================
    from ui.utils import configurar_ventana

    ventana = ttk.Toplevel(app)
    ventana.title("Reportes de Egresos")
    configurar_ventana(app, ventana, ancho=720, alto=520,
                       min_ancho=600, min_alto=420)

    # Encabezado
    header = ttk.Frame(ventana)
    header.pack(fill="x", padx=10, pady=8)

    ttk.Label(
        header,
        text="Doble clic (o selecciona + boton) para ir a un reporte:",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w")

    # Arbol
    frame_arbol = ttk.Frame(ventana)
    frame_arbol.pack(fill="both", expand=True, padx=10, pady=5)

    columnas = ("registros", "total")
    arbol = ttk.Treeview(
        frame_arbol, columns=columnas,
        show="tree headings", height=12,
    )
    arbol.heading("#0", text="Anio / Mes / Sucursal", anchor="w")
    arbol.heading("registros", text="Registros", anchor="center")
    arbol.heading("total", text="Total", anchor="e")

    arbol.column("#0", width=200, minwidth=180, anchor="w")
    arbol.column("registros", width=90, anchor="center")
    arbol.column("total", width=120, anchor="e")

    arbol.pack(fill="both", expand=True, side="left")

    sb = ttk.Scrollbar(frame_arbol, orient="vertical", command=arbol.yview)
    sb.pack(side="right", fill="y")
    arbol.configure(yscrollcommand=sb.set)

    # Panel de detalle
    panel = ttk.LabelFrame(ventana, text="Detalle del reporte seleccionado")
    panel.pack(fill="x", padx=10, pady=5)

    lbl_detalle = ttk.Label(
        panel,
        text="Selecciona un nodo del arbol",
        font=("Segoe UI", 10),
        justify="left",
    )
    lbl_detalle.pack(anchor="w", padx=10, pady=8)

    # Barra de botones
    fr = ttk.Frame(ventana)
    fr.pack(pady=8)

    # Mapa de metadatos: nodo -> (anio, mes, sucursal)
    metadatos = {}

    def _ir_al_nodo(item):
        """Cambia los selectores del modulo al reporte del nodo."""
        md = metadatos.get(item)
        if not md:
            return
        anio, mes, sucursal = md

        app.var_anio.set(str(anio))
        if mes:
            app.var_mes.set(mes)
        if sucursal:
            app.var_sucursal.set(sucursal)

        app.registros = cargar_db_egresos(anio)
        app._anio_cargado = anio
        app._refrescar_tabla()
        ventana.destroy()

    def _ir_a_seleccionado():
        sel = arbol.selection()
        if not sel:
            messagebox.showinfo("Reportes", "Selecciona un reporte.")
            return
        _ir_al_nodo(sel[0])

    # ============================================================
    # 3. Poblar arbol
    # ============================================================
    def _orden_mes(m):
        try:
            return MESES_ES.index(m)
        except ValueError:
            return 99

    for anio in sorted(datos.keys(), reverse=True):
        meses_dict = datos[anio]

        # Totales del anio
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
            text=f"{anio}",
            values=(f"{total_anio} regs", f"${monto_anio:,.2f}"),
            open=False,
            tags=("anio",),
        )

        # Meses
        meses_ordenados = sorted(meses_dict.keys(), key=_orden_mes)
        primer_mes = meses_ordenados[0] if meses_ordenados else ""
        primer_sucursal = "Baalak"
        if primer_mes:
            sucs = sorted(meses_dict[primer_mes].keys())
            if sucs:
                primer_sucursal = sucs[0]
        metadatos[nodo_anio] = (anio, primer_mes, primer_sucursal)

        for mes in meses_ordenados:
            sucursales_dict = meses_dict[mes]
            total_mes = sum(len(r) for r in sucursales_dict.values())
            monto_mes = sum(
                sum(reg.get("total", 0) for reg in regs)
                for regs in sucursales_dict.values()
            )

            nodo_mes = arbol.insert(
                nodo_anio, "end",
                text=f"{mes.capitalize()}",
                values=(f"{total_mes} regs", f"${monto_mes:,.2f}"),
                open=False,
                tags=("mes",),
            )

            sucs_ordenadas = sorted(sucursales_dict.keys())
            primer_suc = sucs_ordenadas[0] if sucs_ordenadas else "Baalak"
            metadatos[nodo_mes] = (anio, mes, primer_suc)

            # Sucursales
            for sucursal in sucs_ordenadas:
                regs = sucursales_dict[sucursal]
                n = len(regs)
                monto = sum(r.get("total", 0) for r in regs)

                nodo_suc = arbol.insert(
                    nodo_mes, "end",
                    text=f"{sucursal}",
                    values=(f"{n} facturas", f"${monto:,.2f}"),
                    tags=("sucursal",),
                )
                metadatos[nodo_suc] = (anio, mes, sucursal)

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
        anio, mes, sucursal = md

        if "anio" in tags:
            lineas = [f"Anio {anio}", ""]
            meses_dict = datos.get(anio, {})
            for m in sorted(meses_dict.keys(), key=_orden_mes):
                sucursales_dict = meses_dict[m]
                n = sum(len(r) for r in sucursales_dict.values())
                t = sum(
                    sum(x.get("total", 0) for x in r)
                    for r in sucursales_dict.values()
                )
                lineas.append(
                    f"  - {m.capitalize():<15} {n:>3} facturas   ${t:>12,.2f}"
                )
            lbl_detalle.configure(text="\n".join(lineas))

        elif "mes" in tags:
            lineas = [f"{mes.capitalize()} {anio}", ""]
            sucursales_dict = datos.get(anio, {}).get(mes, {})
            for s in sorted(sucursales_dict.keys()):
                regs = sucursales_dict[s]
                n = len(regs)
                t = sum(x.get("total", 0) for x in regs)
                lineas.append(
                    f"  - {s:<12} {n:>3} facturas   ${t:>12,.2f}"
                )
            lbl_detalle.configure(text="\n".join(lineas))

        elif "sucursal" in tags:
            lineas = [f"{sucursal} - {mes.capitalize()} {anio}", ""]
            regs = datos.get(anio, {}).get(mes, {}).get(sucursal, [])
            if regs:
                # Separar PUE y PPD
                pue = [r for r in regs if r.get("metodo_pago") != "PPD"]
                ppd = [r for r in regs if r.get("metodo_pago") == "PPD"]
                lineas.append(f"  PUE: {len(pue)} facturas")
                lineas.append(f"  PPD: {len(ppd)} facturas")
                lineas.append("")

                primeras = sorted(regs, key=lambda x: x.get("id", 0))[:5]
                for r in primeras:
                    lineas.append(
                        f"  - Factura {r.get('folio', '?'):<10} "
                        f"{r.get('fecha', ''):<12} "
                        f"${r.get('total', 0):>10,.2f}"
                    )
                if len(regs) > 5:
                    lineas.append(f"  ... y {len(regs) - 5} mas")
            lbl_detalle.configure(text="\n".join(lineas))

    arbol.bind("<<TreeviewSelect>>", _al_seleccionar)
    arbol.bind("<Double-Button-1>", lambda e: _ir_a_seleccionado())
    arbol.bind("<Return>", lambda e: _ir_a_seleccionado())

    # Expandir el primer anio
    hijos = arbol.get_children()
    if hijos:
        arbol.item(hijos[0], open=True)