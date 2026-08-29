"""Informe de auditoría: se genera siempre, sin que el usuario lo pida (CLAUDE.md §2.7).

`auditar` corre las siete reglas sobre un presupuesto y devuelve un `InformeAuditoria` inmutable con
los hallazgos ordenados y con el índice que permite atribuir cada hallazgo a su partida.

Ese índice existe porque `Hallazgo` no lleva `codigo_partida` (insuficiencia del contrato registrada
en la bitácora de la Sesión I4): un hallazgo referencia `origen_ids`, y solo el presupuesto sabe qué
partida produjo cada origen. `auditar` construye el mapa `origen_id -> codigo_partida` a partir de
los ítems y lo guarda en el informe, que resuelve la atribución sin tocar los contratos.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType

from core.contracts.presupuesto import Presupuesto
from core.contracts.verificacion import Hallazgo, ReglaVerificacion, Severidad
from core.verification.reglas import REGLAS
from core.verification.texto import formatear_decimal

__all__ = ["InformeAuditoria", "auditar"]

DECIMALES_PRESENTACION = 2

_SEVERIDADES = tuple(sorted(Severidad, reverse=True))
_GRAVES = frozenset({Severidad.ERROR, Severidad.CRITICO})


def _clave_orden(hallazgo: Hallazgo) -> tuple[int, str, str, str]:
    primer_origen = hallazgo.origen_ids[0] if hallazgo.origen_ids else ""
    return (-int(hallazgo.severidad), hallazgo.regla, primer_origen, hallazgo.descripcion)


def _celda(valor: Decimal | None) -> str:
    return "" if valor is None else formatear_decimal(valor, DECIMALES_PRESENTACION)


@dataclass(frozen=True, slots=True)
class InformeAuditoria:
    """Resultado de auditar un presupuesto. Los hallazgos se ordenan por gravedad descendente."""

    codigo_presupuesto: str
    hallazgos: tuple[Hallazgo, ...] = ()
    partida_por_origen: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "hallazgos", tuple(sorted(self.hallazgos, key=_clave_orden)))
        object.__setattr__(
            self, "partida_por_origen", MappingProxyType(dict(self.partida_por_origen))
        )

    @property
    def cumple(self) -> bool:
        """True si no hay ningún hallazgo de severidad ERROR o CRITICO."""
        return not any(hallazgo.severidad in _GRAVES for hallazgo in self.hallazgos)

    def por_severidad(self) -> dict[Severidad, int]:
        """Cuántos hallazgos hay de cada severidad, de la más grave a la más leve."""
        conteo = {severidad: 0 for severidad in _SEVERIDADES}
        for hallazgo in self.hallazgos:
            conteo[hallazgo.severidad] += 1
        return {severidad: total for severidad, total in conteo.items() if total}

    def por_regla(self) -> dict[str, list[Hallazgo]]:
        """Hallazgos agrupados por código de regla, en el orden en que aparecen en el informe."""
        agrupados: dict[str, list[Hallazgo]] = defaultdict(list)
        for hallazgo in self.hallazgos:
            agrupados[hallazgo.regla].append(hallazgo)
        return dict(agrupados)

    def partida_de(self, hallazgo: Hallazgo) -> str | None:
        """Código de la partida del primer origen del hallazgo, o None si no atribuye ninguna.

        Un hallazgo que referencia el presupuesto completo (el cierre de la curva) no lleva
        orígenes y devuelve None.
        """
        if not hallazgo.origen_ids:
            return None
        return self.partida_por_origen.get(hallazgo.origen_ids[0])

    def a_markdown(self) -> str:
        """Informe legible: cabecera, resumen por severidad y tabla de hallazgos.

        Los montos y cantidades de la tabla se redondean a dos decimales, que es el único lugar
        donde se redondea (CLAUDE.md §2.3); la descripción de cada hallazgo conserva el valor
        exacto que lo motivó.
        """
        veredicto = "CUMPLE" if self.cumple else "NO CUMPLE"
        lineas = [
            f"# Informe de auditoria del presupuesto {self.codigo_presupuesto}",
            "",
            f"Hallazgos: {len(self.hallazgos)} · Resultado: {veredicto}",
            "",
            "## Resumen por severidad",
            "",
            "| Severidad | Hallazgos |",
            "|---|---|",
        ]
        lineas.extend(
            f"| {severidad.name} | {total} |" for severidad, total in self.por_severidad().items()
        )
        lineas.extend(
            [
                "",
                "## Hallazgos",
                "",
                "| # | Regla | Severidad | Partida | Descripcion | Impacto | Observado "
                "| Esperado |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for numero, hallazgo in enumerate(self.hallazgos, start=1):
            lineas.append(
                f"| {numero} | {hallazgo.regla} | {hallazgo.severidad.name} "
                f"| {self.partida_de(hallazgo) or '-'} | {hallazgo.descripcion} "
                f"| {_celda(hallazgo.impacto)} | {_celda(hallazgo.valor_observado)} "
                f"| {_celda(hallazgo.valor_esperado)} |"
            )
        lineas.append("")
        return "\n".join(lineas)


def auditar(
    presupuesto: Presupuesto, reglas: Sequence[ReglaVerificacion] = REGLAS
) -> InformeAuditoria:
    """Corre las reglas sobre el presupuesto y devuelve el informe.

    Nunca modifica el presupuesto: las reglas solo leen.
    """
    hallazgos: list[Hallazgo] = []
    for regla in reglas:
        hallazgos.extend(regla.evaluar(presupuesto))
    return InformeAuditoria(
        codigo_presupuesto=presupuesto.codigo,
        hallazgos=tuple(hallazgos),
        partida_por_origen=_indice_de_partidas(presupuesto),
    )


def _indice_de_partidas(presupuesto: Presupuesto) -> dict[str, str]:
    """`origen_id -> codigo_partida`, más la identidad de cada código.

    Casi todas las reglas referencian ítems por su `origen_id`, pero R6 compara APU entre sí y solo
    puede referenciar códigos de partida. Registrar también `codigo -> codigo` deja que
    `partida_de` resuelva ambos casos con una sola consulta. Los `origen_id` reales tienen
    prioridad: se registran primero.
    """
    indice: dict[str, str] = {}
    for partida in presupuesto.partidas:
        indice.setdefault(partida.item.origen_id, partida.item.codigo_partida)
    for partida in presupuesto.partidas:
        indice.setdefault(partida.item.codigo_partida, partida.item.codigo_partida)
    return indice
