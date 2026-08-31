"""Rutas de cómputo por dominio (UC-01): un adaptador extrae `ItemComputo` de un archivo de
muestra.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from api.esquemas import ItemComputoRespuesta
from core.contracts import AdaptadorDominio, Dominio, ItemComputo

router = APIRouter(tags=["computos"])


def _adaptador(dominio: str, codigos: dict[str, str] | None) -> AdaptadorDominio:
    """El adaptador del dominio pedido. El civil exige el mapeo de códigos por tipo de elemento."""
    if dominio == Dominio.CIVIL:
        if codigos is None:
            raise ValueError(
                "el dominio civil exige 'codigos' (mapeo de tipo de elemento a codigo_partida)"
            )
        from adapters.civil.tabular import AdaptadorCivilTabular

        return AdaptadorCivilTabular(codigos)
    if dominio == Dominio.TELECOM:
        from adapters.telecom.adaptador import AdaptadorTelecom

        return AdaptadorTelecom()
    if dominio == Dominio.INDUSTRIAL:
        from adapters.industrial.adaptador import AdaptadorIndustrial

        return AdaptadorIndustrial()
    if dominio == Dominio.SISTEMAS:
        from adapters.sistemas.adaptador import AdaptadorSistemas

        return AdaptadorSistemas()
    raise ValueError(f"dominio no reconocido: {dominio!r}")


@router.post("/computos/{dominio}", response_model=list[ItemComputoRespuesta])
def computar(
    dominio: str,
    archivo: Annotated[UploadFile, File()],
    codigos: Annotated[str | None, Form()] = None,
) -> list[ItemComputoRespuesta]:
    """Extrae las cantidades de obra de la fuente subida con el adaptador del dominio pedido.

    `codigos` es un JSON de texto (form field) con el mapeo que exige el adaptador civil; el resto
    de los dominios no lo necesita. El archivo se guarda en un directorio temporal con su nombre
    original, porque los adaptadores leen por extensión.
    """
    mapeo_codigos = json.loads(codigos) if codigos is not None else None
    adaptador = _adaptador(dominio, mapeo_codigos)
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / archivo.filename
        ruta.write_bytes(archivo.file.read())
        items = adaptador.extraer(ruta)
    return [_a_respuesta(item) for item in items]


def _a_respuesta(item: ItemComputo) -> ItemComputoRespuesta:
    return ItemComputoRespuesta(
        codigo_partida=item.codigo_partida,
        descripcion=item.descripcion,
        unidad=item.unidad,
        cantidad=str(item.cantidad),
        origen_id=item.origen_id,
        origen_tipo=item.origen_tipo.value,
        dominio=item.dominio.value,
        regla=item.regla,
        parametros={clave: str(valor) for clave, valor in item.parametros.items()},
        especificaciones=dict(item.especificaciones),
    )
