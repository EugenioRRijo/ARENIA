"""Los CSV ARENAZA suman exactamente los totales de cada PDF y registran el 80/90."""
import csv
from decimal import Decimal
from pathlib import Path

from tests.fixtures.presupuestos_arenaza import (
    PRESUPUESTO_1,
    PRESUPUESTO_2,
    TOTAL_1,
    TOTAL_2,
    TUBO_CORRUGADO,
)

CARPETA = Path("data/telecom/fuentes")


def _total_csv(nombre):
    with open(CARPETA / nombre, newline="", encoding="utf-8") as f:
        return sum(Decimal(fila["total"]) for fila in csv.DictReader(f))


def test_totales_exactos():
    assert TOTAL_1 == Decimal("1109.29")
    assert TOTAL_2 == Decimal("5410.73")
    assert _total_csv("presupuesto_1_arenaza.csv") == TOTAL_1
    assert _total_csv("presupuesto_2_arenaza.csv") == TOTAL_2


def test_conteo_renglones():
    assert len(PRESUPUESTO_1) == 14
    assert len(PRESUPUESTO_2) == 26


def test_inconsistencia_80_90_registrada():
    assert TUBO_CORRUGADO["cantidad_computos"] == Decimal("80")
    assert TUBO_CORRUGADO["cantidad_presupuesto"] == Decimal("90")


def test_fixture_coincide_con_csv():
    for renglones, nombre in [(PRESUPUESTO_1, "presupuesto_1_arenaza.csv"),
                              (PRESUPUESTO_2, "presupuesto_2_arenaza.csv")]:
        assert sum(r.total for r in renglones) == _total_csv(nombre)
