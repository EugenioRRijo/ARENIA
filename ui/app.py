"""Interfaz Streamlit multipagina del sistema APU (Sesion F.1, Tarea 4).

Enrutador `st.navigation` sobre las seis pantallas de `ui/paginas/`: actualizacion masiva de
precios (UC-02), catalogo, elaborar presupuesto (UC-01), historico de cambios de precio, el
simulador de listas de prueba y el visor 3D del modelo IFC (Tarea 7).

Cada pagina expone `def render() -> None` sin efectos al importarse (los suyos, y los de este
modulo, los comprueba `tests/unit/test_ui_importable.py` con `importlib.import_module`): este
modulo importa esas funciones para poder registrarlas, pero **no** construye ningun objeto de
Streamlit (`st.Page`, `st.navigation`) a nivel de modulo, solo dentro de `main()`, que unicamente
corre cuando la app se ejecuta de verdad (`if __name__ == "__main__"`). `st.set_page_config` se
llama una unica vez aqui, antes de `st.navigation` (regla de Streamlit para apps multipagina): las
paginas ya no la llaman por su cuenta, a diferencia del `ui/app.py` de una sola pantalla que existia
antes de esta sesion.

Las paginas no comparten constantes de presentacion con este enrutador (evita un import circular
`ui.app` <-> `ui.paginas.*`): cada una define su propio valor por defecto trivial de UI (por ejemplo
`RUTA_BASE_POR_DEFECTO = "data/apu.db"`, ya repetido igual en `scripts/simular_lista.py`), mientras
que la unica definicion de presentacion que sí importan todas es la compartida de verdad:
`core.verification.informe.DECIMALES_PRESENTACION` y `core.verification.texto.formatear_decimal`
(principio DRY, CLAUDE.md §2).

Uso::

    uv sync --extra ui --extra api --extra civil
    uv run streamlit run ui/app.py
"""

from __future__ import annotations

import streamlit as st

from ui.paginas import actualizacion, catalogo, elaborar, historico, simulador, visor

TITULO_APP = "Sistema APU"


def main() -> None:
    """Punto de entrada de `streamlit run ui/app.py`: configura la pagina y arranca el enrutador."""
    st.set_page_config(page_title=TITULO_APP, layout="wide")
    paginas = [
        st.Page(actualizacion.render, title="Actualizacion de precios (UC-02)", default=True),
        st.Page(catalogo.render, title="Catalogo"),
        st.Page(elaborar.render, title="Elaborar presupuesto (UC-01)"),
        st.Page(historico.render, title="Historico de precios"),
        st.Page(simulador.render, title="Simulador de listas"),
        st.Page(visor.render, title="Visor 3D"),
    ]
    st.navigation(paginas).run()


if __name__ == "__main__":
    main()
