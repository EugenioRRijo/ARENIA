"""Adaptador tabular del dominio telecom (Sesion I5).

Lee una topologia de red en CSV (nodos y enlaces) y devuelve las cantidades de obra trazables que
describe. Un nodo (punto WiFi, switch, rack, UPS...) es una cantidad tabular directa
(`OrigenTipo.CSV`); un enlace (tramo de cable UTP o fibra) deriva su cantidad de la regla
parametrica `longitud_m * (1 + reserva)` -la reserva cubre el excedente de instalacion: curvas,
empalmes y holgura de servicio-, evaluada por `adapters/telecom/evaluador.py` (regla R1 de
verificacion: trazabilidad geometrica).
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from adapters.telecom.evaluador import evaluar_regla
from core.contracts import AdaptadorDominio, Dominio, ItemComputo, OrigenTipo

_TIPO_NODO = "nodo"
_TIPO_ENLACE = "enlace"
_REGLA_LONGITUD_ENLACE = "longitud_m * (1 + reserva)"


def _parsear_especificaciones(texto: str | None) -> dict[str, str]:
    """`"clave=valor;clave=valor"` -> `{"clave": "valor", ...}`. Cadena vacia -> diccionario vacio.

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


def _decimal_o_cero(valor: str | None) -> Decimal:
    valor = (valor or "").strip()
    return Decimal(valor) if valor else Decimal("0")


class AdaptadorTelecom(AdaptadorDominio):
    """Extrae cantidades de obra de una topologia de red (nodos y enlaces) desde un CSV.

    Cada fila `nodo` es una cantidad tabular directa; cada fila `enlace` deriva su cantidad de una
    regla trazable. `origen_id` es la clave `id` de la fila del CSV en ambos casos.
    """

    dominio = Dominio.TELECOM

    def extraer(self, fuente: Path | str) -> list[ItemComputo]:
        items: list[ItemComputo] = []
        with open(fuente, newline="", encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                tipo = fila["tipo"].strip()
                if tipo == _TIPO_NODO:
                    items.append(self._item_nodo(fila))
                elif tipo == _TIPO_ENLACE:
                    items.append(self._item_enlace(fila))
                else:
                    raise ValueError(f"tipo de fila no reconocido en {fuente!r}: {tipo!r}")
        return items

    def _item_nodo(self, fila: dict[str, str]) -> ItemComputo:
        return ItemComputo(
            codigo_partida=fila["codigo_partida"],
            descripcion=fila["descripcion"],
            unidad=fila["unidad"],
            cantidad=Decimal(fila["cantidad"]),
            origen_id=fila["id"],
            origen_tipo=OrigenTipo.CSV,
            dominio=Dominio.TELECOM,
            especificaciones=_parsear_especificaciones(fila.get("especificaciones")),
        )

    def _item_enlace(self, fila: dict[str, str]) -> ItemComputo:
        parametros = {
            "longitud_m": Decimal(fila["longitud_m"]),
            "reserva": _decimal_o_cero(fila.get("reserva")),
        }
        cantidad = evaluar_regla(_REGLA_LONGITUD_ENLACE, parametros)
        especificaciones = {
            "origen": fila["origen"],
            "destino": fila["destino"],
            **_parsear_especificaciones(fila.get("especificaciones")),
        }
        return ItemComputo(
            codigo_partida=fila["codigo_partida"],
            descripcion=fila["descripcion"],
            unidad=fila["unidad"],
            cantidad=cantidad,
            origen_id=fila["id"],
            origen_tipo=OrigenTipo.REGLA,
            dominio=Dominio.TELECOM,
            regla=_REGLA_LONGITUD_ENLACE,
            parametros=parametros,
            especificaciones=especificaciones,
        )
