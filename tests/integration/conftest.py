"""Fixtures de las pruebas de integración: una base SQLite en memoria ya sembrada.

Ninguna prueba escribe en `data/`: el motor vive en memoria y el script de siembra se ejerce
sobre `tmp_path` (CLAUDE.md §9 y restricciones del sprint).
"""

from __future__ import annotations

import pytest

from core.catalog import abrir_sesion, crear_esquema, crear_motor
from scripts.seed import sembrar


@pytest.fixture
def motor():
    """Motor SQLite en memoria con el esquema completo ya creado."""
    engine = crear_motor("sqlite://")
    crear_esquema(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sesion(motor):
    """Sesión sobre el motor en memoria con la línea base ya sembrada y confirmada."""
    with abrir_sesion(motor) as sesion:
        sembrar(sesion)
        yield sesion
