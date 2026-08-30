"""Errores del catálogo."""

from __future__ import annotations


# El sufijo `Error` (N818) se omite a propósito: los identificadores del proyecto van en
# español y «CatalogoIncompletoError» mezcla los dos idiomas en un solo nombre.
class CatalogoIncompleto(LookupError):  # noqa: N818
    """Falta un dato imprescindible para reconstruir un APU: un precio o un rendimiento.

    Es `LookupError` porque siempre significa «esto no está en el catálogo», nunca «esto está mal».
    """
