# -*- coding: utf-8 -*-
"""
dialogos/descargar_sat.py
Dialogo para elegir el periodo de descarga del SAT y ejecutar
el flujo completo (solicitar -> esperar -> descargar -> procesar).

Flujo:
  1. Pedir mes/año al usuario
  2. Solicitar descarga al SAT -> obtiene id_solicitud
  3. Abrir dialogos/espera_sat.py con el verificador correcto
  4. Cuando el SAT termina (estado=3), descargar paquetes y procesar
"""

import threading
from datetime import datetime
from pathlib import Path

import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox

from config.campos import MESES_ES


def abrir_dialogo_descargar_sat(app):
    """
    Abre el dialogo de descarga del SAT.

    Parametros:
      - app: instancia de AppEgresos.

    Devuelve True si se lanzo una descarga, False si se cancelo.
    """
    from ui.utils import configurar_ventana

    # Valores por defecto: mes y año actuales
    hoy = datetime.now()
    mes_default = MESES_ES[hoy.month - 1]
    anio_default = str(hoy.year)

    ventana = ttk.Toplevel(app)
    ventana.title("📥 Descargar del SAT")
    configurar_ventana(app, ventana, ancho=450, alto=350,
                       min_ancho=400, min_alto=300)

    # Encabezado
    ttk.Label(
        ventana,
        text="📥 Descargar facturas del SAT",
        font=("Segoe UI", 15, "bold"),
    ).pack(pady=(20, 5))

    ttk.Label(
        ventana,
        text="Descarga los CFDI recibidos (facturas de compra)\n"
             "del periodo seleccionado.",
        font=("Segoe UI", 9),
        foreground="gray",
        justify="center",
    ).pack(pady=(0, 20))

    # Formulario
    form = ttk.Frame(ventana)
    form.pack(fill="x", padx=30, pady=10)

    ttk.Label(form, text="Año:").grid(
        row=0, column=0, sticky="e", padx=(0, 10), pady=8)
    var_anio = tk.StringVar(value=anio_default)
    ttk.Entry(form, textvariable=var_anio, width=8).grid(
        row=0, column=1, sticky="w", pady=8)

    ttk.Label(form, text="Mes:").grid(
        row=1, column=0, sticky="e", padx=(0, 10), pady=8)
    var_mes = tk.StringVar(value=mes_default)
    ttk.Combobox(
        form,
        textvariable=var_mes,
        values=MESES_ES,
        width=15,
        state="readonly",
    ).grid(row=1, column=1, sticky="w", pady=8)

    # Nota
    ttk.Label(
        ventana,
        text="⚠️ La descarga puede tardar varios minutos.\n"
             "El SAT procesa la solicitud en segundo plano.",
        font=("Segoe UI", 8),
        foreground="gray",
        justify="center",
    ).pack(pady=(15, 10))

    # Botón para configurar e.firma
    def _abrir_config():
        from dialogos.egresos_config import abrir_dialogo_config_egresos
        abrir_dialogo_config_egresos(app)

    resultado = {"ok": False}

    def _descargar():
        anio_txt = var_anio.get().strip()
        mes_nombre = var_mes.get()

        # Validaciones
        try:
            anio = int(anio_txt)
            if anio < 2020 or anio > 2100:
                raise ValueError()
        except ValueError:
            messagebox.showwarning(
                "Año inválido",
                "Ingresa un año válido (ej. 2026).",
                parent=ventana)
            return

        if mes_nombre not in MESES_ES:
            messagebox.showwarning(
                "Mes inválido",
                "Selecciona un mes válido.",
                parent=ventana)
            return

        mes_idx = MESES_ES.index(mes_nombre) + 1

        # ⚠️ VALIDAR CONFIG ANTES de cerrar la ventana
        from config.config_egresos import cargar_config_egresos
        cfg = cargar_config_egresos()
        rfc = cfg.get("rfc_receptor", "")
        cer = cfg.get("certificado_cer", "")
        key = cfg.get("certificado_key", "")
        pwd = cfg.get("password_fiel", "")

        if not all([rfc, cer, key, pwd]):
            messagebox.showwarning(
                "Configuración incompleta",
                "Falta configurar la e.firma.\n\n"
                "Ve a ⚙️ Configurar e.firma (SAT) primero.",
                parent=ventana)
            return

        # Ahora sí, cerrar y lanzar
        resultado["ok"] = True
        ventana.destroy()

        _lanzar_descarga(app, anio, mes_idx, mes_nombre)

    def _cancelar():
        ventana.destroy()

    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(fill="x", padx=30, pady=(10, 20))

    ttk.Button(
        fr_btn,
        text="⚙️ Configurar e.firma (SAT)",
        command=_abrir_config,
        bootstyle="secondary-outline",
    ).pack(side="left", padx=5)

    ttk.Button(
        fr_btn,
        text="📥 Descargar",
        command=_descargar,
        bootstyle="info-outline",
    ).pack(side="right", padx=5)

    ventana.protocol("WM_DELETE_WINDOW", _cancelar)
    ventana.bind("<Escape>", lambda e: _cancelar())

    ventana.wait_window()
    return resultado["ok"]


