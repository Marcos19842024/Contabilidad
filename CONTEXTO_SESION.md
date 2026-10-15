# Sesión de trabajo — 2026-10-15 (v2.2.0)

## Resumen
Sistema completo de autenticación, perfiles y usuarios. La app arranca
en login. Sidebar y Config General se filtran por perfil. Módulos
activables/desactivables y perfiles editables desde la UI.

## Qué se hizo

### 1. Autenticación (Fases 1–3)
- **`core/auth.py`** — PBKDF2-SHA256, 600k iteraciones, salt 16 bytes por
  usuario. `hashear_password()`, `verificar_password()` (comparación en
  tiempo constante), `generar_password_temporal()` (12+ chars legibles).
- **`core/sesion.py`** — sesión activa en memoria. NO se persiste. El
  perfil activo vive aquí, no en `config_ui.json`, para evitar escalada
  de privilegios editando el JSON.
- **`core/usuarios.py`** — CRUD de `usuarios.json` (raíz de datos).
  Reglas de negocio: no eliminar/desactivar al último admin activo.
- **`shared/perfiles.py`** — 5 perfiles iniciales (admin, contabilidad,
  almacen, cajero, medico). Admin blindado. Fuente de verdad en
  `config_ui.json#perfiles`, defaults aquí.
- **`dialogos/login.py`** — login modal + bootstrap de primer arranque.
  En macOS, sin `transient` ni `grab_set` sobre padre withdrawn.
- **`main.py`** — DPI awareness → crear AppPrincipal → withdraw →
  mostrar_login → si OK, deiconify + mainloop.

### 2. Sidebar con sesión (Fase 3)
- Bloque de sesión arriba: `👤 Ana (Administrador)`.
- Footer: `Configuración`/`Mi cuenta` (según perfil) · `Ayuda` ·
  `🚪 Cerrar sesión`.
- Cerrar sesión vuelve al login sin reiniciar el proceso.

### 3. Config General con tabs filtrados (Fases 4a–4c)
- Tab **🔒 Mi cuenta** (todos los perfiles) — cambiar la propia contraseña.
- Tabs admin: 🎨 Apariencia, 🏥 Veterinaria, 🧩 Módulos, 🧑 Perfiles,
  👥 Usuarios.
- CRUD de usuarios desde la UI. Contraseña editable en el diálogo de
  edición (vacío = no cambiar).
- Sucursales extraídas a `dialogos/sucursal_detalle.py`.

### 4. Perfiles editables (Sub-fases A y B)
- Perfiles movidos a `config_ui.json#perfiles`. Defaults como semilla.
- Admin blindado: no editable, no eliminable, siempre `modulos="*"`.
- CRUD de perfiles desde la UI. No se elimina un perfil con usuarios
  asignados (rechazo con lista de usuarios).
- Cambios en perfiles aplican al siguiente login del usuario afectado,
  no en caliente.

### 5. Bugs resueltos
- Login en macOS con `transient` sobre padre withdrawn → queda colgado.
- Bootstrap no bloqueante → doble ventana superpuesta.
- Cancelar bootstrap → admin huérfano con contraseña perdida.
- Cerrar ventana principal con Config abierto → messagebox de error.
- `_abrir_configuracion` faltante tras refactor.
- `_abrir_ayuda` duplicado.

## Estado actual
- ✅ Login obligatorio (PBKDF2-SHA256, 600k iteraciones).
- ✅ Sesión en memoria, sin persistencia del perfil.
- ✅ Sidebar filtrado por activo ∧ permitido por perfil.
- ✅ Perfiles editables desde Config General (admin intocable).
- ✅ Usuarios editables desde Config General.
- ✅ Módulos activables/desactivables desde Config.
- ✅ Tab "Mi cuenta" para cambiar la propia contraseña.
- ✅ `scripts/probar_auth.py` con 86 checks verdes.
- ✅ `python3 verificar_config.py` OK.
- ⏳ Pendiente: pruebas con SAT real y cliente final.

## Cómo trabajar
- Configuración compartida → `core/config_ui.py`.
- Cuentas de usuario → `core/usuarios.py` + `usuarios.json`.
- Perfiles → `config_ui.json#perfiles` (semilla en `shared/perfiles.py`).
- Sesión activa → `core/sesion.py`.
- Sucursales → `config/veterinaria.py` (fuente de verdad).
- Registro de módulos → `shared/registro_modulos.py`.
- Antes de tocar: correr `python3 verificar_config.py` y
  `python3 scripts/probar_auth.py`.
- Los JSON de datos NO van a git (`config_ui.json`, `usuarios.json`).

## Pendientes (deuda técnica)

### Testing
- [ ] Ampliar `verificar_config.py` con bloque `[10]` para `usuarios.json`.
- [ ] Ampliar `scripts/probar_auth.py` con tests de integración de perfiles.
- [ ] pytest sobre snapshots reales (anonimizados).
- [ ] Tests del pipeline de Ingresos.

### Autenticación
- [ ] Migración de usuarios huérfanos (perfil borrado tras asignar usuario).
- [ ] Log de auditoría de cambios de perfiles/usuarios.
- [ ] (Opcional) Bloqueo por intentos fallidos.
- [ ] (Opcional) Expiración de sesión.

### Módulos y arquitectura
- [ ] Refactor v3.0.0 por dominio funcional.
- [ ] Rotación de snapshots SAT.
- [ ] Anexar + reordenar Excel de Egresos con anotaciones.

### Documentación
- [ ] Sección de login y perfiles en `MANUAL.md`.