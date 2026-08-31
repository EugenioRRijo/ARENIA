"""Esquemas Pydantic, espejo de los contratos del nucleo.

Los montos (`Decimal`) viajan siempre como texto (`str`), nunca como `float` (CLAUDE.md §2.3): la
conversion a `Decimal` ocurre en la frontera, construyendo siempre desde el mismo texto que
persiste `core.models.tipos.DecimalExacto`.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class PartidaRespuesta(BaseModel):
    """Cabecera de una partida del catalogo."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    descripcion: str
    unidad: str
    dominio: str


class InsumoRespuesta(BaseModel):
    """Un insumo del catalogo, con su precio en la lista vigente si la hay."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    descripcion: str
    tipo: str
    unidad: str | None
    precio_vigente: str | None


class ListaRespuesta(BaseModel):
    """Cabecera de una lista de precios registrada."""

    model_config = ConfigDict(from_attributes=True)

    nombre: str
    moneda: str
    fecha_vigencia: date
    origen: str


class CargaListaRespuesta(BaseModel):
    """Lo que produjo cargar un archivo de precios: la lista creada y los insumos desconocidos."""

    lista: ListaRespuesta
    desconocidos: list[str]


class CambioRespuesta(BaseModel):
    """Un cambio de precio del historial (UC-02)."""

    insumo: str
    precio_anterior: str
    precio_nuevo: str
    variacion: str
    fecha: date
