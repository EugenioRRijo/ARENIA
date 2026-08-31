from decimal import Decimal

from scripts.simular_lista import simular

PRECIOS = {
    "Cemento Portland": ("material", "saco", Decimal("15")),
    "Arena lavada": ("material", "m3", Decimal("30")),
}


def test_es_determinista_con_la_misma_semilla():
    a = simular(PRECIOS, Decimal("10"), semilla=42, solo=None)
    assert a == simular(PRECIOS, Decimal("10"), semilla=42, solo=None)
    assert a != simular(PRECIOS, Decimal("10"), semilla=43, solo=None)


def test_respeta_el_filtro_y_el_formato():
    filas = simular(PRECIOS, Decimal("10"), semilla=1, solo={"Cemento Portland"})
    assert [f[1] for f in filas if f[3] != Decimal("15.00")] in (["Cemento Portland"], [])
    for _tipo, _insumo, _unidad, precio in filas:
        assert isinstance(precio, Decimal) and precio >= 0
        assert precio == precio.quantize(Decimal("0.01"))
