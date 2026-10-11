# -*- coding: utf-8 -*-
"""
config/config_ingresos.py
Configuración específica del módulo de Ingresos:
  - Gmail (usuario, password, etiqueta)
  - (futuro) otras opciones de Ingresos

El tema global y las sucursales viven en config_ui.json
(ver core/config_ui.py, config/temas.py, config/veterinaria.py)
"""

from core.rutas import GMAIL_CONFIG_FILE


GMAIL_CONFIG_DEFAULT = {
    "usuario": "",
    "password_app": "",
    "etiqueta": "Facturas QVET",
    "filtro_remitente": "",
    "dias_atras": 30,
}


def cargar_config_correo():
    """Carga ingresos/gmail_config.json o defaults."""
    import json
    if GMAIL_CONFIG_FILE.exists():
        try:
            with open(GMAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in GMAIL_CONFIG_DEFAULT.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(GMAIL_CONFIG_DEFAULT)


def guardar_config_correo(cfg):
    """Guarda ingresos/gmail_config.json."""
    import json
    GMAIL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GMAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)