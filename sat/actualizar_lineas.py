# -*- coding: utf-8 -*-
"""
sat/actualizar_lineas.py
Lee el número de línea del nombre de los XML movidos
y lo guarda en el JSON.
"""
import sys
from pathlib import Path

# Agregar la raíz del proyecto al path
_raiz = Path(__file__).parent.parent
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

import re

from sat.guardar_egresos import cargar_db_egresos, guardar_db_egresos


ANIO = 2026
MES = "septiembre"

# Carpetas
BASE_EGRESO = Path.home() / "Documents" / f"Contabilidad {ANIO}" / f"Contabilidad {MES}" / "Egreso"
...
import re
from pathlib import Path

from sat.guardar_egresos import cargar_db_egresos, guardar_db_egresos


ANIO = 2026
MES = "septiembre"

# Carpetas
BASE_EGRESO = Path.home() / "Documents" / f"Contabilidad {ANIO}" / f"Contabilidad {MES}" / "Egreso"


def extraer_linea_del_nombre(nombre):
    """
    Extrae el número de línea del nombre del XML.
    Formato: <linea>-<folio>.xml
    """
    match = re.match(r"^(\d+)-", nombre)
    if match:
        return int(match.group(1))
    return None


def main():
    print("=" * 60)
    print("ACTUALIZAR NÚMEROS DE LÍNEA EN EL JSON")
    print("=" * 60)

    # Cargar JSON
    registros = cargar_db_egresos(ANIO)
    print(f"Registros en JSON: {len(registros)}")

    # Indexar registros por folio
    por_folio = {}
    for reg in registros:
        folio = str(reg.get("folio", "")).strip()
        if folio:
            por_folio[folio] = reg

    print(f"Registros con folio: {len(por_folio)}")
    print()

    # Buscar XML en las carpetas
    carpetas = {
        "PUE": BASE_EGRESO / "PUE",
        "PPD": BASE_EGRESO / "PPD",
        "Animalia": BASE_EGRESO / "Animalia",
    }

    actualizados = 0
    no_encontrados = 0

    for nombre_carpeta, carpeta in carpetas.items():
        if not carpeta.exists():
            continue

        for ruta in carpeta.glob("*.xml"):
            nombre = ruta.name
            linea = extraer_linea_del_nombre(nombre)

            # Extraer folio del nombre
            match = re.match(r"^\d+-(.+)\.xml$", nombre)
            if not match:
                continue
            folio = match.group(1)

            # Buscar registro por folio
            reg = por_folio.get(folio)
            if reg:
                reg["linea"] = linea
                reg["ruta_xml_destino"] = str(ruta)
                reg["carpeta"] = nombre_carpeta
                actualizados += 1
            else:
                no_encontrados += 1

    print(f"✅ Actualizados: {actualizados}")
    print(f"⚠️  No encontrados: {no_encontrados}")
    print()

    # Guardar
    guardar_db_egresos(registros, ANIO)
    print("✅ JSON actualizado")


if __name__ == "__main__":
    main()
