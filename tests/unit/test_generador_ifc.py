from decimal import Decimal

import pytest

pytest.importorskip("ifcopenshell")


def test_genera_una_tanquilla_con_pset_y_volumen(tmp_path):
    import ifcopenshell
    import ifcopenshell.util.element

    from scripts.generar_tanquilla_ifc import generar

    ruta = tmp_path / "tanquilla.ifc"
    generar(ruta, a=Decimal("0.80"), h=Decimal("0.80"), e=Decimal("0.10"))
    modelo = ifcopenshell.open(str(ruta))
    elementos = modelo.by_type("IfcBuildingElementProxy")
    assert len(elementos) == 1
    psets = ifcopenshell.util.element.get_psets(elementos[0])
    apu = psets["Pset_APU"]
    assert apu["COVENIN_Codigo"] == "LB-04-CON" and apu["Unidad"] == "m3"
    qto = psets["Qto_APU"]
    assert Decimal(str(qto["VolumenConcreto"])) == Decimal("0.224")
    assert elementos[0].GlobalId
