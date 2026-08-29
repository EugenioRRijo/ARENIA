"""Adaptador del dominio telecom: topologia de red en CSV (Sesion I5).

Reproduce, a partir de la muestra `data/samples/telecom/topologia_arenaza.csv` (derivada de
`data/samples/telecom/Presupuesto_1_ARENAZA.pdf`), 9 nodos (puntos WiFi, switches, rack, UPS) y
5 enlaces de cable UTP. Cada nodo es una cantidad tabular directa; cada enlace deriva su cantidad de
la regla `longitud_m * (1 + reserva)`, evaluada por `adapters/telecom/evaluador.py` (independiente
del de `adapters/civil`: cada adaptador es autonomo, CLAUDE.md paragrafo 2).
"""

from __future__ import annotations

import ast
import sys
from decimal import Decimal
from pathlib import Path

from adapters.telecom.adaptador import AdaptadorTelecom
from adapters.telecom.evaluador import evaluar_regla
from core.contracts import Dominio, OrigenTipo

RAIZ = Path(__file__).resolve().parents[2]
RUTA_MUESTRA = RAIZ / "data" / "samples" / "telecom" / "topologia_arenaza.csv"
PAQUETE_TELECOM = RAIZ / "adapters" / "telecom"


def _extraer():
    return AdaptadorTelecom().extraer(RUTA_MUESTRA)


def test_extrae_nodos_y_enlaces_de_la_muestra():
    adaptador = AdaptadorTelecom()
    assert adaptador.dominio is Dominio.TELECOM

    items = adaptador.extraer(RUTA_MUESTRA)
    assert len(items) == 14

    nodos = [item for item in items if item.origen_tipo is OrigenTipo.CSV]
    enlaces = [item for item in items if item.origen_tipo is OrigenTipo.REGLA]
    assert len(nodos) == 9
    assert len(enlaces) == 5

    for item in items:
        assert item.dominio is Dominio.TELECOM
        assert item.codigo_partida.startswith("TC-")
        assert isinstance(item.cantidad, Decimal)

    rack = next(item for item in nodos if item.origen_id == "RACK-01")
    assert rack.unidad == "pieza"
    assert rack.cantidad == Decimal("1")
    assert rack.especificaciones["tipo_equipo"] == "rack"


def test_los_enlaces_son_trazables_por_regla():
    items = _extraer()
    enlaces = {item.origen_id: item for item in items if item.origen_tipo is OrigenTipo.REGLA}

    esperado = {
        "ENL-01": Decimal("5.50"),
        "ENL-02": Decimal("33.00"),
        "ENL-03": Decimal("23.00"),
        "ENL-04": Decimal("28.75"),
        "ENL-05": Decimal("15"),
    }
    assert set(enlaces) == set(esperado)

    for origen_id, cantidad_esperada in esperado.items():
        enlace = enlaces[origen_id]
        assert enlace.regla is not None
        assert enlace.cantidad == cantidad_esperada
        # la cantidad declarada se reproduce evaluando la regla contra sus propios parametros
        # (regla R1 de verificacion: trazabilidad geometrica)
        assert evaluar_regla(enlace.regla, enlace.parametros) == enlace.cantidad
        assert enlace.unidad == "m"
        assert enlace.especificaciones["origen"]
        assert enlace.especificaciones["destino"]


def test_origen_id_es_la_clave_de_fila():
    items = _extraer()
    ids_esperados = {
        "RACK-01",
        "SW-CORE",
        "SW-DIST",
        "AP-01",
        "AP-02",
        "AP-03",
        "AP-04",
        "AP-05",
        "UPS-01",
        "ENL-01",
        "ENL-02",
        "ENL-03",
        "ENL-04",
        "ENL-05",
    }
    ids_obtenidos = {item.origen_id for item in items}
    assert ids_obtenidos == ids_esperados
    # cada origen_id es unico: es la clave de fila del CSV, no un valor repetido entre filas
    assert len(ids_obtenidos) == len(items)


def _imports_de(archivo: Path):
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            yield nodo.module


def test_no_importa_nada_de_core_salvo_contracts():
    permitidos = set(sys.stdlib_module_names) | {"__future__"}
    for archivo in sorted(PAQUETE_TELECOM.rglob("*.py")):
        for modulo in _imports_de(archivo):
            raiz_modulo = modulo.split(".")[0]
            if raiz_modulo == "core":
                assert modulo == "core.contracts" or modulo.startswith("core.contracts."), (
                    f"{archivo.relative_to(RAIZ).as_posix()} importa {modulo!r}; "
                    "adapters/telecom solo puede importar core.contracts"
                )
            elif raiz_modulo not in permitidos:
                assert raiz_modulo in {"adapters"}, (
                    f"{archivo.relative_to(RAIZ).as_posix()} importa {modulo!r} fuera de la "
                    "biblioteca estandar y de core.contracts"
                )
