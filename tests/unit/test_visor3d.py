from pathlib import Path

import pytest

pytest.importorskip("ifcopenshell")

MUESTRA = Path(__file__).resolve().parents[2] / "data" / "samples" / "tanquilla.ifc"


def test_la_tanquilla_se_tesela_a_una_malla_valida():
    from ui.visor3d import mallas

    resultado = mallas(MUESTRA)
    assert len(resultado) == 1
    malla = resultado[0]
    assert len(malla["vertices"]) % 3 == 0 and len(malla["vertices"]) >= 24
    assert len(malla["caras"]) % 3 == 0 and malla["caras"]
    assert malla["global_id"]
