# Contexto del Proyecto - Vet Suite

## Stack
- Python 3.13 (dev en 3.14)
- tkinter + ttkbootstrap
- openpyxl, cfdiclient, pdfplumber, lxml
- Empaquetado automático con GitHub Actions (tags `v*`)

## Módulos
- **INGRESOS**: descarga de Gmail, procesa XML+PDF, genera Excel
- **EGRESOS**: descarga del SAT, procesa, clasifica, genera Excel PUE/PPD
- **ESTÉTICA Y TRANSPORTES**: clientes, mascotas, rutas, tarifas
- **RECORDATORIOS**: citas y vacunas, envío por WhatsApp (wa.me)

---

## Arquitectura de configuración

### Configuración COMPARTIDA (los 4 módulos)

Vive en **`config_ui.json`** en la raíz de datos. Acceso único vía
`core/config_ui.py`.

**Claves:**
- `"tema"` → nombre del tema ttkbootstrap (ej. `"darkly"`)
- `"veterinaria"` → `{nombre, sucursal_activa, sucursales: [...]}`

**Sucursales (fuente de verdad única):**
- Definidas en `config/veterinaria.py` (`SUCURSALES_DEFAULT`).
- Se editan SOLO desde **Configuración General → tab 🏥 Veterinaria**.
- Cada sucursal: `{id, nombre, nombre_corto, direccion, telefono, activa, coordenadas}`
- `nombre_corto` es el identificador estable que usan los módulos
  (ej. Egresos guarda `reg["sucursal"] = "Baalak"`).
- Los `nombre_corto` actuales: `"Baalak"`, `"Prado"`, `"Animalia"`.
- La activa se marca con el botón **● Marcar como activa** (no hay checkbox).
- El diálogo de detalle NO tiene checkbox "activa" — se maneja desde la tabla.

**Módulo compartido de acceso:**
- `core/config_ui.py` → única API para leer/escribir `config_ui.json`.
- `core/config_ui.leer()` crea el archivo con `{}` si no existe.
- `core/config_ui.set_seccion(nombre, valor)` → merge no destructivo.
- `AppPrincipal.__init__` fuerza un guardado inicial de defaults para que
  el archivo exista desde el primer arranque.

### Configuración POR MÓDULO

| Módulo | Carpeta datos | Archivos clave |
|--------|---------------|----------------|
| Ingresos | `<raíz>/ingresos/` (dev) o `~/Documents/Vet Suite/ingresos/` (prod) | `gmail_config.json`, `historial_autocompletado.json`, `registros_ingresos_YYYY.json`, `catalogo_qvet.json`, `categorias_manuales.json` |
| Egresos | `<raíz>/egresos/` o `~/Documents/Vet Suite/egresos/` | `config_egresos.json`, `proveedores_tc.json`, `proveedores_sucursal.json`, `observaciones_egresos.json`, `solicitud_sat_activa.json`, `registros_egresos_YYYY.json` |
| Estética y Transportes | `<raíz>/estetica_transportes/` o `~/Documents/Vet Suite/estetica_transportes/` | `clientes_maestro.json`, `mascotas.json`, `servicios_estetica.json`, `tarifas_transporte.json`, `transportes_cliente.json`, `geocoding_cache.json` |
| Recordatorios | `<raíz>/recordatorios/` o `~/Documents/Vet Suite/recordatorios/` | `agenda_importada.json`, `vacunas_importada.json`, `historial_envios.json` |

**Reglas de configuración por módulo:**
- Cada módulo lee/escribe SU carpeta de datos.
- NO acceder a archivos de otros módulos.
- La sucursal activa se lee SIEMPRE de `config.veterinaria.sucursal_activa()`,
  nunca se cachea en el módulo.
- `config_ui.json` es el ÚNICO JSON que vive en la raíz del proyecto.

### Estructura de datos en disco

**Dev:** `<raíz proyecto>/{ingresos,egresos,estetica_transportes,recordatorios}/` + `config_ui.json`
**Prod:** `~/Documents/Vet Suite/{ingresos,egresos,estetica_transportes,recordatorios}/` + `config_ui.json`

**Reportes y facturas visibles** (iguales en dev y prod):

