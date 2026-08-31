"""UC-03 (Sesion I2): normalizacion semantica de descripciones de partida.

`ml.normalization.NormalizadorPartidas` recibe el catalogo como pares (codigo, descripcion) planos
-- `ml/` solo puede importar `core.contracts` (CLAUDE.md §2; `test_arquitectura.py`), asi que no
conoce la base de datos: la capa de composicion (UI) le pasa lo que consulta `core.catalog` -- y
devuelve las partidas mas similares por similitud del coseno, ordenadas de mayor a menor puntaje y
nunca por debajo del umbral declarado (RF-15).

El catalogo de estas pruebas son las cinco partidas de la linea base, tomadas de la unica copia
(`tests/fixtures/apu_linea_base.py`, principio DRY). El modelo de similitud es una precondicion del
UC-03 («el modelo esta disponible localmente», docs/ERS.md): si no puede cargarse (primera vez sin
red), las pruebas se saltan declarando el motivo, igual que hacen las de ifcopenshell con el extra
civil.
"""

from __future__ import annotations

import os

import pytest

# En Windows sin modo desarrollador, huggingface_hub avisa con un UserWarning que su cache no
# puede usar symlinks (primera descarga del modelo): es una degradacion documentada, no un
# problema del sistema, y rompe el DoD de cero advertencias (`-W error`). Su propia variable
# oficial lo desactiva.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

pytest.importorskip("sentence_transformers")

from tests.fixtures import apu_linea_base as linea_base  # noqa: E402

CATALOGO = {apu.codigo_partida: apu.descripcion for apu in linea_base.APUS_LINEA_BASE}

#: El "presupuesto conocido" de la prueba de aceptacion (RF-17): las cinco partidas de la linea
#: base redactadas como las escribiria otro proyectista. Reconocer >= 80 % (4 de 5) en el primer
#: puesto es el criterio del PLAN (Sesion I2).
PARAFRASIS = {
    "LB-01-EXC": "Excavacion manual de zanja para tuberia y fosos de tanquillas",
    "LB-02-TUB": "Colocacion de tubo PVC de 4 pulgadas con sus conexiones",
    "LB-03-ENC": "Encofrado de madera para el vaciado de las tanquillas",
    "LB-04-CON": "Concreto vaciado en las paredes de las tanquillas",
    "LB-05-REL": "Relleno y compactacion de la zanja con material granular",
}


@pytest.fixture(scope="module")
def normalizador():
    from ml.normalization import NormalizadorPartidas

    try:
        return NormalizadorPartidas(CATALOGO)
    except OSError as exc:  # el modelo no esta disponible localmente y no pudo descargarse
        pytest.skip(f"modelo de similitud no disponible: {exc}")


def test_propuestas_ordenadas_por_puntaje_y_sobre_el_umbral(normalizador):
    """RF-15: a lo sumo tres propuestas, de mayor a menor puntaje, ninguna bajo el umbral."""
    from ml.normalization import UMBRAL_POR_DEFECTO

    propuestas = normalizador.similares("Vaciado de concreto para las tanquillas del drenaje")

    assert 1 <= len(propuestas) <= 3
    assert propuestas[0].codigo == "LB-04-CON"
    puntajes = [propuesta.puntaje for propuesta in propuestas]
    assert puntajes == sorted(puntajes, reverse=True)
    assert all(puntaje >= UMBRAL_POR_DEFECTO for puntaje in puntajes)


def test_descripcion_identica_es_la_primera_propuesta_con_puntaje_cercano_a_uno(normalizador):
    propuestas = normalizador.similares(CATALOGO["LB-03-ENC"])

    assert propuestas[0].codigo == "LB-03-ENC"
    assert propuestas[0].descripcion == CATALOGO["LB-03-ENC"]
    assert propuestas[0].puntaje > 0.99


def test_acepta_al_menos_80_por_ciento_del_presupuesto_conocido(normalizador):
    """RF-17 / prueba de aceptacion del PLAN (Sesion I2): sobre un presupuesto conocido el
    sistema reconoce correctamente al menos el 80 % de las partidas (primer puesto).
    """
    aciertos = sum(
        1
        for codigo, redaccion in PARAFRASIS.items()
        if (propuestas := normalizador.similares(redaccion)) and propuestas[0].codigo == codigo
    )
    assert aciertos / len(PARAFRASIS) >= 0.8, f"reconocidas {aciertos} de {len(PARAFRASIS)}"


def test_nada_supera_el_umbral_no_propone_nada(normalizador):
    """Flujo alternativo 2a del UC-03: sin candidato sobre el umbral, la lista sale vacia y el
    llamador ofrece crear la partida desde cero.
    """
    assert normalizador.similares("Auditoria contable de nomina y facturacion electronica") == []


def test_catalogo_vacio_no_propone_sin_error(normalizador):
    """Flujo alternativo 2b del UC-03: primer proyecto, catalogo vacio, ninguna propuesta."""
    from ml.normalization import NormalizadorPartidas

    vacio = NormalizadorPartidas({})
    assert vacio.similares("Excavacion en tierra") == []


def test_cuantos_acota_el_numero_de_propuestas(normalizador):
    propuestas = normalizador.similares(CATALOGO["LB-04-CON"], cuantos=1)
    assert len(propuestas) == 1 and propuestas[0].codigo == "LB-04-CON"
