# -*- coding: utf-8 -*-
"""
sat/mover_egresos.py
Renombra y mueve los XML de Egresos a sus carpetas correspondientes.

Estructura:
  Egreso/
  ├── Animalia/
  │   ├── PUE/
  │   │   ├── Efectivo/
  │   │   ├── TC/
  │   │   ├── TD/
  │   │   ├── Transferencia/
  │   │   └── PPD/
  │   └── PPD/
  │       ├── Efectivo/
  │       ├── TC/
  │       ├── TD/
  │       ├── Transferencia/
  │       └── PPD/
  └── Baalak/
      └── (misma estructura)

Nombre del archivo: <linea>-<folio>.xml
"""

import shutil
from datetime import datetime
from pathlib import Path

from config.campos import MESES_ES
from core.rutas import BASE_DIR


# Formas de pago válidas (nombre de carpeta)
FORMAS_PAGO_VALIDAS = ["Efectivo", "TC", "TD", "Transferencia", "PPD"]


def ruta_egreso(anio, mes_idx):
    """Carpeta base de Egresos."""
    return (
        BASE_DIR / f"Contabilidad {anio}"
        / f"Contabilidad {MESES_ES[mes_idx - 1]}"
        / "Egreso"
    )


def _ruta_carpeta(anio, mes_idx, sucursal, metodo, forma_pago):
    """
    Devuelve la ruta a la carpeta específica según
    sucursal + metodo + forma_pago.

    Ej: Egreso/Baalak/PUE/TC/
    """
    # Normalizar
    sucursal = "Animalia" if str(sucursal).strip() == "Animalia" else "Baalak"
    metodo = "PPD" if str(metodo).strip() == "PPD" else "PUE"

    if metodo == "PPD":
        # PPD siempre va a PPD/PPD/
        forma = "PPD"
    else:
        # PUE: según la forma de pago
        forma = str(forma_pago).strip()
        if forma not in FORMAS_PAGO_VALIDAS or forma == "PPD":
            forma = "Efectivo"  # default

    return ruta_egreso(anio, mes_idx) / sucursal / metodo / forma


def _ordenar_facturas(facturas):
    """Ordena por fecha ascendente, luego por folio."""
    def _orden(r):
        try:
            partes = r.get("fecha", "").split("/")
            if len(partes) == 3:
                return (int(partes[2]), int(partes[1]), int(partes[0]))
        except Exception:
            pass
        return (0, 0, 0)
    return sorted(facturas, key=_orden)