/Documents/
├── Contabilidad 2025/
│ └── Contabilidad enero/
│ ├── Ingreso/
│ │ ├── Facturas Central/
│ │ └── Deposito/
│ └── Egreso/
│ ├── Baalak/
│ │ ├── PUE/
│ │ │ ├── Efectivo/
│ │ │ ├── TC/
│ │ │ ├── TD/
│ │ │ ├── Transferencia/
│ │ │ └── PPD/
│ │ └── PPD/
│ │ └── PPD/
│ ├── Animalia/
│ ├── PDFs/
│ └── Deposito_Egreso/
├── Contabilidad 2026/
│ └── (misma estructura)
├── Reportes Recordatorios/
└── Vet Suite/
└── (datos de la app en prod)

### Migraciones implementadas (v2.1.1)

- `recordatorios/sucursales.json` → `config_ui.json#veterinaria`
  - Se ejecuta al importar `config/veterinaria.py` por primera vez.
  - El archivo viejo se renombra a `.json.bak`.
- `config/temas.py#TEMA` (constante global) → `obtener_tema()` (función).
  - Se mantiene `__getattr__` para retrocompatibilidad.
- `config/ajustes.py` → **ELIMINADO**. Todos los imports migrados a
  `config/config_ingresos.py`.
- Cachés de Recordatorios: formato lista → `{sucursal, clientes}`.
  - Migración automática en `AppRecordatorios._normalizar_cache`.
- `dialogos/sucursal_editor.py` → **ELIMINADO**. El único editor de
  sucursales es Config General → tab Veterinaria.

### Migraciones implementadas (v2.1.2)

- `sat/guardar_egresos.py` ahora usa `core.rutas_egresos.ruta_registros_egresos`
  (única fuente de verdad). Antes calculaba su propia carpeta.
- `registros_egresos_YYYY.json` movido de la raíz a `egresos/`.
- `catalogo_qvet.json` movido de la raíz a `ingresos/`.
- `Reportes Recordatorios` movido de `~/Documents/Vet Suite/` a `~/Documents/`.

---

## Archivos clave

### Compartido / infraestructura
| Archivo | Propósito |
|---------|-----------|
| `main.py` | Entry point |
| `app/principal.py` | Pantalla de inicio (fuerza escritura inicial de `config_ui.json`) |
| `core/config_ui.py` | Única API de acceso a `config_ui.json` |
| `core/rutas.py` | Rutas de Ingresos + `CONFIG_UI_FILE` re-exportado |
| `core/rutas_egresos.py` | Rutas de Egresos (fuente de verdad de rutas del módulo) |
| `core/rutas_estetica.py` | Rutas de Estética |
| `core/rutas_recordatorios.py` | Rutas de Recordatorios + `_cargar_json` / `_guardar_json` |
| `core/sat_historial.py` | Historial completo de descargas SAT (snapshots) |
| `ui/utils.py` | `configurar_ventana()` |
| `ui/widgets.py` | Widgets custom |
| `config/temas.py` | Tema visual (`obtener_tema`, `guardar_tema`, colores) |
| `config/veterinaria.py` | Sucursales y datos del negocio (fuente de verdad) |
| `config/campos.py` | Definiciones de campos (MESES_ES, etc.) |
| `config/config_ingresos.py` | Config de Gmail (ex `ajustes.py`) |
| `config/config_egresos.py` | Config del módulo de Egresos |
| `dialogos/config_general.py` | Config General (Apariencia + Veterinaria) |
| `dialogos/temas.py` | Selector de tema |
| `dialogos/manual.py` | Visor del manual |
| `dialogos/gmail_config.py` | Config de Gmail |
| `scripts/probar_egresos.py` | CLI de pruebas (reprocesar XMLs, snapshots, FIEL) |

### Ingresos
| Archivo | Propósito |
|---------|-----------|
| `modulos/ingresos.py` | Módulo Ingresos |
| `modulos/lector_facturas.py` | Parser PDF (prioridad) + XML + agrupado |
| `modulos/correo_facturas.py` | Descarga de Gmail |
| `dialogos/adjuntos.py` | Ver adjuntos |
| `dialogos/sincronizar.py` | Sincronización Gmail |
| `dialogos/registrar_productos.py` | Reclasificar productos |
| `dialogos/reclasificador.py` | Reclasificador masivo |
| `core/persistencia.py` | Carga/guarda JSONs |
| `core/correo_utils.py` | Utilidades de correo |
| `excel/generador.py` | Orquestación de Excel (crear/anexar) |
| `excel/escritor.py` | Escritura de filas/encabezados/totales |
| `excel/constantes.py` | Columnas, fórmulas, colores |
| `excel/estilos.py` | Estilos openpyxl |

