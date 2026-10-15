# -*- coding: utf-8 -*-
"""
core/sesion.py
Estado en memoria de la sesión activa.

Regla: el perfil activo NO se persiste. Si el proceso muere, la sesión
se pierde y hay que volver a hacer login. Esto es intencional: así un
JSON de config no puede escalar privilegios.

Uso:
    from core import sesion
    sesion.iniciar_sesion(usuario_dict)
    if sesion.es_admin(): ...
    sesion.cerrar_sesion()
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Sesion:
    usuario_id: str
    nombre: str
    perfil_id: str
    inicio: datetime


_actual: Sesion | None = None


def iniciar_sesion(usuario: dict) -> Sesion:
    """
    Inicia sesión a partir de un dict de usuario con al menos:
      - id, nombre, perfil
    Devuelve la Sesion creada. Si ya había una, la pisa.
    """
    global _actual
    for campo in ("id", "nombre", "perfil"):
        if campo not in usuario:
            raise ValueError(f"Falta el campo {campo!r} en el usuario")
    _actual = Sesion(
        usuario_id=usuario["id"],
        nombre=usuario["nombre"],
        perfil_id=usuario["perfil"],
        inicio=datetime.now(),
    )
    return _actual


def cerrar_sesion() -> None:
    global _actual
    _actual = None


def actual() -> Sesion | None:
    return _actual


def hay_sesion() -> bool:
    return _actual is not None


def es_admin() -> bool:
    return _actual is not None and _actual.perfil_id == "admin"


def limpiar_para_tests() -> None:
    """Solo para tests. No usar en producción."""
    global _actual
    _actual = None