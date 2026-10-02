# Manual de Usuario — Sistema de Contabilidad QVET

**Versión:** 2.0.0  
**Última actualización:** Octubre 2026

---

## Índice

1. Introducción
2. Instalación
3. Configuración inicial
4. Flujo de trabajo diario (Ingresos)
5. Reclasificación de productos
6. Generación de Excel (Ingresos)
7. Reportes (Ingresos)
8. Adjuntos
9. Módulo de Egresos
10. Configuración avanzada
11. Solución de problemas
12. Preguntas frecuentes
13. Glosario

---

## 1. Introducción

### ¿Qué es el Sistema de Contabilidad QVET?

Aplicación de escritorio que automatiza la captura y el reporte de las facturas de QVET.

Tiene dos módulos:

- **Ingresos**: descarga facturas del correo Gmail, las procesa y genera el reporte mensual.
- **Egresos**: descarga facturas del SAT con tu e.firma, las procesa y genera los reportes PUE y PPD.

### ¿Para qué sirve?

Antes tenías que hacer todo a mano: abrir el correo, descargar XMLs, copiar datos, llenar Excel.

Ahora la app hace todo automáticamente. Tú solo:

1. Presionas un botón.
2. Revisas que todo esté bien.
3. Generas el Excel.

### Requisitos

Hardware:

- Windows 10 o superior.
- macOS 10.13 o superior.
- 4 GB de RAM mínimo.
- 200 MB de espacio libre.

Software:

- Cuenta de Gmail (para Ingresos).
- e.firma del SAT (.cer y .key) (para Egresos).

---

## 2. Instalación

### 2.1 Windows

1. Descarga el ZIP desde GitHub Releases.
2. Descomprime el archivo.
3. Doble clic en `SistemaIngresos.exe`.
4. Si Windows avisa, clic en "Más información" → "Ejecutar de todas formas".
5. Mueve la carpeta a un lugar fijo (no muevas solo el .exe).

### 2.2 macOS

1. Descarga el ZIP desde GitHub Releases.
2. Descomprime el archivo.
3. Arrastra `Sistema Ingresos.app` a Aplicaciones.
4. Clic derecho → Abrir.
5. Si macOS bloquea, ejecuta en Terminal:
   `xattr -cr "/Applications/Sistema Ingresos.app"`

### 2.3 Primer arranque

Al abrir la app por primera vez se crea automáticamente la carpeta de datos:

- Windows: `C:\Users\<usuario>\Documents\Contabilidad App\`
- macOS: `~/Documents/Contabilidad App/`

---

## 3. Configuración inicial

### 3.1 Conectar con Gmail (para Ingresos)

1. Genera una contraseña de aplicación en: https://myaccount.google.com/apppasswords
2. Abre la app, entra a Ingresos, clic en Sincronizar.
3. Si es la primera vez, llena:
   - Correo de Gmail
   - Contraseña de app (16 caracteres)
   - Etiqueta de Gmail (ej. FACTURAS BAALAK)
   - Filtro opcional
4. Clic en Guardar.

### 3.2 Configurar la e.firma (para Egresos)

1. Abre Egresos.
2. Clic en `⚙️ Configuración SAT`.
3. Llena:
   - RFC del receptor
   - Certificado (.cer)
   - Llave privada (.key)
   - Contraseña de la e.firma
4. Clic en Guardar.

La app convierte los archivos automáticamente. No tienes que hacer nada extra.

### 3.3 Elegir tema visual

1. En Ingresos, clic en Cambiar tema.
2. Elige un tema.
3. Aplicar y guardar.

Temas recomendados:

- darkly (oscuro)
- superhero (oscuro con azules)
- flatly (claro)

---

## 4. Flujo de trabajo diario (Ingresos)

### 4.1 Sincronizar facturas del correo

1. Clic en Sincronizar.
2. Elige modo:
   - "Solo correos NO leídos" (recomendado)
   - "Todos los correos"
   - "Editar configuración"
3. Espera mientras se descargan.
4. Cuando termina, elige:
   - "Procesar TODAS automáticamente" (recomendado)
   - "Solo guardar los archivos"
5. Revisa el resumen.

### 4.2 Leer facturas manualmente

1. Clic en Leer factura.
2. Selecciona el XML.
3. Selecciona el PDF (opcional).
4. Verifica el formulario.
5. Guardar.

### 4.3 El formulario

El formulario tiene secciones:

- GENERAL: No. Factura, QVET, Fecha, Nombre, RFC, Folio Fiscal.
- U (Alimentos): Importe e IVA.
- ACCESORIOS, MEDICAMENTOS, HIGIENE, ESTETICA, TRANSPORTE, PENSION, VACUNA, CLINICA.
- TOTAL (auto).
- TIPO DE PAGO: Efectivo, TC, TD, Cheque, Transferencia, Vale.

Si la suma de categorías no coincide con la de pagos, aparece una alerta roja.

### 4.4 Guardar registros

1. Verifica los datos.
2. Clic en Guardar.
3. El registro aparece en la tabla.

### 4.5 Ver adjuntos

1. Selecciona un registro.
2. Clic derecho → Ver adjuntos.
3. Doble clic en un archivo para abrirlo.

---

## 5. Reclasificación de productos

### 5.1 Productos huérfanos

Son productos que no están en el catálogo o que están mal clasificados.

La app te avisa con un diálogo y ofrece registrarlos.

### 5.2 El reclasificador

1. Clic en Reclasificar.
2. Busca el producto.
3. Filtra por categoría u origen.
4. Cambia la categoría.
5. Guardar.

### 5.3 Registrar productos nuevos

Desde el reclasificador:

1. Clic en "+ Nuevo producto".
2. Llena nombre y categoría.
3. Guardar.

---

## 6. Generación de Excel (Ingresos)

### 6.1 Cómo generar el resumen

1. Verifica el mes en la barra superior.
2. Clic en Generar Excel.
3. Decide según el caso:

Si el archivo NO existe: se crea automáticamente.

Si el archivo YA existe:

- "Sí" → Anexar solo los registros NUEVOS.
- "No" → Reordenar TODO (borra y regenera con backup).
- "Cancelar" → No hacer nada.

### 6.2 Anexar vs Reordenar

Anexar:

- Agrega solo los nuevos.
- Mantiene ediciones manuales.
- Rápido.

Reordenar:

- Borra el actual.
- Crea uno nuevo con todas las filas.
- Ordena por fecha y No. factura.
- Crea un backup antes.

### 6.3 Backups

Los backups se guardan en la misma carpeta como:

`<archivo>_backup_YYYY-MM-DD_HH-MM-SS.xlsx`

No se borran automáticamente. Puedes eliminarlos manualmente cuando ya no los necesites.

### 6.4 Recuperar un backup

1. Abre la carpeta del Excel.
2. Busca el archivo con `_backup_`.
3. Renómbralo quitando el `_backup_FECHA_HORA`.

---

## 7. Reportes (Ingresos)

1. Clic en Reportes.
2. Explorar el árbol:
   - 2026
     - Septiembre
       - Central
       - Prado
3. Doble clic en un nodo para ir al reporte.

---

## 8. Adjuntos

### 8.1 Ver adjuntos

Clic derecho → Ver adjuntos.

### 8.2 Adjuntar manualmente

Clic derecho → Adjuntar factura.

### 8.3 Abrir carpeta

Clic derecho → Ver adjuntos → Abrir carpeta.

---

## 9. Módulo de Egresos

### 9.1 ¿Qué es?

El módulo de Egresos descarga automáticamente las facturas de compra (CFDI recibidos) desde el SAT usando tu e.firma, las procesa y genera los reportes PUE y PPD en Excel.

A diferencia de Ingresos (que descarga del correo), Egresos se autentica directamente con el SAT.

### 9.2 Configurar la e.firma

Necesitas 3 cosas:

1. Archivo `.cer` — Certificado de la e.firma.
2. Archivo `.key` — Llave privada de la e.firma.
3. Contraseña de la e.firma.

Estos archivos los descargaste cuando tramitaste tu e.firma.

Pasos en la app:

1. Abre Egresos.
2. Clic en `⚙️ Configuración SAT`.
3. Llena RFC, certificado, llave y contraseña.
4. Clic en Guardar.

La app convierte los archivos automáticamente a un formato moderno. No tienes que hacer nada extra.

### 9.3 Descargar del SAT

Paso 1 — Clic en `📥 Descargar del SAT`.

Paso 2 — Elegir Año y Mes.

Paso 3 — Clic en Descargar.

Paso 4 — La app:

1. Se autentica con el SAT.
2. Envía la solicitud.
3. Abre la ventana de espera.

Paso 5 — Esperar.

El SAT procesa en cola. Puede tardar entre minutos y horas.

La ventana de espera muestra:

- Contador de tiempo transcurrido.
- Mensajes motivadores.
- Estado actual (En cola, En proceso, Terminada).
- Número de CFDIs encontrados.

Paso 6 — Cuando el SAT termina, la app automáticamente:

1. Descarga los paquetes (ZIPs).
2. Extrae los XML.
3. Procesa cada XML.
4. Guarda en el JSON del año.
5. Mueve los XML a PUE / PPD / Animalia.
6. Actualiza los números de línea.
7. Genera los Excel PUE y PPD.

#### Importante: solo una solicitud a la vez

El SAT solo permite **una solicitud activa por contribuyente**.

Si tienes una en proceso, el botón cambia a `🔄 Verificar solicitud pendiente`.

Si lleva más de 24 horas sin respuesta, el botón vuelve a `📥 Descargar del SAT` (probablemente expiró).

### 9.4 Esperar y verificar

Si cerraste la app mientras el SAT procesaba:

1. Abre Egresos de nuevo.
2. El botón dirá `🔄 Verificar solicitud`.
3. Clic para retomar la espera.

La app recuerda el `id_solicitud` y sigue verificando automáticamente.

### 9.5 Clasificar Animalia / Baalak

Por defecto, todas las facturas se asignan a **Baalak**.

Si tienes facturas de **Animalia**:

1. Clic en `🏢 Clasificar sucursal`.
2. Se abre la lista de facturas del año.
3. Cambia la sucursal con el combobox de cada fila.
4. Puedes filtrar por sucursal, emisor o folio.
5. Clic en `💾 Guardar clasificación`.

Las facturas marcadas como Animalia se **excluyen del Excel**.

### 9.6 Ver y editar registros

La tabla muestra los registros del mes/sucursal seleccionados.

#### Filtros

Arriba de la tabla:

- Sucursal: Baalak / Animalia.
- Año y Mes.
- Ver: **Todas / PUE / PPD**.

#### Editar un registro

1. Doble clic en una fila → abre el diálogo.
2. Cambia:
   - Sucursal
   - Método de pago (PUE/PPD)
   - Forma de pago
   - Observación
   - Folio
3. Clic en Guardar.

Los datos del SAT (UUID, RFC, emisor, fecha, total) **no se pueden editar**.

#### Eliminar un registro

1. Clic derecho en la fila → Eliminar.
2. Confirmar.

Se elimina el registro y su XML asociado.

#### Ver el XML

1. Clic derecho en la fila → Abrir carpeta del XML.

### 9.7 Generar Excel PUE/PPD

1. Verifica el mes en el selector.
2. Clic en `📊 Generar Excel`.
3. Se crean (o actualizan):
   - `RELACION FACTURAS PUE - [mes] [año].xlsx`
   - `RELACION FACTURAS PPD - [mes] [año].xlsx`

Los archivos van a:

`Documents/Contabilidad [año]/Contabilidad [mes]/Egreso/Deposito_Egreso/`

#### Anexar vs Reemplazar

Si el archivo **ya existe**:

- **Sí** → Reordenar TODO (crea backup antes).
- **No** → Ya existe, no hacer nada.
- **Cancelar** → Omitir.

El backup se guarda como:

`RELACION FACTURAS PUE - septiembre 2026_backup_2026-10-02_14-30-00.xlsx`

### 9.8 Reportes de Egresos

Clic en `📈 Reportes`. Se abre un árbol:
2026
├── Septiembre
│ ├── Baalak
│ └── Animalia
└── Octubre
├── Baalak
└── Animalia


Doble clic en cualquier nodo:

- Cambia los selectores.
- Refresca la tabla.
- Muestra totales del nodo.

### 9.9 Solución de problemas (Egresos)

#### Error 301 — XML Mal Formado

"Fecha final inválida"

Causa: intentaste descargar un período futuro.

Solución: elige un mes pasado o el actual.

#### Error 304 — Ya existe una solicitud

Causa: tienes una solicitud activa.

Solución: espera unos minutos, presiona `🔄 Verificar solicitud`, o espera a que expiren las 24 horas.

#### Mi solicitud lleva mucho tiempo en proceso

Es normal. El SAT está saturado.

Puede tardar desde minutos hasta horas.

Recomendación: cierra la app y vuelve más tarde. La solicitud sigue viva en el SAT.

#### Los totales del Excel no coinciden

Posibles causas:

1. Facturas de Animalia mal marcadas.
2. PUE/PPD mal clasificados.
3. Facturas sin descargar.

#### La app no encuentra los XML

Verifica que existan en `/tmp/sat_descargas/`.

Si no están, vuelve a descargar del SAT.

#### El botón dice "🔄 Verificar solicitud" pero ya expiró

La app limpia automáticamente las solicitudes con más de 24 horas.

Si no lo hace, ejecuta en Terminal:

```bash
python3 -c "from config.config_egresos import limpiar_solicitud_activa; limpiar_solicitud_activa(); print('Limpiada')"