### Egresos
| Archivo | Propósito |
|---------|-----------|
| `modulos/egresos.py` | Módulo Egresos |
| `sat/descarga.py` | Descarga SAT (cfdiclient) + `probar_fiel()` + historial |
| `sat/conversion.py` | Conversión FIEL (NO TOCAR) |
| `sat/procesar_completo.py` | Procesa XMLs y orquesta (NO genera Excel) |
| `sat/mover_egresos.py` | Mueve y renombra XMLs por fecha real de factura |
| `sat/guardar_egresos.py` | Guarda DB de egresos (usa `core.rutas_egresos`) |
| `dialogos/descargar_sat.py` | Diálogo de descarga + botón "Probar FIEL" |
| `dialogos/egresos_config.py` | Config del SAT |
| `dialogos/egresos_editar.py` | Edita registro + adjuntos |
| `dialogos/clasificar_sucursal.py` | Clasifica proveedor → sucursal (usa `config.veterinaria`) |
| `dialogos/reportes_egresos.py` | Reportes |
| `dialogos/espera_sat.py` | Ventana de espera del SAT |
| `core/persistencia_egresos.py` | Carga/guarda JSONs |
| `excel/egresos.py` | Genera Excel PUE/PPD |

### Estética y Transportes
| Archivo | Propósito |
|---------|-----------|
| `modulos/estetica_transportes.py` | Módulo completo |
| `dialogos/cliente_detalle.py` | Detalle del cliente (4 tabs) |
| `dialogos/mascota_editar.py` | Alta/edición de mascota |
| `dialogos/catalogo_editor.py` | Ver/eliminar servicios y tarifas |
| `dialogos/duplicados_basura.py` | Duplicados + basura |
| `core/geocoding.py` | Geocodificación con Nominatim |

### Recordatorios
| Archivo | Propósito |
|---------|-----------|
| `modulos/recordatorios.py` | Ventana principal |
| `core/recordatorios/sucursales.py` | Adaptador → `config.veterinaria` |
| `core/recordatorios/formatear.py` | Formateo fechas/teléfonos/strings |
| `core/recordatorios/servicios.py` | Diccionario + procesarServicio |
| `core/recordatorios/plantillas.py` | Encabezados de citas/vacunas |
| `core/recordatorios/procesar_excel.py` | Importación + agrupación + mensajes |
| `core/recordatorios/envio.py` | WhatsApp (wa.me) + portapapeles |
| `core/recordatorios/historial.py` | Historial de envíos |

---

## Reglas importantes

1. **NO tocar `sat/conversion.py`** — usa openssl 1.1.1
2. **NO tocar el password de `Fiel()`** — se pasa vacío porque `preparar_fiel()` ya desencripta
3. **Solo UNA solicitud SAT a la vez** — el SAT rechaza simultáneas
4. **Los JSON de datos NO van a git** (están en .gitignore)
5. **Los archivos se nombran `<serie>-<folio>.xml`** (sin número de línea)
6. **La numeración de línea se calcula al vuelo** en tabla y Excel
7. **Dev y prod usan la MISMA estructura de carpetas** — solo cambia la base
8. **`config_ui.json` es COMPARTIDO por los 4 módulos** — acceso único vía `core/config_ui.py`
9. **Las sucursales SOLO se editan desde Config General → tab 🏥 Veterinaria**
10. **`nombre_corto` de sucursal es el identificador estable** entre módulos
11. **Los reportes visibles van SIEMPRE a `~/Documents/Contabilidad AAAA/`** (excepto Recordatorios que va a `~/Documents/Reportes Recordatorios/`)
12. **Los mensajes de Recordatorios se cachean con la sucursal activa** (`{"sucursal": id, "clientes": [...]}`). Al abrir, si la sucursal cambió, se regeneran los NO enviados.
13. **El Excel de Ingresos solo anexa registros nuevos.** Si modificas un registro existente, debes elegir "No" (reordenar todo) al generar el Excel. El anexado compara por folio fiscal y no. de factura.
14. **Las fórmulas del Excel de Ingresos reflejan el desglose por remisión.** Ej.: `=(228+115+125)/1.16`. Cada paréntesis es una remisión.
15. **El importe del PDF ya viene con IVA incluido.** No dividir dos veces. El divisor solo se aplica en la fórmula y en el cálculo numérico interno.
16. **Los XMLs de Egresos se archivan según la fecha real de emisión de cada factura**, no el mes de la solicitud. Un CFDI emitido el 20/04/2026 va a `Contabilidad abril/...` aunque la descarga se haga en octubre.
17. **`config_ui.json` es el ÚNICO JSON que vive en la raíz del proyecto.** Los JSON de cada módulo van en su carpeta.
18. **`procesar_todo` (Egresos) NO genera Excel.** El usuario lo genera con el botón "📊 Generar Excel" tras revisar la tabla.
19. **El Excel de Egresos se ordena por fecha + folio** antes de escribirse.

