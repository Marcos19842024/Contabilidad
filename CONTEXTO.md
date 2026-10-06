# Contexto del Proyecto - Sistema de Contabilidad QVET

## Stack
- Python 3.13
- tkinter + ttkbootstrap
- openpyxl, cfdiclient, pyinstaller
- Empaquetado automático con GitHub Actions (tags `v*`)

## Módulos
- **INGRESOS**: descarga de Gmail, procesa XML+PDF, genera Excel
- **EGRESOS**: descarga del SAT, procesa, clasifica, genera Excel PUE/PPD

## Estructura de datos

/Documents/Contabilidad App/
├── config_egresos.json (FIEL)
├── historial_egresos.json (emisores únicos)
├── solicitud_sat_activa.json (id de solicitud en curso)
└── registros_egresos_YYYY.json (registros del año)

/Documents/Contabilidad 2026/Contabilidad [mes]/Egreso/
└── [Baalak|Animalia]/[PUE|PPD]/[Efectivo|TC|TD|Transferencia|PPD]/
├── S1-1234.xml
└── S1-1234.PDF


## Archivos clave
| Archivo | Propósito |
|---------|-----------|
| `modulos/ingresos.py` | Módulo Ingresos |
| `modulos/egresos.py` | Módulo Egresos |
| `sat/descarga.py` | Descarga SAT (cfdiclient) |
| `sat/conversion.py` | Conversión FIEL (NO TOCAR) |
| `sat/procesar_completo.py` | Procesa XMLs y genera Excel |
| `sat/mover_egresos.py` | Mueve y renombra XMLs |
| `dialogos/descargar_sat.py` | Diálogo de descarga |
| `dialogos/egresos_editar.py` | Edita registro + adjuntos |
| `dialogos/adjuntos.py` | Ver adjuntos (Ingresos) |
| `lector_facturas.py` | Parser PDF/XML + agrupado |
| `excel/egresos.py` | Genera Excel PUE/PPD |
| `MANUAL.md` | Manual del usuario v2.0 |

## Reglas importantes
1. **NO tocar `sat/conversion.py`** — la conversión de FIEL usa openssl 1.1.1
2. **NO tocar el password de `Fiel()`** — se pasa vacío porque `preparar_fiel()` ya desencripta
3. **Solo UNA solicitud SAT a la vez** — el SAT rechaza simultáneas
4. **Los JSON de datos NO van a git** (están en .gitignore)
5. **Los archivos se nombran `<serie>-<folio>.xml`** (sin número de línea)
6. **La numeración de línea se calcula al vuelo** en tabla y Excel

## Empaquetado
- Push de tag `v*` → GitHub Actions compila para Windows y macOS
- `requirements.txt` debe tener cada dependencia en línea separada
- `--collect-all cfdiclient` y `--collect-all lxml` en build.yml (archivos de datos)

## Estado actual
- ✅ Ingresos funcional
- ✅ Egresos: descarga, procesa, mueve, Excel
- ✅ Auto-clasificación de proveedores
- ✅ Manual integrado
- ✅ Empaquetado automático
- ⏳ Pendiente: prueba con SAT real

## Últimos commits
- v3.1.8: fix requirements.txt (pyinstaller + cfdiclient separados)
- v3.1.7: agregar cfdiclient a requirements.txt
- v3.1.6: --collect-all cfdiclient y lxml