9.10 Historial de Egresos
La app mantiene un historial de:

RFCs de emisores

Nombres de emisores

Observaciones usadas

Se guarda en:

~/Documents/Contabilidad App/historial_egresos.json

Se usa para autocompletar en los diálogos de edición.

10. Configuración avanzada
10.1 Cambiar tema
Ver sección 3.3.

10.2 Ver logs
Clic en Ver logs (Ingresos). Se abre la carpeta de logs.

10.3 Reset caché
Clic en Reset caché (Ingresos). Aparece confirmación.

11. Solución de problemas generales
11.1 La app no abre en Windows
Clic derecho → Ejecutar como administrador.

11.2 La app no abre en macOS
Ejecuta en Terminal:

xattr -cr "/Applications/Sistema Ingresos.app"

11.3 La sincronización falla
Causas posibles:

Sin internet.

Contraseña de app incorrecta.

Etiqueta de Gmail mal escrita.

Filtro muy estricto.

11.4 El Excel está bloqueado
Cierra Excel y vuelve a intentar.

11.5 Los totales no cuadran
Revisa el desglose por categoría o las facturas de Animalia.

12. Preguntas frecuentes

Dónde se guardan los datos?
Windows: C:\Users\<usuario>\Documents\Contabilidad App\

macOS: ~/Documents/Contabilidad App/

