"""Motor de costos: deriva un precio unitario a partir de una composición de APU.

Fórmula (CLAUDE.md §4, ``Decimal``, sin redondeos intermedios)::

    materiales         = Σ cantidad × precio            <- NO se divide entre rendimiento
    equipos            = Σ (cantidad × precio × depreciación) / rendimiento
    mano_obra          = ( Σ cantidad × sueldo × (1 + fcas)
                            + bono × Σ cantidad ) / rendimiento
    costo_directo      = materiales + equipos + mano_obra
    con_administracion = costo_directo × (1 + administración)
    precio_unitario    = con_administracion × (1 + utilidad)  <- en cascada, NO (1 + adm + util)

``calcular_apu`` es una función pura: no accede a base de datos ni mantiene estado. Recibe una
``ComposicionAPU`` y unos ``ParametrosCosto`` y devuelve un ``ResultadoAPU``.
"""

from __future__ import annotations

from decimal import Decimal

from core.contracts.apu import ComposicionAPU, ParametrosCosto, ResultadoAPU


def calcular_apu(composicion: ComposicionAPU, parametros: ParametrosCosto) -> ResultadoAPU:
    """Calcula el precio unitario de una partida a partir de su composición.

    Los materiales entran completos, sin dividir entre el rendimiento (error probable n.º 1).
    Administración y utilidad se aplican en cascada, una sobre la otra (error probable n.º 2).
    """
    materiales = sum((linea.total for linea in composicion.materiales), Decimal(0))

    equipos_total = sum((linea.total for linea in composicion.equipos), Decimal(0))
    equipos = equipos_total / composicion.rendimiento

    sueldos_con_fcas = sum(
        (linea.total * (1 + parametros.fcas) for linea in composicion.mano_obra), Decimal(0)
    )
    bono_total = parametros.bono_alimentacion * composicion.total_obreros
    mano_obra = (sueldos_con_fcas + bono_total) / composicion.rendimiento

    costo_directo = materiales + equipos + mano_obra
    con_administracion = costo_directo * (1 + parametros.administracion)
    precio_unitario = con_administracion * (1 + parametros.utilidad)

    return ResultadoAPU(
        materiales=materiales,
        equipos=equipos,
        mano_obra=mano_obra,
        costo_directo=costo_directo,
        con_administracion=con_administracion,
        precio_unitario=precio_unitario,
    )
