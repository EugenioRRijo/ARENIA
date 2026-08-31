import json
from pathlib import Path

RUTA = Path(__file__).resolve().parents[2] / "docs" / "api.json"


def test_el_esquema_exportado_cubre_las_rutas_clave():
    esquema = json.loads(RUTA.read_text(encoding="utf-8"))
    rutas = esquema["paths"]
    for esperada in (
        "/salud",
        "/partidas",
        "/listas-precios",
        "/computos/{dominio}",
        "/presupuestos",
        "/presupuestos/{codigo}/actualizacion",
    ):
        assert esperada in rutas, esperada


def test_el_esquema_esta_al_dia_con_la_aplicacion():
    from api.main import app

    assert (
        json.loads(RUTA.read_text(encoding="utf-8"))["paths"].keys()
        == app.openapi()["paths"].keys()
    )
