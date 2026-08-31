"""Rutas de consulta del catalogo: salud, partidas e insumos con su precio vigente."""

from __future__ import annotations

from fastapi import APIRouter

from api.dependencias import SesionDep
from api.esquemas import InsumoRespuesta, PartidaRespuesta
from core.catalog import Catalogo, CatalogoIncompleto
from core.contracts.dominio import Dominio

router = APIRouter(tags=["catalogo"])


@router.get("/salud")
def salud() -> dict[str, str]:
    """Ping de disponibilidad, sin tocar la base de datos."""
    return {"estado": "ok"}


@router.get("/partidas", response_model=list[PartidaRespuesta])
def listar_partidas(sesion: SesionDep, dominio: Dominio | None = None) -> list[PartidaRespuesta]:
    """Partidas del catalogo, ordenadas por codigo; filtradas por dominio si se indica."""
    return [
        PartidaRespuesta.model_validate(partida) for partida in Catalogo(sesion).partidas(dominio)
    ]


@router.get("/insumos", response_model=list[InsumoRespuesta])
def listar_insumos(sesion: SesionDep) -> list[InsumoRespuesta]:
    """Insumos del catalogo con su precio en la lista vigente; `None` si no hay lista vigente."""
    catalogo = Catalogo(sesion)
    precios: dict[int, str] = {}
    try:
        lista = catalogo.lista_vigente()
    except CatalogoIncompleto:
        lista = None
    if lista is not None:
        precios = {precio.insumo_id: str(precio.precio) for precio in lista.precios}
    return [
        InsumoRespuesta(
            codigo=insumo.codigo,
            descripcion=insumo.descripcion,
            tipo=insumo.tipo,
            unidad=insumo.unidad,
            precio_vigente=precios.get(insumo.id),
        )
        for insumo in catalogo.insumos()
    ]
