"""Adaptador del dominio sistemas: alcance funcional (Sesión I5).

Lee una tabla CSV de casos de uso y calcula, para cada uno, los puntos de función no ajustados
(PFNA) por el método de análisis de puntos de función de IFPUG, con los pesos medios de
complejidad de cada tipo de función (International Function Point Users Group, tabla estándar de
complejidad media):

| Tipo de función                          | Sigla | Peso medio | Columna del CSV |
|-------------------------------------------|-------|-----------:|------------------|
| Entrada externa (External Input)           | EI    |          4 | `entradas`       |
| Salida externa (External Output)           | EO    |          5 | `salidas`        |
| Consulta externa (External Inquiry)        | EQ    |          4 | `consultas`      |
| Archivo lógico interno (Internal Logical File) | ILF |         10 | `archivos`       |
| Archivo de interfaz externa (External Interface File) | EIF |   7 | `interfaces`     |

`REGLA_PUNTOS_FUNCION` es la expresión trazable que combina esos pesos: cada `ItemComputo` la
guarda en `regla` junto con las cinco cantidades en `parametros`, de modo que el informe de
auditoría puede reevaluarla (regla R1 de `core/verification/`, CLAUDE.md §7).

Nota sobre la unidad ("pf"): `core.contracts.unidades._ALIAS` es la única tabla de alias del
sistema (CLAUDE.md §2) y solo cubre unidades físicas de obra (m3, m2, m, pieza, kg, etc.); "punto
de función" no es una de ellas. `normalizar_unidad("pf")` la deja tal cual (minúsculas, sin
espacios), sin traducirla ni fallar, que es el comportamiento documentado para unidades
desconocidas. No se modifica `core/contracts/unidades.py` para agregarla (regla del contrato
congelado, CLAUDE.md §5 y §9): se documenta como hallazgo en
`docs/bitacora/2026-08-29-I5-sistemas.md`.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from adapters.sistemas.evaluador import evaluar_regla
from core.contracts import AdaptadorDominio, Dominio, ItemComputo, OrigenTipo

REGLA_PUNTOS_FUNCION = "4*entradas + 5*salidas + 4*consultas + 10*archivos + 7*interfaces"

_COLUMNAS_CONTEO = ("entradas", "salidas", "consultas", "archivos", "interfaces")


def _parsear_especificaciones(texto: str | None) -> dict[str, str]:
    """`"clave=valor;clave=valor"` -> `{"clave": "valor", ...}`. Cadena vacía -> diccionario vacío.

    Mismo formato que `adapters/civil/tabular.py`, repetido aquí porque el evaluador de este
    dominio es deliberadamente independiente del de civil (docstring de `adapters/sistemas/
    evaluador.py`) y esta función no forma parte de ningún contrato compartido.
    """
    resultado: dict[str, str] = {}
    for par in (texto or "").split(";"):
        par = par.strip()
        if not par:
            continue
        clave, _, valor = par.partition("=")
        resultado[clave.strip()] = valor.strip()
    return resultado


class AdaptadorSistemas(AdaptadorDominio):
    """Extrae puntos de función no ajustados (PFNA) de una tabla CSV de alcance funcional.

    Cada fila es un caso de uso, con su propio `codigo_partida`: a diferencia del adaptador civil
    tabular, este no recibe un mapeo externo de códigos porque la fuente ya los declara. La
    cantidad de cada `ItemComputo` es el PFNA evaluado con `REGLA_PUNTOS_FUNCION` sobre las cinco
    columnas de conteo de la fila.
    """

    dominio = Dominio.SISTEMAS

    def extraer(self, fuente: Path | str) -> list[ItemComputo]:
        items: list[ItemComputo] = []
        with open(fuente, newline="", encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                parametros = {columna: Decimal(fila[columna]) for columna in _COLUMNAS_CONTEO}
                cantidad = evaluar_regla(REGLA_PUNTOS_FUNCION, parametros)
                items.append(
                    ItemComputo(
                        codigo_partida=fila["codigo_partida"],
                        descripcion=f"{fila['modulo']}: {fila['caso_de_uso']}",
                        unidad="pf",
                        cantidad=cantidad,
                        origen_id=fila["id"],
                        origen_tipo=OrigenTipo.REGLA,
                        dominio=Dominio.SISTEMAS,
                        regla=REGLA_PUNTOS_FUNCION,
                        parametros=parametros,
                        especificaciones=_parsear_especificaciones(fila.get("especificaciones")),
                    )
                )
        return items
