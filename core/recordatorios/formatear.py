# core/recordatorios/formatear.py
"""
Funciones de formateo: fechas, teléfonos, strings, etc.
Portado de la app Android (BaalakApps) a Python.
"""

from datetime import datetime, date, timedelta


MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

MESES_ES_NOMBRE = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def format_string(cadena: str) -> str:
    """
    Convierte a Tipo Oración respetando acentos y limpiando caracteres raros:
    "FRANCISCO RULLAN ." → "Francisco Rullan"
    "PALOMA CAHUICH ." → "Paloma Cahuich"
    """
    if not cadena or not str(cadena).strip():
        return ""

    # Limpiar caracteres raros al inicio y final (puntos, comas, etc.)
    texto = str(cadena).strip()
    texto = texto.strip(".,;:-_ \t\n")

    # Reemplazar separadores internos
    texto = texto.replace("-", " ").replace("_", " ")

    # Capitalizar por palabras
    palabras = texto.lower().split()
    return " ".join(p.capitalize() for p in palabras if p)


def format_numbers(cadena: str) -> str:
    """Extrae solo los dígitos."""
    if not cadena:
        return ""
    return "".join(c for c in str(cadena) if c.isdigit())


def normalizar_telefono(cadena: str) -> str:
    """
    Normaliza un teléfono mexicano a formato internacional:
    - 10 dígitos → agrega "52" al inicio
    - 12 dígitos que empiezan con "52" → ya está listo
    - Otro → devuelve los dígitos tal cual
    """
    digitos = format_numbers(cadena)
    if not digitos:
        return ""
    if len(digitos) == 10:
        return "52" + digitos
    if len(digitos) == 12 and digitos.startswith("52"):
        return digitos
    if len(digitos) == 13 and digitos.startswith("521"):
        return digitos
    return digitos


def _parsear_fecha(fecha_str: str):
    """
    Intenta parsear una fecha en varios formatos.
    Devuelve un objeto date o None.
    """
    if not fecha_str:
        return None

    # Si es un datetime de openpyxl, convertir directo
    if hasattr(fecha_str, "year") and hasattr(fecha_str, "month") and hasattr(fecha_str, "day"):
        try:
            return date(fecha_str.year, fecha_str.month, fecha_str.day)
        except Exception:
            pass

    fecha_str = str(fecha_str).strip()

    # Formato "21 de marzo de 2026"
    if " de " in fecha_str.lower():
        partes = fecha_str.lower().split(" de ")
        if len(partes) == 3:
            try:
                dia = int(partes[0])
                mes = MESES_ES.get(partes[1].strip())
                anio = int(partes[2].split()[0])
                if mes:
                    return date(anio, mes, dia)
            except (ValueError, TypeError):
                pass

    # Formato ISO con tiempo "2026-03-21 00:00:00" o "2026-03-21T10:00:00"
    if "-" in fecha_str:
        try:
            return datetime.strptime(fecha_str.split(" ")[0].split("T")[0], "%Y-%m-%d").date()
        except ValueError:
            pass

    # Formato "21/03/2026"
    if "/" in fecha_str:
        partes = fecha_str.split("/")
        if len(partes) == 3:
            try:
                dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
                if anio < 100:
                    anio += 2000
                return date(anio, mes, dia)
            except (ValueError, TypeError):
                pass

    return None


def format_date_long(fecha_str) -> str:
    """
    Convierte una fecha a formato largo español:
    "2026-03-21" → "21 de marzo de 2026"
    """
    if not fecha_str:
        return ""

    # Si ya está en formato largo, devolverla tal cual
    if " de " in str(fecha_str).lower():
        return str(fecha_str)

    fecha = _parsear_fecha(fecha_str)
    if not fecha:
        return str(fecha_str)

    return f"{fecha.day} de {MESES_ES_NOMBRE[fecha.month]} de {fecha.year}"


def es_manana(fecha_str) -> bool:
    """Devuelve True si la fecha es mañana."""
    fecha = _parsear_fecha(fecha_str)
    if not fecha:
        return False
    return fecha == (date.today() + timedelta(days=1))


def es_hoy(fecha_str) -> bool:
    """Devuelve True si la fecha es hoy."""
    fecha = _parsear_fecha(fecha_str)
    if not fecha:
        return False
    return fecha == date.today()


def es_pasado(fecha_str) -> bool:
    """Devuelve True si la fecha ya pasó."""
    fecha = _parsear_fecha(fecha_str)
    if not fecha:
        return False
    return fecha < date.today()


def dias_hasta(fecha_str):
    """Devuelve los días que faltan (positivo) o pasaron (negativo)."""
    fecha = _parsear_fecha(fecha_str)
    if not fecha:
        return None
    return (fecha - date.today()).days


def format_fecha_para_mensaje(fecha_str) -> str:
    """
    Formatea la fecha para el mensaje.
    Si es mañana, devuelve "mañana".
    Si no, "el día 15 de octubre de 2026".
    """
    if es_manana(fecha_str):
        return "mañana"
    return f"el día {format_date_long(fecha_str)}"


def extraer_nombre_clinica(nombre_completo: str) -> str:
    """
    Quita prefijos como "Clínica Veterinaria " y deja "Baalak (Central)".
    """
    if not nombre_completo:
        return ""
    nombre = str(nombre_completo).strip()
    prefijos = [
        "Clínica Veterinaria ",
        "La clínica veterinaria ",
        "la clínica veterinaria ",
    ]
    for prefijo in prefijos:
        if nombre.lower().startswith(prefijo.lower()):
            return nombre[len(prefijo):].strip()
    return nombre