---

## Módulo Ingresos — procesamiento de facturas

### Prioridad de lectura
- **SIEMPRE** deben venir XML + PDF. Si falta uno → `ValueError` y se informa.
- **Los productos** se leen del **PDF** por remisión. El XML solo aporta cabecera
  (RFC, nombre, folio fiscal, total, fecha, pagos).
- **NO hay fallback a conceptos del XML.** Si el PDF no trae productos → error.
- El **total del XML NUNCA se pisa con el del PDF**. Si difieren > $0.01, se
  loguea pero se usa el XML.
- Pagos: del PDF si están; si no, `FormaPago` del XML.

### Clasificación por categoría
- Catálogo QVET (`ingresos/catalogo_qvet.json`) + excepciones manuales (`ingresos/categorias_manuales.json`).
- **Categorías válidas:** `U`, `ACCESORIOS`, `MEDICAMENTOS`, `HIGIENE`,
  `ESTETICA`, `TRANSPORTE`, `PENSION`, `VACUNA`, `CLINICA`.
- Categoría no encontrada → `U` + aviso de reclasificación.
- Producto con IVA/IEPS en categoría `SIN_IVA` (VACUNA, CLINICA) → `U` + aviso.

### Separación por tipo fiscal

**Regla clave:** cada columna del Excel tiene **un único tratamiento fiscal**.
Ninguna columna mezcla IVA con IEPS ni con exentos.

| Categoría | Columnas del Excel | Contenido |
|---|---|---|
| U, ACCESORIOS, ESTETICA, TRANSPORTE, PENSION | IMPORTE + IVA (16%) | Base sin IVA + fórmula `=base*0.16` |
| VACUNA, CLINICA | IMPORTE | Base tal cual (sin IVA) |
| MEDICAMENTOS | IMPORTE (sin IVA) + SIN IVA + IVA (16%) | Exentos / base gravados / IVA de gravados |
| HIGIENE | IMPORTE (sin IVA) + SIN IVA + IVA (16%) + SIN IEPS 6% + IEPS (6%) + SIN IEPS 7% + IEPS (7%) | Igual pero con 3 impuestos |

**Nota:** los títulos `IMPORTE (sin IVA)` son confusos — no significa "base de gravados"
sino "productos que por ley no llevan IVA". Lo decide el usuario y no se cambia.

### Fórmulas en el Excel

Cada columna construye una fórmula que refleja el desglose por remisión:

- **1 producto en la remisión** → `114`
- **2+ productos en la misma remisión** → `(114+100)`
- **Varias remisiones** → `(114+100)+(200)+(58)`
- **Si la columna tiene divisor (IVA/IEPS):** se saca al final: `=((114+100)+(200)+(58))/1.16`
- **Si la columna no tiene divisor (exentos):** se mantienen los grupos: `=(50+30)+(80)`
- **1 solo producto en la columna con divisor:** `=58/1.16`
- **1 solo producto sin divisor:** `=58`

**Divisores:**
- IVA 16% → `/1.16`
- IEPS 6% → `/1.06`
- IEPS 7% → `/1.07`
- Sin impuesto → sin división

### Valores guardados en el registro

- `datos_completos["X_importe"]` → número plano (base sin IVA para gravados).
- `datos_completos["X_iva"]` → número plano (para validación interna).
- `datos_completos["X_importe__expr"]` → string con la fórmula sin el `=`.

En el Excel, la columna base usa `={X_importe__expr}`. La columna IVA usa
siempre `=X_base{r}*0.16` (fórmula viva, NO expresión).

