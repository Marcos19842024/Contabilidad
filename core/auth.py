# -*- coding: utf-8 -*-
"""
core/auth.py
Hash y verificación de contraseñas.

Usa PBKDF2-SHA256 con 600k iteraciones (recomendación OWASP 2023) y salt
aleatorio por usuario. Todo con stdlib. Sin dependencias externas.

Formato del hash guardado:
    pbkdf2_sha256$<iteraciones>$<salt_b64>$<hash_b64>

Regla: NUNCA guardar contraseñas en claro. NUNCA loguear el hash ni la
contraseña. NUNCA comparar hashes con == (usar hmac.compare_digest).
"""

import base64
import hashlib
import hmac
import secrets


ALGO = "pbkdf2_sha256"
ITERACIONES = 600_000
SALT_BYTES = 16
HASH_BYTES = 32


# ---------------------------------------------------------------
# Utilidades base64
# ---------------------------------------------------------------

def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


# ---------------------------------------------------------------
# API pública
# ---------------------------------------------------------------

def hashear_password(password: str) -> str:
    """
    Devuelve el hash listo para guardar en usuarios.json.
    Cada llamada genera un salt nuevo (dos hashes de la misma contraseña
    son distintos).
    """
    if not isinstance(password, str) or not password:
        raise ValueError("La contraseña no puede estar vacía")

    salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERACIONES, dklen=HASH_BYTES
    )
    return f"{ALGO}${ITERACIONES}${_b64(salt)}${_b64(dk)}"


def verificar_password(password: str, hash_guardado: str) -> bool:
    """
    Devuelve True si la contraseña corresponde al hash.
    Comparación en tiempo constante (hmac.compare_digest).
    Devuelve False ante cualquier formato inválido, sin lanzar excepción.
    """
    if not isinstance(password, str) or not isinstance(hash_guardado, str):
        return False
    try:
        partes = hash_guardado.split("$")
        if len(partes) != 4:
            return False
        algo, iters_str, salt_b64, hash_b64 = partes
        if algo != ALGO:
            return False
        iters = int(iters_str)
        salt = _unb64(salt_b64)
        esperado = _unb64(hash_b64)
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iters, dklen=len(esperado)
        )
        return hmac.compare_digest(dk, esperado)
    except Exception:
        return False


def hash_es_valido(hash_guardado: str) -> bool:
    """Chequeo de formato sin verificar contraseña. Útil para validar JSON."""
    if not isinstance(hash_guardado, str):
        return False
    partes = hash_guardado.split("$")
    if len(partes) != 4:
        return False
    algo, iters_str, salt_b64, hash_b64 = partes
    if algo != ALGO:
        return False
    try:
        int(iters_str)
        _unb64(salt_b64)
        _unb64(hash_b64)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------
# Generación de contraseñas temporales legibles
# ---------------------------------------------------------------

# Palabras sin tildes, sin ñ, sin ambigüedad al copiar.
# Todas en minúsculas en el archivo; se capitalizan al generar.
_PALABRAS = (
    "agua", "aire", "arroz", "arbol", "arena", "avion", "azul",
    "barco", "blanco", "bosque", "brazo", "brisa", "buho",
    "cabra", "campo", "canto", "caracol", "carta", "casa", "cima",
    "cielo", "cobre", "cocina", "corona", "costa", "cuadro",
    "delfin", "diente", "duna",
    "eco", "estrella",
    "farol", "fiesta", "fuego", "fuente",
    "gato", "girasol", "grillo", "gruta",
    "helado", "hierba", "hoja", "hueso",
    "isla",
    "jardin", "jarra", "jirafa",
    "ladera", "lampara", "lapiz", "leche", "leon", "libro", "limon",
    "llave", "luna",
    "madera", "maiz", "mano", "mapa", "mar", "mesa", "metal", "miel",
    "molino", "monte", "moto", "muro",
    "naranja", "nido", "nube", "nuez",
    "ola", "olivo", "oro", "oso",
    "pajaro", "palma", "pan", "papel", "pared", "pasto", "pato",
    "pera", "perro", "piedra", "pino", "piso", "playa", "pluma",
    "pozo", "puente", "puerta",
    "queso",
    "rama", "rana", "raton", "rayo", "reloj", "rio", "rosa", "rueda",
    "sabana", "sal", "sapo", "silla", "sol", "sombra", "sopa",
    "taladro", "taza", "techo", "tela", "tigre", "tinta", "tomate",
    "torre", "tortuga", "trigo", "tronco",
    "uva",
    "vaca", "valle", "vapor", "vaso", "vela", "ventana", "verde",
    "vidrio", "viento", "violin", "volcan",
    "yate", "yema",
    "zanja", "zapato", "zorro", "zumo",
)


def generar_password_temporal() -> str:
    """
    Formato: Palabra + Palabra + NN  →  ej. 'GorrionZapato42'
    Mínimo 12 caracteres garantizados (rechaza combinaciones cortas).
    Sin símbolos ni guiones: fácil de dictar y copiar.
    """
    MIN_LEN = 12
    for _ in range(50):   # reintenta si la combinación es muy corta
        p1 = secrets.choice(_PALABRAS).capitalize()
        p2 = secrets.choice(_PALABRAS).capitalize()
        n = secrets.randbelow(90) + 10
        pwd = f"{p1}{p2}{n}"
        if len(pwd) >= MIN_LEN:
            return pwd
    # Fallback imposible en la práctica: forzar una palabra larga
    p1 = "Tortuga"
    p2 = secrets.choice(_PALABRAS).capitalize()
    n = secrets.randbelow(90) + 10
    return f"{p1}{p2}{n}"