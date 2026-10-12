#!/usr/bin/env python3
"""
Script CLI para probar el pipeline de Egresos sin tocar el SAT.

Uso:
    # Listar snapshots disponibles
    python3 scripts/probar_egresos.py --listar-snapshots

    # Correr el pipeline sobre XMLs de prueba (mes/año actuales)
    python3 scripts/probar_egresos.py egresos/_mock/

    # Correr sobre septiembre 2026
    python3 scripts/probar_egresos.py /tmp/sat_descargas/ --anio 2026 --mes 9

    # Solo procesar, sin mover/guardar/excel
    python3 scripts/probar_egresos.py /tmp/sat_descargas/ --dry-run --hasta procesar --anio 2026 --mes 9

    # Reprocesar un snapshot real del SAT
    python3 scripts/probar_egresos.py --desde-snapshot ABC123

    # Ver un error guardado
    python3 scripts/probar_egresos.py --reproducir-error 2026-10-11_1102_solicitar_descarga.json

    # Probar la FIEL sin gastar solicitud
    python3 scripts/probar_egresos.py --probar-fiel

    # Activar/desactivar historial
    python3 scripts/probar_egresos.py --historial on
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


ETAPAS = ["procesar", "mover", "guardar", "excel"]


# ─────────────────────────────────────────────────────────────
# Etapas del pipeline
# ─────────────────────────────────────────────────────────────

def etapa_procesar(carpeta_xmls: Path, ctx: dict, dry_run: bool) -> dict:
    from sat.procesar_completo import procesar_todo

    anio = ctx.get("anio")
    mes_idx = ctx.get("mes_idx")
    if anio is None or mes_idx is None:
        hoy = datetime.now()
        anio = anio if anio is not None else hoy.year
        mes_idx = mes_idx if mes_idx is not None else hoy.month

    print(f"  → Procesando XMLs en {carpeta_xmls}")
    print(f"    Año: {anio}  Mes: {mes_idx}")
    resumen = procesar_todo(anio, mes_idx, carpeta_xml=str(carpeta_xmls))
    print(f"    ✓ {resumen}")
    return {**ctx, "resumen": resumen}


def etapa_mover(carpeta_xmls: Path, ctx: dict, dry_run: bool) -> dict:
    if dry_run:
        print("  → [DRY-RUN] Omitiendo mover")
    else:
        print("  → [INFO] procesar_todo ya mueve los XMLs internamente")
    return ctx


def etapa_guardar(carpeta_xmls: Path, ctx: dict, dry_run: bool) -> dict:
    if dry_run:
        print("  → [DRY-RUN] Omitiendo guardar")
    else:
        print("  → [INFO] procesar_todo ya guarda en DB internamente")
    return ctx


def etapa_excel(carpeta_xmls: Path, ctx: dict, dry_run: bool) -> dict:
    if dry_run:
        print("  → [DRY-RUN] Omitiendo Excel")
    else:
        print("  → [INFO] procesar_todo ya genera el Excel internamente")
    return ctx


ETAPAS_FN = {
    "procesar": etapa_procesar,
    "mover": etapa_mover,
    "guardar": etapa_guardar,
    "excel": etapa_excel,
}


# ─────────────────────────────────────────────────────────────
# Orquestador
# ─────────────────────────────────────────────────────────────

def correr_pipeline(carpeta_xmls: Path, dry_run: bool = False,
                    hasta: str = "excel",
                    anio: int | None = None,
                    mes_idx: int | None = None) -> int:
    if not carpeta_xmls.exists():
        print(f"✗ La carpeta no existe: {carpeta_xmls}")
        return 2
    xmls = list(carpeta_xmls.glob("*.xml"))
    if not xmls:
        print(f"✗ No hay XMLs en: {carpeta_xmls}")
        return 2

    print(f"▶ Pipeline de Egresos — {len(xmls)} XMLs")
    print(f"  Carpeta: {carpeta_xmls}")
    print(f"  Modo: {'DRY-RUN' if dry_run else 'REAL'}")
    print(f"  Hasta: {hasta}")
    if anio and mes_idx:
        print(f"  Periodo: {mes_idx:02d}/{anio}")
    print()

    if hasta not in ETAPAS:
        print(f"✗ Etapa inválida: {hasta}")
        return 2
    idx_fin = ETAPAS.index(hasta)

    ctx: dict = {"anio": anio, "mes_idx": mes_idx}
    for i, nombre in enumerate(ETAPAS):
        if i > idx_fin:
            break
        print(f"[{i+1}/{idx_fin+1}] {nombre.upper()}")
        try:
            ctx = ETAPAS_FN[nombre](carpeta_xmls, ctx, dry_run)
        except Exception as e:
            print(f"  ✗ Error en '{nombre}': {e}")
            traceback.print_exc()
            return 1
        print()

    print("✓ Pipeline completado")
    return 0


# ─────────────────────────────────────────────────────────────
# Comandos especiales
# ─────────────────────────────────────────────────────────────

def cmd_listar_snapshots() -> int:
    from core import sat_historial
    snapshots = sat_historial.listar_snapshots()
    if not snapshots:
        print("No hay snapshots en el historial.")
        print(f"  Carpeta: {sat_historial.HISTORIAL_DIR}")
        return 0

    print(f"▶ {len(snapshots)} snapshots:\n")
    for s in snapshots:
        print(f"  {s.get('id_solicitud', '?')}")
        print(f"    carpeta:        {s.get('_carpeta', '?')}")
        print(f"    rfc:            {s.get('rfc', '?')}")
        print(f"    periodo:        {s.get('fecha_desde', '?')} → {s.get('fecha_hasta', '?')}")
        print(f"    estado:         {s.get('estado_final', '?')}")
        print(f"    xmls:           {s.get('num_xmls', 0)}")
        print(f"    verificaciones: {len(s.get('verificaciones', []))}")
        print()
    return 0


def cmd_desde_snapshot(id_o_carpeta: str, dry_run: bool, hasta: str,
                       anio: int | None = None,
                       mes_idx: int | None = None) -> int:
    from core import sat_historial
    carpeta_xmls = sat_historial.ruta_xmls_de_snapshot(id_o_carpeta)
    if carpeta_xmls is None:
        print(f"✗ No se encontró snapshot: {id_o_carpeta}")
        print("  Usa --listar-snapshots")
        return 2
    print(f"▶ Snapshot: {id_o_carpeta}")
    print(f"  XMLs en: {carpeta_xmls}\n")

    # Si no los dan, intenta inferirlos del meta.json
    if anio is None or mes_idx is None:
        meta = _leer_meta_snapshot(id_o_carpeta)
        if meta:
            anio = anio if anio is not None else _anio_de_fecha(meta.get("fecha_desde"))
            mes_idx = mes_idx if mes_idx is not None else _mes_de_fecha(meta.get("fecha_desde"))

    return correr_pipeline(carpeta_xmls, dry_run=dry_run, hasta=hasta,
                           anio=anio, mes_idx=mes_idx)


def cmd_reproducir_error(nombre: str) -> int:
    from core import sat_historial
    ruta = Path(nombre)
    if not ruta.is_absolute():
        ruta = sat_historial.ERRORES_DIR / nombre
    if not ruta.exists():
        print(f"✗ No existe: {ruta}")
        if sat_historial.ERRORES_DIR.exists():
            print("\nErrores guardados:")
            for f in sorted(sat_historial.ERRORES_DIR.glob("*.json"), reverse=True):
                print(f"  {f.name}")
        return 2

    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("▶ Error guardado:")
    for k, v in data.items():
        print(f"  {k}: {v}")
    return 0


def cmd_probar_fiel() -> int:
    from config.config_egresos import cargar_config_egresos
    from sat.descarga import probar_fiel
    cfg = cargar_config_egresos()
    res = probar_fiel(
        cfg.get("certificado_cer", ""),
        cfg.get("certificado_key", ""),
        cfg.get("password_fiel", ""),
    )
    if res["ok"]:
        print(f"✓ {res['mensaje']}")
        print(f"  Token: {res['token_preview']}")
        return 0
    print(f"✗ {res['mensaje']}")
    return 1


def cmd_historial(accion: str) -> int:
    from config.config_egresos import activar_historial_sat, historial_sat_activo
    if accion == "on":
        activar_historial_sat(True)
        print("✓ Historial del SAT ACTIVADO.")
    elif accion == "off":
        activar_historial_sat(False)
        print("✓ Historial del SAT DESACTIVADO.")
    elif accion == "status":
        estado = "ACTIVADO" if historial_sat_activo() else "DESACTIVADO"
        print(f"Historial del SAT: {estado}")
    else:
        print(f"✗ Acción inválida: {accion}. Usa on|off|status.")
        return 2
    return 0


# ─────────────────────────────────────────────────────────────
# Helpers de snapshot
# ─────────────────────────────────────────────────────────────

def _leer_meta_snapshot(id_o_carpeta: str) -> dict:
    from core import sat_historial
    carpeta = sat_historial.HISTORIAL_DIR / id_o_carpeta
    if not carpeta.is_dir():
        carpeta = sat_historial._buscar_snapshot(id_o_carpeta)
    if carpeta is None:
        return {}
    return sat_historial._leer_json(carpeta / "meta.json")


def _anio_de_fecha(fecha) -> int | None:
    if not fecha:
        return None
    try:
        return int(str(fecha)[:4])
    except Exception:
        return None


def _mes_de_fecha(fecha) -> int | None:
    if not fecha:
        return None
    try:
        return int(str(fecha)[5:7])
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prueba el pipeline de Egresos sin tocar el SAT.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("carpeta", nargs="?", type=Path,
                        help="Carpeta con XMLs de prueba.")
    parser.add_argument("--dry-run", action="store_true",
                    help="Solo omite mover/guardar/excel. procesar siempre corre completo.")
    parser.add_argument("--hasta", choices=ETAPAS, default="excel",
                        help="Detenerse después de esta etapa.")
    parser.add_argument("--anio", type=int, default=None,
                        help="Año del periodo (ej. 2026). Default: año actual.")
    parser.add_argument("--mes", type=int, default=None,
                        help="Mes 1-12 (ej. 9 = septiembre). Default: mes actual.")
    parser.add_argument("--desde-snapshot", metavar="ID_O_CARPETA",
                        help="Reprocesar un snapshot del SAT.")
    parser.add_argument("--listar-snapshots", action="store_true",
                        help="Listar snapshots disponibles.")
    parser.add_argument("--reproducir-error", metavar="ARCHIVO",
                        help="Mostrar un error guardado.")
    parser.add_argument("--probar-fiel", action="store_true",
                        help="Validar la FIEL sin gastar solicitud.")
    parser.add_argument("--historial", choices=["on", "off", "status"],
                        help="Activar/desactivar/ver el historial del SAT.")

    args = parser.parse_args()

    # Validar mes
    if args.mes is not None and (args.mes < 1 or args.mes > 12):
        print(f"✗ Mes inválido: {args.mes}. Debe ser 1-12.")
        return 2

    if args.listar_snapshots:
        return cmd_listar_snapshots()
    if args.reproducir_error:
        return cmd_reproducir_error(args.reproducir_error)
    if args.desde_snapshot:
        return cmd_desde_snapshot(args.desde_snapshot, args.dry_run, args.hasta,
                                  anio=args.anio, mes_idx=args.mes)
    if args.probar_fiel:
        return cmd_probar_fiel()
    if args.historial:
        return cmd_historial(args.historial)

    if not args.carpeta:
        parser.print_help()
        return 2

    return correr_pipeline(args.carpeta, dry_run=args.dry_run, hasta=args.hasta,
                           anio=args.anio, mes_idx=args.mes)


if __name__ == "__main__":
    sys.exit(main())