¿Cómo hago backup?
Copia la carpeta completa a un USB o la nube.

¿Puedo usar la app en varias computadoras?
Sí, pero los datos no se sincronizan. Copia manualmente la carpeta.

¿Qué pasa si cambio de año?
La app crea automáticamente un archivo nuevo.

¿Cómo actualizo la app?
Descarga la nueva versión.

Descomprime en una carpeta diferente.

Prueba que funcione.

Reemplaza la carpeta anterior.

NO borres la carpeta Contabilidad App.

¿Qué hago si la app se cierra sola?
Ábrela desde CMD/Terminal para ver el error.

¿Cuántas solicitudes al SAT puedo hacer?
Solo una a la vez por contribuyente. El SAT rechaza solicitudes simultáneas.

¿Dónde queda el historial de Egresos?
En ~/Documents/Contabilidad App/historial_egresos.json.

¿Puedo recuperar un Excel que reemplacé?
Sí. Los backups están en la misma carpeta con el nombre:

<archivo>_backup_YYYY-MM-DD_HH-MM-SS.xlsx

Renómbralo quitando el _backup_....

13. Glosario
Término	Significado
QVET	Sistema de gestión veterinaria.
CFDI	Comprobante Fiscal Digital por Internet.
XML	Archivo del CFDI.
PDF	Representación impresa del CFDI.
UUID	Identificador único del CFDI.
Folio Fiscal	Ver UUID.
RFC	Registro Federal de Contribuyentes.
IVA	Impuesto al Valor Agregado (16%).
IEPS	Impuesto Especial sobre Producción y Servicios.
Serie	Prefijo del folio.
Folio	Número consecutivo de la factura.
PUE	Pago en Una Exhibición.
PPD	Pago en Parcialidades o Diferido.
FIEL	Firma Electrónica Avanzada (e.firma).
.cer	Certificado de la e.firma.
.key	Llave privada de la e.firma.
Backup	Copia de seguridad.
Log	Registro de actividad.
Caché	Almacén temporal de datos.
Soporte
Si tienes problemas:

Revisa este manual primero.

Revisa los logs.

Contacta al desarrollador.

Fin del manual.

Versión: 2.0.0
Última actualización: Octubre 2026