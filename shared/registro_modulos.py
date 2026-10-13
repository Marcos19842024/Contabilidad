# -*- coding: utf-8 -*-
"""
shared/registro_modulos.py
Registro declarativo de módulos de Vet Suite.

Cada módulo se declara aquí una sola vez. La ventana principal solo itera
sobre esta lista. Agregar un módulo nuevo = agregar una entrada acá,
sin tocar app/principal.py.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


CATEGORIAS = {
    "operacion":    {"nombre": "Operación",      "orden": 1},
    "clientes":     {"nombre": "Clientes",       "orden": 2},
    "comunicacion": {"nombre": "Comunicación",   "orden": 3},
    "reportes":     {"nombre": "Reportes",       "orden": 4},
    "admin":        {"nombre": "Administración", "orden": 5},
}


@dataclass(frozen=True)
class Modulo:
    id: str
    nombre: str
    descripcion: str
    icono: str
    categoria: str
    factory: Callable                         # legacy: abre como Toplevel
    atajo: Optional[str] = None
    activo: bool = True
    panel: Optional[Callable] = None          # nuevo: abre embebido


# ── Factories (imports perezosos para evitar ciclos) ─────────────────────

def _abrir_ingresos(master):
    from modulos.ingresos import AppIngresos
    return AppIngresos(master=master)


def _abrir_egresos(master):
    from modulos.egresos import AppEgresos
    return AppEgresos(master=master)


def _abrir_estetica(master):
    from modulos.estetica_transportes import AppEsteticaTransportes
    return AppEsteticaTransportes(master=master)

def _panel_estetica(master, on_volver=None):
    from modulos.estetica_transportes import PanelEsteticaTransportes
    return PanelEsteticaTransportes(master=master, on_volver=on_volver)

def _abrir_recordatorios(master):
    from modulos.recordatorios import AppRecordatorios
    return AppRecordatorios(master=master)


# ── Declaración de módulos ───────────────────────────────────────────────

MODULOS: tuple[Modulo, ...] = (
    Modulo(
        id="ingresos",
        nombre="Ingresos",
        descripcion="Facturas de venta\n(descarga del Qvet o Gmail)",
        icono="💰",
        categoria="operacion",
        factory=_abrir_ingresos,
        atajo="Control-Key-1",
    ),
    Modulo(
        id="egresos",
        nombre="Egresos",
        descripcion="Facturas de compra\n(descarga del SAT)",
        icono="💸",
        categoria="operacion",
        factory=_abrir_egresos,
        atajo="Control-Key-2",
    ),
    Modulo(
        id="estetica_transportes",
        nombre="Estética y Transportes",
        descripcion="Clientes, mascotas, rutas y tarifas",
        icono="🐾",
        categoria="clientes",
        factory=_abrir_estetica,
        panel=_panel_estetica,        # ← esto activa el embed
        atajo="Control-Key-3",
    ),
    Modulo(
        id="recordatorios",
        nombre="Recordatorios",
        descripcion="Citas y vacunas\npor WhatsApp",
        icono="📅",
        categoria="comunicacion",
        factory=_abrir_recordatorios,
        atajo="Control-Key-4",
    ),
    # ← módulos nuevos van aquí, sin tocar la UI
)


def modulos_activos() -> list[Modulo]:
    return [m for m in MODULOS if m.activo]


def modulos_por_categoria() -> dict[str, list[Modulo]]:
    grupos: dict[str, list[Modulo]] = {}
    for m in modulos_activos():
        grupos.setdefault(m.categoria, []).append(m)
    return dict(sorted(
        grupos.items(),
        key=lambda kv: CATEGORIAS.get(kv[0], {}).get("orden", 99),
    ))


def buscar_modulo(id_modulo: str) -> Optional[Modulo]:
    for m in MODULOS:
        if m.id == id_modulo:
            return m
    return None