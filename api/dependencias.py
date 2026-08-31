"""Sesion de base de datos por peticion. Lo unico de la API que sabe de configuracion."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from core.catalog import abrir_sesion, crear_esquema, crear_motor

URL_POR_DEFECTO = "sqlite:///data/apu.db"
_motor = None


def _obtener_motor():
    global _motor
    if _motor is None:
        _motor = crear_motor(os.environ.get("APU_BASE", URL_POR_DEFECTO))
        crear_esquema(_motor)
    return _motor


def sesion_api() -> Iterator[Session]:
    with abrir_sesion(_obtener_motor()) as sesion:
        yield sesion


#: Alias de tipo para inyectar la sesion en las rutas sin disparar B008 (ruff): un `Depends(...)`
#: como valor por defecto es una llamada en la firma; dentro de `Annotated` no lo es.
SesionDep = Annotated[Session, Depends(sesion_api)]
