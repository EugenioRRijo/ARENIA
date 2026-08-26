"""Cantidad de obra trazable: la unidad de intercambio entre adaptadores y núcleo."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType

from core.contracts.dominio import Dominio
from core.contracts.unidades import normalizar_unidad


class OrigenTipo(StrEnum):
    """De dónde salió la cantidad. Determina qué significa `origen_id`."""

    IFC = "ifc"  # origen_id = GlobalId del elemento IFC
    REGLA = "regla"  # origen_id = objeto paramétrico; `regla` = expresión evaluada
    TABULAR = "tabular"  # origen_id = fila de la hoja o tabla de entrada
    CSV = "csv"  # origen_id = fila o clave del CSV
    MANUAL = "manual"  # origen_id = referencia declarada por el usuario


@dataclass(frozen=True, slots=True)
class ItemComputo:
    """Una cantidad de obra con su procedencia.

    `regla` y `parametros` registran la expresión y los valores que la produjeron (regla R1).
    `especificaciones` guarda atributos comparables con el modelo y el APU, por ejemplo
    {"diametro": "4 pulg", "material": "PVC"} (regla R4).
    """

    codigo_partida: str
    descripcion: str
    unidad: str
    cantidad: Decimal
    origen_id: str
    origen_tipo: OrigenTipo
    dominio: Dominio
    regla: str | None = None
    parametros: Mapping[str, Decimal] = field(default_factory=dict, hash=False)
    especificaciones: Mapping[str, str] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        if not self.codigo_partida.strip():
            raise ValueError("codigo_partida no puede estar vacío")
        if not self.origen_id.strip():
            raise ValueError("origen_id no puede estar vacío: toda cantidad debe ser trazable")
        if not isinstance(self.cantidad, Decimal):
            raise TypeError(f"cantidad debe ser Decimal, no {type(self.cantidad).__name__}")
        if self.cantidad < 0:
            raise ValueError(f"cantidad no puede ser negativa: {self.cantidad}")
        if self.origen_tipo is OrigenTipo.REGLA and not self.regla:
            raise ValueError("un ItemComputo de origen REGLA debe declarar la expresión en 'regla'")
        object.__setattr__(self, "unidad", normalizar_unidad(self.unidad))
        object.__setattr__(self, "parametros", MappingProxyType(dict(self.parametros)))
        object.__setattr__(self, "especificaciones", MappingProxyType(dict(self.especificaciones)))
