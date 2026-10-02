# -*- coding: utf-8 -*-
"""
dialogos/espera_sat.py
Ventana de espera mientras el SAT procesa la solicitud.
Muestra:
  - Mensaje motivador
  - Contador de tiempo transcurrido
  - Estado de la solicitud
  - Número de CFDIs encontrados
"""

import threading
import time
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import messagebox
from datetime import datetime
from pathlib import Path


# ============================================================
# MENSAJES MOTIVADORES
# ============================================================
MENSAJES = [
    "☕ Tómate un café mientras procesamos tu descarga",
    "📚 Aprovecha para revisar tus pendientes",
    "🎵 Pon música mientras esperas",
    "💧 Hidrátate, la descarga sigue en curso",
    "🌿 Respira profundo, ya casi está listo",
    "📱 Revisa tus mensajes mientras esperas",
    "🧘 Relájate, el SAT está trabajando",
    "🍎 Come algo mientras esperamos",
    "☀️ Estira las piernas, ya casi terminamos",
    "📖 Lee algo mientras el SAT procesa",
]


def abrir_ventana_espera_sat(app, verificador, on_completado=None):
    """
    Abre una ventana de espera mientras el SAT procesa la solicitud.
    
    Parámetros:
      - app: instancia de AppEgresos
      - verificador: función que devuelve el estado de la solicitud.
                     Debe devolver un dict con:
                     {
                         "estado": "1"|"2"|"3"|"4"|"5"|"6",
                         "mensaje": "...",
                         "numero_cfdis": "0",
                         "paquetes": [...]
                     }
      - on_completado: función que se llama cuando el estado es 3 (terminada).
    """
    from ui.utils import configurar_ventana

    ventana = ttk.Toplevel(app)
    ventana.title("⏳ Esperando al SAT...")
    configurar_ventana(app, ventana, ancho=550, alto=450,
                       min_ancho=500, min_alto=400)

    # ---- Encabezado ----
    ttk.Label(
        ventana,
        text="⏳ Esperando respuesta del SAT...",
        font=("Segoe UI", 16, "bold"),
        bootstyle="info"
    ).pack(pady=(20, 10))

    # ---- Mensaje motivador ----
    import random
    mensaje_inicial = random.choice(MENSAJES)

    lbl_mensaje = ttk.Label(
        ventana,
        text=mensaje_inicial,
        font=("Segoe UI", 12),
        foreground="#2c3e50"
    )
    lbl_mensaje.pack(pady=(0, 20))

    # ---- Contador de tiempo ----
    frame_contador = ttk.LabelFrame(ventana, text="Tiempo transcurrido", padding=15)
    frame_contador.pack(fill="x", padx=20, pady=5)

    lbl_tiempo = ttk.Label(
        frame_contador,
        text="00:00:00",
        font=("Consolas", 28, "bold"),
        bootstyle="info"
    )
    lbl_tiempo.pack()

    # ---- Estado de la solicitud ----
    frame_estado = ttk.LabelFrame(ventana, text="Estado de la solicitud", padding=15)
    frame_estado.pack(fill="x", padx=20, pady=10)

    # Verificación #
    lbl_verificacion = ttk.Label(
        frame_estado,
        text="Verificación #0",
        font=("Segoe UI", 10)
    )
    lbl_verificacion.pack(anchor="w")

    # Estado
    lbl_estado = ttk.Label(
        frame_estado,
        text="Estado: Esperando...",
        font=("Segoe UI", 10)
    )
    lbl_estado.pack(anchor="w")

    # CFDIs
    lbl_cfdis = ttk.Label(
        frame_estado,
        text="CFDIs encontrados: 0",
        font=("Segoe UI", 10)
    )
    lbl_cfdis.pack(anchor="w")

    # Última verificación
    lbl_ultima = ttk.Label(
        frame_estado,
        text="Última verificación: —",
        font=("Segoe UI", 9),
        foreground="gray"
    )
    lbl_ultima.pack(anchor="w")

    # ---- Barra de progreso (animada) ----
    barra = ttk.Progressbar(
        ventana,
        mode="indeterminate",
        bootstyle="info-striped",
        length=500
    )
    barra.pack(pady=15, padx=20, fill="x")
    barra.start(15)

    # ---- Estado del proceso ----
    estado = {
        "cancelar": False,
        "inicio": time.time(),
        "verificaciones": 0,
        "completado": False,
    }

    # ---- Función para actualizar el contador ----
    def actualizar_contador():
        if estado["cancelar"] or estado["completado"]:
            return

        transcurrido = int(time.time() - estado["inicio"])
        horas = transcurrido // 3600
        minutos = (transcurrido % 3600) // 60
        segundos = transcurrido % 60

        try:
            lbl_tiempo.configure(text=f"{horas:02d}:{minutos:02d}:{segundos:02d}")
        except Exception:
            return

        # Programar la siguiente actualización
        ventana.after(1000, actualizar_contador)

    # ---- Función para cambiar el mensaje motivador ----
    def cambiar_mensaje():
        if estado["cancelar"] or estado["completado"]:
            return

        try:
            lbl_mensaje.configure(text=random.choice(MENSAJES))
        except Exception:
            return

        # Cambiar cada 30 segundos
        ventana.after(30000, cambiar_mensaje)

    # ---- Función de verificación en hilo separado ----
    def verificar_en_hilo():
        while not estado["cancelar"] and not estado["completado"]:
            estado["verificaciones"] += 1
            num = estado["verificaciones"]

            try:
                # Verificar el estado
                resultado = verificador()

                estado_solicitud = str(resultado.get("estado", "?"))
                mensaje = resultado.get("mensaje", "")
                num_cfdis = resultado.get("numero_cfdis", "0")
                paquetes = resultado.get("paquetes", [])

                # Actualizar la UI desde el hilo principal
                def actualizar_ui():
                    try:
                        lbl_verificacion.configure(
                            text=f"Verificación #{num}"
                        )
                        lbl_estado.configure(
                            text=f"Estado: {estado_solicitud} — {mensaje}"
                        )
                        lbl_cfdis.configure(
                            text=f"CFDIs encontrados: {num_cfdis}"
                        )
                        lbl_ultima.configure(
                            text=f"Última verificación: {datetime.now().strftime('%H:%M:%S')}"
                        )
                    except Exception:
                        pass

                ventana.after(0, actualizar_ui)

                # Interpretar el estado
                estados = {
                    "1": "Aceptada (en cola)",
                    "2": "En proceso",
                    "3": "Terminada",
                    "4": "Error",
                    "5": "Rechazada",
                    "6": "Vencida",
                }

                if estado_solicitud == "3":
                    # ¡Terminada!
                    estado["completado"] = True

                    def finalizar():
                        try:
                            barra.stop()
                            barra.configure(mode="determinate", value=100)
                            lbl_mensaje.configure(
                                text="✅ ¡Descarga lista!",
                                foreground="#27ae60"
                            )
                        except Exception:
                            pass

                        # Notificar
                        if on_completado:
                            try:
                                on_completado(resultado)
                            except Exception as e:
                                print(f"Error en callback: {e}")

                        # Cerrar después de 2 segundos
                        ventana.after(2000, ventana.destroy)

                    ventana.after(0, finalizar)
                    return

                elif estado_solicitud in ("4", "5", "6"):
                    # Error
                    estado["completado"] = True

                    def mostrar_error():
                        try:
                            barra.stop()
                            lbl_mensaje.configure(
                                text=f"❌ {estados.get(estado_solicitud, 'Error')}",
                                foreground="#e74c3c"
                            )
                        except Exception:
                            pass

                        messagebox.showerror(
                            "Error del SAT",
                            f"La solicitud terminó con error:\n\n"
                            f"Estado: {estado_solicitud}\n"
                            f"Mensaje: {mensaje}",
                            parent=ventana
                        )
                        ventana.destroy()

                    ventana.after(0, mostrar_error)
                    return

                # Esperar 2 minutos antes de la siguiente verificación
                for _ in range(120):
                    if estado["cancelar"] or estado["completado"]:
                        return
                    time.sleep(1)

            except Exception as e:
                print(f"Error al verificar: {e}")
                time.sleep(30)

    # ---- Cancelar ----
    def cancelar():
        if messagebox.askyesno(
            "Cancelar espera",
            "¿Quieres cancelar la espera?\n\n"
            "La solicitud sigue en el SAT. Puedes verificarla después.",
            parent=ventana
        ):
            estado["cancelar"] = True
            try:
                barra.stop()
            except Exception:
                pass
            ventana.destroy()

    # ---- Botón cancelar ----
    fr_btn = ttk.Frame(ventana)
    fr_btn.pack(pady=15)

    ttk.Button(
        fr_btn,
        text="❌ Cancelar espera",
        command=cancelar,
        bootstyle="danger-outline"
    ).pack()

    ventana.protocol("WM_DELETE_WINDOW", cancelar)

    # ---- Iniciar hilos ----
    ventana.after(100, actualizar_contador)
    ventana.after(100, cambiar_mensaje)

    hilo = threading.Thread(target=verificar_en_hilo, daemon=True)
    hilo.start()