import builtins
import sys
from pathlib import Path

import pytest

pytest.importorskip("ifcopenshell")

MUESTRA = Path(__file__).resolve().parents[2] / "data" / "samples" / "tanquilla.ifc"

#: Modulos que un import perezoso mal hecho dejaria en el cache con ifcopenshell ya cargado; se
#: limpian antes y se restauran despues de simular su ausencia (ver `_SinIfcopenshell`).
_MODULOS_RELACIONADOS_CON_IFC = (
    "ifcopenshell",
    "ifcopenshell.geom",
    "ifcopenshell.util",
    "ifcopenshell.util.element",
    "adapters.civil.ifc",
    "ui.visor3d",
    "ui.paginas.visor",
    "ui.app",
)


def test_la_tanquilla_se_tesela_a_una_malla_valida():
    from ui.visor3d import mallas

    resultado = mallas(MUESTRA)
    assert len(resultado) == 1
    malla = resultado[0]
    assert len(malla["vertices"]) % 3 == 0 and len(malla["vertices"]) >= 24
    assert len(malla["caras"]) % 3 == 0 and malla["caras"]
    assert malla["global_id"]


class _SinIfcopenshell:
    """Simula, dentro de este mismo entorno (que sí tiene ifcopenshell), un entorno sin el extra
    `civil`: limpia del cache de modulos todo lo que pudiera haber importado ifcopenshell y bloquea
    `import ifcopenshell` (y sus submodulos) con un `ImportError`, para que un import a nivel de
    modulo mal hecho en `ui.app`/`ui.paginas.visor`/`ui.visor3d` se delate de inmediato. Restaura
    el cache original al salir, monkeypatch aparte, para no afectar otras pruebas de la suite.
    """

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._monkeypatch = monkeypatch

    def __enter__(self) -> None:
        self._respaldo = {
            nombre: sys.modules[nombre]
            for nombre in _MODULOS_RELACIONADOS_CON_IFC
            if nombre in sys.modules
        }
        for nombre in _MODULOS_RELACIONADOS_CON_IFC:
            sys.modules.pop(nombre, None)

        import_original = builtins.__import__

        def import_bloqueado(nombre, *args, **kwargs):
            if nombre == "ifcopenshell" or nombre.startswith("ifcopenshell."):
                raise ImportError(f"simulado: extra civil no instalado ({nombre})")
            return import_original(nombre, *args, **kwargs)

        self._monkeypatch.setattr(builtins, "__import__", import_bloqueado)

    def __exit__(self, *excepcion) -> None:
        for nombre in _MODULOS_RELACIONADOS_CON_IFC:
            sys.modules.pop(nombre, None)
        sys.modules.update(self._respaldo)


def test_ui_app_y_el_visor_se_importan_sin_ifcopenshell(monkeypatch):
    """`ui.app` registra seis paginas; antes de esta tarea ninguna requeria el extra `civil`. Este
    fix debe mantener esa propiedad: importar `ui.app` (y por lo tanto `ui.paginas.visor` y
    `ui.visor3d`) no debe requerir ifcopenshell, solo usarlo cuando el visor se ejecuta de verdad.
    """
    import importlib

    with _SinIfcopenshell(monkeypatch):
        modulo_app = importlib.import_module("ui.app")
        modulo_visor = importlib.import_module("ui.paginas.visor")
        modulo_3d = importlib.import_module("ui.visor3d")

    assert modulo_app is not None
    assert modulo_visor is not None
    assert modulo_3d is not None


def test_cargar_dependencias_civiles_reporta_la_ausencia_del_extra(monkeypatch):
    """Sin ifcopenshell, el cargador perezoso de `ui.paginas.visor` relanza `ImportError` (que
    `render()` convierte en un mensaje con `st.error`, no en una traza cruda)."""
    from ui.paginas import visor

    with _SinIfcopenshell(monkeypatch):
        with pytest.raises(ImportError):
            visor._cargar_dependencias_civiles()


def test_cargar_dependencias_civiles_funciona_con_el_extra_instalado():
    """Con el extra `civil` instalado (el caso normal del sprint), el cargador perezoso sí entrega
    ifcopenshell y `AdaptadorCivilIFC` utilizables."""
    from ui.paginas import visor

    ifcopenshell, adaptador_civil_ifc = visor._cargar_dependencias_civiles()

    assert ifcopenshell.version
    assert adaptador_civil_ifc.dominio.value == "civil"
