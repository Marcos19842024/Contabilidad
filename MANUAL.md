# Manual de Usuario - Vet Suite

**Versión:** 2.1.0  
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
10. Módulo de Estética y Transportes
11. Módulo de Recordatorios
12. Configuración avanzada
13. Solución de problemas
14. Preguntas frecuentes
15. Glosario

---

## 1. Introducción

### ¿Qué es Vet Suite?

Aplicación de escritorio que automatiza la contabilidad, la gestión de clientes y los recordatorios de la veterinaria.

Tiene **cuatro módulos**:

- **Ingresos**: descarga facturas del correo Gmail, las procesa y genera el reporte mensual.
- **Egresos**: descarga facturas del SAT con tu e.firma, las procesa y genera los reportes PUE y PPD.
- **Estética y Transportes**: gestiona clientes, mascotas, rutas y tarifas para agendar servicios.
- **Recordatorios**: envía recordatorios de citas y vacunas por WhatsApp.

### ¿Para qué sirve?

**Contabilidad:** antes tenías que hacer todo a mano (abrir correo, descargar XMLs, copiar datos, llenar Excel). Ahora la app lo hace automáticamente.

**Operaciones:** la app te ayuda a saber cuánto tiempo ocupa una estética o un transporte, y a enviar recordatorios a los clientes sin trabajo manual.

### Requisitos

Hardware:

- Windows 10 o superior.
- macOS 10.13 o superior.
- 4 GB de RAM mínimo.
- 200 MB de espacio libre.

Software:

- Cuenta de Gmail (para Ingresos).
- e.firma del SAT (.cer y .key) (para Egresos).
- WhatsApp Desktop instalado (recomendado para Recordatorios).

---

## 2. Instalación

### 2.1 Windows

1. Descarga el ZIP desde GitHub Releases.
2. Descomprime el archivo.
3. Doble clic en `VetSuite.exe`.
4. Si Windows avisa, clic en "Más información" → "Ejecutar de todas formas".
5. Mueve la carpeta a un lugar fijo (no muevas solo el .exe).

### 2.2 macOS

1. Descarga el ZIP desde GitHub Releases.
2. Descomprime el archivo.
3. Arrastra `Vet Suite.app` a Aplicaciones.
4. Clic derecho → Abrir.
5. Si macOS bloquea, ejecuta en Terminal:
   `xattr -cr "/Applications/Vet Suite.app"`

### 2.3 Primer arranque

Al abrir la app por primera vez se crea automáticamente la carpeta de datos:

