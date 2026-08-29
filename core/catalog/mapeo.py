"""Conversión entre modelos persistidos y contratos de interfaz.

**Único** lugar del sistema donde se cruza esa frontera (docs/modelo_datos.md §8). Los modelos se
usan cualificados (`models.X`) y los contratos por su nombre, para que nunca se confundan los siete
pares homónimos.
"""

from __future__ import annotations

from core import models
from core.catalog.errores import CatalogoIncompleto
from core.contracts.apu import (
    ComposicionAPU,
    LineaEquipo,
    LineaManoObra,
    LineaMaterial,
    Rendimiento,
    TipoRendimiento,
)


def a_composicion(
    partida: models.Partida,
    lista: models.ListaPrecios,
    rendimiento: models.Rendimiento,
) -> ComposicionAPU:
    """Arma la `ComposicionAPU` del contrato con los precios de `lista` y el rendimiento dado.

    Las líneas se recorren por `orden`, que es el del documento original: sin él las tuplas del
    contrato no serían iguales a las del fixture de la línea base.
    """
    precios = {precio.insumo_id: precio.precio for precio in lista.precios}
    materiales: list[LineaMaterial] = []
    equipos: list[LineaEquipo] = []
    mano_obra: list[LineaManoObra] = []

    for linea in sorted(partida.composicion, key=lambda linea: linea.orden):
        insumo = linea.insumo
        precio = precios.get(insumo.id)
        if precio is None:
            raise CatalogoIncompleto(
                f"el insumo {insumo.codigo} ({insumo.descripcion}) no tiene precio en la lista "
                f"'{lista.nombre}'; no se puede valorar la partida {partida.codigo}"
            )
        if insumo.tipo == models.TipoInsumo.MATERIAL:
            materiales.append(
                LineaMaterial(insumo.descripcion, insumo.unidad or "", linea.cantidad, precio)
            )
        elif insumo.tipo == models.TipoInsumo.EQUIPO:
            if linea.depreciacion is None:
                raise CatalogoIncompleto(
                    f"el equipo {insumo.codigo} ({insumo.descripcion}) no declara depreciación "
                    f"en la partida {partida.codigo}"
                )
            equipos.append(
                LineaEquipo(insumo.descripcion, linea.cantidad, precio, linea.depreciacion)
            )
        else:
            mano_obra.append(LineaManoObra(insumo.descripcion, linea.cantidad, precio))

    return ComposicionAPU(
        codigo_partida=partida.codigo,
        descripcion=partida.descripcion,
        unidad=partida.unidad,
        rendimiento=rendimiento.valor,
        materiales=tuple(materiales),
        equipos=tuple(equipos),
        mano_obra=tuple(mano_obra),
    )


def a_rendimiento(rendimiento: models.Rendimiento) -> Rendimiento:
    """Convierte un rendimiento persistido en el `Rendimiento` del contrato."""
    return Rendimiento(
        codigo_partida=rendimiento.partida.codigo,
        valor=rendimiento.valor,
        tipo=TipoRendimiento(rendimiento.tipo),
        fecha=rendimiento.fecha,
        condiciones=rendimiento.condiciones,
        referencia_ejecucion=(
            rendimiento.ejecucion.referencia if rendimiento.ejecucion is not None else None
        ),
    )
