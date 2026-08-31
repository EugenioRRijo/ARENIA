"""API de F.1: el nucleo expuesto por HTTP. Montos como texto (Decimal), nunca float."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parents[2]
MUESTRA_PRECIOS = RAIZ / "data" / "samples" / "precios" / "lista_2026-06-01.csv"


@pytest.fixture
def cliente(sesion):
    from api.dependencias import sesion_api
    from api.main import app

    app.dependency_overrides[sesion_api] = lambda: sesion
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


def test_salud(cliente):
    r = cliente.get("/salud")
    assert r.status_code == 200 and r.json()["estado"] == "ok"


def test_partidas_lista_las_cinco_de_la_linea_base(cliente):
    r = cliente.get("/partidas")
    assert r.status_code == 200
    codigos = {p["codigo"] for p in r.json()}
    assert {"LB-01-EXC", "LB-02-TUB", "LB-03-ENC", "LB-04-CON", "LB-05-REL"} <= codigos


def test_insumos_traen_precio_vigente_como_texto(cliente):
    r = cliente.get("/insumos")
    cemento = next(i for i in r.json() if i["descripcion"] == "Cemento Portland")
    assert cemento["precio_vigente"] == "15"  # str exacto, jamas 15.0


def test_cargar_lista_de_precios_reporta_desconocidos_vacios(cliente):
    with MUESTRA_PRECIOS.open("rb") as f:
        r = cliente.post(
            "/listas-precios",
            files={"archivo": (MUESTRA_PRECIOS.name, f, "text/csv")},
            data={"nombre": "Lista API", "moneda": "USD", "fecha_vigencia": "2026-06-01"},
        )
    assert r.status_code == 201
    assert r.json()["desconocidos"] == []
    assert cliente.get("/listas-precios").status_code == 200