- Windows: `C:\Users\<usuario>\Documents\Vet Suite\`
- macOS: `~/Documents/Vet Suite/`

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

La config se guarda en `~/Documents/Vet Suite/ingresos/gmail_config.json`.

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

1. En la pantalla principal, clic en `⚙️ Configuración`.
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
4. La app procesa el XML y el PDF automáticamente.
5. El registro aparece en la tabla.

### 4.3 La tabla de registros

La tabla muestra:

- No. Factura, QVET, Fecha, Nombre, RFC.
- Total, Efectivo, TC, TD, Cheque, Transferencia.
- Folio Fiscal, Centro.
- Ícono 📎 si tiene adjuntos.

Los campos de categorías (U, ACCESORIOS, MEDICAMENTOS, HIGIENE, ESTETICA, TRANSPORTE, PENSION, VACUNA, CLINICA) **se guardan automáticamente** cuando procesas una factura, y se usan al generar el Excel.

### 4.4 Ver adjuntos y editar

1. Doble clic en un registro → abre el diálogo de edición.
2. Puedes:
   - Ver el XML y PDF adjuntos.
   - Editar campos editables (los datos del SAT no se pueden cambiar).
   - Eliminar el registro.
3. Guardar o cerrar.

### 4.5 Filtros

En la barra superior:

- Centro: Central / Prado.
- Año.
- Mes.

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

Doble clic en un registro → pestaña de adjuntos.

### 8.2 Adjuntar manualmente

Clic derecho → Adjuntar factura.

### 8.3 Abrir carpeta

Clic derecho → Ver adjuntos → Abrir carpeta.

---

## 9. Módulo de Egresos

### 9.1 ¿Qué es?

El módulo de Egresos descarga automáticamente las facturas de compra (CFDI recibidos) desde el SAT usando tu e.firma, las procesa y genera los reportes PUE y PPD en Excel.

### 9.2 Configurar la e.firma

Necesitas 3 cosas:

1. Archivo `.cer` — Certificado de la e.firma.
2. Archivo `.key` — Llave privada de la e.firma.
3. Contraseña de la e.firma.

Pasos en la app:

1. Abre Egresos.
2. Clic en `⚙️ Configuración SAT`.
3. Llena RFC, certificado, llave y contraseña.
4. Clic en Guardar.

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

Si lleva más de 24 horas sin respuesta, el botón vuelve a `📥 Descargar del SAT`.

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

### 9.8 Reportes de Egresos

Clic en `📈 Reportes`. Se abre un árbol:

    2026
    ├── Septiembre
    │   ├── Baalak
    │   └── Animalia
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

Recomendación: cierra la app y vuelve más tarde.

---

## 10. Módulo de Estética y Transportes

### 10.1 ¿Qué es?

Módulo auxiliar para **determinar qué espacio dar en la agenda de QVET**.

Sirve para saber de antemano:

- Cuánto tarda un servicio de estética para cada mascota.
- Cuánto tarda un transporte a la ubicación del cliente.
- Qué características tiene la mascota (raza, carácter, precauciones).
- Qué servicios adicionales requiere (baño medicado, transporte, etc.).

Con eso puedes asignar un espacio en la agenda con información real en lugar de adivinar.

### 10.2 Datos que guarda

- **Cliente**: nombre, población, dirección, notas.
- **Transporte**: distancia, tiempo, tarifa, notas.
- **Mascotas**: nombre, raza, carácter, precauciones, notas.
- **Catálogos**: servicios de estética con duración, tarifas de transporte.

### 10.3 Importar clientes desde Excel

1. Clic en `📥 Importar Excel`.
2. Selecciona el Excel de clientes (debe tener columnas `CLIENTE`, `POBLACIÓN`, `DIRECCIÓN`).
3. La app detecta automáticamente el tipo de Excel.
4. Revisa el preview (cuántas filas).
5. Clic en Sí para importar.

**Solo importa los que no existan** (merge por nombre).

### 10.4 Buscar clientes

1. Escribe en el buscador (nombre, población, dirección o mascota).
2. La tabla filtra en vivo.
3. Doble clic en un cliente → abre el detalle con 4 pestañas.

### 10.5 Pestañas del detalle

**Datos:**
- Nombre, población, dirección.
- Notas del cliente.

**Transporte:**
- Latitud / Longitud (botón de geocodificación automática).
- Distancia y tiempo (botón "Calcular ruta").
- Tarifa (combobox con el catálogo).
- Notas de transporte.

**Estética / Mascotas:**
- Lista de mascotas.
- Doble clic para editar.
- Botón "+ Agregar mascota".
- Notas de estética (a nivel cliente).

**Historial (en construcción).**

### 10.6 Alertas ⚠️

Si un cliente tiene **notas en cualquier pestaña**, aparece un ⚠️ en la tabla principal.

### 10.7 Duplicados y basura

Clic en `⚠️ Duplicados / Basura`:

- **Duplicados**: elige con cuál te quedas.
- **Basura**: edita, elimina o restaura.

### 10.8 Catálogos editables

Clic en `📚 Catálogos`:

- **Servicios de estética**: código, descripción, precio, duración.
- **Tarifas de transporte**: código, precio.

Doble clic en un registro para editar.

---

## 11. Módulo de Recordatorios

### 11.1 ¿Qué es?

Envía recordatorios de **citas** y **vacunas** a tus clientes por WhatsApp.

**Requisitos:**

- WhatsApp Desktop instalado y vinculado a tu número.
- Los Excel de agenda y vacunas exportados de QVET.

### 11.2 Exportar los Excel desde QVET

1. En QVET, ve a la sección de agenda y exporta.
2. El archivo se descarga como `exportacion.xlsx` (o `exportacion(1).xlsx`).
3. Repite para vacunas.
4. NO importa cómo se llame el archivo, la app detecta el tipo por columnas.

### 11.3 Importar Excel

1. Clic en `📥 Importar Excel`.
2. Selecciona 1 o más Excel (con Ctrl+clic).
3. La app detecta el tipo de cada uno.
4. Revisa el resumen.
5. Clic en Sí.

**Cada Excel debe tener las siguientes columnas:**

**Citas:**
`FECHA | INICIO | TIPO VISITA | PROPIETARIO | MASCOTA | TELÉFONO | ASUNTO | AGENDA | ESTADO`

**Vacunas:**
`CLIENTE | TELÉFONO 1 | MASCOTA | TIPO DE RECORDATORIO | VACUNA | PRÓXIMA FECHA`

### 11.4 Tabs de Citas y Vacunas

Después de importar, verás 2 tabs:

- **Citas**: clientes agrupados por teléfono.
- **Vacunas**: clientes agrupados por teléfono y mascota.

Cada cliente tiene su **checkbox**:

- ⬜ Pendiente
- ✅ Enviado

### 11.5 Ver el mensaje

1. Clic en un cliente.
2. El mensaje aparece abajo.

### 11.6 Enviar por WhatsApp

1. Selecciona un cliente.
2. Clic en `Enviar por WhatsApp`.
3. La app:
   - Copia el mensaje al portapapeles.
   - Abre WhatsApp Desktop con el chat del cliente.
4. En WhatsApp:
   - Pega el mensaje con **Cmd+V** (Mac) o **Ctrl+V** (Windows).
   - Presiona **Enter**.
5. Vuelve a la app.
6. La app te pregunta: **"¿Ya enviaste?"**
7. Clic en Sí → se marca como enviado.

**Ventaja:** los emojis se preservan al pegar, y usas tu número actual.

### 11.7 Marcar y desmarcar

- `Marcar como enviado`: si ya enviaste el mensaje.
- `Desmarcar`: si te equivocaste.

### 11.8 Sucursales

Clic en `Configurar sucursales`:

- Agregar una sucursal nueva.
- Editar existentes.
- Activar/desactivar.

La sucursal activa determina el nombre que aparece en los mensajes.

### 11.9 Al cambiar de sucursal

Los mensajes de los clientes **no enviados** se regeneran con el nuevo nombre de sucursal.

Los mensajes **ya enviados** no cambian (para preservar el histórico).

### 11.10 Limpiar todo

Clic en `Limpiar todo`. Pide confirmación.

Borra todos los clientes importados y el historial de mensajes en pantalla.

### 11.11 Estadísticas

En la parte inferior de la ventana:

Citas: 14 (Enviados: 3 | Pendientes: 11)
Vacunas: 20 (Enviados: 8 | Pendientes: 12)


---

## 12. Configuración avanzada

### 12.1 Cambiar tema

En la pantalla principal, clic en `⚙️ Configuración`.

### 12.2 Ver logs

Clic en `Ver logs` (Ingresos). Se abre la carpeta de logs.

### 12.3 Reset caché

Clic en `Reset caché` (Ingresos). Aparece confirmación.

---

## 13. Solución de problemas generales

### 13.1 La app no abre en Windows

Clic derecho → Ejecutar como administrador.

### 13.2 La app no abre en macOS

Ejecuta en Terminal:

`xattr -cr "/Applications/Vet Suite.app"`

### 13.3 La sincronización falla

Causas posibles:

- Sin internet.
- Contraseña de app incorrecta.
- Etiqueta de Gmail mal escrita.
- Filtro muy estricto.

### 13.4 El Excel está bloqueado

Cierra Excel y vuelve a intentar.

### 13.5 WhatsApp no abre el chat

Verifica:

1. Que WhatsApp Desktop esté instalado.
2. Que esté vinculado con tu número.
3. Que el enlace `wa.me` esté asociado a WhatsApp Desktop (Settings → Default Apps).

### 13.6 Los emojis no se ven en la app

Tkinter (la librería gráfica) no renderiza emojis de forma nativa. Es normal.

**Los emojis SÍ se ven correctamente en WhatsApp** cuando pegas el mensaje.

---

## 14. Preguntas frecuentes

### ¿Dónde se guardan los datos?

- Windows: `C:\Users\<usuario>\Documents\Vet Suite\`
- macOS: `~/Documents/Vet Suite/`

### ¿Cómo hago backup?

Copia la carpeta completa a un USB o la nube.

### ¿Puedo usar la app en varias computadoras?

Sí, pero los datos no se sincronizan. Copia manualmente la carpeta.

### ¿Qué pasa si cambio de año?

La app crea automáticamente un archivo nuevo.

### ¿Cómo actualizo la app?

1. Descarga la nueva versión.
2. Descomprime en una carpeta diferente.
3. Prueba que funcione.
4. Reemplaza la carpeta anterior.

NO borres la carpeta `Vet Suite`.

### ¿Qué hago si la app se cierra sola?

Ábrela desde CMD/Terminal para ver el error.

### ¿Cuántas solicitudes al SAT puedo hacer?

Solo una a la vez por contribuyente.

### ¿Puedo recuperar un Excel que reemplacé?

Sí. Los backups están en la misma carpeta con el nombre:

`<archivo>_backup_YYYY-MM-DD_HH-MM-SS.xlsx`

### ¿Puedo enviar varios recordatorios a la vez?

Sí. Selecciona uno, envía, confirma, y pasa al siguiente. El flujo es rápido (~5 segundos por mensaje).

### ¿Qué pasa si cambio el nombre de la sucursal?

Los mensajes nuevos usan el nuevo nombre. Los ya enviados no cambian.

---

## 15. Glosario

| Término | Significado |
|---------|-------------|
| QVET | Sistema de gestión veterinaria. |
| CFDI | Comprobante Fiscal Digital por Internet. |
| XML | Archivo del CFDI. |
| PDF | Representación impresa del CFDI. |
| UUID | Identificador único del CFDI. |
| Folio Fiscal | Ver UUID. |
| RFC | Registro Federal de Contribuyentes. |
| IVA | Impuesto al Valor Agregado (16%). |
| IEPS | Impuesto Especial sobre Producción y Servicios. |
| Serie | Prefijo del folio. |
| Folio | Número consecutivo de la factura. |
| PUE | Pago en Una Exhibición. |
| PPD | Pago en Parcialidades o Diferido. |
| FIEL | Firma Electrónica Avanzada (e.firma). |
| .cer | Certificado de la e.firma. |
| .key | Llave privada de la e.firma. |
| Backup | Copia de seguridad. |
| Log | Registro de actividad. |
| Caché | Almacén temporal de datos. |
| Geocodificación | Obtener coordenadas desde una dirección. |
| wa.me | Enlace oficial de WhatsApp para abrir un chat. |

---

## Soporte

Si tienes problemas:

1. Revisa este manual primero.
2. Revisa los logs.
3. Contacta al desarrollador.

---

**Fin del manual.**

**Versión:** 2.1.0  
**Última actualización:** Octubre 2026