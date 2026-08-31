"""Normalizacion semantica de partidas (UC-03, Sesion I2). Requiere el extra `ml`."""

from ml.normalization.normalizador import (
    MODELO_POR_DEFECTO,
    PROPUESTAS_POR_DEFECTO,
    UMBRAL_POR_DEFECTO,
    NormalizadorPartidas,
    PartidaSimilar,
)

__all__ = [
    "MODELO_POR_DEFECTO",
    "PROPUESTAS_POR_DEFECTO",
    "UMBRAL_POR_DEFECTO",
    "NormalizadorPartidas",
    "PartidaSimilar",
]
