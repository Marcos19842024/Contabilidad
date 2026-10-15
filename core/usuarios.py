# -*- coding: utf-8 -*-
"""
core/usuarios.py
CRUD de usuarios.json (cuentas de la app).

Ubicación: raíz de datos (junto a config_ui.json).
  Dev:  <raíz proyecto>/usuarios.json
  Prod: ~/Documents/Vet Suite/usuarios.json

NO crea el archivo si no existe: eso lo hace main.py al primer arranque.
NO hashea contraseñas: eso lo hace core/auth.py.

Formato:
{
  "version": 1,
  "usuarios": [
    {
      "id": "ana",
      "nombre": "Ana García",
      "perfil": "admin",
      "password_hash": "pbkdf2_sha256$...$...$...",
      "activo": true,
      "creado": "2026-10-13T10:00:00",
      "ultimo_login": null
    }
  ]
}
"""

import json
import re
import sys
import threading
from datetime import datetime
from pathlib import Path


VERSION = 1
_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,31}$")
_LOCK = threading.RLock()


# ---------------------------------------------------------------
# Ruta del archivo
# ---------------------------------------------------------------

def _carpeta_datos() -> Path:
    if getattr(sys, "frozen", False):
        carpeta = Path.home() / "Documents" / "Vet Suite"
    else:
        carpeta = Path(__file__).parent.parent
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


USUARIOS_FILE = _carpeta_datos() / "usuarios.json"


# ---------------------------------------------------------------
# Validación
# ---------------------------------------------------------------

def id_es_valido(uid: str) -> bool:
    """3–32 caracteres, empieza con letra, solo [a-z0-9_]."""
    return isinstance(uid, str) and bool(_ID_RE.match(uid))


# ---------------------------------------------------------------
# Lectura / escritura
# ---------------------------------------------------------------

def _leer_crudo() -> dict:
    if not USUARIOS_FILE.exists():
        raise FileNotFoundError(
            f"No existe {USUARIOS_FILE}. "
            "main.py (o el script de pruebas) debe crear el admin inicial."
        )
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("usuarios.json debe ser un dict en la raíz")
    return data


def _escribir_crudo(data: dict) -> None:
    if not isinstance(data, dict):
        raise TypeError("usuarios.json debe ser un dict en la raíz")
    with _LOCK:
        USUARIOS_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = USUARIOS_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(USUARIOS_FILE)


def existe() -> bool:
    return USUARIOS_FILE.exists()


# ---------------------------------------------------------------
# API pública
# ---------------------------------------------------------------

def listar() -> list[dict]:
    """Lista de usuarios. Vacía si el archivo no existe."""
    if not existe():
        return []
    return list(_leer_crudo().get("usuarios", []))


def obtener(uid: str) -> dict | None:
    for u in listar():
        if u.get("id") == uid:
            return dict(u)
    return None


def crear(
    uid: str,
    nombre: str,
    perfil: str,
    password_hash: str,
) -> dict:
    """
    Crea un usuario. Lanza ValueError si el id es inválido o ya existe.
    NO valida el perfil: eso lo hace shared/perfiles.py.
    NO hashea: el llamador pasa el hash listo.
    """
    if not id_es_valido(uid):
        raise ValueError(
            f"id inválido {uid!r}. "
            "Debe empezar con letra y usar solo a-z, 0-9, _ (3–32 chars)."
        )
    if not nombre or not nombre.strip():
        raise ValueError("El nombre no puede estar vacío")
    if obtener(uid) is not None:
        raise ValueError(f"Ya existe un usuario con id {uid!r}")

    with _LOCK:
        data = _leer_crudo()
        usuarios = list(data.get("usuarios", []))
        nuevo = {
            "id": uid,
            "nombre": nombre.strip(),
            "perfil": perfil,
            "password_hash": password_hash,
            "activo": True,
            "creado": datetime.now().isoformat(timespec="seconds"),
            "ultimo_login": None,
        }
        usuarios.append(nuevo)
        data["usuarios"] = usuarios
        data["version"] = VERSION
        _escribir_crudo(data)
        return dict(nuevo)


def actualizar(uid: str, **campos) -> dict:
    """
    Actualiza campos de un usuario existente.
    Campos permitidos: nombre, perfil, password_hash, activo, ultimo_login.
    Lanza KeyError si no existe, ValueError si el campo no está permitido.
    """
    permitidos = {"nombre", "perfil", "password_hash", "activo", "ultimo_login"}
    invalidos = set(campos) - permitidos
    if invalidos:
        raise ValueError(f"Campos no editables: {invalidos}")

    with _LOCK:
        data = _leer_crudo()
        usuarios = list(data.get("usuarios", []))
        for i, u in enumerate(usuarios):
            if u.get("id") == uid:
                u = dict(u)
                u.update(campos)
                usuarios[i] = u
                data["usuarios"] = usuarios
                _escribir_crudo(data)
                return dict(u)
    raise KeyError(f"No existe el usuario {uid!r}")


def eliminar(uid: str) -> None:
    """Elimina un usuario. KeyError si no existe."""
    with _LOCK:
        data = _leer_crudo()
        usuarios = list(data.get("usuarios", []))
        nuevo = [u for u in usuarios if u.get("id") != uid]
        if len(nuevo) == len(usuarios):
            raise KeyError(f"No existe el usuario {uid!r}")
        data["usuarios"] = nuevo
        _escribir_crudo(data)


def marcar_login(uid: str) -> None:
    """Sella la fecha de último login."""
    actualizar(uid, ultimo_login=datetime.now().isoformat(timespec="seconds"))


# ---------------------------------------------------------------
# Reglas de negocio: admins
# ---------------------------------------------------------------

def admins_activos() -> list[dict]:
    """Usuarios con perfil 'admin' y activo=True."""
    return [
        u for u in listar()
        if u.get("perfil") == "admin" and u.get("activo", True)
    ]


def quedarian_admins_sin(uid: str) -> int:
    """
    Cuántos admins activos quedarían si se eliminara o desactivara a uid.
    Sirve para bloquear dejar el sistema sin admins.
    """
    return sum(
        1 for u in admins_activos() if u.get("id") != uid
    )


# ---------------------------------------------------------------
# Bootstrap: crear el primer admin
# ---------------------------------------------------------------

def crear_admin_inicial(nombre: str = "Administrador") -> tuple[dict, str]:
    """
    Crea usuarios.json con un único admin si no existe.
    Devuelve (usuario, password_temporal).
    Si ya existe el archivo, lanza FileExistsError.
    """
    from core.auth import hashear_password, generar_password_temporal

    if existe():
        raise FileExistsError(f"Ya existe {USUARIOS_FILE}")

    password = generar_password_temporal()
    hash_ = hashear_password(password)

    data = {
        "version": VERSION,
        "usuarios": [
            {
                "id": "admin",
                "nombre": nombre,
                "perfil": "admin",
                "password_hash": hash_,
                "activo": True,
                "creado": datetime.now().isoformat(timespec="seconds"),
                "ultimo_login": None,
            }
        ],
    }
    with _LOCK:
        _escribir_crudo(data)
    return (dict(data["usuarios"][0]), password)