# ============================================================
# LANZAR DESCARGA (solicitar -> esperar -> descargar -> procesar)
# ============================================================
def _lanzar_descarga(app, anio, mes_idx, mes_nombre):
    """Ejecuta el flujo de descarga en un hilo separado."""
    from config.config_egresos import cargar_config_egresos

    cfg = cargar_config_egresos()
    rfc = cfg.get("rfc_receptor", "")
    cer = cfg.get("certificado_cer", "")
    key = cfg.get("certificado_key", "")
    pwd = cfg.get("password_fiel", "")

    # (La config ya fue validada en _descargar antes de cerrar la ventana)

    # Rango de fechas: del primer dia del mes al ultimo dia (23:59:59)
    # IMPORTANTE: el SAT NO acepta fechas futuras.
    from calendar import monthrange

    fecha_inicio = datetime(anio, mes_idx, 1, 0, 0, 0)

    ultimo_dia = monthrange(anio, mes_idx)[1]
    fecha_fin = datetime(anio, mes_idx, ultimo_dia, 23, 59, 59)

    # Si el mes es el actual, recortar a HOY (23:59:59)
    hoy = datetime.now()
    if anio == hoy.year and mes_idx == hoy.month:
        fecha_fin = hoy.replace(hour=23, minute=59, second=59)

    # Si el rango queda en el futuro, avisar
    if fecha_inicio > hoy:
        messagebox.showwarning(
            "Fechas invalidas",
            f"No se puede descargar {mes_nombre} {anio} porque aun no ha pasado.",
            parent=app)
        return

    from sat.descarga import solicitar_descarga

    # 1) Solicitar
    try:
        resultado = solicitar_descarga(
            cer, key, pwd, rfc,
            fecha_inicio, fecha_fin,
        )
    except Exception as e:
        messagebox.showerror(
            "Error al solicitar descarga",
            f"No se pudo solicitar la descarga:\n\n{e}",
            parent=app)
        return

    id_solicitud = resultado.get("id_solicitud")
    if not id_solicitud:
        # El SAT rechazó la solicitud. Mostrar motivo real.
        cod = resultado.get("cod_estatus", "?")
        msg = resultado.get("mensaje", "Sin mensaje")

        # Traducir los códigos más comunes
        traduccion = {
            "301": "XML mal formado (revisa fechas o RFC)",
            "302": "RFC no válido o sin permisos",
            "303": "Certificado no válido",
            "304": "Ya existe una solicitud en proceso para este periodo",
            "305": "Rango de fechas inválido",
            "306": "Sin información para ese periodo",
            "404": "No se encontró la solicitud",
            "5000": "OK",
        }
        explicacion = traduccion.get(str(cod), "Error desconocido")

        messagebox.showerror(
            "Solicitud rechazada por el SAT",
            f"El SAT rechazó la solicitud.\n\n"
            f"Código: {cod}\n"
            f"Motivo: {explicacion}\n\n"
            f"Mensaje del SAT:\n{msg}",
            parent=app)
        return

    # Guardar la solicitud activa para poder retomarla
    from config.config_egresos import guardar_solicitud_activa
    from datetime import datetime as _dt
    guardar_solicitud_activa({
        "id_solicitud": id_solicitud,
        "rfc": rfc,
        "anio": anio,
        "mes_idx": mes_idx,
        "mes_nombre": mes_nombre,
        "fecha_solicitud": _dt.now().isoformat(timespec="seconds"),
    })

    # 2) Abrir ventana de espera con el verificador
    from dialogos.espera_sat import abrir_ventana_espera_sat
    from sat.descarga import verificar_solicitud

    def _verificador():
        return verificar_solicitud(cer, key, pwd, rfc, id_solicitud)

    def _on_completado(resultado_verif):
        # Cuando el SAT termina, descargar paquetes y procesar
        paquetes = resultado_verif.get("paquetes", [])
        _descargar_y_procesar(app, cer, key, pwd, rfc, paquetes, anio, mes_idx)

    abrir_ventana_espera_sat(app, _verificador, on_completado=_on_completado)


