# -*- coding: utf-8 -*-
"""
sat/descarga.py
Modulo unificado para descargar CFDIs del SAT.

Reutiliza la logica exacta de los test_*.py que ya funcionaron:
  - test_conversion.py   -> preparar_fiel + autenticar
  - test_solicitud.py    -> solicitar descarga
  - test_verificacion.py -> verificar estado
  - test_descarga.py     -> descargar paquetes y extraer XMLs

NO modifica conversion.py ni la logica de la FIEL.
"""

import base64
import zipfile
from datetime import datetime
from pathlib import Path

from cfdiclient import (
    Autenticacion,
    DescargaMasiva,
    Fiel,
    SolicitaDescargaRecibidos,
    VerificaSolicitudDescarga,
)


# ============================================================
# PREPARAR LA FIEL (igual que test_conversion.py)
# ============================================================
def _cargar_fiel(ruta_cer, ruta_key, password):
    """Prepara la FIEL y devuelve un objeto Fiel listo para usar."""
    from sat.conversion import preparar_fiel

    ruta_cer_der, ruta_key_der = preparar_fiel(ruta_cer, ruta_key, password)

    with open(ruta_cer_der, "rb") as f:
        cer_der = f.read()
    with open(ruta_key_der, "rb") as f:
        key_der = f.read()

    # Password vacio: el key ya viene desencriptado
    return Fiel(cer_der, key_der, "")


# ============================================================
# AUTENTICAR (igual que test_conversion.py)
# ============================================================
def obtener_token(ruta_cer, ruta_key, password):
    """Autentica con el SAT y devuelve un token."""
    fiel = _cargar_fiel(ruta_cer, ruta_key, password)
    auth = Autenticacion(fiel)
    return auth.obtener_token()


# ============================================================
# SOLICITAR DESCARGA (igual que test_solicitud.py)
# ============================================================
def solicitar_descarga(ruta_cer, ruta_key, password, rfc,
                       fecha_inicio, fecha_fin,
                       tipo_solicitud="CFDI"):
    """
    Solicita una descarga de CFDI recibidos.

    Parametros:
      - fecha_inicio, fecha_fin: datetime.datetime

    Devuelve el dict de cfdiclient:
      {"id_solicitud": "...", "cod_estatus": "5000", "mensaje": "..."}
    """
    fiel = _cargar_fiel(ruta_cer, ruta_key, password)
    token = Autenticacion(fiel).obtener_token()

    solicitud = SolicitaDescargaRecibidos(fiel)
    resultado = solicitud.solicitar_descarga(
        token=token,
        rfc_solicitante=rfc,
        fecha_inicial=fecha_inicio,
        fecha_final=fecha_fin,
        rfc_receptor=rfc,
        tipo_solicitud=tipo_solicitud,
    )
    return resultado


# ============================================================
# VERIFICAR ESTADO (igual que test_verificacion.py)
# ============================================================
def verificar_solicitud(ruta_cer, ruta_key, password, rfc, id_solicitud):
    """
    Verifica el estado de una solicitud (con reintentos por timeout).
    """
    import time as _time

    fiel = _cargar_fiel(ruta_cer, ruta_key, password)

    ultimo_error = None
    for intento in range(3):
        try:
            token = Autenticacion(fiel).obtener_token()
            verificacion = VerificaSolicitudDescarga(fiel)
            resultado = verificacion.verificar_descarga(
                token=token,
                rfc_solicitante=rfc,
                id_solicitud=id_solicitud,
            )

            estado = str(resultado.get("estado_solicitud", "?"))
            mensaje_sat = resultado.get("mensaje", "")
            codigo = str(resultado.get("codigo_estado_solicitud", ""))

            # Interpretar mensajes confusos
            mensaje_mostrar = mensaje_sat
            if estado == "5":
                # Rechazada - el SAT a veces no da motivo claro
                if "aceptada" in mensaje_sat.lower():
                    mensaje_mostrar = (
                        "Solicitud rechazada. Posible causa: ya existe "
                        "una solicitud en proceso para el mismo periodo. "
                        "Espera unos minutos o usa un rango de fechas distinto."
                    )
                else:
                    mensaje_mostrar = f"Solicitud rechazada: {mensaje_sat}"

            return {
                "estado": estado,
                "mensaje": mensaje_mostrar,
                "numero_cfdis": str(resultado.get("numero_cfdis", "0")),
                "paquetes": resultado.get("paquetes", []) or [],
                "codigo": codigo,
            }
        except Exception as e:
            ultimo_error = e
            msg = str(e).lower()
            if "timed out" in msg or "timeout" in msg:
                _time.sleep(5)
                continue
            raise

    return {
        "estado": "2",
        "mensaje": "El SAT no responde, reintentando...",
        "numero_cfdis": "0",
        "paquetes": [],
        "codigo": "",
    }


