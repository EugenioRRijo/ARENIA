"""La meta del sprint del prototipo: que audite fases y no se salte ninguna."""

from __future__ import annotations

import pytest

from scripts.meta_prototipo import FASES, TITULOS, main


def test_toda_meta_declarada_tiene_titulo():
    for codigo in (codigo for metas in FASES.values() for codigo in metas):
        assert codigo in TITULOS, f"la meta {codigo} no tiene titulo"


def test_las_fases_van_de_p0_a_p5():
    assert list(FASES) == ["P0", "P1", "P2", "P3", "P4", "P5"]


def test_hasta_una_fase_inexistente_se_rechaza():
    with pytest.raises(SystemExit):
        main(["--hasta", "P9"])
