# -*- coding: utf-8 -*-
"""
core/adjuntos.py
Gestión de archivos adjuntos por registro (copiar, mover, eliminar).
"""

import shutil
from datetime import datetime
from pathlib import Path

from config.campos import MESES_ES
from core.rutas import ruta_ingreso
from core.utilidades import parse_fecha


def carpeta_de_registro(reg):
    """Devuelve la carpeta donde viven los adjuntos de un registro."""
    try:
        centro = reg.get("centro", "Central")
        anio = int(reg.get("anio", datetime.now().year))
        mes_nombre = reg.get("mes", MESES_ES[datetime.now().month - 1])
        mes_idx = MESES_ES.index(mes_nombre) + 1
        fecha_carpeta = parse_fecha(reg.get("fecha", ""))
        return ruta_ingreso(centro, anio, mes_idx) / fecha_carpeta
    except Exception:
        return None


def archivos_del_registro(reg):
    """
    Devuelve la lista de adjuntos que pertenecen a un registro,
    comparando por prefijo del No. de factura.
    """
    carpeta = carpeta_de_registro(reg)
    if not carpeta or not carpeta.exists():
        return []
    no_factura = str(reg.get("no_factura", "")).strip()
    if not no_factura:
        return []
    prefijo = no_factura.lower()
    encontrados = []
    for archivo in carpeta.iterdir():
        if not archivo.is_file():
            continue
        nombre = archivo.name.lower()
        if not nombre.startswith(prefijo):
            continue
        resto = nombre[len(prefijo):]
        if resto == "" or resto[0] in (".", "-", "_", " "):
            encontrados.append(archivo)
    return encontrados


def eliminar_archivos_de_registro(reg):
    """Elimina los adjuntos de un registro. Devuelve (eliminados, errores)."""
    eliminados, errores = [], []
    for archivo in archivos_del_registro(reg):
        try:
            archivo.unlink()
            eliminados.append(archivo)
        except Exception as e:
            errores.append((archivo, str(e)))
    return eliminados, errores


def eliminar_carpeta_si_vacia(reg):
    """Elimina la carpeta del registro si está vacía. Devuelve (ok, msg)."""
    carpeta = carpeta_de_registro(reg)
    if not carpeta:
        return False, "No se pudo determinar la carpeta."
    if not carpeta.exists():
        return False, "La carpeta ya no existe."
    try:
        contenido = list(carpeta.iterdir())
    except Exception as e:
        return False, f"No se pudo leer la carpeta: {e}"
    if contenido:
        return False, f"La carpeta aún contiene {len(contenido)} archivo(s)/carpeta(s)."
    try:
        carpeta.rmdir()
        return True, str(carpeta)
    except Exception as e:
        return False, f"No se pudo eliminar la carpeta: {e}"


def carpeta_destino_factura(reg):
    """Devuelve (y crea) la carpeta destino para los adjuntos del registro."""
    carpeta = carpeta_de_registro(reg)
    if carpeta:
        carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def nombre_destino(no_factura, ruta_origen):
    """Devuelve el nombre destino para un adjunto (No. factura + extensión)."""
    ext = Path(ruta_origen).suffix
    return f"{no_factura}{ext}"


def adjuntar_archivos(reg, rutas_origen):
    """
    Copia los archivos origen a la carpeta del registro.
    Devuelve (copiados, errores).
    """
    carpeta = carpeta_destino_factura(reg)
    if not carpeta:
        return [], [(None, "No se pudo determinar la carpeta destino.")]
    no_factura = str(reg.get("no_factura", "")).strip()
    copiados, errores = [], []
    for origen in rutas_origen:
        try:
            origen = Path(origen)
            if not origen.is_file():
                errores.append((origen, "No es un archivo válido."))
                continue
            destino = carpeta / nombre_destino(no_factura, origen)
            shutil.copy2(origen, destino)
            copiados.append((origen, destino))
        except Exception as e:
            errores.append((origen, str(e)))
    return copiados, errores