def mover_y_renombrar_egresos(registros, anio, mes_idx, carpeta_origen):
    """
    Renombra y mueve los XML de Egresos a sus carpetas según
    sucursal, método y forma de pago.

    Actualiza cada registro con:
      - linea
      - ruta_xml / ruta_xml_destino
      - carpeta (sucursal/metodo/forma)

    Parámetros:
      - registros: lista de facturas.
      - anio: año.
      - mes_idx: índice del mes (1-12).
      - carpeta_origen: dónde están los XMLs sin procesar.

    Devuelve:
      - (movidos, errores)
    """
    carpeta_origen = Path(carpeta_origen)
    movidos = []
    errores = []

    # Separar por sucursal + metodo + forma
    # Guardamos un contador de línea por grupo
    from collections import defaultdict
    por_grupo = defaultdict(list)

    for reg in registros:
        sucursal = reg.get("sucursal", "Baalak")
        metodo = reg.get("metodo_pago", "PUE")
        forma = reg.get("forma_pago_texto", "Efectivo")
        if metodo == "PPD":
            forma = "PPD"
        elif forma not in FORMAS_PAGO_VALIDAS or forma == "PPD":
            forma = "Efectivo"

        clave = (sucursal, metodo, forma)
        por_grupo[clave].append(reg)

    # Ordenar cada grupo y renumerar
    for clave, facturas in por_grupo.items():
        sucursal, metodo, forma = clave
        facturas_ordenadas = _ordenar_facturas(facturas)

        # Carpeta destino
        carpeta_destino = _ruta_carpeta(anio, mes_idx, sucursal, metodo, forma)
        carpeta_destino.mkdir(parents=True, exist_ok=True)

        # Renumerar y mover
        for i, reg in enumerate(facturas_ordenadas, 1):
            folio = reg.get("folio", "")
            if not folio:
                errores.append((reg.get("id", "?"), "Sin folio"))
                continue

            # Nombre destino: <linea>-<folio>.xml
            num_linea = i
            nombre_xml = f"{num_linea}-{folio}.xml"
            ruta_destino = carpeta_destino / nombre_xml

            # Buscar el XML origen
            ruta_origen = reg.get("ruta_xml", "")
            if not ruta_origen:
                # Buscar en carpeta_origen por UUID o folio
                candidatos = list(carpeta_origen.glob(f"*{folio}*.xml"))
                if not candidatos:
                    candidatos = list(carpeta_origen.glob(f"*{reg.get('uuid', '')}*.xml"))
                if candidatos:
                    ruta_origen = str(candidatos[0])

            ruta_origen = Path(ruta_origen) if ruta_origen else None

            if not ruta_origen or not ruta_origen.exists():
                # Si ya está en la carpeta destino, solo actualizamos el registro
                if ruta_destino.exists():
                    reg["linea"] = num_linea
                    reg["ruta_xml"] = str(ruta_destino)
                    reg["ruta_xml_destino"] = str(ruta_destino)
                    reg["carpeta"] = f"{sucursal}/{metodo}/{forma}"
                    movidos.append({
                        "folio": folio,
                        "destino": str(ruta_destino),
                        "linea": num_linea,
                    })
                    continue

                errores.append((folio, "XML origen no encontrado"))
                continue

            # Si ya está en su lugar, solo actualizar
            if ruta_origen.resolve() == ruta_destino.resolve():
                reg["linea"] = num_linea
                reg["ruta_xml"] = str(ruta_destino)
                reg["ruta_xml_destino"] = str(ruta_destino)
                reg["carpeta"] = f"{sucursal}/{metodo}/{forma}"
                movidos.append({
                    "folio": folio,
                    "destino": str(ruta_destino),
                    "linea": num_linea,
                })
                continue

            # Mover el XML
            try:
                # Si ya existe en destino, eliminar el anterior
                if ruta_destino.exists():
                    ruta_destino.unlink()
                shutil.move(str(ruta_origen), str(ruta_destino))

                reg["linea"] = num_linea
                reg["ruta_xml"] = str(ruta_destino)
                reg["ruta_xml_destino"] = str(ruta_destino)
                reg["carpeta"] = f"{sucursal}/{metodo}/{forma}"

                movidos.append({
                    "folio": folio,
                    "origen": str(ruta_origen),
                    "destino": str(ruta_destino),
                    "linea": num_linea,
                })

            except Exception as e:
                errores.append((folio, str(e)))

    # Guardar el JSON con los nuevos números de línea
    from sat.guardar_egresos import guardar_db_egresos
    guardar_db_egresos(registros, anio)

    return movidos, errores


def mover_un_registro(registro, anio, mes_idx):
    """
    Mueve UN solo registro (usado cuando cambias su sucursal o forma de pago).
    Devuelve (ok, mensaje).
    """
    try:
        sucursal = registro.get("sucursal", "Baalak")
        metodo = registro.get("metodo_pago", "PUE")
        forma = registro.get("forma_pago_texto", "Efectivo")
        if metodo == "PPD":
            forma = "PPD"

        carpeta_destino = _ruta_carpeta(anio, mes_idx, sucursal, metodo, forma)
        carpeta_destino.mkdir(parents=True, exist_ok=True)

        folio = registro.get("folio", "")
        linea = registro.get("linea", 1) or 1
        nombre_xml = f"{linea}-{folio}.xml"
        ruta_destino = carpeta_destino / nombre_xml

        ruta_origen = registro.get("ruta_xml", "")
        ruta_origen = Path(ruta_origen) if ruta_origen else None

        # Si ya está en destino, no hacer nada
        if ruta_origen and ruta_origen.exists() and ruta_origen.resolve() == ruta_destino.resolve():
            return True, "Sin cambios"

        # Mover
        if ruta_origen and ruta_origen.exists():
            if ruta_destino.exists():
                ruta_destino.unlink()
            shutil.move(str(ruta_origen), str(ruta_destino))

        registro["ruta_xml"] = str(ruta_destino)
        registro["ruta_xml_destino"] = str(ruta_destino)
        registro["carpeta"] = f"{sucursal}/{metodo}/{forma}"

        return True, f"Movido a {sucursal}/{metodo}/{forma}/"

    except Exception as e:
        return False, str(e)