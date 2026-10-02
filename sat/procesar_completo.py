# -*- coding: utf-8 -*-
"""
sat/procesar_completo.py
Orquesta el procesamiento completo de los XML descargados del SAT:

  1. procesar_carpeta()        -> leer XMLs y construir facturas
  2. guardar_facturas()        -> guardar en JSON
  3. mover_y_renombrar_egresos -> mover XMLs a PUE/PPD/Animalia
  4. actualizar_lineas + rutas -> actualizar JSON con lineas y rutas
  5. generar Excel PUE + PPD   -> en Deposito_Egreso/

NO modifica ningun modulo existente. Solo los usa.
"""

from datetime import datetime
from pathlib import Path

from config.campos import MESES_ES
from sat.guardar_egresos import (
    cargar_db_egresos,
    guardar_db_egresos,
)
from sat.mover_egresos import (
    mover_y_renombrar_egresos,
    ruta_egreso,
)
from sat.procesar_xml import procesar_carpeta
from excel.egresos import generar_excel_pue, generar_excel_ppd


# ============================================================
# PASO 1 + 2: Procesar XML y guardar en JSON
# ============================================================
def procesar_y_guardar(carpeta_xml, anio):
    """
    Procesa todos los XML de la carpeta y los guarda en el JSON.

    Devuelve: (nuevas, duplicadas, facturas)
    """
    facturas = procesar_carpeta(carpeta_xml)

    if not facturas:
        return 0, 0, []

    from sat.guardar_egresos import guardar_facturas
    nuevas, duplicadas = guardar_facturas(facturas, anio=anio)

    return nuevas, duplicadas, facturas


# ============================================================
# PASO 3: Mover XMLs a PUE/PPD/Animalia
# ============================================================
def mover_xmls(anio, mes_idx, carpeta_origen="/tmp/sat_descargas"):
    """
    Mueve y renombra los XML a las carpetas PUE/PPD/Animalia.
    Devuelve (movidos, errores).
    """
    registros = cargar_db_egresos(anio)

    movidos, errores = mover_y_renombrar_egresos(
        registros,
        anio=anio,
        mes_idx=mes_idx,
        carpeta_origen=carpeta_origen,
    )

    return movidos, errores


# ============================================================
# PASO 4: Actualizar lineas y rutas en el JSON
# ============================================================
def actualizar_json(anio, mes_nombre):
    """
    Actualiza los campos 'linea' y 'ruta_xml' en el JSON buscando
    los XMLs ya movidos en las carpetas del mes.

    Reutiliza la logica de actualizar_lineas.py + actualizar_rutas.py
    pero SIN depender de sus constantes globales.
    """
    import re

    base_egreso = (
        Path.home() / "Documents"
        / f"Contabilidad {anio}"
        / f"Contabilidad {mes_nombre}"
        / "Egreso"
    )

    registros = cargar_db_egresos(anio)

    # Indexar XML por folio
    xml_por_folio = {}
    for subcarpeta in ["PUE", "PPD", "Animalia"]:
        carpeta = base_egreso / subcarpeta
        if not carpeta.exists():
            continue
        for ruta in carpeta.glob("*.xml"):
            match = re.match(r"^(\d+)-(.+)\.xml$", ruta.name)
            if match:
                linea = int(match.group(1))
                folio = match.group(2)
                xml_por_folio[folio] = {
                    "ruta": str(ruta),
                    "linea": linea,
                    "carpeta": subcarpeta,
                }

    actualizados = 0
    no_encontrados = 0
    for reg in registros:
        folio = str(reg.get("folio", "")).strip()
        if not folio:
            continue

        info = xml_por_folio.get(folio)
        if info:
            reg["ruta_xml"] = info["ruta"]
            reg["ruta_xml_destino"] = info["ruta"]
            reg["linea"] = info["linea"]
            reg["carpeta"] = info["carpeta"]
            actualizados += 1
        else:
            no_encontrados += 1

    guardar_db_egresos(registros, anio)

    return actualizados, no_encontrados


