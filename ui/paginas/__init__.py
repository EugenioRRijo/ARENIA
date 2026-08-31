"""Paginas de la interfaz Streamlit multipagina (Sesion F.1, Tarea 4).

Cada modulo expone `def render() -> None` sin efectos al importarse (los efectos viven dentro de
`render`, nunca a nivel de modulo): `tests/unit/test_ui_importable.py` importa los seis modulos de
`ui.app` y `ui.paginas` y no debe fallar ni abrir una sesion de base de datos. `ui/app.py` importa
cada `render` para registrarlo en `st.navigation`.
"""
