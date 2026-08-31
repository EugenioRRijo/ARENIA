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


def _items_payload():
    from tests.fixtures.computo_auditado import items_auditados

    return [
        {
            "codigo_partida": i.codigo_partida,
            "descripcion": i.descripcion,
            "unidad": i.unidad,
            "cantidad": str(i.cantidad),
            "origen_id": i.origen_id,
            "origen_tipo": i.origen_tipo.value,
            "dominio": i.dominio.value,
            "regla": i.regla,
            "parametros": {k: str(v) for k, v in i.parametros.items()},
            "especificaciones": dict(i.especificaciones),
        }
        for i in items_auditados()
    ]


def test_computo_civil_desde_la_muestra(cliente):
    ruta = RAIZ / "data" / "samples" / "civil" / "tanquillas_y_zanja.csv"
    codigos = {
        "excavacion": "LB-01-EXC",
        "tuberia": "LB-02-TUB",
        "encofrado": "LB-03-ENC",
        "concreto": "LB-04-CON",
        "relleno": "LB-05-REL",
    }
    import json

    with ruta.open("rb") as f:
        r = cliente.post(
            "/computos/civil",
            files={"archivo": (ruta.name, f, "text/csv")},
            data={"codigos": json.dumps(codigos)},
        )
    assert r.status_code == 200 and len(r.json()) == 6
    assert all(i["origen_id"] for i in r.json())


def test_elaborar_presupuesto_por_http_reproduce_el_total_auditado(cliente):
    r = cliente.post(
        "/presupuestos",
        json={
            "codigo": "API-001",
            "fecha": "2026-04-28",
            "moneda": "USD",
            "proyecto": "Drenaje de la clínica",
            "items": _items_payload(),
        },
    )
    assert r.status_code == 201
    assert r.json()["total"] == "1586.61"  # texto exacto
    assert r.json()["hallazgos"] >= 7  # audita siempre
    detalle = cliente.get("/presupuestos/API-001").json()
    assert detalle["total"] == "1586.61" and len(detalle["partidas"]) == 5
    assert "Informe" in cliente.get("/presupuestos/API-001/informe").text
    assert cliente.get("/presupuestos/API-001/excel").content[:2] == b"PK"


def test_actualizacion_por_http_solo_revalora_el_concreto(cliente):
    cliente.post(
        "/presupuestos",
        json={
            "codigo": "API-001",
            "fecha": "2026-04-28",
            "moneda": "USD",
            "proyecto": "Drenaje de la clínica",
            "items": _items_payload(),
        },
    )
    with MUESTRA_PRECIOS.open("rb") as f:
        cliente.post(
            "/listas-precios",
            files={"archivo": (MUESTRA_PRECIOS.name, f, "text/csv")},
            data={"nombre": "L2", "moneda": "USD", "fecha_vigencia": "2026-06-01"},
        )
    r = cliente.post(
        "/presupuestos/API-001/actualizacion", json={"lista": "L2", "codigo_nuevo": "API-002"}
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total_nuevo"] == "1636.70"
    filas = {f["codigo_partida"]: f for f in cuerpo["filas"]}
    assert filas["LB-04-CON"]["variacion_pct"] != "0"
    assert sum(1 for f in cuerpo["filas"] if f["variacion_pct"] not in ("0", "0.00")) == 1


def test_codigo_de_presupuesto_repetido_en_dos_proyectos_no_revienta_en_500(cliente, sesion):
    """`codigo` solo es unico por proyecto (`UniqueConstraint(proyecto_id, codigo)`): si dos
    proyectos comparten codigo, las rutas que resuelven `{codigo}` deben responder 409 con
    detalle claro (nunca `MultipleResultsFound` sin manejar) y desambiguar con `?proyecto=`
    (hallazgo Important de la revision de la Tarea 2).
    """
    from core import models

    payload_base = {
        "codigo": "COL-001",
        "fecha": "2026-04-28",
        "moneda": "USD",
        "items": _items_payload(),
    }
    r1 = cliente.post("/presupuestos", json={**payload_base, "proyecto": "Drenaje de la clínica"})
    assert r1.status_code == 201

    sesion.add(models.Proyecto(nombre="Segundo proyecto", descripcion="", dominio="civil"))
    sesion.commit()
    r2 = cliente.post("/presupuestos", json={**payload_base, "proyecto": "Segundo proyecto"})
    assert r2.status_code == 201

    # Sin 'proyecto': el codigo es ambiguo entre los dos proyectos. 409 claro, nunca un 500 crudo.
    for r in (
        cliente.get("/presupuestos/COL-001"),
        cliente.get("/presupuestos/COL-001/informe"),
        cliente.get("/presupuestos/COL-001/excel"),
        cliente.post(
            "/presupuestos/COL-001/actualizacion",
            json={"lista": "no importa", "codigo_nuevo": "COL-002"},
        ),
    ):
        assert r.status_code == 409
        assert "COL-001" in r.json()["detalle"]

    # Con 'proyecto': cada ruta resuelve sin ambiguedad, sobre el proyecto indicado.
    detalle = cliente.get("/presupuestos/COL-001", params={"proyecto": "Segundo proyecto"})
    assert detalle.status_code == 200 and detalle.json()["total"] == "1586.61"
    assert (
        cliente.get(
            "/presupuestos/COL-001/informe", params={"proyecto": "Drenaje de la clínica"}
        ).status_code
        == 200
    )
