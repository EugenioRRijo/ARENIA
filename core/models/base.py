"""Clase declarativa común de todos los modelos."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Raíz declarativa. `Base.metadata` es el esquema completo del sistema."""
