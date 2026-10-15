# -*- coding: utf-8 -*-
"""
shared/perfiles.py
Perfiles de trabajo (roles) y validación.

La fuente de verdad de los perfiles actuales es config_ui.json#perfiles.
Este módulo declara:
  - Los DEFAULTS (semilla si la clave no existe).
  - Las CAPACIDADES especiales (puede_configurar) que no se editan desde
    la UI y viven en código.
  - La validación de ids.
  - El acceso de consulta: perfil_por_id(), modulo_permitido(), etc.

Reglas:
  - El perfil "admin" es intocable. Siempre existe, siempre ve todo,
    siempre puede configurar. Si falta en config_ui, se regenera.
  - Un perfil se identifica por su `id` (snake_case, estable).
    El `nombre` es solo etiqueta visible.
  - Los perfiles default se pueden eliminar desde la UI.
  - Un módulo nuevo NO se añade solo a los perfiles con lista explícita.
    Hay que marcarlo en cada perfil que deba verlo.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Perfil:
    id: str
    nombre: str
    descripcion: str
    modulos: tuple[str, ...] | str   # "*" o tupla de ids
    puede_configurar: bool = False


# ---------------------------------------------------------------
# Defaults (semilla y fallback)
# ---------------------------------------------------------------

PERFILES_DEFAULT: tuple[Perfil, ...] = (
    Perfil(
        id="admin",
        nombre="Administrador",
        descripcion="Acceso completo. Único que puede configurar módulos, "
                    "perfiles y usuarios.",
        modulos="*",
        puede_configurar=True,
    ),
    Perfil(
        id="contabilidad",
        nombre="Contabilidad",
        descripcion="Ingresos y egresos.",
        modulos=("ingresos", "egresos"),
    ),
    Perfil(
        id="almacen",
        nombre="Almacén",
        descripcion="Recepción de mercancía y facturas (Ingresos).",
        modulos=("ingresos",),
    ),
    Perfil(
        id="cajero",
        nombre="Cajero",
        descripcion="Atención al cliente: estética, transportes y "
                    "recordatorios.",
        modulos=("estetica_transportes", "recordatorios"),
    ),
    Perfil(
        id="medico",
        nombre="Médico",
        descripcion="Recordatorios de citas y vacunas.",
        modulos=("recordatorios",),
    ),
)


ADMIN_ID = "admin"


# ---------------------------------------------------------------
# Capacidades blindadas (no editables desde la UI)
# ---------------------------------------------------------------

def _puede_configurar(perfil_id: str) -> bool:
    """Solo admin puede configurar. Blindado aquí, no en config_ui."""
    return perfil_id == ADMIN_ID


# ---------------------------------------------------------------
# Carga desde config_ui (con migración automática)
# ---------------------------------------------------------------

def _normalizar_modulos(valor) -> tuple[str, ...] | str:
    """
    Acepta "*" o lista/tupla de strings. Devuelve la forma canónica.
    """
    if valor == "*":
        return "*"
    if isinstance(valor, (list, tuple)):
        return tuple(str(m) for m in valor)
    return ()


def _dict_a_perfil(d: dict) -> Perfil | None:
    """Convierte un dict de config en Perfil. None si es inválido."""
    if not isinstance(d, dict):
        return None
    pid = d.get("id")
    if not isinstance(pid, str) or not pid:
        return None
    return Perfil(
        id=pid,
        nombre=str(d.get("nombre", pid)),
        descripcion=str(d.get("descripcion", "")),
        modulos=_normalizar_modulos(d.get("modulos", [])),
        puede_configurar=_puede_configurar(pid),
    )


def _perfil_a_dict(p: Perfil) -> dict:
    return {
        "id": p.id,
        "nombre": p.nombre,
        "descripcion": p.descripcion,
        "modulos": p.modulos if p.modulos == "*" else list(p.modulos),
    }


def _sembrar_perfiles() -> list[dict]:
    """Copia los defaults a config_ui.json. Se llama solo si falta la clave."""
    from core import config_ui
    semilla = [_perfil_a_dict(p) for p in PERFILES_DEFAULT]
    config_ui.set_seccion("perfiles", semilla)
    return semilla


def _leer_perfiles_crudos() -> list[dict]:
    """
    Devuelve la lista de perfiles como dicts desde config_ui.
    Si la clave no existe, la siembra con los defaults.
    """
    from core import config_ui
    crudos = config_ui.get_seccion("perfiles", None)
    if not isinstance(crudos, list) or not crudos:
        crudos = _sembrar_perfiles()
    return list(crudos)


def _blindar_admin(perfiles: list[dict]) -> list[dict]:
    """
    Asegura que 'admin' exista y tenga los valores blindados.
    Si no existe, lo inserta al principio.
    Si existe pero con valores alterados, los corrige.
    Devuelve la lista corregida.
    """
    admin_default = next(p for p in PERFILES_DEFAULT if p.id == ADMIN_ID)
    admin_dict = _perfil_a_dict(admin_default)
    admin_dict["puede_configurar"] = True   # por si acaso, redundante

    for i, p in enumerate(perfiles):
        if p.get("id") == ADMIN_ID:
            if (p.get("modulos") != "*"
                    or p.get("nombre") != admin_default.nombre):
                perfiles[i] = admin_dict
            return perfiles

    return [admin_dict] + perfiles


# ---------------------------------------------------------------
# API pública
# ---------------------------------------------------------------

def perfiles() -> tuple[Perfil, ...]:
    """
    Devuelve los perfiles actuales como tuplas de Perfil.
    Siempre incluye a admin (blindado).
    """
    crudos = _blindar_admin(_leer_perfiles_crudos())
    perfiles_validos = [_dict_a_perfil(d) for d in crudos]
    return tuple(p for p in perfiles_validos if p is not None)


def perfil_por_id(pid: str) -> Perfil | None:
    for p in perfiles():
        if p.id == pid:
            return p
    return None


def ids_perfiles() -> tuple[str, ...]:
    return tuple(p.id for p in perfiles())


def perfil_actual() -> Perfil | None:
    """Perfil de la sesión activa. None si no hay sesión."""
    from core import sesion
    s = sesion.actual()
    if s is None:
        return None
    return perfil_por_id(s.perfil_id)


def modulo_permitido(modulo_id: str) -> bool:
    """
    True si el perfil de la sesión puede ver este módulo.
    Sin sesión → False.
    """
    p = perfil_actual()
    if p is None:
        return False
    if p.modulos == "*":
        return True
    return modulo_id in p.modulos


def puede_configurar() -> bool:
    p = perfil_actual()
    return p is not None and p.puede_configurar


# ---------------------------------------------------------------
# Validación de ids
# ---------------------------------------------------------------

import re as _re

_ID_PERFIL_RE = _re.compile(r"^[a-z][a-z0-9_]{2,31}$")


def id_perfil_es_valido(pid: str) -> bool:
    """3–32 chars, empieza con letra, solo [a-z0-9_]."""
    return isinstance(pid, str) and bool(_ID_PERFIL_RE.match(pid))


# ---------------------------------------------------------------
# Escritura (solo para admin, vía UI)
# ---------------------------------------------------------------

def _perfil_a_dict_editable(p: Perfil) -> dict:
    """Serializa un Perfil para config_ui.json (sin puede_configurar)."""
    return {
        "id": p.id,
        "nombre": p.nombre,
        "descripcion": p.descripcion,
        "modulos": p.modulos if p.modulos == "*" else list(p.modulos),
    }


def guardar_perfiles(lista: list[Perfil]) -> None:
    """
    Reemplaza config_ui.json#perfiles con la lista dada.
    Fuerza que admin esté presente y blindado.
    """
    from core import config_ui

    # Filtrar cualquier intento de tocar admin desde fuera
    limpios = [p for p in lista if p.id != ADMIN_ID]

    # Insertar admin blindado al principio
    admin_default = next(p for p in PERFILES_DEFAULT if p.id == ADMIN_ID)
    todos = [admin_default] + limpios

    config_ui.set_seccion("perfiles", [_perfil_a_dict_editable(p) for p in todos])


def agregar_perfil(perfil: Perfil) -> None:
    """Añade un perfil. ValueError si el id ya existe o es inválido."""
    if not id_perfil_es_valido(perfil.id):
        raise ValueError(f"id inválido: {perfil.id!r}")
    if perfil.id == ADMIN_ID:
        raise ValueError("No se puede crear un perfil con id 'admin'")
    if perfil_por_id(perfil.id) is not None:
        raise ValueError(f"Ya existe un perfil con id {perfil.id!r}")

    actuales = list(perfiles())
    actuales.append(perfil)
    guardar_perfiles(actuales)


def actualizar_perfil(pid: str, **campos) -> None:
    """
    Actualiza nombre, descripcion, modulos de un perfil existente.
    No permite cambiar el id ni editar admin.
    """
    if pid == ADMIN_ID:
        raise ValueError("El perfil admin no se puede editar")
    permitidos = {"nombre", "descripcion", "modulos"}
    invalidos = set(campos) - permitidos
    if invalidos:
        raise ValueError(f"Campos no editables: {invalidos}")

    actuales = list(perfiles())
    for i, p in enumerate(actuales):
        if p.id == pid:
            actuales[i] = Perfil(
                id=p.id,
                nombre=campos.get("nombre", p.nombre),
                descripcion=campos.get("descripcion", p.descripcion),
                modulos=campos.get("modulos", p.modulos),
                puede_configurar=False,   # nunca editable desde aquí
            )
            guardar_perfiles(actuales)
            return
    raise KeyError(f"No existe el perfil {pid!r}")


def eliminar_perfil(pid: str) -> None:
    """
    Elimina un perfil. KeyError si no existe, ValueError si es admin.
    NO verifica si tiene usuarios: eso lo hace el caller.
    """
    if pid == ADMIN_ID:
        raise ValueError("El perfil admin no se puede eliminar")
    actuales = [p for p in perfiles() if p.id != pid]
    if len(actuales) == len(list(perfiles())):
        raise KeyError(f"No existe el perfil {pid!r}")
    guardar_perfiles(actuales)


def usuarios_con_perfil(pid: str) -> list[dict]:
    """Lista de usuarios asignados a un perfil (vía core.usuarios)."""
    from core import usuarios
    return [u for u in usuarios.listar() if u.get("perfil") == pid]

# ---------------------------------------------------------------
# Compatibilidad con el nombre anterior
# ---------------------------------------------------------------

# Antes existía PERFILES (tupla). Ahora es una función. Dejo un alias
# que devuelve la tupla actual, para no romper imports existentes.
def PERFILES_actuales() -> tuple[Perfil, ...]:
    """Alias retrocompatible. Preferir perfiles()."""
    return perfiles()