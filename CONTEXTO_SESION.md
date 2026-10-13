# Sesión de trabajo — 2026-10-13 (v2.1.7)

## Resumen
Rediseño completo de la ventana principal: sidebar estilo QVET con
categorías colapsables + migración de los 4 módulos a embed (Frame).
Además: botón "Probar FIEL" movido a Config, fix de paneles acumulados.

## Qué se hizo

### 1. Registro declarativo de módulos (`shared/registro_modulos.py`)
- Archivo nuevo. Cada módulo se declara una sola vez con:
  `id, nombre, descripcion, icono, categoria, factory, panel, atajo, activo`.
- `factory(master)` → abre como Toplevel (legacy).
- `panel(master, on_volver)` → abre como Frame embebido (preferido).
- Helpers: `modulos_activos()`, `modulos_por_categoria()`, `buscar_modulo()`.
- Agregar un módulo nuevo = una entrada en `MODULOS`, sin tocar `app/principal.py`.

### 2. Rediseño de `app/principal.py` — sidebar estilo QVET
- Sidebar lateral oscuro (`#2b2b2b`), categorías colapsables
  (`▶`/`▼`), módulos indentados debajo de su categoría.
- Sin iconos ni flechas en las categorías (solo texto).
- El módulo activo se resalta con fondo amarillo (`#f0a500`) y texto negro.
- Sidebar usa `tk.Frame` + `tk.Label` (no ttk) para evitar que
  ttkbootstrap sobrescriba `bg`/`fg`.
- Área central: pantalla de bienvenida simple (sin tarjetas de módulos)
  cuando no hay módulo abierto; barra "←" + panel embebido cuando sí.
- Botón "Volver" del embed es solo la flecha `←`, sin texto ni contorno
  (`bootstyle="link"`).
- Atajos Ctrl+1..Ctrl+4 declarados en el registro, bindeados por el shell.

### 3. Migración de los 4 módulos a embed
Todos siguen el mismo patrón: `AppX(ttk.Toplevel)` → `PanelX(ttk.Frame)`,
y se mantiene `AppX(ttk.Toplevel)` como **wrapper legacy** para no romper
imports existentes.

- **Estética y Transportes** → `PanelEsteticaTransportes(ttk.Frame)`.
- **Recordatorios** → `PanelRecordatorios(ttk.Frame)`.
- **Egresos** → `PanelEgresos(ttk.Frame)`.
  - Fix: `_preguntar_accion_excel` usa `parent.winfo_toplevel()` para
    `transient`, así funciona con Frame o Toplevel como parent.
- **Ingresos** → `PanelIngresos(ttk.Frame)`.
  - `_actualizar_titulo` convertido en no-op (no aplica en Frame).

### 4. Fix: paneles acumulados al cambiar de módulo
- Al abrir un módulo embebido sin haber hecho "←", el panel anterior
  quedaba vivo y se apilaba debajo del nuevo.
- Fix en `app/principal.py::_abrir_embed`: destruye el panel anterior
  (y limpia el área embed) antes de crear el nuevo.

### 5. Mover botón "Probar FIEL" a Config
- Antes: en `dialogos/descargar_sat.py` (junto al botón Descargar).
- Ahora: en `dialogos/egresos_config.py` (junto a las credenciales FIEL).
- Prueba los valores **actuales del formulario** (aunque no estén guardados).
- Corre en hilo, muestra estado verde/rojo.
- Sigue sin gastar solicitud (usa `Autenticacion`).

## Estado actual
- ✅ Sidebar QVET con categorías colapsables y módulos indentados.
- ✅ Los 4 módulos migrados a embed (Frame).
- ✅ Wrappers legacy `AppX(ttk.Toplevel)` mantenidos.
- ✅ Botón "Probar FIEL" en Config, no en Descargar.
- ✅ Sin paneles acumulados al cambiar de módulo.
- ✅ `python3 verificar_config.py` OK.
- ⏳ Pendiente: pruebas con SAT real y cliente final.

## Próximos pasos sugeridos
- A) **Refactor v3.0.0 por dominio funcional** (el grande).
- B) **Rotación de snapshots SAT** (evitar llenar el disco).
- C) **Anexar + reordenar Excel de Egresos** cuando ya existe con anotaciones.
- D) **Tests con pytest** sobre snapshots reales (anonimizados).
- E) **Tests de `core/config_ui.py`** y `shared/registro_modulos.py`.

## Cómo trabajar
- Configuración compartida → `core/config_ui.py`.
- Sucursales → `config/veterinaria.py` (fuente de verdad).
- Registro de módulos → `shared/registro_modulos.py`.
- Antes de tocar: correr `python3 verificar_config.py`.
- Los JSON de datos NO van a git.
- `config_ui.json` se autocrea; no lo borres.
- Historial del SAT: `python3 scripts/probar_egresos.py --historial status`.

## Pendientes de la sesión (deuda técnica)

### Egresos
- [ ] **Anexar + reordenar Excel.** El diálogo de 3 opciones (Anexar /
  Reemplazar / Omitir) ya existe en `_preguntar_accion_excel`.
- [ ] **`actualizar_json` y `mover_y_renombrar_egresos`** hacen cosas
  parecidas. Fusionar en el refactor.

### Testing
- [ ] **pytest** sobre snapshots reales (anonimizados).
- [ ] Tests de `core/config_ui.py`.
- [ ] Tests de `shared/registro_modulos.py`.
- [ ] Tests del pipeline de Ingresos.

### Arquitectura
- [ ] **Refactor v3.0.0 por dominio funcional:**
  - `ingresos/`, `egresos/`, `estetica_transportes/`, `recordatorios/`
  - Cada dominio autocontenido (módulo + lógica + rutas + diálogos + tests).
  - `shared/` para código transversal (config_ui, registro_modulos, rutas base).

### Otros
- [ ] **Rotación de snapshots SAT** (borrar los más viejos automáticamente).
- [ ] **Revisar 5 XMLs ignorados** en `/tmp/sat_descargas/` (no son Ingreso,
  probablemente notas de crédito).