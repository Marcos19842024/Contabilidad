# core/recordatorios/servicios.py
"""
Diccionario de servicios y procesamiento de textos.
Portado de la app Android (BaalakApps).
"""

from core.recordatorios.formatear import format_string


# Mapa de servicios: código → texto legible
SERVICIOS_MAP = {
    # Transporte
    "transporte de clínica": "transporte",
    "transporte": "transporte",

    # Consultas
    "consulta": "consulta",
    "consulta nocturna": "consulta nocturna",
    "consulta festivos": "consulta en festivos",
    "urgencias": "urgencias",

    # Seguimiento y control
    "seguimiento": "seguimiento",
    "control sin costo": "control sin costo",
    "control sc": "control sin costo",
    "seguimiento sct": "seguimiento",

    # Medicina preventiva
    "medicina preventiva": "medicina preventiva",
    "vacunación": "vacunación",
    "vacunacion": "vacunación",
    "desparasitación": "desparasitación",
    "desparasitacion": "desparasitación",

    # Hospitalización y cirugía
    "hospitalización": "hospitalización",
    "hospitalizacion": "hospitalización",
    "cirugía": "cirugía",
    "cirugia": "cirugía",
    "procedimiento": "procedimiento",

    # Diagnóstico
    "análisis clínicos": "análisis clínicos",
    "analisis clinicos": "análisis clínicos",
    "rx-us": "radiografía y ultrasonido",
    "rx": "radiografía",
    "us": "ultrasonido",
    "radiografía - us": "radiografía y ultrasonido",
    "radiografia - us": "radiografía y ultrasonido",
    "radiografía": "radiografía",
    "radiografia": "radiografía",
    "ultrasonido": "ultrasonido",

    # Tratamientos
    "tratamiento": "tratamiento",
    "láser": "láser terapia",
    "laser": "láser terapia",
    "láser terapia": "láser terapia",
    "laser terapia": "láser terapia",
    "fisioterapia": "fisioterapia",

    # Documentos
    "certificado médico": "certificado médico",
    "certificado medico": "certificado médico",

    # Servicio FCM
    "servicio fcm": "servicio FCM",
    "fcm": "servicio FCM",

    # Términos quirúrgicos
    "castración": "castración",
    "castracion": "castración",
    "ovh": "OVH (esterilización)",
    "esterilización": "esterilización",
    "esterilizacion": "esterilización",
    "eutanasia": "eutanasia",
}

# Términos quirúrgicos (para búsqueda especial en asunto)
TERMINOS_QUIRURGICOS = ["castración", "castracion", "ovh", "esterilización", "esterilizacion", "eutanasia"]


def combinar_servicios(servicios: list) -> str:
    """
    Combina una lista de servicios en texto legible:
    ["baño", "transporte"] → "baño y transporte"
    ["corte", "baño", "transporte"] → "corte, baño y transporte"
    """
    if not servicios:
        return ""
    unicos = list(dict.fromkeys(servicios))  # dedupe preservando orden
    if len(unicos) == 1:
        return unicos[0]
    if len(unicos) == 2:
        return f"{unicos[0]} y {unicos[1]}"
    return f"{', '.join(unicos[:-1])} y {unicos[-1]}"


def procesar_servicio_estetica(asunto: str, estado: str) -> str:
    """
    Procesa servicios de estética combinando asunto + estado.
    Detecta: baño (B), corte (CP), baño medicado (BM), transporte (T).
    """
    texto_completo = f"{asunto or ''} {estado or ''}".lower()
    servicios = []

    # Detección de transporte (cualquier variante de T)
    tiene_transporte = False
    if "transporte" in texto_completo:
        tiene_transporte = True
    elif " t " in f" {texto_completo} " or texto_completo.strip() == "t":
        tiene_transporte = True
    elif "byt" in texto_completo or "by t" in texto_completo or "b y t" in texto_completo:
        tiene_transporte = True

    # Detección de baño medicado (BM)
    tiene_bm = "bm" in texto_completo or "baño medicado" in texto_completo

    # Detección de corte (CP)
    tiene_cp = (
        "cp" in texto_completo.split()
        or "corte" in texto_completo
        or "cp y" in texto_completo
        or "cp," in texto_completo
        or texto_completo.strip().startswith("cp")
    )

    # Detección de baño (B, no BM, no BYT)
    tiene_b = False
    if "baño" in texto_completo and "medicado" not in texto_completo:
        tiene_b = True
    elif "byt" in texto_completo or "by t" in texto_completo or "b y t" in texto_completo:
        tiene_b = True
    elif " b " in f" {texto_completo} " or texto_completo.strip() == "b":
        tiene_b = True

    # Construir lista de servicios en orden lógico
    if tiene_cp:
        servicios.append("corte")
    if tiene_b:
        servicios.append("baño")
    if tiene_bm:
        servicios.append("baño medicado")
    if tiene_transporte:
        servicios.append("transporte")

    if not servicios:
        # No se detectaron servicios específicos → procesar como texto genérico
        return _procesar_texto_generico(texto_completo)

    return combinar_servicios(servicios)


def _procesar_texto_generico(texto: str) -> str:
    """Cuando no hay servicios detectados, intenta mapear partes del texto."""
    if not texto or not texto.strip():
        return ""

    partes = texto.replace("-", " ").replace("_", " ").replace(",", " ").split()
    partes = [p.strip() for p in partes if p.strip()]

    servicios = []
    for parte in partes:
        if parte in ("cp", "bm", "b", "t"):
            continue
        parte_lower = parte.lower()
        for key, valor in SERVICIOS_MAP.items():
            if key in parte_lower or parte_lower in key:
                if valor not in servicios:
                    servicios.append(valor)
                break

    if not servicios:
        return format_string(texto)

    return combinar_servicios(servicios)


def procesar_servicio(tipo_visita: str, asunto: str, estado: str) -> str:
    """
    Procesa el servicio final combinando tipo_visita, asunto y estado.
    Es la función principal que llama el resto del código.
    """
    asunto = asunto or ""
    estado = estado or ""
    tipo_visita = tipo_visita or ""

    # 1. Si el asunto contiene término quirúrgico específico → ese gana
    asunto_lower = asunto.lower()
    for termino in TERMINOS_QUIRURGICOS:
        if termino in asunto_lower:
            return SERVICIOS_MAP.get(termino, termino)

    tipo_lower = tipo_visita.lower().strip()

    # 2. Si es peluquería o estética → procesar especial
    if "peluquer" in tipo_lower or "estética" in tipo_lower or "estetica" in tipo_lower:
        return procesar_servicio_estetica(asunto, estado)

    # 3. Para otros tipos → buscar en todos los campos
    servicios = []
    for campo in (tipo_visita, estado, asunto):
        if not campo or not campo.strip():
            continue
        campo_lower = campo.lower()
        for key, valor in SERVICIOS_MAP.items():
            if key in campo_lower and valor not in servicios:
                servicios.append(valor)

        # Términos compuestos
        if "rx" in campo_lower and "us" in campo_lower:
            if "radiografía y ultrasonido" not in servicios:
                servicios.append("radiografía y ultrasonido")

    if not servicios:
        return format_string(tipo_visita)

    return combinar_servicios(servicios)