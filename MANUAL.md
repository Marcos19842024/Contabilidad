# Manual de Usuario - Vet Suite

**Versión:** 2.2.0  
**Última actualización:** Octubre 2026

---

## Índice

1. Introducción
2. Instalación
3. Inicio de sesión y perfiles
4. Configuración inicial
5. Flujo de trabajo diario (Ingresos)
6. Reclasificación de productos
7. Generación de Excel (Ingresos)
8. Reportes (Ingresos)
9. Adjuntos
10. Módulo de Egresos
11. Módulo de Estética y Transportes
12. Módulo de Recordatorios
13. Administración del sistema
14. Configuración avanzada
15. Solución de problemas
16. Preguntas frecuentes
17. Glosario

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

### ¿Quién puede ver qué?

La app tiene **perfiles de trabajo**. Cada usuario entra con un perfil que
determina qué módulos ve:

| Perfil | Módulos visibles |
|--------|------------------|
| Administrador | Todos (Ingresos, Egresos, Estética, Recordatorios) + configuración |
| Contabilidad | Ingresos, Egresos |
| Almacén | Ingresos |
| Cajero | Estética y Transportes, Recordatorios |
| Médico | Recordatorios |

El administrador puede crear perfiles nuevos o modificar los existentes
(ver sección 13).

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

Al abrir la app por primera vez:

