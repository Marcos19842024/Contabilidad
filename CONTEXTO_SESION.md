# Sesión de trabajo — 2026-10-12 (v2.1.2)

## Resumen
Fix del archivado de XMLs de Egresos por fecha real de factura
+ historial completo del SAT + limpieza de rutas de JSONs.

## Qué se hizo

### 1. Historial del SAT (`core/sat_historial.py`)
- Módulo nuevo que guarda **todo** lo que viene del SAT:
  - `meta.json` por solicitud (id, RFC, fechas, estado, verificaciones)
  - `01_solicita.json`, `02_verifica_N.json`, `03_descarga_N.json/.zip`
  - `xmls/` extraídos del ZIP
  - `_errores/` con errores del SAT
- Snapshots en `egresos/_sat_historial/<timestamp>_<id>/`
- Flag en `config_egresos.json`: `guardar_historial_sat`
- Override por entorno: `VET_SUITE_HISTORIAL=1`
- **Regla:** nunca sobreescribe, nunca borra automáticamente, nunca falla
  por el historial (si algo sale mal, loguea y sigue).

### 2. `sat/descarga.py` engancha el historial
- `solicitar_descarga` → guarda `01_solicita.json`
- `verificar_solicitud` → guarda cada `02_verifica_N.json`
- `descargar_paquetes` → guarda el ZIP + extrae `xmls/`
- `guardar_error` en cada excepción
- Firma de `descargar_paquetes` ahora acepta `id_solicitud`

### 3. `probar_fiel()` — validar FIEL sin gastar solicitud
- `sat/descarga.py::probar_fiel(cer, key, pwd)` → solo `Autenticacion`.
- El SAT no cuenta `Autenticacion` como solicitud.
- Botón **"🔑 Probar FIEL"** en `dialogos/descargar_sat.py`.
- Corre en hilo, muestra estado en label (verde/rojo).

### 4. `scripts/probar_egresos.py` — CLI de pruebas
- Reprocesa XMLs de una carpeta sin tocar el SAT.
- Flags: `--dry-run`, `--hasta`, `--anio`, `--mes`, `--desde-snapshot`,
  `--listar-snapshots`, `--reproducir-error`, `--probar-fiel`, `--historial`.
- **Ojo:** `procesar_todo` siempre corre completo; `--dry-run` solo omite
  las etapas cosméticas.

### 5. Fix: XMLs de Egresos por fecha real de factura
- `sat/mover_egresos.py::mover_y_renombrar_egresos` ahora agrupa por
  `(anio_factura, mes_factura, sucursal, metodo, forma)`.
- Nuevo helper `_parsear_fecha_ddmmyyyy()`.
- Los XMLs van a `Contabilidad <mes-real>/Egreso/<Sucursal>/<Metodo>/<Forma>/`.
- `ruta_xml` en la DB apunta al mes real.
- **Regla nueva:** un CFDI del 20/04/2026 va a `Contabilidad abril/...`
  aunque la descarga se haga en octubre.

### 6. Fix: `sat/guardar_egresos.py` usa `core.rutas_egresos`
- Antes calculaba su propia `_carpeta_datos()` (apuntaba a la raíz).
- Ahora importa `ruta_registros_egresos` de `core.rutas_egresos`.
- `registros_egresos_YYYY.json` movido de la raíz a `egresos/`.

### 7. Cambio: `procesar_todo` NO genera Excel
- `sat/procesar_completo.py::generar_excels` eliminada.
- `procesar_todo` solo procesa, mueve y actualiza DB.
- El Excel se genera con el botón **"📊 Generar Excel"** de la app.
- Resumen de `procesar_todo` ahora devuelve `excel: {None...}`.

### 8. Fix: Excel ordenado por fecha + folio
- `_ordenar_facturas` (en `sat/mover_egresos.py`) ahora se importa desde
  `modulos/egresos.py::_generar_excel` y se aplica antes de generar.

### 9. Limpieza de rutas
- `catalogo_qvet.json` movido de la raíz a `ingresos/`.
- `Reportes Recordatorios` movido de `~/Documents/Vet Suite/` a `~/Documents/`.

### 10. Reglas nuevas en `CONTEXTO.md`
- Regla 16: XMLs de Egresos por fecha real de factura.
- Regla 17: `config_ui.json` es el único JSON en la raíz.
- Regla 18: `procesar_todo` no genera Excel.
- Regla 19: Excel de Egresos ordenado por fecha + folio.

## Estado actual
- ✅ Todo funciona: Ingresos, Egresos, Estética, Recordatorios, Config General.
- ✅ XMLs de Egresos se archivan por fecha real de factura.
- ✅ Historial del SAT operativo (activado).
- ✅ CLI de pruebas funcional.
- ✅ Botón "Probar FIEL" verificado (autenticó correctamente).
- ⏳ Pendiente: pruebas con SAT real y cliente final.

## Próximos pasos sugeridos
- A) **Anexar + reordenar Excel** cuando ya existe y tiene anotaciones.
- B) **Tests con pytest** sobre snapshots del SAT.
- C) **Rotación de snapshots SAT** (evitar llenar el disco).
- D) **Mover Reportes Recordatorios** (ya hecho) + verificar otros módulos.
- E) **Refactor v3.0.0 por dominio funcional.**

## Cómo trabajar
- Configuración compartida → `core/config_ui.py`.
- Sucursales → `config/veterinaria.py` (fuente de verdad).
- Antes de tocar: correr `python3 verificar_config.py`.
- Los JSON de datos NO van a git.
- `config_ui.json` se autocrea; no lo borres.
- Historial del SAT: `python3 scripts/probar_egresos.py --historial status`.

## Pendientes de la sesión (deuda técnica)

### Egresos
- [ ] **Anexar + reordenar Excel.** Hoy: "Sí" = backup + regenerar (pierde
  anotaciones); "No" = no hace nada; no hay "Anexar".
- [ ] **`actualizar_json` y `mover_y_renombrar_egresos`** hacen cosas
  parecidas. Fusionar en el refactor.
- [ ] **5 XMLs ignorados** en `/tmp/sat_descargas/` (no son Ingreso,
  probablemente notas de crédito). Revisar.

### Testing
- [ ] **pytest** sobre snapshots reales (anonimizados).
- [ ] Tests de `core/config_ui.py`.
- [ ] Tests del pipeline de Ingresos.

### Arquitectura
- [ ] Refactor v3.0.0 por dominio funcional.