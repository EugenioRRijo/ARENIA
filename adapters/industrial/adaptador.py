"""Adaptador del dominio industrial: registro de activos con frecuencia de intervención (Sesión I5).

Lee un CSV de activos de planta (bombas, tableros, compresores, transformadores, válvulas, motores…)
y convierte cada fila en un `ItemComputo` trazable: la cantidad de obra es el número de
intervenciones de mantenimiento esperadas en el horizonte de planificación, `frecuencia_anual *
horizonte_anios`, declarada como regla para que el informe de auditoría muestre la expresión exacta
que la produjo (regla R1, CLAUDE.md §7). La muestra y sus supuestos están en
`data/samples/industrial/README.md`.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from adapters.industrial.evaluador import evaluar_regla
from core.contracts import AdaptadorDominio, Dominio, ItemComputo, OrigenTipo

REGLA_INTERVENCIONES = "frecuencia_anual * horizonte_anios"


def _parsear_especificaciones(texto: str | None) -> dict[str, str]:
    """`"clave=valor;clave=valor"` -> `{"clave": "valor", ...}`. Cadena vacía -> diccionario vacío.

    Convierte el texto de la columna `especificaciones` del CSV en el diccionario que espera
    `ItemComputo.especificaciones` (regla R4).
    """
    resultado: dict[str, str] = {}
    for par in (texto or "").split(";"):
        par = par.strip()
        if not par:
            continue
        clave, _, valor = par.partition("=")
        resultado[clave.strip()] = valor.strip()
    return resultado


class AdaptadorIndustrial(AdaptadorDominio):
    """Extrae cantidades de mantenimiento de un registro de activos de planta.

    Cada fila del CSV es un activo con su frecuencia de intervención anual; la cantidad de obra
    (unidad declarada en la fila, típicamente "intervencion") es esa frecuencia multiplicada por el
    horizonte de planificación en años, evaluada por `REGLA_INTERVENCIONES` (trazable, regla R1).
    """

    dominio = Dominio.INDUSTRIAL

    def extraer(self, fuente: Path | str) -> list[ItemComputo]:
        items: list[ItemComputo] = []
        with open(fuente, newline="", encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                parametros = {
                    "frecuencia_anual": Decimal(fila["frecuencia_anual"]),
                    "horizonte_anios": Decimal(fila["horizonte_anios"]),
                }
                cantidad = evaluar_regla(REGLA_INTERVENCIONES, parametros)
                items.append(
                    ItemComputo(
                        codigo_partida=fila["codigo_partida"],
                        descripcion=fila["descripcion"],
                        unidad=fila["unidad"],
                        cantidad=cantidad,
                        origen_id=fila["id_activo"],
                        origen_tipo=OrigenTipo.REGLA,
                        dominio=Dominio.INDUSTRIAL,
                        regla=REGLA_INTERVENCIONES,
                        parametros=parametros,
                        especificaciones=_parsear_especificaciones(fila.get("especificaciones")),
                    )
                )
        return items