### Validaciones

- **Ajuste de centavos:** si `suma_bases + suma_impuestos` difiere del total XML
por ±$0.01, se ajusta a la **base más grande** (no al IVA).
- **Deduplicación:** productos con mismo nombre + cantidad + remisión → se omite
el segundo (con log).
- **Check rojo en Excel:** `Total Remisiones` vs `Total Factura`. Si difieren
> $0.01, la celda va en rojo.

### Sincronización de filtros al leer factura

`_leer_factura` **sincroniza los filtros del UI** (año/mes/centro) con los del
registro guardado, para que la factura aparezca en la tabla.

`_guardar_silencioso` **siempre actualiza** `self.registros` y
`self._anio_cargado`, incluso cuando la factura es de otro año.

---

## Módulo Egresos

### Propósito
- Descargar CFDI recibidos del SAT
- Procesar XMLs (parsear, clasificar por sucursal, separar PUE/PPD)
- Mover XMLs a carpetas por sucursal/método/forma de pago
- Generar Excel PUE/PPD

### Datos en `/egresos/`
- `config_egresos.json` — RFC, FIEL, último periodo, flag de historial
- `registros_egresos_YYYY.json` — DB anual de registros
- `solicitud_sat_activa.json` — solicitud pendiente (temporal)
- `proveedores_tc.json`, `proveedores_sucursal.json`, `observaciones_egresos.json`
- `_sat_historial/` — snapshots de descargas SAT (no va a git)

### Flujo de descarga y procesamiento

1. **Descargar del SAT** (botón): solicita, espera, descarga, procesa y mueve XMLs.
   **NO genera Excel.**
2. **Revisar** en la tabla: editar sucursal, método o forma de pago. La app mueve el XML
   y actualiza la DB (`mover_un_registro`).
3. **Generar Excel** (botón): genera el Excel del mes/sucursal filtrado,
   **ordenado por fecha + folio**.

### Estructura de carpetas (real)

/Documents/Contabilidad AAAA/Contabilidad <mes>/Egreso/
├── <Sucursal>/ # Baalak | Animalia
│ ├── PUE/
│ │ ├── Efectivo/
│ │ ├── TC/
│ │ ├── TD/
│ │ ├── Transferencia/
│ │ └── PPD/ # (cuando metodo=PPD)
│ └── PPD/
│ └── PPD/
└── Deposito_Egreso/ # Excel generados


**La carpeta refleja la fecha real de emisión de la factura**, no el mes de la solicitud.

### Historial del SAT (`core/sat_historial.py`)

Cada solicitud al SAT se guarda como un "snapshot" en
`egresos/_sat_historial/<timestamp>_<id_solicitud>/`:

- `meta.json` — metadatos de la solicitud
- `01_solicita.json` — respuesta de SolicitaDescarga
- `02_verifica_N.json` — cada verificación
- `03_descarga_N.zip` — el ZIP tal cual lo entrega el SAT
- `xmls/` — XMLs extraídos
- `_errores/` — errores guardados aparte

**Activar/desactivar:**
python3 scripts/probar_egresos.py --historial on|off|status

**Override por entorno:**
export VET_SUITE_HISTORIAL=1

**Reprocesar / listar / errores:**
python3 scripts/probar_egresos.py --desde-snapshot <id>
python3 scripts/probar_egresos.py --listar-snapshots
python3 scripts/probar_egresos.py --reproducir-error <archivo>


### Probar FIEL sin gastar solicitud

- `sat/descarga.py::probar_fiel(cer, key, pwd)` → valida credenciales con `Autenticacion`.
- Botón **"🔑 Probar FIEL"** en `dialogos/descargar_sat.py`.
- **No gasta solicitud**: el SAT no cuenta `Autenticacion` como solicitud de descarga.

### Reglas
- **Los XMLs se mueven por fecha real de emisión de cada factura.**
- **`procesar_todo` NO genera Excel.** El usuario decide cuándo.
- **La numeración de línea se calcula al vuelo.**
- **Editar un registro mueve el XML** (`mover_un_registro`).

---

## Módulo Estética y Transportes

### Propósito
- Buscar clientes por nombre, población, dirección o mascota
- Ver/editar datos de transporte (distancia, tiempo, tarifa, notas)
- Ver/editar datos de estética (mascotas: raza, carácter, precauciones, servicio)

