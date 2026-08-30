"""Adaptador tabular del dominio civil (Sesión I3.2).

Lee una tabla CSV de geometría (tanquillas y zanjas) y devuelve las cantidades de obra trazables
que producen las reglas paramétricas de `adapters/civil/reglas.py`. Es la entrada tabular prevista
por la compuerta G1 (CLAUDE.md, sección 8.2) si el adaptador IFC no reproduce el cálculo manual;
aquí se implementa de forma independiente porque el brief de esta sesión la pide como entrega
propia.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from adapters.civil.evaluador import evaluar_regla
from adapters.civil.reglas import (
    REGLA_VOLUMEN_TUBERIA,
    computar_relleno,
    computar_tanquillas,
    computar_zanja,
)
from core.contracts import AdaptadorDominio, Dominio, ItemComputo

_TIPO_TANQUILLA = "tanquilla"
_TIPO_ZANJA = "zanja"


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


class AdaptadorCivilTabular(AdaptadorDominio):
    """Extrae cantidades de obra civiles de una tabla CSV de geometría.

    Cada fila es una tanquilla o una zanja (columna `tipo`); si `codigos` declara un código de
    partida para `relleno`, se emite además un ítem de relleno que balancea toda la excavación, el
    concreto y el volumen de tubería de la fuente completa (regla R5, Sesión I4).
    """

    dominio = Dominio.CIVIL

    def __init__(self, codigos: Mapping[str, str]) -> None:
        self._codigos = dict(codigos)

    def extraer(self, fuente: Path | str) -> list[ItemComputo]:
        items: list[ItemComputo] = []
        ids_procesadas: list[str] = []
        excavacion_total = Decimal("0")
        concreto_total = Decimal("0")
        volumen_tuberia_total = Decimal("0")
        factor_volumen_tuberia: Decimal | None = None

        with open(fuente, newline="", encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                fila_id = fila["id"]
                ids_procesadas.append(fila_id)
                especificaciones = _parsear_especificaciones(fila.get("especificaciones"))
                tipo = fila["tipo"].strip()

                if tipo == _TIPO_TANQUILLA:
                    concreto, encofrado, excavacion = computar_tanquillas(
                        origen_id=fila_id,
                        codigos=self._codigos,
                        a=Decimal(fila["a"]),
                        h=Decimal(fila["h"]),
                        e=Decimal(fila["e"]),
                        n=Decimal(fila["n"]),
                        sobreancho=Decimal(fila["sobreancho"]),
                        espesor_fondo=Decimal(fila["espesor_fondo"]),
                        especificaciones=especificaciones,
                    )
                    items.extend([concreto, encofrado, excavacion])
                    concreto_total += concreto.cantidad
                    excavacion_total += excavacion.cantidad
                elif tipo == _TIPO_ZANJA:
                    diametro_zanja = Decimal(fila["diametro"])
                    excavacion, tuberia = computar_zanja(
                        origen_id=fila_id,
                        codigos=self._codigos,
                        longitud=Decimal(fila["longitud"]),
                        ancho=Decimal(fila["ancho"]),
                        profundidad=Decimal(fila["profundidad"]),
                        diametro=diametro_zanja,
                        desperdicio=Decimal(fila["desperdicio"]),
                        especificaciones=especificaciones,
                    )
                    items.extend([excavacion, tuberia])
                    excavacion_total += excavacion.cantidad
                    # Factor de conversión m -> m3 de la tubería (área de la sección): se deriva
                    # de REGLA_VOLUMEN_TUBERIA con longitud=1 para no repetir el coeficiente 0.7854.
                    factor_volumen_tuberia = evaluar_regla(
                        REGLA_VOLUMEN_TUBERIA,
                        {"longitud": Decimal("1"), "diametro": diametro_zanja},
                    )
                    volumen_tuberia_total += factor_volumen_tuberia * tuberia.cantidad
                else:
                    raise ValueError(f"tipo de fila no reconocido en {fuente!r}: {tipo!r}")

        if "relleno" in self._codigos:
            if factor_volumen_tuberia is None:
                raise ValueError(
                    "no se puede construir el balance de relleno sin una fila de zanja "
                    "(se necesita el diametro de tuberia)"
                )
            balance = (
                f"{{{self._codigos['excavacion']}}} - {{{self._codigos['concreto']}}} - "
                f"{{{self._codigos['tuberia']}}} * {factor_volumen_tuberia}"
            )
            items.append(
                computar_relleno(
                    origen_id="relleno:" + ",".join(ids_procesadas),
                    codigos=self._codigos,
                    excavacion=excavacion_total,
                    concreto=concreto_total,
                    volumen_tuberia=volumen_tuberia_total,
                    balance=balance,
                )
            )

        return items