def _descargar_y_procesar(app, cer, key, pwd, rfc, paquetes, anio, mes_idx):
    """Descarga paquetes y procesa todo. Se ejecuta en hilo."""
    def _worker():
        try:
            from sat.descarga import descargar_paquetes

            # Descargar
            carpeta_destino = "/tmp/sat_descargas"
            descargar_paquetes(
                cer, key, pwd, rfc, paquetes,
                carpeta_destino=carpeta_destino,
            )

            # Procesar todo
            from sat.procesar_completo import procesar_todo
            resumen = procesar_todo(anio, mes_idx, carpeta_xml=carpeta_destino)

            # Limpiar la solicitud activa (ya terminó todo)
            from config.config_egresos import limpiar_solicitud_activa
            limpiar_solicitud_activa()

            # Mostrar resumen
            def _mostrar():
                messagebox.showinfo(
                    "Descarga completa",
                    f"✅ Descarga y procesamiento exitosos\n\n"
                    f"Facturas nuevas: {resumen['nuevas']}\n"
                    f"Duplicadas: {resumen['duplicadas']}\n"
                    f"XMLs movidos: {resumen['movidos']}\n"
                    f"Excel PUE: {resumen['excel'].get('total_pue', 0)} facturas\n"
                    f"Excel PPD: {resumen['excel'].get('total_ppd', 0)} facturas\n\n"
                    f"Carpeta: {resumen['excel'].get('carpeta')}",
                    parent=app)
            app.after(0, _mostrar)

        except Exception as e:
            err = str(e)
            def _mostrar_error():
                messagebox.showerror(
                    "Error en descarga/procesamiento",
                    f"{err}",
                    parent=app)
            app.after(0, _mostrar_error)

    threading.Thread(target=_worker, daemon=True).start()


# ============================================================
# VERIFICAR SOLICITUD PENDIENTE (retomar)
# ============================================================
def verificar_solicitud_pendiente(app):
    """
    Retoma una solicitud que quedó en curso.
    - Lee el id_solicitud guardado
    - Abre la ventana de espera
    - Cuando termina, descarga y procesa, y limpia la solicitud
    """
    from config.config_egresos import (
        cargar_solicitud_activa,
        cargar_config_egresos,
    )

    datos = cargar_solicitud_activa()
    if not datos:
        messagebox.showinfo(
            "Sin solicitudes",
            "No hay ninguna solicitud pendiente.",
            parent=app)
        return

    cfg = cargar_config_egresos()
    rfc = cfg.get("rfc_receptor", "")
    cer = cfg.get("certificado_cer", "")
    key = cfg.get("certificado_key", "")
    pwd = cfg.get("password_fiel", "")

    if not all([rfc, cer, key, pwd]):
        messagebox.showwarning(
            "Configuración incompleta",
            "Falta configurar la e.firma.\n\n"
            "Ve a ⚙️ Configuración SAT primero.",
            parent=app)
        return

    id_solicitud = datos.get("id_solicitud", "")
    anio = datos.get("anio", 0)
    mes_idx = datos.get("mes_idx", 1)

    if not id_solicitud:
        messagebox.showerror(
            "Solicitud inválida",
            "El archivo de solicitud no tiene id_solicitud.",
            parent=app)
        return

    # Abrir ventana de espera
    from dialogos.espera_sat import abrir_ventana_espera_sat
    from sat.descarga import verificar_solicitud

    def _verificador():
        return verificar_solicitud(cer, key, pwd, rfc, id_solicitud)

    def _on_completado(resultado_verif):
        paquetes = resultado_verif.get("paquetes", [])
        _descargar_y_procesar(
            app, cer, key, pwd, rfc, paquetes, anio, mes_idx,
        )
        # Limpiar la solicitud activa
        from config.config_egresos import limpiar_solicitud_activa
        limpiar_solicitud_activa()

    abrir_ventana_espera_sat(app, _verificador, on_completado=_on_completado)