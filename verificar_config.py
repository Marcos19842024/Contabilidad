# -*- coding: utf-8 -*-
"""Script de verificación post-refactor. Ejecutar: python3 verificar_config.py"""
import sys
import json

print("=" * 60)
print("VERIFICACIÓN DE REFACTOR — config_ui compartido")
print("=" * 60)

errores = []

# 1) tema.py sin bug de TEMA
print("\n[1] config.temas ...")
try:
    from config.temas import obtener_tema, tema_es_oscuro, COLORES
    print(f"    obtener_tema()  = {obtener_tema()!r}")
    print(f"    tema_es_oscuro() = {tema_es_oscuro()}")
    print(f"    COLORES tiene {len(COLORES)} claves")
    print("    ✅ OK")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    errores.append(("config.temas", e))

# 2) veterinaria.py lee bien
print("\n[2] config.veterinaria ...")
try:
    from config.veterinaria import (
        obtener_veterinaria, sucursales, sucursal_activa,
        nombre_clinica_activa,
    )
    vet = obtener_veterinaria()
    print(f"    nombre = {vet.get('nombre')!r}")
    print(f"    sucursal_activa = {vet.get('sucursal_activa')!r}")
    print(f"    total sucursales = {len(sucursales())}")
    print(f"    activa → {nombre_clinica_activa()!r}")
    print("    ✅ OK")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    errores.append(("config.veterinaria", e))

# 3) config_ui.py fuente única
print("\n[3] core.config_ui ...")
try:
    from core import config_ui
    data = config_ui.leer()
    print(f"    archivo = {config_ui.CONFIG_UI_FILE}")
    print(f"    claves  = {list(data.keys())}")
    print("    ✅ OK")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    errores.append(("core.config_ui", e))

# 4) adaptador de recordatorios
print("\n[4] core.recordatorios.sucursales ...")
try:
    from core.recordatorios.sucursales import (
        cargar_sucursales, sucursal_activa as sa,
        nombre_clinica_activa as nca,
    )
    data = cargar_sucursales()
    print(f"    sucursal_activa = {data.get('sucursal_activa')!r}")
    print(f"    activa → {nca()!r}")
    print("    ✅ OK")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    errores.append(("core.recordatorios.sucursales", e))

# 5) config de ingresos (shim)
print("\n[5] config.config_ingresos ...")
try:
    from config.config_ingresos import cargar_config_correo
    cfg = cargar_config_correo()
    print(f"    etiqueta = {cfg.get('etiqueta')!r}")
    print("    ✅ OK")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    errores.append(("config.config_ingresos", e))

# 6) rutas_egresos / rutas_estetica / rutas_recordatorios
print("\n[6] rutas de módulos ...")
for mod in ("core.rutas_egresos", "core.rutas_estetica",
            "core.rutas_recordatorios", "core.rutas"):
    try:
        m = __import__(mod, fromlist=["CARPETA_DATOS"])
        carpeta = getattr(m, "CARPETA_DATOS", None)
        print(f"    {mod:35s} → {carpeta}")
    except Exception as e:
        print(f"    ❌ {mod}: {e}")
        errores.append((mod, e))

# 7) contenido real de config_ui.json
print("\n[7] contenido de config_ui.json ...")
try:
    from core import config_ui
    if config_ui.CONFIG_UI_FILE.exists():
        with open(config_ui.CONFIG_UI_FILE, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), ensure_ascii=False, indent=2))
    else:
        print("    (no existe todavía)")
    print("    ✅ OK")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    errores.append(("config_ui.json", e))

# Resumen
print("\n" + "=" * 60)
if errores:
    print(f"❌ {len(errores)} error(es):")
    for mod, e in errores:
        print(f"   - {mod}: {e}")
    sys.exit(1)
else:
    print("✅ TODO OK")
    print("=" * 60)