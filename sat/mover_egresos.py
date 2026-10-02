# -*- coding: utf-8 -*-
"""
sat/mover_egresos.py
Renombra y mueve los XML de Egresos a sus carpetas correspondientes.
"""
import shutil
from datetime import datetime
from pathlib import Path

from config.campos import MESES_ES
from core.rutas import BASE_DIR


def ruta_egreso(anio, mes_idx):
    """Carpeta base de Egresos."""
    return (
        BASE_DIR / f"Contabilidad {anio}"
        / f"Contabilidad {MESES_ES[mes_idx - 1]}"
        / "Egreso"
    )


def mover_y_renombrar_egresos(registros, anio, mes_idx, carpeta_origen):
    """
    Renombra y mueve los XML de Egresos a sus carpetas.
    
    Parámetros:
      - registros: lista de facturas (con 'id', 'folio', 'metodo_pago',
                   'sucursal', 'ruta_xml').
      - anio: año de las facturas.
      - mes_idx: índice del mes (1-12).
      - carpeta_origen: carpeta donde están los XML originales.
    
    Devuelve:
      - (movidos, errores)
    """
    carpeta_origen = Path(carpeta_origen)
    base = ruta_egreso(anio, mes_idx)

    # Crear carpetas
    carpeta_pue = base / "PUE"
    carpeta_ppd = base / "PPD"
    carpeta_animalia = base / "Animalia"
    carpeta_deposito = base / "Deposito_Egreso"
    carpeta_pdfs = base / "PDFs"

    for c in [carpeta_pue, carpeta_ppd, carpeta_animalia,
              carpeta_deposito, carpeta_pdfs]:
        c.mkdir(parents=True, exist_ok=True)

    movidos = []
    errores = []

    # Separar por PUE y PPD, ordenar por fecha
    pue_facturas = []
    ppd_facturas = []
    animalia_facturas = []

    for reg in registros:
        sucursal = reg.get("sucursal", "Baalak")
        metodo = reg.get("metodo_pago", "PUE")

        if sucursal == "Animalia":
            animalia_facturas.append(reg)
        elif metodo == "PPD":
            ppd_facturas.append(reg)
        else:
            pue_facturas.append(reg)

    # Ordenar por fecha
    def _orden(r):
        try:
            partes = r.get("fecha", "").split("/")
            if len(partes) == 3:
                return (int(partes[2]), int(partes[1]), int(partes[0]))
        except Exception:
            pass
        return (0, 0, 0)

    pue_facturas.sort(key=_orden)
    ppd_facturas.sort(key=_orden)
    animalia_facturas.sort(key=_orden)

    # Mover PUE
    for i, reg in enumerate(pue_facturas, 1):
        _mover_archivo(reg, carpeta_pue, i, movidos, errores)

    # Mover PPD
    for i, reg in enumerate(ppd_facturas, 1):
        _mover_archivo(reg, carpeta_ppd, i, movidos, errores)

    # Mover Animalia
    for i, reg in enumerate(animalia_facturas, 1):
        _mover_archivo(reg, carpeta_animalia, i, movidos, errores)

    # Guardar el JSON con los números de línea
    from sat.guardar_egresos import guardar_db_egresos
    guardar_db_egresos(registros, anio)

    return movidos, errores


def _mover_archivo(reg, carpeta_destino, num_linea_default, movidos, errores):
    """Mueve un archivo XML a la carpeta destino con el nombre correcto."""
    ruta_origen = reg.get("ruta_xml", "")
    folio = reg.get("folio", "")

    if not ruta_origen or not folio:
        errores.append((reg.get("id", "?"), "Sin ruta o folio"))
        return

    ruta_origen = Path(ruta_origen)
    if not ruta_origen.exists():
        errores.append((folio, f"No existe: {ruta_origen}"))
        return

    # Detectar si el XML ya está renombrado (<linea>-<folio>.xml)
    import re
    match = re.match(r"^(\d+)-", ruta_origen.name)
    if match:
        num_linea = int(match.group(1))
    else:
        num_linea = num_linea_default

    # Nombre destino: <linea>-<folio>.xml
    nombre_destino = f"{num_linea}-{folio}.xml"
    ruta_destino = carpeta_destino / nombre_destino

    # Si ya existe, agregar contador
    contador = 1
    while ruta_destino.exists():
        nombre_destino = f"{num_linea}-{folio}_{contador}.xml"
        ruta_destino = carpeta_destino / nombre_destino
        contador += 1

    try:
        # Mover (shutil.move funciona entre discos)
        shutil.move(str(ruta_origen), str(ruta_destino))
        # Guardar el número de línea en el registro
        reg["linea"] = num_linea
        reg["ruta_xml_destino"] = str(ruta_destino)

        movidos.append({
            "folio": folio,
            "origen": str(ruta_origen),
            "destino": str(ruta_destino),
            "linea": num_linea,
        })
    except Exception as e:
        errores.append((folio, str(e)))
