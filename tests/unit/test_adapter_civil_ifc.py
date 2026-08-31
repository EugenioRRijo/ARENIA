from decimal import Decimal
from pathlib import Path

import pytest

pytest.importorskip("ifcopenshell")

RAIZ = Path(__file__).resolve().parents[2]
MUESTRA = RAIZ / "data" / "samples" / "tanquilla.ifc"


def test_g1_lo_extraido_coincide_con_el_calculo_manual():
    from adapters.civil.ifc import AdaptadorCivilIFC

    items = AdaptadorCivilIFC().extraer(MUESTRA)
    assert len(items) == 1
    item = items[0]
    assert item.cantidad == Decimal("0.224")  # (0.8^2 - 0.6^2) * 0.8, calculo manual
    assert item.unidad == "m3" and item.codigo_partida == "LB-04-CON"
    assert item.origen_tipo.value == "ifc" and len(item.origen_id) == 22  # GlobalId IFC


def test_solo_importa_core_contracts():
    import ast

    fuente = (RAIZ / "adapters" / "civil" / "ifc.py").read_text(encoding="utf-8")
    for nodo in ast.walk(ast.parse(fuente)):
        modulos = (
            [a.name for a in nodo.names]
            if isinstance(nodo, ast.Import)
            else ([nodo.module] if isinstance(nodo, ast.ImportFrom) and nodo.module else [])
        )
        for m in modulos:
            if m.startswith("core"):
                assert m.startswith("core.contracts"), m
