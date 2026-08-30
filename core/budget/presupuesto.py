"""Armado del presupuesto: de las cantidades de obra al precio de cada renglón.

`generar_presupuesto` cose las tres piezas del núcleo sin conocer ningún dominio: recibe los
`ItemComputo` que produjo un adaptador, las composiciones del catálogo y los parámetros de costo, y
llama al motor puro `core.costing.calcular_apu` una vez por renglón.

`elaborar` es el flujo completo de la Sesión I0.5: presupuesto, curva y **auditoría siempre**, sin
que el usuario la pida (principio 7 de CLAUDE.md §2). Por eso devuelve `ResultadoElaboracion`, que
lleva el informe junto al presupuesto: no hay forma de obtener uno sin el otro.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from core.budget.curva import PeriodoPlan, con_curva, generar_curva
from core.contracts.apu import ComposicionAPU, ParametrosCosto
from core.contracts.item_computo import ItemComputo
from core.contracts.presupuesto import PartidaPresupuestada, Presupuesto
from core.costing import calcular_apu
from core.verification import auditar
from core.verification.informe import InformeAuditoria

__all__ = ["ResultadoElaboracion", "elaborar", "generar_presupuesto"]

MONEDA_POR_DEFECTO = "USD"


@dataclass(frozen=True, slots=True)
class ResultadoElaboracion:
    """Lo que produce una elaboración: el presupuesto y el informe que siempre lo acompaña."""

    presupuesto: Presupuesto
    informe: InformeAuditoria


def generar_presupuesto(
    items: Sequence[ItemComputo],
    composiciones: Mapping[str, ComposicionAPU],
    parametros: ParametrosCosto,
    codigo: str,
    fecha: date,
    moneda: str = MONEDA_POR_DEFECTO,
) -> Presupuesto:
    """Un `PartidaPresupuestada` por ítem, en el orden recibido, con su precio recién calculado.

    Lanza `ValueError` con la lista de códigos si alguna cantidad no tiene composición de APU: un
    presupuesto incompleto es un presupuesto sin precio, no un presupuesto con ceros.
    """
    faltantes = _codigos_sin_composicion(items, composiciones)
    if faltantes:
        raise ValueError("no hay composicion de APU para las partidas: " + ", ".join(faltantes))

    partidas = tuple(
        PartidaPresupuestada(
            item=item,
            apu=composiciones[item.codigo_partida],
            resultado=calcular_apu(composiciones[item.codigo_partida], parametros),
        )
        for item in items
    )
    return Presupuesto(codigo=codigo, fecha=fecha, moneda=moneda, partidas=partidas)


def elaborar(
    items: Sequence[ItemComputo],
    composiciones: Mapping[str, ComposicionAPU],
    parametros: ParametrosCosto,
    codigo: str,
    fecha: date,
    moneda: str = MONEDA_POR_DEFECTO,
    plan: Sequence[PeriodoPlan] | None = None,
) -> ResultadoElaboracion:
    """Genera el presupuesto, le añade la curva si hay plan y lo audita siempre.

    Sin `plan` el presupuesto no lleva curva y la regla R2 lo hace constar como INFO; con plan, la
    curva cierra exactamente en el total.
    """
    presupuesto = generar_presupuesto(items, composiciones, parametros, codigo, fecha, moneda)
    if plan is not None:
        presupuesto = con_curva(presupuesto, generar_curva(presupuesto, plan))
    return ResultadoElaboracion(presupuesto=presupuesto, informe=auditar(presupuesto))


def _codigos_sin_composicion(
    items: Sequence[ItemComputo], composiciones: Mapping[str, ComposicionAPU]
) -> list[str]:
    faltantes: list[str] = []
    for item in items:
        if item.codigo_partida not in composiciones and item.codigo_partida not in faltantes:
            faltantes.append(item.codigo_partida)
    return faltantes