1. Se crea automáticamente la carpeta de datos:
   - Windows: `C:\Users\<usuario>\Documents\Vet Suite\`
   - macOS: `~/Documents/Vet Suite/`

2. Se crea un **usuario administrador** con una contraseña temporal
   aleatoria (ej. `TortugaZapato42`).

3. La app **muestra la contraseña UNA SOLA VEZ**, con un botón para
   copiarla al portapapeles.

4. Anota la contraseña en un lugar seguro y marca la casilla
   "Ya anoté la contraseña" para continuar.

> ⚠️ **Si cierras esa ventana sin marcar la casilla**, la app borra el
> administrador recién creado y vuelve a empezar en el siguiente arranque.
> Esto es para evitar dejar un usuario con contraseña que nadie conoce.

5. Después te pide iniciar sesión con `admin` y la contraseña temporal.

6. Una vez dentro, **cambia la contraseña** desde Configuración → Mi cuenta
   (ver sección 13).

---

## 3. Inicio de sesión y perfiles

### 3.1 Iniciar sesión

Al abrir la app, siempre pide usuario y contraseña:

1. **Usuario**: el nombre de usuario (minúsculas, sin espacios).
2. **Contraseña**.
3. Enter o clic en "Entrar".

Si los datos no coinciden, verás "Usuario o contraseña incorrectos". No
te dice cuál de los dos falló (por seguridad).

### 3.2 Cerrar sesión

En el panel lateral izquierdo, al pie:

`🚪 Cerrar sesión`

Vuelve al login sin cerrar la app. Útil si varias personas usan la misma
computadora con perfiles distintos.

### 3.3 Olvidé mi contraseña

No hay auto-recuperación. Pídele al **administrador** que te cambie la
contraseña desde Configuración → Usuarios (ver sección 13).

### 3.4 Mi cuenta (cambiar mi contraseña)

Cualquier usuario puede cambiar su propia contraseña:

1. Clic en **Mi cuenta** (o **Configuración** si eres admin) en el pie
   del panel lateral.
2. Pestaña **🔒 Mi cuenta**.
3. Escribe la contraseña actual, la nueva y su confirmación.
4. Clic en "Cambiar contraseña".

Reglas:

- La nueva debe tener **mínimo 8 caracteres**.
- La nueva no puede ser igual a la actual.
- La confirmación debe coincidir.

### 3.5 ¿Qué es un perfil?

Un **perfil** determina qué módulos puede ver un usuario. Por ejemplo:

- Un **cajero** solo ve Estética, Transportes y Recordatorios.
- Un **contador** solo ve Ingresos y Egresos.

El perfil no cambia lo que el usuario puede hacer con los datos: si un
usuario ve un módulo, puede usarlo completo. Si no lo ve, no existe para él.

### 3.6 ¿Qué pasa si me cambian el perfil?

El cambio aplica en el **próximo inicio de sesión**. La sesión activa
mantiene el perfil con el que entró. Esto evita cambios sorpresivos a
mitad de una tarea.

---

## 4. Configuración inicial

### 4.1 Conectar con Gmail (para Ingresos)

1. Genera una contraseña de aplicación en: https://myaccount.google.com/apppasswords
2. Abre la app, entra a Ingresos, clic en Sincronizar.
3. Si es la primera vez, llena:
   - Correo de Gmail
   - Contraseña de app (16 caracteres)
   - Etiqueta de Gmail (ej. FACTURAS BAALAK)
   - Filtro opcional
4. Clic en Guardar.

La config se guarda en `~/Documents/Vet Suite/ingresos/gmail_config.json`.

### 4.2 Configurar la e.firma (para Egresos)

1. Abre Egresos.
2. Clic en `⚙️ Configuración SAT`.
3. Llena:
   - RFC del receptor
   - Certificado (.cer)
   - Llave privada (.key)
   - Contraseña de la e.firma
4. Clic en Guardar.

La app convierte los archivos automáticamente. No tienes que hacer nada extra.

### 4.3 Elegir tema visual

Solo el **administrador** puede cambiar el tema:

1. En el panel lateral, clic en **Configuración**.
2. Pestaña **🎨 Apariencia**.
3. Elige un tema.
4. Aplicar y guardar.

Temas recomendados:

- darkly (oscuro)
- superhero (oscuro con azules)
- flatly (claro)

---

## 5. Flujo de trabajo diario (Ingresos)

### 5.1 Sincronizar facturas del correo

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

### 5.2 Leer facturas manualmente

1. Clic en Leer factura.
2. Selecciona el XML.
3. Selecciona el PDF (opcional).
4. La app procesa el XML y el PDF automáticamente.
5. El registro aparece en la tabla.

### 5.3 La tabla de registros

La tabla muestra:

- No. Factura, QVET, Fecha, Nombre, RFC.
- Total, Efectivo, TC, TD, Cheque, Transferencia.
- Folio Fiscal, Centro.
- Ícono 📎 si tiene adjuntos.

Los campos de categorías (U, ACCESORIOS, MEDICAMENTOS, HIGIENE, ESTETICA, TRANSPORTE, PENSION, VACUNA, CLINICA) **se guardan automáticamente** cuando procesas una factura, y se usan al generar el Excel.

### 5.4 Ver adjuntos y editar

1. Doble clic en un registro → abre el diálogo de edición.
2. Puedes:
   - Ver el XML y PDF adjuntos.
   - Editar campos editables (los datos del SAT no se pueden cambiar).
   - Eliminar el registro.
3. Guardar o cerrar.

### 5.5 Filtros

En la barra superior:

- Centro: Central / Prado.
- Año.
- Mes.

---

## 6. Reclasificación de productos

### 6.1 Productos huérfanos

Son productos que no están en el catálogo o que están mal clasificados.

La app te avisa con un diálogo y ofrece registrarlos.

### 6.2 El reclasificador

1. Clic en Reclasificar.
2. Busca el producto.
3. Filtra por categoría u origen.
4. Cambia la categoría.
5. Guardar.

### 6.3 Registrar productos nuevos

Desde el reclasificador:

1. Clic en "+ Nuevo producto".
2. Llena nombre y categoría.
3. Guardar.

---

## 7. Generación de Excel (Ingresos)

### 7.1 Cómo generar el resumen

1. Verifica el mes en la barra superior.
2. Clic en Generar Excel.
3. Decide según el caso:

Si el archivo NO existe: se crea automáticamente.

Si el archivo YA existe:

- "Sí" → Anexar solo los registros NUEVOS.
- "No" → Reordenar TODO (borra y regenera con backup).
- "Cancelar" → No hacer nada.

### 7.2 Anexar vs Reordenar

Anexar:

- Agrega solo los nuevos.
- Mantiene ediciones manuales.
- Rápido.

Reordenar:

- Borra el actual.
- Crea uno nuevo con todas las filas.
- Ordena por fecha y No. factura.
- Crea un backup antes.

### 7.3 Backups

Los backups se guardan en la misma carpeta como:

`<archivo>_backup_YYYY-MM-DD_HH-MM-SS.xlsx`

No se borran automáticamente. Puedes eliminarlos manualmente cuando ya no los necesites.

### 7.4 Recuperar un backup

1. Abre la carpeta del Excel.
2. Busca el archivo con `_backup_`.
3. Renómbralo quitando el `_backup_FECHA_HORA`.

---

## 8. Reportes (Ingresos)

1. Clic en Reportes.
2. Explorar el árbol:
   - 2026
     - Septiembre
       - Central
       - Prado
3. Doble clic en un nodo para ir al reporte.

---

## 9. Adjuntos

### 9.1 Ver adjuntos

Doble clic en un registro → pestaña de adjuntos.

### 9.2 Adjuntar manualmente

Clic derecho → Adjuntar factura.

### 9.3 Abrir carpeta

Clic derecho → Ver adjuntos → Abrir carpeta.

---

## 10. Módulo de Egresos

### 10.1 ¿Qué es?

El módulo de Egresos descarga automáticamente las facturas de compra (CFDI recibidos) desde el SAT usando tu e.firma, las procesa y genera los reportes PUE y PPD en Excel.

### 10.2 Configurar la e.firma

Necesitas 3 cosas:

1. Archivo `.cer` — Certificado de la e.firma.
2. Archivo `.key` — Llave privada de la e.firma.
3. Contraseña de la e.firma.

Pasos en la app:

1. Abre Egresos.
2. Clic en `⚙️ Configuración SAT`.
3. Llena RFC, certificado, llave y contraseña.
4. Clic en Guardar.

### 10.3 Probar la e.firma sin gastar solicitud

En `⚙️ Configuración SAT` hay un botón **🔑 Probar FIEL**.

- Prueba los valores **actuales del formulario** (aunque no los hayas
  guardado).
- No gasta solicitud al SAT (usa autenticación, no descarga).
- Muestra resultado en verde (éxito) o rojo (error).

Úsalo cuando cambies la e.firma o si sospechas que algo está mal antes
de lanzar una descarga completa.

### 10.4 Descargar del SAT

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

**Importante:** la descarga **NO genera el Excel**. Después de revisar la
tabla, tú decides cuándo generarlo (ver sección 10.7).

#### Importante: solo una solicitud a la vez

El SAT solo permite **una solicitud activa por contribuyente**.

Si tienes una en proceso, el botón cambia a `🔄 Verificar solicitud pendiente`.

Si lleva más de 24 horas sin respuesta, el botón vuelve a `📥 Descargar del SAT`.

### 10.5 Esperar y verificar

Si cerraste la app mientras el SAT procesaba:

1. Abre Egresos de nuevo.
2. El botón dirá `🔄 Verificar solicitud`.
3. Clic para retomar la espera.

La app recuerda el `id_solicitud` y sigue verificando automáticamente.

### 10.6 Clasificar Animalia / Baalak

Por defecto, todas las facturas se asignan a **Baalak**.

Si tienes facturas de **Animalia**:

1. Clic en `🏢 Clasificar sucursal`.
2. Se abre la lista de facturas del año.
3. Cambia la sucursal con el combobox de cada fila.
4. Puedes filtrar por sucursal, emisor o folio.
5. Clic en `💾 Guardar clasificación`.

Las facturas marcadas como Animalia se **excluyen del Excel**.

### 10.7 Ver y editar registros

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

### 10.8 Generar Excel PUE/PPD

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

### 10.9 Reportes de Egresos

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

### 10.10 Solución de problemas (Egresos)

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

## 11. Módulo de Estética y Transportes

### 11.1 ¿Qué es?

Módulo auxiliar para **determinar qué espacio dar en la agenda de QVET**.

Sirve para saber de antemano:

- Cuánto tarda un servicio de estética para cada mascota.
- Cuánto tarda un transporte a la ubicación del cliente.
- Qué características tiene la mascota (raza, carácter, precauciones).
- Qué servicios adicionales requiere (baño medicado, transporte, etc.).

Con eso puedes asignar un espacio en la agenda con información real en lugar de adivinar.

### 11.2 Datos que guarda

- **Cliente**: nombre, población, dirección, notas.
- **Transporte**: distancia, tiempo, tarifa, notas.
- **Mascotas**: nombre, raza, carácter, precauciones, notas.
- **Catálogos**: servicios de estética con duración, tarifas de transporte.

### 11.3 Importar clientes desde Excel

1. Clic en `📥 Importar Excel`.
2. Selecciona el Excel de clientes (debe tener columnas `CLIENTE`, `POBLACIÓN`, `DIRECCIÓN`).
3. La app detecta automáticamente el tipo de Excel.
4. Revisa el preview (cuántas filas).
5. Clic en Sí para importar.

**Solo importa los que no existan** (merge por nombre).

### 11.4 Buscar clientes

1. Escribe en el buscador (nombre, población, dirección o mascota).
2. La tabla filtra en vivo.
3. Doble clic en un cliente → abre el detalle con 4 pestañas.

### 11.5 Pestañas del detalle

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

### 11.6 Alertas ⚠️

Si un cliente tiene **notas en cualquier pestaña**, aparece un ⚠️ en la tabla principal.

### 11.7 Duplicados y basura

Clic en `⚠️ Duplicados / Basura`:

- **Duplicados**: elige con cuál te quedas.
- **Basura**: edita, elimina o restaura.

### 11.8 Catálogos editables

Clic en `📚 Catálogos`:

- **Servicios de estética**: código, descripción, precio, duración.
- **Tarifas de transporte**: código, precio.

Doble clic en un registro para editar.

---

## 12. Módulo de Recordatorios

### 12.1 ¿Qué es?

Envía recordatorios de **citas** y **vacunas** a tus clientes por WhatsApp.

**Requisitos:**

- WhatsApp Desktop instalado y vinculado a tu número.
- Los Excel de agenda y vacunas exportados de QVET.

### 12.2 Exportar los Excel desde QVET

1. En QVET, ve a la sección de agenda y exporta.
2. El archivo se descarga como `exportacion.xlsx` (o `exportacion(1).xlsx`).
3. Repite para vacunas.
4. NO importa cómo se llame el archivo, la app detecta el tipo por columnas.

### 12.3 Importar Excel

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

### 12.4 Tabs de Citas y Vacunas

Después de importar, verás 2 tabs:

- **Citas**: clientes agrupados por teléfono.
- **Vacunas**: clientes agrupados por teléfono y mascota.

Cada cliente tiene su **checkbox**:

- ⬜ Pendiente
- ✅ Enviado

### 12.5 Ver el mensaje

1. Clic en un cliente.
2. El mensaje aparece abajo.

### 12.6 Enviar por WhatsApp

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

### 12.7 Marcar y desmarcar

- `Marcar como enviado`: si ya enviaste el mensaje.
- `Desmarcar`: si te equivocaste.

### 12.8 Sucursales

Las sucursales **no se editan desde Recordatorios**. Se editan desde el
panel general de la app:

1. Panel lateral → **Configuración** (solo admin).
2. Pestaña **🏥 Veterinaria**.
3. Ahí se agregan, editan, eliminan y se marca la sucursal activa.

La sucursal activa determina el nombre que aparece en los mensajes de
Recordatorios y el origen de rutas en Estética.

### 12.9 Al cambiar de sucursal activa

Los mensajes de los clientes **no enviados** se regeneran con el nuevo nombre de sucursal.

Los mensajes **ya enviados** no cambian (para preservar el histórico).

### 12.10 Limpiar todo

Clic en `Limpiar todo`. Pide confirmación.

Borra todos los clientes importados y el historial de mensajes en pantalla.

### 12.11 Estadísticas

En la parte inferior de la ventana:

Citas: 14 (Enviados: 3 | Pendientes: 11)
Vacunas: 20 (Enviados: 8 | Pendientes: 12)


---

## 13. Administración del sistema

> Esta sección es **solo para el perfil Administrador**. Los demás
> perfiles no ven los tabs aquí descritos.

Todo se administra desde el panel lateral → **Configuración** →
pestañas 🎨 Apariencia, 🏥 Veterinaria, 🧩 Módulos, 🧑 Perfiles y 👥 Usuarios.

### 13.1 Usuarios

**Crear un usuario:**

1. Configuración → pestaña **👥 Usuarios**.
2. Clic en `+ Nuevo usuario`.
3. Llena:
   - **Usuario (login)**: minúsculas, sin espacios. Empieza con letra.
     Solo a-z, 0-9, _ (3–32 caracteres).
   - **Nombre completo**: como quieres que aparezca en pantalla.
   - **Perfil**: qué módulos verá.
   - **Usuario activo**: si puede iniciar sesión.
   - **Contraseña inicial**: se genera automáticamente. Puedes
     regenerarla (botón ↻), verla (botón 👁) o copiarla (📋).
4. Clic en **💾 Guardar**.

Al guardar, la app muestra la contraseña inicial **una sola vez** en un
mensaje. Anótala y entrégasela al usuario.

**Editar un usuario:**

- Doble clic en la fila.
- Cambia lo que necesites.
- **Dejar la contraseña en blanco** para no cambiarla.
- Escribir una nueva + su confirmación para cambiarla.
- Guardar.

**Eliminar un usuario:**

- Selecciona la fila.
- Clic en `🗑️ Eliminar`.
- Confirmar.

**Reglas de seguridad:**

- No puedes eliminar tu propia cuenta.
- No puedes eliminar ni desactivar al último administrador activo.
- No puedes eliminar un perfil que tenga usuarios asignados (ver 13.2).

**Desactivar un usuario:**

- Edítalo, desmarca "Usuario activo" y guarda.
- Un usuario inactivo no puede iniciar sesión, pero su cuenta sigue
  existiendo (útil si va a volver).

### 13.2 Perfiles

**Ver los perfiles:**

Configuración → pestaña **🧑 Perfiles**.

La tabla muestra cada perfil y qué módulos ve. El perfil **Administrador
es intocable**: siempre existe, siempre ve todo y no se puede editar ni
eliminar.

**Crear un perfil:**

1. Clic en `+ Nuevo perfil`.
2. Llena:
   - **ID del perfil**: minúsculas, sin espacios (ej. `veterinario`).
     No se puede cambiar después.
   - **Nombre visible**: como quieres que aparezca en la tabla (ej.
     "Veterinario").
   - **Descripción**: opcional.
   - **Módulos visibles**: marca los que verá este perfil.
3. Guardar.

**Editar un perfil:**

- Doble clic en la fila.
- Cambia nombre, descripción o módulos.
- El **ID** no se puede cambiar (es la clave que usan los usuarios).
- Guardar.

**Eliminar un perfil:**

- Selecciona la fila.
- `🗑️ Eliminar`.
- Si el perfil tiene usuarios asignados, la app **rechaza** la operación
  y muestra la lista de usuarios. Reasígnalos a otro perfil primero.

**Ejemplos de perfiles:**

| ID | Nombre | Módulos |
|----|--------|---------|
| admin | Administrador | Todos (intocable) |
| contabilidad | Contabilidad | Ingresos, Egresos |
| almacen | Almacén | Ingresos |
| cajero | Cajero | Estética y Transportes, Recordatorios |
| medico | Médico | Recordatorios |

### 13.3 Módulos (activar/desactivar)

Configuración → pestaña **🧩 Módulos**.

Cada módulo tiene un interruptor. Los desactivados **no aparecen en el
panel lateral**, aunque el perfil los permita. Útil para ocultar un
módulo temporalmente sin tocar los perfiles.

La visibilidad final de un módulo es:

    visible = activo (config)  Y  permitido por el perfil

Ejemplo: si desactivas Egresos, nadie lo ve (ni el admin), aunque su
perfil lo tenga marcado.

### 13.4 Sucursales

Configuración → pestaña **🏥 Veterinaria**.

Aquí se administran las sucursales del negocio:

- **+ Nueva**: agregar una sucursal.
- **✏️ Editar**: cambiar nombre, dirección, teléfono, coordenadas.
- **🗑️ Eliminar**: solo si no es la activa.
- **● Marcar como activa**: la sucursal que se usa como origen de rutas
  en Estética y como emisor en Recordatorios.

La sucursal activa se marca con **●**.

### 13.5 Cambiar mi propia contraseña

Ver sección 3.4.

---

## 14. Configuración avanzada

### 14.1 Cambiar tema

Solo admin. Configuración → pestaña **🎨 Apariencia**.

### 14.2 Ver logs

Clic en `Ver logs` (Ingresos). Se abre la carpeta de logs.

### 14.3 Reset caché

Clic en `Reset caché` (Ingresos). Aparece confirmación.

---

## 15. Solución de problemas generales

### 15.1 La app no abre en Windows

Clic derecho → Ejecutar como administrador.

### 15.2 La app no abre en macOS

Ejecuta en Terminal:

`xattr -cr "/Applications/Vet Suite.app"`

### 15.3 No puedo iniciar sesión

- Verifica que el usuario esté escrito en minúsculas y sin espacios.
- Verifica que el teclado no esté en mayúsculas.
- Si olvidaste la contraseña, contacta al administrador.

### 15.4 No veo un módulo que debería ver

Tres causas posibles:

1. **Tu perfil no lo permite.** Pídele al admin que revise tu perfil.
2. **El módulo está desactivado globalmente.** El admin lo puede activar
   desde Configuración → 🧩 Módulos.
3. **Hay un cambio pendiente.** Los cambios de perfil aplican al siguiente
   inicio de sesión. Cierra sesión y vuelve a entrar.

### 15.5 La sincronización falla

Causas posibles:

- Sin internet.
- Contraseña de app incorrecta.
- Etiqueta de Gmail mal escrita.
- Filtro muy estricto.

### 15.6 El Excel está bloqueado

Cierra Excel y vuelve a intentar.

### 15.7 WhatsApp no abre el chat

Verifica:

1. Que WhatsApp Desktop esté instalado.
2. Que esté vinculado con tu número.
3. Que el enlace `wa.me` esté asociado a WhatsApp Desktop (Settings → Default Apps).

### 15.8 Los emojis no se ven en la app

Tkinter (la librería gráfica) no renderiza emojis de forma nativa. Es normal.

**Los emojis SÍ se ven correctamente en WhatsApp** cuando pegas el mensaje.

---

## 16. Preguntas frecuentes

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

### ¿Qué pasa si olvido mi contraseña?

Contacta al administrador. Él puede cambiarla desde Configuración → Usuarios.

### ¿Puedo tener varias sesiones abiertas al mismo tiempo?

No. Cada instalación de la app mantiene una sesión activa. Si quieres
cambiar de usuario, cierra sesión primero.

### ¿Los usuarios pueden ver los datos de otros módulos?

No. Cada usuario solo ve los módulos de su perfil. Lo que no ve, no
existe para él. Además, cada usuario ve todos los datos del módulo que
tiene permitido (no hay restricción por usuario dentro de un módulo).

### ¿Puedo crear más administradores?

Sí. Crea un usuario nuevo y asígnale el perfil `admin`. El sistema solo
bloquea eliminarlo si sería el último admin activo.

---

## 17. Glosario

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
| Perfil | Conjunto de módulos que puede ver un usuario. |
| Sesión | Estado activo de un usuario tras iniciar sesión. |
| Administrador | Usuario con acceso total a la app y su configuración. |

---

## Soporte

Si tienes problemas:

1. Revisa este manual primero.
2. Revisa los logs.
3. Contacta al desarrollador.

---

**Fin del manual.**

**Versión:** 2.2.0  
**Última actualización:** Octubre 2026