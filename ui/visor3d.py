"""Teselacion de un modelo IFC a mallas renderizables (Sesion F.1, Tarea 7).

`mallas()` recorre los `IfcProduct` del archivo que traen geometria propia (`Representation` no
vacio) y los tesela con `ifcopenshell.geom.create_shape` en coordenadas de mundo
(`use-world-coords`, disponible por nombre en el build 0.8 instalado: `settings.set(...)`). Cada
malla resultante trae los vertices aplanados (x, y, z por cada vertice, en el mismo orden que
`shape.geometry.verts`) y las caras como indices de vertice por triadas (`shape.geometry.faces`),
listas para construir un `THREE.BufferGeometry` en `ui/paginas/visor.py` sin volver a tocar
ifcopenshell desde el navegador.

Un producto sin `Representation` (por ejemplo `IfcBuilding`, `IfcBuildingStorey`, `IfcSite`: la
jerarquia espacial del modelo) no tiene geometria propia y se salta; no es un error. Este modulo
solo lee geometria: no filtra por `Pset_APU` (ese filtro es del adaptador civil,
`adapters/civil/ifc.py`, que entrega la tabla elemento <-> partida <-> cantidad junto al visor).

`ifcopenshell` (y `ifcopenshell.geom`) se importan dentro de `mallas()`, no a nivel de modulo:
antes de esta tarea ninguna pagina registrada en `ui/app.py` requeria el extra `civil`, y un import
a nivel de modulo aqui obligaria a instalarlo solo para poder importar `ui.app` (rompiendo las
otras cinco pantallas en un entorno con `uv sync --extra ui --extra api`, sin `--extra civil`). El
import perezoso hace que el costo de la dependencia solo se pague cuando de verdad se tesela un
modelo (`ui/paginas/visor.py` captura el `ImportError` y muestra un mensaje, no una traza cruda).
"""

from __future__ import annotations

from pathlib import Path


def mallas(ruta: Path | str) -> list[dict]:
    """Tesela cada `IfcProduct` con geometria propia del archivo IFC en `ruta`.

    Devuelve una lista de diccionarios con `global_id`, `nombre`, `vertices` (floats x, y, z
    aplanados) y `caras` (indices de vertice por triadas), uno por elemento con representacion
    geometrica. Un modelo sin ningun elemento con geometria devuelve una lista vacia: la pagina
    distingue ese caso (nada que renderizar) de un archivo inexistente o corrupto (`ruta` invalida
    hace fallar `ifcopenshell.open` antes de llegar aqui). Lanza `ImportError` si el extra `civil`
    (ifcopenshell) no esta instalado; quien llama decide como mostrarlo.
    """
    import ifcopenshell
    import ifcopenshell.geom

    modelo = ifcopenshell.open(str(ruta))
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)

    resultado: list[dict] = []
    for producto in modelo.by_type("IfcProduct"):
        if producto.Representation is None:
            continue
        forma = ifcopenshell.geom.create_shape(settings, producto)
        resultado.append(
            {
                "global_id": producto.GlobalId,
                "nombre": producto.Name or "",
                "vertices": list(forma.geometry.verts),
                "caras": list(forma.geometry.faces),
            }
        )
    return resultado
