"""Pruebas del modo entrega de `ui/app.py` (Sesion P5.1, prototipo AREN.IA).

El filtro de pantallas es una funcion pura sobre `DefinicionPagina`, que no es de Streamlit: se
prueba sin construir ningun `st.Page` ni arrancar la aplicacion.
"""

from __future__ import annotations

from ui.app import VARIABLE_MODO_ENTREGA, modo_entrega_activo, paginas_visibles

TITULOS_NUEVE = (
    "Actualizacion de precios (UC-02)",
    "Catalogo",
    "Componer partida (UC-10 / UC-11)",
    "Elaborar presupuesto (UC-01)",
    "Escenarios (UC-08)",
    "Historico de precios",
    "Partidas similares (UC-03)",
    "Simulador de listas",
    "Visor 3D",
)

TITULOS_ARENIA = (
    "Actualizacion de precios (UC-02)",
    "Catalogo",
    "Componer partida (UC-10 / UC-11)",
    "Elaborar presupuesto (UC-01)",
    "Historico de precios",
)

TITULOS_INVESTIGACION = (
    "Escenarios (UC-08)",
    "Partidas similares (UC-03)",
    "Simulador de listas",
    "Visor 3D",
)


def test_sin_modo_entrega_se_ven_las_nueve_en_el_orden_de_hoy() -> None:
    titulos = tuple(pagina.titulo for pagina in paginas_visibles(False))
    assert titulos == TITULOS_NUEVE


def test_modo_entrega_muestra_exactamente_las_cinco_de_arenia_en_orden() -> None:
    titulos = tuple(pagina.titulo for pagina in paginas_visibles(True))
    assert titulos == TITULOS_ARENIA


def test_modo_entrega_oculta_las_cuatro_de_investigacion() -> None:
    titulos = {pagina.titulo for pagina in paginas_visibles(True)}
    assert titulos.isdisjoint(TITULOS_INVESTIGACION)
    assert all(not pagina.investigacion for pagina in paginas_visibles(True))


def test_modo_entrega_solo_se_activa_con_el_valor_exacto_1() -> None:
    assert modo_entrega_activo({VARIABLE_MODO_ENTREGA: "1"}) is True
    assert modo_entrega_activo({}) is False
    assert modo_entrega_activo({VARIABLE_MODO_ENTREGA: "0"}) is False
    assert modo_entrega_activo({VARIABLE_MODO_ENTREGA: "si"}) is False
