"""La meta del sprint del prototipo: que audite fases y no se salte ninguna."""

from __future__ import annotations

import pytest

from scripts.meta_alpha import Estado
from scripts.meta_prototipo import (
    FASES,
    TITULOS,
    _archivos_de_fuentes,
    _generador_corpus_simulado,
    evaluar_p2_fuentes_referenciadas,
    main,
)


def test_toda_meta_declarada_tiene_titulo():
    for codigo in (codigo for metas in FASES.values() for codigo in metas):
        assert codigo in TITULOS, f"la meta {codigo} no tiene titulo"


def test_las_fases_van_de_p0_a_p5():
    assert list(FASES) == ["P0", "P1", "P2", "P3", "P4", "P5"]


def test_hasta_una_fase_inexistente_se_rechaza():
    with pytest.raises(SystemExit):
        main(["--hasta", "P9"])


# ------------------------------------------------------------------------------------------
# Ronda 1 de correcciones: un `.md` externo no fichado debe hacer fallar P2 (hallazgo 1) y
# `scripts/simular_corpus.py` debe ser detectado como generador del corpus simulado (hallazgo 2).
# ------------------------------------------------------------------------------------------


def test_p2_un_md_nuevo_no_fichado_hace_fallar(tmp_path):
    """Un `.md` archivado como fuente (no el indice ni la nota de campo) que el README no
    mencione debe dar FALLA: P2 no puede quedar ciega ante nuevas fuentes en Markdown.
    """
    raiz_fuentes = tmp_path / "fuentes"
    raiz_fuentes.mkdir()
    (raiz_fuentes / "README.md").write_text("indice", encoding="utf-8")
    (raiz_fuentes / "2026-09-16-nota-practica-apu.md").write_text("nota", encoding="utf-8")
    (raiz_fuentes / "captura_pagina_precios.md").write_text("captura archivada", encoding="utf-8")

    archivos = _archivos_de_fuentes(raiz_fuentes)
    assert "captura_pagina_precios.md" in archivos
    assert "README.md" not in archivos
    assert "2026-09-16-nota-practica-apu.md" not in archivos

    estado, evidencia = evaluar_p2_fuentes_referenciadas(archivos, "el readme no la menciona")
    assert estado is Estado.FALLA
    assert "captura_pagina_precios.md" in evidencia


def test_generador_corpus_detecta_simular_corpus(tmp_path):
    (tmp_path / "scripts").mkdir()
    ruta_generador = tmp_path / "scripts" / "simular_corpus.py"
    ruta_generador.write_text("# genera el corpus simulado", encoding="utf-8")

    assert _generador_corpus_simulado(tmp_path) == ruta_generador


def test_generador_corpus_ausente_da_none(tmp_path):
    assert _generador_corpus_simulado(tmp_path) is None
