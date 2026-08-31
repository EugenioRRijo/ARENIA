"""API FastAPI que expone las operaciones del nucleo (Sesion F.1)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.rutas import catalogo, computos, listas, presupuestos
from core.catalog import CatalogoIncompleto

app = FastAPI(title="Sistema APU multidominio", version="0.1.0")
app.include_router(catalogo.router)
app.include_router(listas.router)
app.include_router(computos.router)
app.include_router(presupuestos.router)


@app.exception_handler(CatalogoIncompleto)
def manejar_catalogo_incompleto(_request: Request, exc: CatalogoIncompleto) -> JSONResponse:
    """Falta un dato imprescindible en el catalogo (precio o rendimiento vigente)."""
    return JSONResponse(status_code=409, content={"detalle": str(exc)})


@app.exception_handler(LookupError)
def manejar_lookup_error(_request: Request, exc: LookupError) -> JSONResponse:
    """El recurso pedido (partida, insumo...) no existe en el catalogo."""
    return JSONResponse(status_code=404, content={"detalle": str(exc)})


@app.exception_handler(ValueError)
def manejar_value_error(_request: Request, exc: ValueError) -> JSONResponse:
    """Datos de entrada invalidos segun las reglas del nucleo."""
    return JSONResponse(status_code=422, content={"detalle": str(exc)})
