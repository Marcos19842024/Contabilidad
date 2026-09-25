# -*- coding: utf-8 -*-
"""
core/utilidades.py
Utilidades de formato de moneda, fechas y evaluación de expresiones.
"""

from datetime import datetime

from config.campos import MESES_ES


def parse_fecha(txt):
    """Convierte una fecha en distintos formatos a 'dd-mm-yyyy'."""
    if not txt:
        return datetime.now().strftime("%d-%m-%Y")
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(txt.strip(), fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return txt.replace("/", "-")


def mes_anio_desde_fecha(fecha_str):
    """
    A partir de una fecha 'dd/mm/aaaa' devuelve (mes_nombre, anio).
    Devuelve (None, None) si no se puede parsear.
    """
    if not fecha_str:
        return None, None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            dt = datetime.strptime(str(fecha_str).strip(), fmt)
            return MESES_ES[dt.month - 1], dt.year
        except ValueError:
            continue
    return None, None


def formatear_moneda(valor):
    """Formatea un número como moneda con dos decimales."""
    try:
        return f"{float(valor):,.2f}"
    except (ValueError, TypeError):
        return "0.00"


def limpiar_moneda(texto):
    """Limpia un texto de moneda y devuelve float."""
    if not texto:
        return 0.0
    texto = str(texto).replace("$", "").replace(",", "").replace(" ", "").strip()
    try:
        return float(texto)
    except ValueError:
        return 0.0


def tokenizar(texto):
    """Tokeniza una expresión matemática simple."""
    tokens = []
    num = ""
    for c in texto:
        if c in "+*/()":
            if num:
                tokens.append(num)
                num = ""
            tokens.append(c)
        elif c == "-":
            if not tokens or tokens[-1] in ("+", "-", "*", "/", "("):
                num += c
            else:
                if num:
                    tokens.append(num)
                    num = ""
                tokens.append(c)
        elif c == " ":
            if num:
                tokens.append(num)
                num = ""
        else:
            num += c
    if num:
        tokens.append(num)
    return tokens


def evaluar_expresion(texto):
    """
    Evalúa una expresión aritmética simple (+ - * / paréntesis).
    Devuelve 0.0 si hay error.
    """
    if texto is None:
        return 0.0
    texto = str(texto).strip()
    if not texto:
        return 0.0
    texto = texto.replace("$", "").replace(",", "").strip()

    if not any(op in texto for op in "+*/()"):
        if texto.count("-") == 0 or (texto.count("-") == 1 and texto.startswith("-")):
            return limpiar_moneda(texto)

    permitidos = set("0123456789.+-*/() ")
    if not all(c in permitidos for c in texto):
        return 0.0

    try:
        tokens = tokenizar(texto)
        if not tokens:
            return 0.0
        pos = [0]

        def parse_expresion():
            valor = parse_termino()
            while pos[0] < len(tokens) and tokens[pos[0]] in ("+", "-"):
                op = tokens[pos[0]]
                pos[0] += 1
                der = parse_termino()
                valor = valor + der if op == "+" else valor - der
            return valor

        def parse_termino():
            valor = parse_factor()
            while pos[0] < len(tokens) and tokens[pos[0]] in ("*", "/"):
                op = tokens[pos[0]]
                pos[0] += 1
                der = parse_factor()
                if op == "*":
                    valor *= der
                else:
                    if der == 0:
                        raise ZeroDivisionError()
                    valor /= der
            return valor

        def parse_factor():
            if pos[0] >= len(tokens):
                raise ValueError("Expresión incompleta")
            tok = tokens[pos[0]]
            if tok == "(":
                pos[0] += 1
                valor = parse_expresion()
                if pos[0] >= len(tokens) or tokens[pos[0]] != ")":
                    raise ValueError("Falta paréntesis")
                pos[0] += 1
                return valor
            elif tok == "-":
                pos[0] += 1
                return -parse_factor()
            else:
                pos[0] += 1
                return float(tok)

        resultado = parse_expresion()
        if pos[0] != len(tokens):
            raise ValueError("Sobran tokens")
        return round(resultado, 2)
    except Exception:
        return 0.0