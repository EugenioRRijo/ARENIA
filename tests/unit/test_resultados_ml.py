"""Sesion I6.3: el informe `docs/resultados_ml.md` (RF-28, meta M8 de `scripts/meta_i6.py`).

`scripts/generar_resultados_ml.py` separa el armado del texto (`generar_informe`, puro y probado
aqui) del acopio de datos (conteo por dominio y evaluacion sobre la linea base, que corren contra
una base sembrada al ejecutar el script). El informe declara el conteo de la compuerta G2, la
tecnica elegida, las metricas obligatorias (MAPE, RMSE, R2) y la limitacion de la tecnica de
reglas, como exige CLAUDE.md §8.1.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

pytest.importorskip("sklearn")  # scripts/generar_resultados_ml.py importa ml (extra `ml`)


def _informe() -> str:
    from ml.prediction import PrediccionPrecio, contrastar_aace, metricas
    from scripts.generar_resultados_ml import generar_informe

    conteos = {"civil": 5, "telecom": 0, "industrial": 0, "sistemas": 0}
    estimados = {"LB-04-CON": Decimal("279.04")}
    reales = {"LB-04-CON": Decimal("272.81")}
    predicciones = [
        PrediccionPrecio(
            codigo_partida="LB-04-CON",
            pu_base=Decimal("242.64"),
            pu_estimado=Decimal("279.04"),
            pu_minimo=Decimal("266.90"),
            pu_maximo=Decimal("291.17"),
        )
    ]
    hallazgos = [
        h
        for codigo in reales
        if (h := contrastar_aace(codigo, reales[codigo], estimados[codigo])) is not None
    ]
    return generar_informe(
        conteos=conteos,
        metricas=metricas(estimados=estimados, reales=reales),
        predicciones=predicciones,
        hallazgos=hallazgos,
    )


def test_el_informe_declara_conteo_tecnica_y_metricas():
    informe = _informe()

    # Compuerta G2: el conteo por dominio y la tecnica que dicta CLAUDE.md §8.1.
    for dominio in ("civil", "telecom", "industrial", "sistemas"):
        assert dominio in informe
    assert "5" in informe and "50" in informe  # el conteo civil y el umbral de la tabla
    assert "reglas" in informe.lower()

    # RF-28: las tres metricas obligatorias, presentes y con nombre.
    for metrica in ("MAPE", "RMSE", "R2"):
        assert metrica in informe

    # La tecnica de reglas se declara como limitacion, no como logro (CLAUDE.md §8.1).
    assert "limitacion" in informe.lower() or "limitación" in informe.lower()


def test_el_informe_tabula_las_predicciones_con_su_rango():
    informe = _informe()
    assert "LB-04-CON" in informe
    assert "279.04" in informe  # estimado
    assert "266.90" in informe and "291.17" in informe  # rango de sensibilidad
