
**El bloque ```bash``` interno rompe el bloque ```markdown``` externo.**

## 🛠️ Solución

Voy a **quitar los bloques de código internos** y dejar el comando como **texto normal** con formato de código inline (backticks simples).

## 📖 Manual corregido — sin bloques anidados

**Borra todo** el contenido de `MANUAL.md` y pega este:

```markdown
# 📖 Manual de Usuario — Sistema de Contabilidad QVET

**Versión:** 1.0.0  
**Última actualización:** Septiembre 2026

---

## 📑 Índice

1. Introducción
2. Instalación
3. Configuración inicial
4. Flujo de trabajo diario
5. Reclasificación de productos
6. Generación de Excel
7. Reportes
8. Adjuntos
9. Configuración avanzada
10. Solución de problemas
11. Preguntas frecuentes
12. Glosario

---

## 1. Introducción

### ¿Qué es el Sistema de Contabilidad QVET?

Es una aplicación de escritorio que automatiza la captura y el reporte de las facturas de ingresos de QVET.

La app:

- Descarga automáticamente los XML y PDF de las facturas desde tu correo de Gmail.
- Lee los datos de cada factura (RFC, importe, IVA, etc.).
- Clasifica los productos por categoría (medicamentos, alimentos, servicios, etc.).
- Genera el reporte mensual en Excel, listo para el contador.

### ¿Para qué sirve?

Antes, tenías que:

1. Abrir el correo.
2. Descargar los XML y PDF de cada factura.
3. Abrir cada uno para copiar los datos.
4. Llenar un Excel a mano.
5. Verificar que todo cuadrara.

Ahora, la app hace todo eso automáticamente. Tú solo:

1. Presionas un botón (Sincronizar).
2. Revisas que todo esté bien.
3. Generas el Excel.
4. Listo.

### Requisitos

Hardware:

- Windows 10 o superior (recomendado).
- macOS 10.13 o superior.
- 4 GB de RAM mínimo.
- 200 MB de espacio libre.

Software:

- Cuenta de Gmail.
- Contraseña de aplicación de Google (te explico cómo generarla).

Conocimientos:

- Manejo básico de Windows o macOS.
- Saber usar Excel.

---

## 2. Instalación

### 2.1 Windows

Paso 1 — Descargar

1. Abre el navegador.
2. Ve a: https://github.com/Marcos19842024/Contabilidad/releases/latest
3. Busca el archivo "Sistema Ingresos vX.X.X - Windows.zip".
4. Clic para descargar.

Paso 2 — Descomprimir

1. Abre el Explorador de archivos.
2. Ve a la carpeta Descargas.
3. Clic derecho en el .zip → Extraer todo...
4. Clic en Extraer.

Paso 3 — Ejecutar

1. Dentro de la carpeta, busca SistemaIngresos.exe.
2. Doble clic para ejecutar.
3. Si Windows muestra un aviso ("Windows protegió tu PC"):
   - Clic en Más información.
   - Clic en Ejecutar de todas formas.

Paso 4 — Mover a un lugar fijo (recomendado)

1. Mueve la carpeta completa a un lugar permanente.
2. Crea un acceso directo:
   - Clic derecho en SistemaIngresos.exe.
   - Enviar a → Escritorio (crear acceso directo).

Importante: no muevas solo el .exe. Necesita la carpeta `_internal` a su lado.

### 2.2 macOS

Paso 1 — Descargar

1. Abre el navegador.
2. Ve a: https://github.com/Marcos19842024/Contabilidad/releases/latest
3. Busca el archivo "Sistema Ingresos vX.X.X - macOS.zip".
4. Clic para descargar.

Paso 2 — Descomprimir

1. Abre Finder.
2. Ve a Descargas.
3. Doble clic en el .zip.

Paso 3 — Instalar

1. Arrastra "Sistema Ingresos.app" a Aplicaciones.
2. Clic derecho en "Sistema Ingresos.app".
3. Selecciona Abrir.
4. Clic en Abrir en el diálogo.

Si macOS la bloquea:

Abre Terminal y ejecuta este comando:

`xattr -cr "/Applications/Sistema Ingresos.app"`

Luego doble clic para abrir.

### 2.3 Primer arranque

Cuando abras la app por primera vez:

1. Verás la ventana principal con la barra lateral.
2. Se crea automáticamente una carpeta de datos:
   - Windows: `C:\Users\<tu_usuario>\Documents\Contabilidad App\`
   - macOS: `~/Documents/Contabilidad App/`

---

## 3. Configuración inicial

### 3.1 Conectar con Gmail

Paso 1 — Generar contraseña de aplicación

1. Abre: https://myaccount.google.com/apppasswords
2. Inicia sesión con tu cuenta de Gmail.
3. En "Nombre de la aplicación", escribe: Sistema Ingresos
4. Clic en Crear.
5. Google te mostrará una contraseña de 16 caracteres.
6. Cópiala (sin espacios).

Importante: guárdala en un lugar seguro. Solo se muestra una vez.

Paso 2 — Configurar en la app

1. Abre la app.
2. En la barra lateral, clic en Sincronizar.
3. Si es la primera vez, se abre el diálogo Configuración de Gmail.
4. Llena los campos:
   - Correo de Gmail: tu correo completo.
   - Contraseña de app: la contraseña de 16 caracteres.
   - Etiqueta de Gmail: el nombre de la etiqueta (ej. FACTURAS BAALAK).
   - Filtrar por remitente: opcional (ej. qvet).
   - Correos de los últimos (días): 30.
5. Clic en Guardar.

### 3.2 ¿Qué es la etiqueta de Gmail?

Es una carpeta dentro de tu Gmail donde se guardan los correos de QVET con las facturas.

Cómo crearla:

1. Abre Gmail.
2. En la barra lateral izquierda, clic en + Crear etiqueta nueva.
3. Ponle un nombre: FACTURAS BAALAK.
4. Clic en Crear.

Cómo hacer que los correos lleguen ahí:

1. En Gmail, busca correos de QVET.
2. Crea un filtro:
   - Clic en el ícono de filtros.
   - En "De", escribe el correo de QVET.
   - Clic en Crear filtro.
   - Marca "Aplicar la etiqueta".
   - Clic en Crear filtro.

### 3.3 Elegir tema visual

1. En la barra lateral, clic en Cambiar tema.
2. Clic en un tema → verás la previsualización.
3. Aplicar y guardar.

Temas recomendados:

- darkly (oscuro).
- superhero (oscuro con azules).
- flatly (claro).

---

## 4. Flujo de trabajo diario

### 4.1 Sincronizar facturas del correo

Paso 1 — Clic en Sincronizar.

Paso 2 — Elegir modo:

- "Solo correos NO leídos" (más rápido).
- "Todos los correos" (últimos 30 días).
- "Editar configuración del correo".

Recomendación: elige "Solo correos NO leídos".

Paso 3 — Esperar. Aparece una ventana con barra de progreso y log.

Tiempo estimado:

- 5 correos: ~30 segundos.
- 50 correos: ~3 minutos.

Paso 4 — Procesar. Cuando termina, aparece un diálogo:

- "Procesar TODAS automáticamente".
- "Solo guardar los archivos".

Recomendación: "Procesar TODAS".

Paso 5 — Revisar el resumen:

- Cuántas facturas se guardaron.
- Cuántas duplicadas.
- Cuántas sin XML.
- Cuántas con error.

### 4.2 Leer facturas manualmente

Paso 1 — Clic en Leer factura.

Paso 2 — Seleccionar el XML.

Paso 3 — Seleccionar el PDF (opcional).

Paso 4 — Verificar que el formulario se llenó bien.

Paso 5 — Guardar.

### 4.3 El formulario

El formulario tiene varias secciones:

GENERAL

- No. DE FACTURA
- QVET
- FECHA DE EMISIÓN
- NOMBRE
- RFC
- FECHA DE TIMBRADO
- FOLIO FISCAL

U (Alimentos)

- IMPORTE: total sin IVA.
- IVA (16%): se calcula automáticamente.

ACCESORIOS

- IMPORTE
- IVA (16%)

MEDICAMENTOS

- IMPORTE (sin IVA)
- SIN IVA
- IVA (16%)

HIGIENE

- IMPORTE (sin IVA)
- SIN IVA
- IVA 16%
- IEPS 6% / 7%

ESTETICA

- IMPORTE
- IVA (16%)

TRANSPORTE

- IMPORTE
- IVA (16%)

PENSION

- IMPORTE
- IVA (16%)

VACUNA

- IMPORTE

CLINICA

- IMPORTE

TOTAL

- TOTAL (auto)

TIPO DE PAGO

- EFECTIVO
- TARJETA CRÉDITO
- TARJETA DÉBITO
- CHEQUE
- TRANSFERENCIA
- VALE

Tip: si la suma de categorías no coincide con la suma de pagos, la app muestra una advertencia en rojo.

### 4.4 Guardar registros

Paso 1 — Verificar.

Paso 2 — Clic en Guardar.

Paso 3 — Ver mensaje de confirmación.

El registro aparece en la tabla.

### 4.5 Ver adjuntos

Paso 1 — Seleccionar un registro.

Paso 2 — Clic derecho → Ver adjuntos.

Paso 3 — Doble clic en un archivo para abrirlo.

---

## 5. Reclasificación de productos

### 5.1 ¿Qué son los productos huérfanos?

Son productos que no están en el catálogo o que están mal clasificados.

Cuando esto pasa, la app:

1. Avisa con un diálogo.
2. Ofrece registrarlo en el catálogo.

### 5.2 El reclasificador

Paso 1 — Clic en Reclasificar.

Paso 2 — Buscar el producto.

Paso 3 — Filtrar por categoría u origen.

Paso 4 — Cambiar categoría.

Paso 5 — Guardar.

### 5.3 Registrar productos nuevos

Desde el reclasificador:

1. Clic en "+ Nuevo producto".
2. Llena nombre y categoría.
3. Guardar.

Desde el aviso de reclasificación:

1. Aparece el aviso con la lista.
2. Clic en "Registrar en catálogo".
3. Elige la categoría para cada uno.
4. Guardar todos.

---

## 6. Generación de Excel

### 6.1 Cómo generar el resumen

Paso 1 — Verificar el mes en la barra superior.

Paso 2 — Clic en Generar Excel.

Paso 3 — Decidir:

Si el archivo NO existe: se crea automáticamente.

Si el archivo YA existe:

- "Sí" → Anexar solo los registros NUEVOS.
- "No" → Reordenar TODO (borra y regenera).
- "Cancelar" → No hacer nada.

### 6.2 Anexar vs Reordenar

Anexar (Sí):

- Agrega solo los registros nuevos.
- Mantiene ediciones manuales.
- Rápido.

Reordenar (No):

- Borra el Excel actual.
- Crea uno nuevo con todas las filas.
- Ordena por fecha y No. factura.
- Crea un backup.

### 6.3 Backups

Cuando eliges "Reordenar", la app:

1. Crea un backup del Excel actual.
2. Borra el original.
3. Crea el nuevo.

### 6.4 Recuperar un backup

1. Abre la carpeta del Excel.
2. Busca el archivo con `_backup_`.
3. Renómbralo quitando el `_backup_FECHA_HORA`.

Tip: los backups NO se borran automáticamente.

---

## 7. Reportes

### 7.1 Ver el árbol años/meses/centros

Paso 1 — Clic en Reportes.

Paso 2 — Explorar el árbol:

- 2026
  - Septiembre
    - Central
    - Prado

Paso 3 — Doble clic en un nodo para ir al reporte.

---

## 8. Adjuntos

### 8.1 Ver adjuntos

Ver sección 4.5.

### 8.2 Adjuntar manualmente

Clic derecho → Adjuntar factura.

### 8.3 Verificar en el explorador

Clic derecho → Ver adjuntos → Abrir carpeta.

---

## 9. Configuración avanzada

### 9.1 Cambiar tema

Ver sección 3.3.

### 9.2 Ver logs

Clic en Ver logs.

Se abre la carpeta de logs.

### 9.3 Reset caché

Clic en Reset caché.

Aparece un diálogo de confirmación.

---

## 10. Solución de problemas

### 10.1 La app no abre en Windows

1. Clic derecho en SistemaIngresos.exe.
2. Ejecutar como administrador.

### 10.2 La app no abre en macOS

Abre Terminal y ejecuta:

`xattr -cr "/Applications/Sistema Ingresos.app"`

### 10.3 La sincronización falla

Causas posibles:

1. Sin internet.
2. Contraseña de app incorrecta.
3. Etiqueta de Gmail mal escrita.
4. Filtro muy estricto.

Verifica los logs.

### 10.4 El Excel está bloqueado

Cierra Excel y vuelve a intentar.

### 10.5 Los totales no cuadran

Causas posibles:

1. Producto mal clasificado.
2. Producto nuevo.
3. Producto con IVA en categoría sin IVA.

Revisa el desglose por categoría.

---

## 11. Preguntas frecuentes

### ¿Dónde se guardan los datos?

Windows: `C:\Users\<tu_usuario>\Documents\Contabilidad App\`

macOS: `~/Documents/Contabilidad App/`

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

Importante: NO borres la carpeta `Contabilidad App`.

### ¿Qué hago si la app se cierra sola?

Abre CMD/Terminal y ejecútala desde ahí para ver el error.

---

## 12. Glosario

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
| Backup | Copia de seguridad. |
| Log | Registro de actividad. |
| Caché | Almacén temporal de datos. |

---

## Próximamente

### Módulo de Egresos

Estamos trabajando en un módulo de Egresos que permitirá:

- Descargar facturas de compra del SAT.
- Procesar los XML automáticamente.
- Generar el reporte de egresos en Excel.

### Pantalla de inicio

Vamos a agregar una pantalla de inicio que te permita elegir entre:

- Reporte de Ingresos (lo que ya tienes).
- Reporte de Egresos (próximamente).

---

## Soporte

Si tienes problemas:

1. Revisa este manual primero.
2. Revisa los logs.
3. Contacta al desarrollador.

---

Fin del manual.

Versión: 1.0.0  
Última actualización: Septiembre 2026