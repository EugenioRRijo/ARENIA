"""Forma en memoria del presupuesto y su curva. Entrada de toda regla de verificación."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from core.contracts.apu import ComposicionAPU, ResultadoAPU
from core.contracts.item_computo import ItemComputo


@dataclass(frozen=True, slots=True)
class PartidaPresupuestada:
    """Un renglón del presupuesto: la cantidad (item), su desglose (apu) y su precio (resultado)."""

    item: ItemComputo
    apu: ComposicionAPU
    resultado: ResultadoAPU

    def __post_init__(self) -> None:
        if self.item.codigo_partida != self.apu.codigo_partida:
            raise ValueError(
                f"el item ({self.item.codigo_partida}) y el APU ({self.apu.codigo_partida}) "
                "no corresponden a la misma partida"
            )

    @property
    def total(self) -> Decimal:
        return self.item.cantidad * self.resultado.precio_unitario


@dataclass(frozen=True, slots=True)
class PuntoCurva:
    """Un período del plan de trabajo: monto invertido en el período y acumulado hasta él."""

    periodo: str
    monto: Decimal
    acumulado: Decimal


@dataclass(frozen=True, slots=True)
class Presupuesto:
    codigo: str
    fecha: date
    moneda: str
    partidas: tuple[PartidaPresupuestada, ...]
    curva: tuple[PuntoCurva, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "partidas", tuple(self.partidas))
        object.__setattr__(self, "curva", tuple(self.curva))

    @property
    def total(self) -> Decimal:
        return sum((partida.total for partida in self.partidas), Decimal(0))

    @property
    def total_curva(self) -> Decimal:
        """Acumulado final de la curva. La regla R2 exige que sea igual a `total`."""
        return self.curva[-1].acumulado if self.curva else Decimal(0)