### Datos en `/estetica_transportes/`
- `clientes_maestro.json` — importado del Excel
- `mascotas.json` — `{cliente: [{nombre, raza, carácter, precauciones, ...}]}`
- `servicios_estetica.json` — catálogo de servicios
- `tarifas_transporte.json` — catálogo de tarifas
- `transportes_cliente.json` — datos de transporte por cliente
- `geocoding_cache.json` — caché de geocodificación

### Reglas
- Importación con detección por contenido + preview + merge
- Búsqueda sin acentos ni mayúsculas
- Notas separadas: cliente, transporte, estética
- ⚠️ en la tabla si hay notas en cualquier pestaña
- Cálculo de ruta con Haversine × 1.3 y velocidad 25 km/h
- Origen de rutas = sucursal activa (`config.veterinaria.sucursal_activa()`)

---

## Módulo Recordatorios

### Propósito
- Importar Excel de agenda y vacunas (exportados de QVET)
- Agrupar clientes por teléfono
- Generar mensajes con formato profesional
- Enviar por WhatsApp (wa.me + portapapeles)
- Historial de envíos + informes

### Flujo
1. Importar Excel (auto-detecta tipo por encabezados)
2. Clientes agrupados en 2 tabs: Citas / Vacunas
3. Seleccionar cliente → ver mensaje
4. "Enviar por WhatsApp" → copia al portapapeles + abre WhatsApp Desktop
5. Pegar (Cmd+V) + enviar
6. Confirmar en la app → se marca como enviado

### Formato de Excel

**Citas:** `FECHA | INICIO | TIPO VISITA | PROPIETARIO | MASCOTA | TELÉFONO | ASUNTO | AGENDA | ESTADO`

**Vacunas:** `CLIENTE | TELÉFONO 1 | MASCOTA | TIPO DE RECORDATORIO | VACUNA | PRÓXIMA FECHA`

### Datos en `/recordatorios/`
- `agenda_importada.json` — `{"sucursal": "BAALAK_CENTRAL", "clientes": [...]}`
- `vacunas_importada.json` — `{"sucursal": "BAALAK_CENTRAL", "clientes": [...]}`
- `historial_envios.json` — envíos por fecha
- `plantillas.json` — (futuro)

### Reglas
- Detección de tipo por columnas (no por nombre de archivo)
- Los emojis se preservan al copiar (van al portapapeles)
- Los emojis NO se muestran en Tk (se reemplazan por texto)
- **Los mensajes se regeneran al cambiar la sucursal activa** (solo clientes no enviados)
- **Al recibir foco, con debounce de 200 ms, verifica si la sucursal cambió**
- **Al abrir, si la sucursal guardada ≠ sucursal activa, regenera**
- La sucursal activa se lee SIEMPRE de `config.veterinaria`
- **NO hay botón de sucursales dentro del módulo** (solo en Config General)

### Reportes
- Van SIEMPRE a `~/Documents/Reportes Recordatorios/`.

---

## Empaquetado

- Push de tag `v*` → GitHub Actions compila para Windows y macOS
- `requirements.txt` debe tener cada dependencia en línea separada
- `--collect-all cfdiclient` y `--collect-all lxml` en build.yml
- `--add-data "MANUAL.md:."` para el manual integrado
- `config_ui.json` NO va en el bundle (se genera en runtime)
- `catalogo_qvet.json` NO va en el bundle (vive en `ingresos/`)
- `MANUAL.md` sí va en el bundle (se busca en `sys._MEIPASS`)

---

## Estado actual

- ✅ Ingresos funcional (con fórmulas por remisión)
- ✅ Egresos: descarga, procesa, mueve, Excel
- ✅ XMLs de Egresos se archivan por fecha real de factura
- ✅ Auto-clasificación de proveedores (usa `config.veterinaria`)
- ✅ Manual integrado
- ✅ Empaquetado automático
- ✅ Estética y Transportes completo
- ✅ Recordatorios completo (con regeneración por sucursal)
- ✅ `config_ui.json` unificado (tema + veterinaria)
- ✅ Migración automática de sucursales viejas
- ✅ Editor único de sucursales (Config General → Veterinaria)
- ✅ Shim `config/ajustes.py` eliminado
- ✅ `dialogos/sucursal_editor.py` eliminado
- ✅ Historial del SAT (`core/sat_historial.py`)
- ✅ CLI de pruebas (`scripts/probar_egresos.py`)
- ✅ Botón "Probar FIEL"
- ✅ `catalogo_qvet.json` en `ingresos/`
- ✅ `Reportes Recordatorios` en `~/Documents/`
- ⏳ Pendiente: pruebas con SAT real y cliente final

