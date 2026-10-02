# -*- coding: utf-8 -*-
"""
sat/actualizar_rutas.py
Actualiza las rutas de los XML en el JSON buscando en las carpetas de Egreso.
"""
import sys
import re
from pathlib import Path

_raiz = Path(__file__).parent.parent
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))

from sat.guardar_egresos import cargar_db_egresos, guardar_db_egresos


ANIO = 2026
MES = "septiembre"

BASE_EGRESO = Path.home() / "Documents" / f"Contabilidad {ANIO}" / f"Contabilidad {MES}" / "Egreso"


def main():
    print("=" * 60)
    print("ACTUALIZAR RUTAS DE XML EN EL JSON")
    print("=" * 60)

    # Cargar JSON
    registros = cargar_db_egresos(ANIO)
    print(f"Registros en JSON: {len(registros)}")

    # Indexar XML por folio
    xml_por_folio = {}

    for subcarpeta in ["PUE", "PPD", "Animalia"]:
        carpeta = BASE_EGRESO / subcarpeta
        if not carpeta.exists():
            continue
        for ruta in carpeta.glob("*.xml"):
            # Extraer folio del nombre: <linea>-<folio>.xml
            match = re.match(r"^(\d+)-(.+)\.xml$", ruta.name)
            if match:
                linea = int(match.group(1))
                folio = match.group(2)
                xml_por_folio[folio] = {
                    "ruta": str(ruta),
                    "linea": linea,
                    "carpeta": subcarpeta,
                }

    print(f"XML encontrados en carpetas: {len(xml_por_folio)}")
    print()

    # Actualizar rutas y líneas
    actualizados = 0
    no_encontrados = 0

    for reg in registros:
        folio = str(reg.get("folio", "")).strip()
        if not folio:
            continue

        info = xml_por_folio.get(folio)
        if info:
            reg["ruta_xml"] = info["ruta"]
            reg["linea"] = info["linea"]
            reg["carpeta"] = info["carpeta"]
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