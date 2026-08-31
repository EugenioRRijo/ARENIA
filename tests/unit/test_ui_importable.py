import importlib


def test_las_paginas_se_importan_sin_efectos():
    for mod in (
        "ui.app",
        "ui.paginas.actualizacion",
        "ui.paginas.catalogo",
        "ui.paginas.elaborar",
        "ui.paginas.historico",
        "ui.paginas.simulador",
        "ui.paginas.visor",
    ):
        importlib.import_module(mod)