# ============================================================
# PASO 5: Generar Excel PUE + PPD
# ============================================================
def generar_excels(anio, mes_idx, mes_nombre):
    """
    Genera los Excel PUE y PPD en la carpeta Deposito_Egreso/.

    Devuelve: dict con las rutas de los archivos generados.
    """
    registros = cargar_db_egresos(anio)

    # Separar por sucursal
    baalak = [r for r in registros if r.get("sucursal") != "Animalia"]

    # Separar PUE / PPD
    pue = [r for r in baalak if r.get("metodo_pago") != "PPD"]
    ppd = [r for r in baalak if r.get("metodo_pago") == "PPD"]

    # Carpeta destino
    carpeta_deposito = ruta_egreso(anio, mes_idx) / "Deposito_Egreso"
    carpeta_deposito.mkdir(parents=True, exist_ok=True)

    resultado = {
        "carpeta": str(carpeta_deposito),
        "pue": None,
        "ppd": None,
        "total_pue": len(pue),
        "total_ppd": len(ppd),
        "total_animalia": len(registros) - len(baalak),
    }

    if pue:
        ruta_pue = carpeta_deposito / f"RELACION FACTURAS PUE - {mes_nombre} {anio}.xlsx"
        generar_excel_pue(pue, ruta_pue, mes_nombre, anio)
        resultado["pue"] = str(ruta_pue)

    if ppd:
        ruta_ppd = carpeta_deposito / f"RELACION FACTURAS PPD - {mes_nombre} {anio}.xlsx"
        generar_excel_ppd(ppd, ruta_ppd, mes_nombre, anio)
        resultado["ppd"] = str(ruta_ppd)

    return resultado


# ============================================================
# ORQUESTADOR COMPLETO
# ============================================================
def procesar_todo(anio, mes_idx, carpeta_xml="/tmp/sat_descargas",
                  callback=None):
    """
    Ejecuta la secuencia completa:
      1. Procesar XML y guardar en JSON
      2. Mover XMLs a PUE/PPD/Animalia
      3. Actualizar lineas/rutas en JSON
      4. Generar Excel PUE + PPD

    Parametros:
      - anio: int, ej. 2026
      - mes_idx: int (1-12), ej. 9
      - carpeta_xml: carpeta donde estan los XML descargados
      - callback: funcion(mensaje) opcional para reportar progreso

    Devuelve un dict con el resumen de cada paso.
    """
    mes_nombre = MESES_ES[mes_idx - 1]

    def _log(msg):
        print(msg)
        if callback:
            try:
                callback(msg)
            except Exception:
                pass

    resumen = {
        "anio": anio,
        "mes": mes_nombre,
        "nuevas": 0,
        "duplicadas": 0,
        "movidos": 0,
        "errores_mover": 0,
        "actualizados": 0,
        "no_encontrados": 0,
        "excel": {},
    }

    # 1 + 2) Procesar y guardar
    _log("→ Procesando XMLs...")
    nuevas, duplicadas, facturas = procesar_y_guardar(carpeta_xml, anio)
    resumen["nuevas"] = nuevas
    resumen["duplicadas"] = duplicadas
    _log(f"   Nuevas: {nuevas} | Duplicadas: {duplicadas}")

    # 3) Mover XMLs
    _log("→ Moviendo XMLs a PUE/PPD/Animalia...")
    movidos, errores = mover_xmls(anio, mes_idx, carpeta_xml)
    resumen["movidos"] = len(movidos)
    resumen["errores_mover"] = len(errores)
    _log(f"   Movidos: {len(movidos)} | Errores: {len(errores)}")

    # 4) Actualizar lineas/rutas
    _log("→ Actualizando JSON con lineas y rutas...")
    actualizados, no_encontrados = actualizar_json(anio, mes_nombre)
    resumen["actualizados"] = actualizados
    resumen["no_encontrados"] = no_encontrados
    _log(f"   Actualizados: {actualizados} | No encontrados: {no_encontrados}")

    # 5) Generar Excel
    _log("→ Generando Excel PUE y PPD...")
    excel = generar_excels(anio, mes_idx, mes_nombre)
    resumen["excel"] = excel
    _log(f"   PUE: {excel.get('total_pue', 0)} facturas")
    _log(f"   PPD: {excel.get('total_ppd', 0)} facturas")
    _log(f"   Animalia excluidas: {excel.get('total_animalia', 0)}")
    _log(f"   Carpeta: {excel.get('carpeta')}")

    return resumen


if __name__ == "__main__":
    # Prueba con valores por defecto (ajustar si es necesario)
    procesar_todo(anio=2026, mes_idx=9)