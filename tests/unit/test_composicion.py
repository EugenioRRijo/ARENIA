"""Funciones puras de composición (Sesión P2.1).

Lo único verificable antes de que existan pruebas de interfaz es lo que se puede llamar sin
Streamlit (spec §4). Estas pruebas fijan ese contorno.
"""

from decimal import Decimal

import pytest

from core.contracts import Dominio, ModalidadManoObra, OrigenTipo
from ui.composicion import (
    ComposicionInvalida,
    composicion_desde_tablas,
    decimal_desde_texto,
    item_desde_cantidad,
)

MATERIALES = [{"descripcion": "Cemento", "unidad": "saco", "cantidad": "7.5", "precio": "8.00"}]
EQUIPOS = [{"descripcion": "Vibrador", "cantidad": "1", "precio": "300.00", "depreciacion": "0.03"}]
MANO_OBRA = [
    {"descripcion": "Obrero de primera", "cantidad": "2", "sueldo": "12.50", "modalidad": "jornal"},
    {"descripcion": "Friso", "cantidad": "1", "sueldo": "6.00", "modalidad": "destajo"},
]


def test_una_tabla_valida_produce_la_composicion_esperada():
    composicion = composicion_desde_tablas(
        "LB-04-VAC", "Vaciado de concreto", "m3", "8", MATERIALES, EQUIPOS, MANO_OBRA
    )

    assert composicion.codigo_partida == "LB-04-VAC"
    assert composicion.rendimiento == Decimal("8")
    assert composicion.materiales[0].cantidad == Decimal("7.5")
    assert composicion.equipos[0].depreciacion == Decimal("0.03")
    assert composicion.mano_obra[1].modalidad is ModalidadManoObra.DESTAJO
    assert composicion.total_obreros == Decimal("2"), "el destajista no cuenta para el bono"


def test_una_cantidad_no_numerica_nombra_el_campo_culpable():
    filas = [{"descripcion": "Cemento", "unidad": "saco", "cantidad": "siete", "precio": "8.00"}]

    with pytest.raises(ComposicionInvalida) as error:
        composicion_desde_tablas("P-01", "Prueba", "m3", "8", filas, [], MANO_OBRA)

    assert "cantidad" in str(error.value)
    assert "Cemento" in str(error.value)


def test_las_filas_vacias_se_descartan():
    filas = MATERIALES + [{"descripcion": "  ", "unidad": "", "cantidad": "", "precio": ""}]

    composicion = composicion_desde_tablas("P-01", "Prueba", "m3", "8", filas, [], MANO_OBRA)

    assert len(composicion.materiales) == 1


def test_un_rendimiento_cero_o_negativo_se_rechaza():
    for valor in ("0", "-3"):
        with pytest.raises(ComposicionInvalida, match="rendimiento"):
            composicion_desde_tablas("P-01", "Prueba", "m3", valor, MATERIALES, [], MANO_OBRA)


def test_la_unidad_con_alias_se_normaliza():
    composicion = composicion_desde_tablas(
        "P-01", "Prueba", "m³", "8", MATERIALES, [], MANO_OBRA
    )

    assert composicion.unidad == "m3"


def test_una_modalidad_desconocida_se_rechaza_nombrando_la_fila():
    filas = [{"descripcion": "Friso", "cantidad": "1", "sueldo": "6.00", "modalidad": "por pieza"}]

    with pytest.raises(ComposicionInvalida) as error:
        composicion_desde_tablas("P-01", "Prueba", "m3", "8", MATERIALES, [], filas)

    assert "Friso" in str(error.value)
    assert "modalidad" in str(error.value)


def test_una_fila_de_mano_de_obra_sin_modalidad_es_jornal():
    filas = [{"descripcion": "Obrero", "cantidad": "1", "sueldo": "12.50"}]

    composicion = composicion_desde_tablas("P-01", "Prueba", "m3", "8", MATERIALES, [], filas)

    assert composicion.mano_obra[0].modalidad is ModalidadManoObra.JORNAL


def test_item_desde_cantidad_es_trazable_y_manual():
    item = item_desde_cantidad(
        "LB-04-VAC",
        "Vaciado de concreto",
        "m3",
        "1.66",
        "memoria de calculo 2026-09",
        Dominio.CIVIL,
    )

    assert item.origen_tipo is OrigenTipo.MANUAL
    assert item.cantidad == Decimal("1.66")
    assert item.origen_id == "memoria de calculo 2026-09"


def test_item_desde_cantidad_exige_origen():
    with pytest.raises(ComposicionInvalida, match="origen"):
        item_desde_cantidad("LB-04-VAC", "Vaciado", "m3", "1.66", "   ", Dominio.CIVIL)


def test_decimal_desde_texto_rechaza_lo_que_no_es_finito():
    assert decimal_desde_texto(" 7.5 ", "cantidad") == Decimal("7.5")
    with pytest.raises(ComposicionInvalida, match="cantidad"):
        decimal_desde_texto("Infinity", "cantidad")