# ============================================================
# DESCARGAR PAQUETES (igual que test_descarga.py)
# ============================================================
def descargar_paquetes(ruta_cer, ruta_key, password, rfc,
                       paquetes, carpeta_destino="/tmp/sat_descargas"):
    """
    Descarga los paquetes (ZIP) y extrae los XML.

    Devuelve: lista de rutas a los XML extraidos.
    """
    fiel = _cargar_fiel(ruta_cer, ruta_key, password)
    token = Autenticacion(fiel).obtener_token()
    descarga = DescargaMasiva(fiel)

    carpeta_destino = Path(carpeta_destino)
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    for paquete in paquetes:
        paquete = paquete.strip()
        if not paquete:
            continue

        resultado = descarga.descargar_paquete(
            token=token,
            rfc_solicitante=rfc,
            id_paquete=paquete,
        )

        # En test_descarga.py la clave era "paquete" (no "paquete_b64")
        contenido_b64 = ""
        if isinstance(resultado, dict):
            contenido_b64 = resultado.get("paquete", "")

        if not contenido_b64:
            print(f"WARN: paquete sin contenido: {paquete}")
            continue

        contenido_zip = base64.b64decode(contenido_b64)
        ruta_zip = carpeta_destino / f"{paquete}.zip"
        ruta_zip.write_bytes(contenido_zip)

        try:
            with zipfile.ZipFile(ruta_zip, "r") as z:
                z.extractall(carpeta_destino)
            ruta_zip.unlink()
        except Exception as e:
            print(f"WARN: error descomprimiendo {ruta_zip}: {e}")

    return list(carpeta_destino.glob("*.xml"))


# ============================================================
# FLUJO COMPLETO (orquesta los 4 pasos)
# ============================================================
def flujo_completo(ruta_cer, ruta_key, password, rfc,
                   fecha_inicio, fecha_fin,
                   carpeta_destino="/tmp/sat_descargas",
                   tipo_solicitud="CFDI",
                   callback_estado=None):
    """
    Flujo completo: solicita -> (espera externa) -> descarga.

    NOTA: Esta funcion SOLO hace solicitar + descargar.
    La espera se maneja en la UI (dialogos/espera_sat.py)
    usando verificar_solicitud() como verificador.

    Devuelve:
      {
        "id_solicitud": "...",
        "xmls": [Path, ...],
        "total_cfdis": int,
      }
    """
    # 1) Solicitar
    resultado_sol = solicitar_descarga(
        ruta_cer, ruta_key, password, rfc,
        fecha_inicio, fecha_fin,
        tipo_solicitud=tipo_solicitud,
    )

    id_solicitud = resultado_sol.get("id_solicitud", "")
    if not id_solicitud:
        raise RuntimeError(
            f"El SAT no devolvio id_solicitud: {resultado_sol}"
        )

    if callback_estado:
        callback_estado({
            "estado": "1",
            "mensaje": "Solicitud aceptada",
            "numero_cfdis": "0",
            "paquetes": [],
        })

    return {
        "id_solicitud": id_solicitud,
        "xmls": [],
        "total_cfdis": 0,
    }


# ============================================================
# PRUEBA DIRECTA
# ============================================================
if __name__ == "__main__":
    from config.config_egresos import cargar_config_egresos

    cfg = cargar_config_egresos()
    print("Config SAT:")
    print("  RFC:  " + str(cfg.get("rfc_receptor")))
    print("  CER:  " + str(cfg.get("certificado_cer")))
    print("  KEY:  " + str(cfg.get("certificado_key")))
    print()
    print("Probando autenticacion (NO toca la FIEL, solo usa preparar_fiel)...")
    try:
        token = obtener_token(
            cfg["certificado_cer"],
            cfg["certificado_key"],
            cfg["password_fiel"],
        )
        print("OK Token: " + token[:60] + "...")
    except Exception as e:
        print("ERROR: " + str(e))
        import traceback
        traceback.print_exc()