---

## Historial de versiones

### v2.1.2 (actual)
- **Fix: XMLs de Egresos se archivan por fecha real de factura** (no mes de solicitud)
- **Refactor: `sat/guardar_egresos.py` usa `core.rutas_egresos`** (única fuente de verdad)
- **Migración: `registros_egresos_YYYY.json` movido a `egresos/`**
- **Migración: `catalogo_qvet.json` movido a `ingresos/`**
- **Migración: `Reportes Recordatorios` movido a `~/Documents/`**
- **Nuevo: `core/sat_historial.py`** — historial completo de descargas SAT
- **Nuevo: `scripts/probar_egresos.py`** — CLI de pruebas
- **Nuevo: `sat/descarga.py::probar_fiel`** — valida FIEL sin gastar solicitud
- **Nuevo: botón "🔑 Probar FIEL" en el diálogo de descarga**
- **Cambio: `procesar_todo` ya no genera Excel** (el usuario lo hace con el botón)
- **Fix: Excel de Egresos se ordena por fecha + folio**
- **Limpieza: `_ordenar_facturas` restaurada y usada en la generación de Excel**
- **Fix: `mover_y_renombrar_egresos` agrupa por `(anio_factura, mes_factura, sucursal, metodo, forma)`**

### v2.1.1
- **Refactor de configuración compartida:**
  - `core/config_ui.py` como única API de `config_ui.json`
  - `config/temas.py` y `config/veterinaria.py` usan `config_ui`
  - Bug del `TEMA` global arreglado (`obtener_tema()`)
  - `config_ui.json` se autocrea al arrancar la app
- **Renombrado `config/ajustes.py` → `config/config_ingresos.py`:**
  - Shim eliminado, imports migrados
- **`dialogos/clasificar_sucursal.py`:** usa sucursales dinámicas
- **`dialogos/config_general.py`:** editor único de sucursales
- **`config/veterinaria.py`:** `nombre_corto` simplificado
- **`modulos/recordatorios.py`:** caché con sucursal, regeneración
- **`modulos/ingresos.py`:** `mapa_campos` (MEDICAMENTOS/HIGIENE separan exentos)
- **`modulos/lector_facturas.py`:** rechaza sin XML o PDF, no pisa total, fórmulas por remisión
- **`excel/escritor.py`:** `_calcular_total_remisiones` con claves correctas

### v2.1.0
- Módulo **Recordatorios** completo
- Fix crash `espera_sat.py` (bad window path name)
- Separación de `config_ui.json` (tema) e `ingresos/gmail_config.json` (correo)

### v2.0.0
- Renombrado a **Vet Suite**
- Nueva arquitectura de rutas de datos en dev y prod
- Módulo **Estética y Transportes** funcional

### v1.0.1
- Ingresos y Egresos funcionales
- Empaquetado automático con GitHub Actions

---

## Pendientes / Deuda técnica

### Egresos
- [ ] **Anexar + reordenar en Excel** cuando ya existe y tiene anotaciones del usuario
- [ ] **Rotación de snapshots SAT** (borrar los más viejos automáticamente)
- [ ] **`actualizar_json` podría fusionarse con `mover_y_renombrar_egresos`** (hacen cosas parecidas)

### Testing
- [ ] **Tests con pytest** sobre snapshots reales del SAT
- [ ] **Tests de `core/config_ui.py`**
- [ ] **Tests del pipeline de facturas de Ingresos**

### Ingresos
- [ ] **Reprocesar duplicadas en sincronizar** para regenerar `__expr` si faltan

### Recordatorios
- [ ] **Informe de recordatorios** (PDF/Excel)

### Estética
- [ ] **Autocompletado en Estética**

### Arquitectura
- [ ] **Refactor v3.0.0 por dominio funcional:**
  - Separar `ingresos/`, `egresos/`, `estetica_transportes/`, `recordatorios/`
  - Cada dominio autocontenido (módulo + lógica + rutas + diálogos + tests)
  - `shared/` para código transversal