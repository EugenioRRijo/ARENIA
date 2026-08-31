"""Rutas de listas de precios y su historial de cambios (UC-02)."""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status
from sqlalchemy import select

from api.dependencias import SesionDep
from api.esquemas import CambioRespuesta, CargaListaRespuesta, ListaRespuesta
from core import models
from core.catalog import crear_lista_desde_archivo

router = APIRouter(tags=["listas"])


@router.get("/listas-precios", response_model=list[ListaRespuesta])
def listar_listas_precios(sesion: SesionDep) -> list[ListaRespuesta]:
    """Listas de precios registradas, de la mas antigua a la mas reciente."""
    consulta = select(models.ListaPrecios).order_by(
        models.ListaPrecios.fecha_vigencia, models.ListaPrecios.id
    )
    return [ListaRespuesta.model_validate(lista) for lista in sesion.scalars(consulta)]


@router.post(
    "/listas-precios",
    response_model=CargaListaRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def cargar_lista_precios(
    sesion: SesionDep,
    archivo: Annotated[UploadFile, File()],
    nombre: Annotated[str, Form()],
    moneda: Annotated[str, Form()],
    fecha_vigencia: Annotated[date, Form()],
) -> CargaListaRespuesta:
    """Crea una lista de precios desde un archivo CSV o XLSX y confirma la transaccion (UC-02)."""
    with tempfile.TemporaryDirectory() as directorio:
        ruta = Path(directorio) / archivo.filename
        ruta.write_bytes(archivo.file.read())
        resumen = crear_lista_desde_archivo(sesion, ruta, nombre, moneda, fecha_vigencia)
    sesion.commit()
    return CargaListaRespuesta(
        lista=ListaRespuesta.model_validate(resumen.lista),
        desconocidos=[leido.descripcion for leido in resumen.desconocidos],
    )


@router.get("/cambios-precio", response_model=list[CambioRespuesta])
def listar_cambios_precio(
    sesion: SesionDep,
    insumo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[CambioRespuesta]:
    """Historial de `CambioPrecio`, filtrable por descripcion de insumo y rango de fecha."""
    consulta = (
        select(models.CambioPrecio)
        .join(models.Insumo)
        .order_by(models.CambioPrecio.fecha, models.CambioPrecio.id)
    )
    if insumo is not None:
        consulta = consulta.where(models.Insumo.descripcion == insumo)
    if desde is not None:
        consulta = consulta.where(models.CambioPrecio.fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(models.CambioPrecio.fecha <= hasta)
    return [
        CambioRespuesta(
            insumo=cambio.insumo.descripcion,
            precio_anterior=str(cambio.precio_anterior),
            precio_nuevo=str(cambio.precio_nuevo),
            variacion=str(cambio.variacion),
            fecha=cambio.fecha,
        )
        for cambio in sesion.scalars(consulta)
    ]
