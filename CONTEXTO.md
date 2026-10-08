# Contexto del Proyecto - Vet Suite

## Stack
- Python 3.13 (dev en 3.14)
- tkinter + ttkbootstrap
- openpyxl, cfdiclient, pyinstaller, openpyxl, pdfplumber
- Empaquetado automático con GitHub Actions (tags `v*`)

## Módulos
- **INGRESOS**: descarga de Gmail, procesa XML+PDF, genera Excel
- **EGRESOS**: descarga del SAT, procesa, clasifica, genera Excel PUE/PPD
- **ESTÉTICA Y TRANSPORTES**: clientes, mascotas, rutas, tarifas
- **RECORDATORIOS**: citas y vacunas, envío por WhatsApp (wa.me)

## Estructura de datos

### Datos internos (JSON, invisibles para el usuario)

**Dev:** `<raíz proyecto>/{ingresos,egresos,estetica_transportes,recordatorios}/`
**Prod:** `~/Documents/Vet Suite/{ingresos,egresos,estetica_transportes,recordatorios}/`

### Reportes y facturas visibles (iguales en dev y prod)

Documents/
├── Contabilidad 2025/
│ └── Contabilidad enero/
│ ├── Ingreso/
│ │ ├── Facturas Central/
│ │ └── Deposito/
│ └── Egreso/
│ ├── PUE/
│ ├── PPD/
│ ├── Animalia/
│ ├── PDFs/
│ └── Deposito_Egreso/
├── Contabilidad 2026/
└── Vet Suite/
└── Reportes Recordatorios/


## Archivos clave

### Ingresos
| Archivo | Propósito |
|---------|-----------|
| `modulos/ingresos.py` | Módulo Ingresos |
| `modulos/lector_facturas.py` | Parser PDF/XML + agrupado |
| `modulos/correo_facturas.py` | Descarga de Gmail |
| `dialogos/adjuntos.py` | Ver adjuntos |
| `dialogos/sincronizar.py` | Sincronización Gmail |
| `dialogos/registrar_productos.py` | Reclasificar productos |
| `dialogos/reclasificador.py` | Reclasificador masivo |
| `core/persistencia.py` | Carga/guarda JSONs |
| `core/rutas.py` | Rutas de Ingresos |
| `core/correo_utils.py` | Utilidades de correo |
| `excel/generador.py` | Escribe Excel de resumen |

### Egresos
| Archivo | Propósito |
|---------|-----------|
| `modulos/egresos.py` | Módulo Egresos |
| `sat/descarga.py` | Descarga SAT (cfdiclient) |
| `sat/conversion.py` | Conversión FIEL (NO TOCAR) |
| `sat/procesar_completo.py` | Procesa XMLs y genera Excel |
| `sat/mover_egresos.py` | Mueve y renombra XMLs |
| `sat/guardar_egresos.py` | Guarda DB de egresos |
| `dialogos/descargar_sat.py` | Diálogo de descarga |
| `dialogos/egresos_config.py` | Config del SAT |
| `dialogos/egresos_editar.py` | Edita registro + adjuntos |
| `dialogos/clasificar_sucursal.py` | Clasifica proveedor → sucursal |
| `dialogos/reportes_egresos.py` | Reportes |
| `dialogos/espera_sat.py` | Ventana de espera del SAT |
| `core/persistencia_egresos.py` | Carga/guarda JSONs |
| `core/rutas_egresos.py` | Rutas de Egresos |
| `config/config_egresos.py` | Config global del módulo |
| `excel/egresos.py` | Genera Excel PUE/PPD |

### Estética y Transportes
| Archivo | Propósito |
|---------|-----------|
| `modulos/estetica_transportes.py` | Módulo completo |
| `dialogos/cliente_detalle.py` | Detalle del cliente (4 tabs) |
| `dialogos/mascota_editar.py` | Alta/edición de mascota |
| `dialogos/catalogo_editor.py` | Ver/eliminar servicios y tarifas |
| `dialogos/duplicados_basura.py` | Duplicados + basura |
| `core/rutas_estetica.py` | Rutas de datos |
| `core/geocoding.py` | Geocodificación con Nominatim |

### Recordatorios
| Archivo | Propósito |
|---------|-----------|
| `modulos/recordatorios.py` | Ventana principal |
| `dialogos/sucursal_editor.py` | Editor de sucursales |
| `core/rutas_recordatorios.py` | Rutas de datos |
| `core/recordatorios/__init__.py` | Paquete |
| `core/recordatorios/formatear.py` | Formateo fechas/teléfonos/strings |
| `core/recordatorios/servicios.py` | Diccionario + procesarServicio |
| `core/recordatorios/sucursales.py` | Catálogo configurable |
| `core/recordatorios/plantillas.py` | Plantillas de citas/vacunas |
| `core/recordatorios/procesar_excel.py` | Importación + agrupación + mensajes |
| `core/recordatorios/envio.py` | WhatsApp (wa.me) + portapapeles |
| `core/recordatorios/historial.py` | Historial de envíos |

