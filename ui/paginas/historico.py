"""Pagina de historico de cambios de precio (UC-02): `CambioPrecio` con filtros (Sesion F.1).

Solo lectura, la misma consulta que expone `api/rutas/listas.py::listar_cambios_precio`, pero
llamando a `core` directo: la UI no consume la API por HTTP (decision del usuario, 2026-08-31, spec
F.1 §4). `core.catalog` no tiene una funcion propia para este listado (la ruta de la API arma la
consulta con `sqlalchemy.select` sobre `core.models` directamente); esta pagina reproduce esa misma
consulta, en el mismo orden y con los mismos tres filtros.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import streamlit as st
from pandas import DataFrame
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core import models
from core.catalog import abrir_sesion, crear_esquema, crear_motor
from core.verification.informe import DECIMALES_PRESENTACION
from core.verification.texto import formatear_decimal

TITULO = "Historico de cambios de precio"
RUTA_BASE_POR_DEFECTO = "data/apu.db"
CIEN = Decimal(100)


def render() -> None:
    """Filtros en la barra lateral; la tabla de cambios en el cuerpo."""
    st.title(TITULO)
    st.caption(
        "Cada fila es un insumo que cambio de precio entre la lista anterior y la lista nueva de "
        "una actualizacion (UC-02)."
    )

    ruta = Path(st.sidebar.text_input("Archivo SQLite", value=RUTA_BASE_POR_DEFECTO))
    insumo, desde, hasta = _filtros()

    motor = crear_motor(f"sqlite:///{ruta.as_posix()}")
    try:
        crear_esquema(motor)
        with abrir_sesion(motor) as sesion:
            cambios = _consultar(sesion, insumo, desde, hasta)
    except (LookupError, ValueError, ArithmeticError, SQLAlchemyError) as error:
        # Mismo criterio que `ui/paginas/actualizacion.py`: un archivo de base de datos corrupto
        # o inaccesible (`OperationalError` de `crear_esquema`) es un mensaje, no una traza cruda.
        # `return` aqui no salta el `finally`: `motor.dispose()` corre igual antes de salir.
        st.error(str(error))
        return
    finally:
        motor.dispose()

    _mostrar(cambios)


def _filtros() -> tuple[str, date | None, date | None]:
    with st.sidebar:
        st.header("Filtros")
        insumo = st.text_input("Insumo (descripcion exacta)", value="")

        con_desde = st.checkbox("Filtrar desde una fecha", value=False)
        desde = st.date_input("Desde", value=date.today()) if con_desde else None

        con_hasta = st.checkbox("Filtrar hasta una fecha", value=False)
        hasta = st.date_input("Hasta", value=date.today()) if con_hasta else None

    return insumo, desde, hasta


def _consultar(
    sesion: Session, insumo: str, desde: date | None, hasta: date | None
) -> list[models.CambioPrecio]:
    consulta = (
        select(models.CambioPrecio)
        .join(models.Insumo)
        .order_by(models.CambioPrecio.fecha, models.CambioPrecio.id)
    )
    if insumo:
        consulta = consulta.where(models.Insumo.descripcion == insumo)
    if desde is not None:
        consulta = consulta.where(models.CambioPrecio.fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(models.CambioPrecio.fecha <= hasta)
    return list(sesion.scalars(consulta))


def _mostrar(cambios: list[models.CambioPrecio]) -> None:
    if not cambios:
        st.info("No hay cambios de precio registrados con esos filtros.")
        return

    tabla = DataFrame(
        [
            {
                "fecha": cambio.fecha,
                "insumo": cambio.insumo.descripcion,
                "precio_anterior": formatear_decimal(
                    cambio.precio_anterior, DECIMALES_PRESENTACION
                ),
                "precio_nuevo": formatear_decimal(cambio.precio_nuevo, DECIMALES_PRESENTACION),
                "variacion_pct": formatear_decimal(cambio.variacion * CIEN, DECIMALES_PRESENTACION),
            }
            for cambio in cambios
        ]
    )
    st.dataframe(tabla, hide_index=True)
