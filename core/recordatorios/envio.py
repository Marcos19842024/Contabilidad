# core/recordatorios/envio.py
"""
Envío de mensajes por WhatsApp usando el protocolo wa.me.
En macOS abre WhatsApp Desktop si está configurado, sino WhatsApp Web.
"""

import subprocess
import sys
import urllib.parse

def abrir_whatsapp_solo_chat(telefono: str):
    """
    Abre WhatsApp en el chat del número, SIN texto pre-llenado.
    El mensaje se pega después con Cmd+V (ya está en el portapapeles).
    """
    if not telefono:
        return False
    url = f"https://wa.me/{telefono}"
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", url])
        elif sys.platform.startswith("win"):
            import os
            os.startfile(url)
        else:
            subprocess.Popen(["xdg-open", url])
        return True
    except Exception as e:
        print(f"[abrir_whatsapp_solo_chat] Error: {e}")
        return False


def abrir_whatsapp(telefono: str, mensaje: str):
    """
    Abre WhatsApp con el mensaje pre-llenado.
    telefono debe venir normalizado (52XXXXXXXXXX).
    Devuelve True si se pudo abrir, False si falló.
    """
    if not telefono or not mensaje:
        return False

    mensaje_codificado = urllib.parse.quote(mensaje, safe="")
    url = f"https://wa.me/{telefono}?text={mensaje_codificado}"

    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", url])
        elif sys.platform.startswith("win"):
            import os
            os.startfile(url)
        else:
            subprocess.Popen(["xdg-open", url])
        return True
    except Exception as e:
        print(f"[abrir_whatsapp] Error: {e}")
        return False


def copiar_al_portapapeles(texto: str) -> bool:
    """
    Copia texto al portapapeles respetando UTF-8 (emojis).
    """
    if not texto:
        return False
    try:
        if sys.platform == "darwin":
            # macOS: pbcopy lee bytes, hay que pasar UTF-8
            proceso = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
            )
            proceso.communicate(input=texto.encode("utf-8"))
            return True
        elif sys.platform.startswith("win"):
            proceso = subprocess.Popen(
                ["clip"], stdin=subprocess.PIPE, shell=True,
            )
            proceso.communicate(input=texto.encode("utf-16le"))
            return True
        else:
            proceso = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE,
            )
            proceso.communicate(input=texto.encode("utf-8"))
            return True
    except Exception as e:
        print(f"[copiar_al_portapapeles] Error: {e}")
        return False