### Compartido
| Archivo | Propósito |
|---------|-----------|
| `app/principal.py` | Pantalla de inicio |
| `main.py` | Entry point |
| `ui/utils.py` | `configurar_ventana()` |
| `ui/widgets.py` | Widgets custom |
| `config/ajustes.py` | Config global (tema) |
| `config/campos.py` | Definiciones de campos |
| `config/temas.py` | Temas y colores |
| `dialogos/config_general.py` | Config desde la app |
| `dialogos/temas.py` | Selector de tema |
| `dialogos/manual.py` | Ver manual |
| `dialogos/gmail_config.py` | Config de Gmail |

## Reglas importantes

1. **NO tocar `sat/conversion.py`** — usa openssl 1.1.1
2. **NO tocar el password de `Fiel()`** — se pasa vacío porque `preparar_fiel()` ya desencripta
3. **Solo UNA solicitud SAT a la vez** — el SAT rechaza simultáneas
4. **Los JSON de datos NO van a git** (están en .gitignore)
5. **Los archivos se nombran `<serie>-<folio>.xml`** (sin número de línea)
6. **La numeración de línea se calcula al vuelo** en tabla y Excel
7. **Dev y prod usan la MISMA estructura de carpetas** — solo cambia la base
8. **En dev los JSON internos van a la raíz del proyecto**, en prod a `~/Documents/Vet Suite/`
9. **Los reportes visibles van SIEMPRE a `~/Documents/Contabilidad AAAA/`** (excepto Recordatorios que va a `~/Documents/Vet Suite/Reportes Recordatorios/`)

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

### Reglas
- Importación con detección por contenido + preview + merge
- Búsqueda sin acentos ni mayúsculas
- Notas separadas: cliente, transporte, estética
- ⚠️ en la tabla si hay notas en cualquier pestaña
- Cálculo de ruta con Haversine × 1.3 y velocidad 25 km/h

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
- `agenda_importada.json` — caché de citas
- `vacunas_importada.json` — caché de vacunas
- `historial_envios.json` — envíos por fecha
- `sucursales.json` — catálogo configurable
- `plantillas.json` — (futuro)

### Reglas
- Detección de tipo por columnas (no por nombre de archivo)
- Los emojis se preservan al copiar (van al portapapeles)
- Los emojis NO se muestran en Tk (se reemplazan por texto)
- El mensaje se regenera al cambiar de sucursal (solo los no enviados)

## Empaquetado
- Push de tag `v*` → GitHub Actions compila para Windows y macOS
- `requirements.txt` debe tener cada dependencia en línea separada
- `--collect-all cfdiclient` y `--collect-all lxml` en build.yml

## Estado actual
- ✅ Ingresos funcional
- ✅ Egresos: descarga, procesa, mueve, Excel
- ✅ Auto-clasificación de proveedores
- ✅ Manual integrado
- ✅ Empaquetado automático
- ✅ Estética y Transportes completo
- ✅ Recordatorios completo
- ⏳ Pendiente: pruebas con SAT real y cliente final

## Historial de versiones

### v2.1.0 (actual)
- Módulo **Recordatorios** completo
  - Importación de Excel de agenda y vacunas
  - Agrupación por cliente + teléfono
  - Generación de mensajes con formato profesional
  - Envío por WhatsApp (wa.me + portapapeles)
  - Historial de envíos
  - Catálogo de sucursales configurable
- Fix crash `espera_sat.py` (bad window path name)
- Fix de rutas: ingreso, egreso, estética y recordatorios separados por dominio
- Separación de `config_ui.json` (tema) y `ingresos/gmail_config.json` (correo)

### v2.0.0
- Renombrado a **Vet Suite** (antes "Sistema de Contabilidad QVET")
- Nueva arquitectura de rutas de datos en dev y prod:
  - Dev:  `<raíz proyecto>/{ingresos,egresos,estetica_transportes,recordatorios}/`
  - Prod: `~/Documents/Vet Suite/{ingresos,egresos,estetica_transportes,recordatorios}/`
- `lector_facturas.py` y `correo_facturas.py` movidos a `modulos/`
- Migración automática de config de Gmail
- Módulo **Estética y Transportes** funcional:
  - Importador inteligente con detección por contenido + preview + merge
  - Duplicados/basura con resolución interactiva
  - Catálogos editables
  - Notas separadas (cliente, transporte, estética)
  - Alertas ⚠️ cuando hay notas

### v1.0.1
- Ingresos y Egresos funcionales
- Empaquetado automático con GitHub Actions

## Pendientes / Deuda técnica

- [ ] **Refactor de estructura** (v3.0.0)
  - Separar por dominio funcional: `ingresos/`, `egresos/`, `estetica_transportes/`, `recordatorios/`
  - Cada dominio autocontenido (módulo + lógica + rutas + diálogos + tests)
  - `shared/` para código transversal
  - No hacer hasta que Recordatorios esté estable

- [ ] **Informe de recordatorios** (PDF/Excel)
  - Historial visual
  - Métricas de envío

- [ ] **Autocompletado en Estética**
  - Lista de nombres de clientes
  - Lista de razas