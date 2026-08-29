"""Reglas paramétricas y adaptador tabular del dominio civil (Sesión I3.2).

Reproduce, a partir de las expresiones declaradas en `adapters/civil/reglas.py`, los mismos números
que la memoria de cálculo auditada (`tests/fixtures/apu_linea_base.py`): 0,224 m3 de concreto y
4,48 m2 de encofrado por tanquilla, y 7,68 m3 de excavación de zanja. No repite esos números salvo
los que el fixture no expone (sobreancho, espesor de fondo, diámetro y desperdicio de tubería, que
son supuestos de esta sesión, declarados también en data/samples/civil/README.md).
"""

from decimal import Decimal
from pathlib import Path

import pytest

from adapters.civil.evaluador import evaluar_regla
from adapters.civil.reglas import (
    CLAVE_BALANCE,
    computar_relleno,
    computar_tanquillas,
    computar_zanja,
)
from adapters.civil.tabular import AdaptadorCivilTabular
from core.contracts import Dominio, OrigenTipo
from tests.fixtures import apu_linea_base as linea_base

# Supuestos de esta muestra, declarados en data/samples/civil/README.md: la memoria auditada no fija
# margen de excavación ni espesor de fondo bajo la tanquilla.
SOBREANCHO = Decimal("0.10")
ESPESOR_FONDO = Decimal("0.10")
DIAMETRO_TUBERIA_M = Decimal("0.1016")  # 4 pulg, coherente con DIAMETRO_TUBERIA_PROYECTO
DESPERDICIO_TUBERIA = Decimal("0.05")

# Un solo código por partida (principio DRY): se reutilizan los de la línea base en vez de inventar
# códigos nuevos, porque este adaptador no decide códigos (los recibe el llamador).
CODIGOS = {
    "concreto": linea_base.APU_CONCRETO.codigo_partida,
    "encofrado": linea_base.APU_ENCOFRADO.codigo_partida,
    "excavacion": linea_base.APU_EXCAVACION.codigo_partida,
    "tuberia": linea_base.APU_TUBERIA.codigo_partida,
    "relleno": linea_base.APU_RELLENO.codigo_partida,
}

RUTA_MUESTRA = (
    Path(__file__).resolve().parents[2] / "data" / "samples" / "civil" / "tanquillas_y_zanja.csv"
)


def _computar_una_tanquilla(n: Decimal):
    geometria = linea_base.GEOMETRIA_TANQUILLA
    return computar_tanquillas(
        origen_id="T-01",
        codigos=CODIGOS,
        a=geometria["a"],
        h=geometria["h"],
        e=geometria["e"],
        n=n,
        sobreancho=SOBREANCHO,
        espesor_fondo=ESPESOR_FONDO,
    )


def _computar_la_zanja():
    return computar_zanja(
        origen_id="Z-01",
        codigos=CODIGOS,
        longitud=linea_base.LONGITUD_TUBERIA_M,
        ancho=linea_base.ZANJA["ancho"],
        profundidad=linea_base.ZANJA["profundidad"],
        diametro=DIAMETRO_TUBERIA_M,
        desperdicio=DESPERDICIO_TUBERIA,
    )


def test_concreto_por_tanquilla_es_0_224():
    concreto, _encofrado, _excavacion = _computar_una_tanquilla(n=Decimal("1"))
    assert concreto.cantidad == linea_base.CANTIDAD_POR_TANQUILLA_MEMORIA["LB-04-CON"]


def test_encofrado_por_tanquilla_es_4_48():
    _concreto, encofrado, _excavacion = _computar_una_tanquilla(n=Decimal("1"))
    assert encofrado.cantidad == linea_base.CANTIDAD_POR_TANQUILLA_MEMORIA["LB-03-ENC"]


def test_cuatro_tanquillas_reproducen_el_computo_corregido():
    concreto, encofrado, _excavacion = _computar_una_tanquilla(n=linea_base.N_TANQUILLAS)
    assert concreto.cantidad == linea_base.COMPUTO_CORREGIDO["LB-04-CON"]
    assert encofrado.cantidad == linea_base.COMPUTO_CORREGIDO["LB-03-ENC"]


def test_zanja_reproduce_7_68():
    excavacion, _tuberia = _computar_la_zanja()
    assert excavacion.cantidad == linea_base.ZANJA["volumen"]


def test_tuberia_con_desperdicio():
    _excavacion, tuberia = _computar_la_zanja()
    assert tuberia.cantidad == Decimal("25.2")


def test_los_items_son_trazables():
    items = [
        *_computar_una_tanquilla(n=linea_base.N_TANQUILLAS),
        *_computar_la_zanja(),
        computar_relleno(
            origen_id="relleno:T-01,Z-01",
            codigos=CODIGOS,
            excavacion=Decimal("11.28"),
            concreto=Decimal("0.896"),
            volumen_tuberia=Decimal("0.2"),
            balance="LB-01-EXC - LB-04-CON - LB-02-TUB * 0.008107338624",
        ),
    ]

    assert len(items) == 6
    for item in items:
        assert item.origen_tipo is OrigenTipo.REGLA
        assert item.dominio is Dominio.CIVIL
        assert item.regla is not None
        assert evaluar_regla(item.regla, item.parametros) == item.cantidad


def test_adaptador_tabular_extrae_la_muestra():
    adaptador = AdaptadorCivilTabular(codigos=CODIGOS)
    assert adaptador.dominio is Dominio.CIVIL

    items = adaptador.extraer(RUTA_MUESTRA)
    assert len(items) == 6

    concreto, encofrado, excavacion_tanquilla, excavacion_zanja, tuberia, relleno = items

    assert concreto.codigo_partida == CODIGOS["concreto"]
    assert encofrado.codigo_partida == CODIGOS["encofrado"]
    assert excavacion_tanquilla.codigo_partida == CODIGOS["excavacion"]
    assert excavacion_zanja.codigo_partida == CODIGOS["excavacion"]
    assert tuberia.codigo_partida == CODIGOS["tuberia"]
    assert relleno.codigo_partida == CODIGOS["relleno"]

    assert concreto.cantidad == linea_base.COMPUTO_CORREGIDO["LB-04-CON"]
    assert encofrado.cantidad == linea_base.COMPUTO_CORREGIDO["LB-03-ENC"]
    assert excavacion_zanja.cantidad == linea_base.ZANJA["volumen"]
    assert tuberia.cantidad == Decimal("25.2")

    assert CLAVE_BALANCE in relleno.especificaciones
    assert relleno.especificaciones[CLAVE_BALANCE].startswith(CODIGOS["excavacion"])


def test_evaluador_rechaza_llamadas_y_atributos():
    parametros = {"a": Decimal("2")}
    with pytest.raises(ValueError):
        evaluar_regla("abs(a)", parametros)
    with pytest.raises(ValueError):
        evaluar_regla("a.bit_length", parametros)


def test_evaluador_exige_parametros():
    with pytest.raises(KeyError):
        evaluar_regla("a + b", {"a": Decimal("1")})
