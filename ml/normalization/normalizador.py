"""Normalizacion semantica de descripciones de partida (UC-03, Sesion I2).

Dada una descripcion en texto libre, propone las partidas del catalogo mas parecidas por similitud
del coseno entre vectores de `sentence-transformers` (modelo multilingue
`paraphrase-multilingual-MiniLM-L12-v2`, el que fija el PLAN). No requiere datos etiquetados ni
entrenamiento: es similitud semantica directa.

Arquitectura (CLAUDE.md §2, `tests/unit/test_arquitectura.py`): `ml/` no conoce la base de datos ni
importa de `core` nada fuera de `core.contracts` -- este modulo, de hecho, no necesita ni los
contratos: recibe el catalogo como pares (codigo, descripcion) planos y la capa de composicion
(`ui/`, `api/`) le pasa lo que consulta `core.catalog`.

El puntaje es un `float`: es una similitud adimensional en [-1, 1], no una cantidad de obra ni un
monto, asi que la regla `Decimal` de CLAUDE.md §2.3 no lo alcanza (los vectores del modelo son
`float32` de origen). Se presenta redondeado solo en la capa de presentacion.

La primera construccion descarga el modelo si no esta en la cache local de Hugging Face
(precondicion del UC-03: «el modelo de similitud esta disponible localmente», docs/ERS.md); las
siguientes lo reutilizan en memoria (`_cargar_modelo` esta cacheado por proceso).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache

#: El modelo que fija el PLAN (Sesion I2): multilingue, entrenado para parafrasis.
MODELO_POR_DEFECTO = "paraphrase-multilingual-MiniLM-L12-v2"

#: Umbral declarado de similitud (RF-15): por debajo no se propone nada y el llamador ofrece
#: crear la partida desde cero (UC-03, flujo 2a). Calibrado con la prueba de aceptacion RF-17
#: sobre la linea base parafraseada (tests/unit/test_normalizacion.py).
UMBRAL_POR_DEFECTO = 0.5

#: RF-15 pide las tres mas similares.
PROPUESTAS_POR_DEFECTO = 3

__all__ = [
    "MODELO_POR_DEFECTO",
    "PROPUESTAS_POR_DEFECTO",
    "UMBRAL_POR_DEFECTO",
    "NormalizadorPartidas",
    "PartidaSimilar",
]


@lru_cache(maxsize=2)
def _cargar_modelo(nombre: str):
    """Un `SentenceTransformer` por nombre y por proceso: cargarlo cuesta segundos y memoria."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(nombre)


@dataclass(frozen=True)
class PartidaSimilar:
    """Una propuesta de reutilizacion: la partida del catalogo y el puntaje que la justifica.

    El puntaje queda registrado como justificacion de la reutilizacion (UC-03, postcondicion).
    """

    codigo: str
    descripcion: str
    puntaje: float


class NormalizadorPartidas:
    """Indice semantico del catalogo de partidas.

    Vectoriza las descripciones una sola vez al construirse (normalizadas a modulo 1, de modo que
    la similitud del coseno es el producto punto) y responde consultas con `similares`.
    """

    def __init__(
        self,
        partidas: Mapping[str, str],
        modelo: str = MODELO_POR_DEFECTO,
        umbral: float = UMBRAL_POR_DEFECTO,
    ) -> None:
        """:param partidas: catalogo como {codigo: descripcion}; puede estar vacio (flujo 2b).
        :param modelo: nombre del modelo de sentence-transformers.
        :param umbral: similitud minima para proponer (RF-15).
        """
        self._partidas = dict(partidas)
        self._codigos = list(self._partidas)
        self._umbral = umbral
        self._modelo = _cargar_modelo(modelo)
        self._vectores = (
            self._modelo.encode(
                [self._partidas[codigo] for codigo in self._codigos],
                normalize_embeddings=True,
            )
            if self._codigos
            else None
        )

    def similares(
        self, descripcion: str, cuantos: int = PROPUESTAS_POR_DEFECTO
    ) -> list[PartidaSimilar]:
        """Las `cuantos` partidas mas parecidas, de mayor a menor puntaje, todas sobre el umbral.

        Lista vacia si el catalogo esta vacio (UC-03, flujo 2b) o si ningun candidato alcanza el
        umbral (flujo 2a): el llamador ofrece entonces crear la partida desde cero.
        """
        if self._vectores is None:
            return []
        consulta = self._modelo.encode([descripcion], normalize_embeddings=True)[0]
        puntajes = self._vectores @ consulta
        mejores = puntajes.argsort()[::-1][:cuantos]
        return [
            PartidaSimilar(
                codigo=self._codigos[indice],
                descripcion=self._partidas[self._codigos[indice]],
                puntaje=float(puntajes[indice]),
            )
            for indice in mejores
            if float(puntajes[indice]) >= self._umbral
        ]
