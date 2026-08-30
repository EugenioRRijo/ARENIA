"""Convención de directivas: las claves de `especificaciones` que el núcleo interpreta.

`ItemComputo.especificaciones` es un diccionario de texto libre que los adaptadores llenan con los
atributos comparables de la cantidad (diámetro, material, espesor). La regla R4 los contrasta contra
el texto del APU. Pero algunas reglas del núcleo necesitan además instrucciones del adaptador —el
balance volumétrico de R5, la tolerancia con la que evaluarlo, la grafía original de una unidad que
`ItemComputo.__post_init__` ya normalizó—, y el contrato no tiene campo para ellas.

Convención (único lugar donde se declara): **una clave que empieza por `_` es una directiva para el
núcleo, no una especificación técnica**. R4 las ignora; R3 y R5 las leen. Los adaptadores declaran
las suyas con el mismo prefijo; `tests/unit/test_verification.py` comprueba que las del adaptador
civil coinciden con estas.

Aquí vive también la convención de etiquetado de los períodos de la curva de inversión: `PuntoCurva`
no lleva código de partida (insuficiencia del contrato registrada en la bitácora de la Sesión I4),
así que el plan de trabajo puede declarar a qué partidas corresponde un período escribiendo sus
códigos entre corchetes al final de la etiqueta: `"Dia 1 [LB-01-EXC, LB-02-TUB]"`. La regla R7 lee
esos códigos y, si no los hay, cae a la comparación textual de descripciones.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

PREFIJO_DIRECTIVA = "_"

CLAVE_BALANCE = "_balance"
CLAVE_TOLERANCIA = "_tolerancia"
CLAVE_UNIDAD_ORIGINAL = "_unidad_original"

SEPARADOR_CODIGOS = ", "

_CORCHETES = re.compile(r"\[([^\[\]]*)\]")


def es_directiva(clave: str) -> bool:
    """True si `clave` es una instrucción para el núcleo y no una especificación técnica."""
    return clave.startswith(PREFIJO_DIRECTIVA)


def etiqueta_con_codigos(etiqueta: str, codigos: Sequence[str]) -> str:
    """`("Dia 1", ("LB-01-EXC", "LB-02-TUB"))` -> `"Dia 1 [LB-01-EXC, LB-02-TUB]"`.

    Sin códigos devuelve la etiqueta tal cual: un período que no declara partidas es legítimo, R7
    solo lo advierte.
    """
    limpios = [codigo.strip() for codigo in codigos if codigo.strip()]
    if not limpios:
        return etiqueta.strip()
    return f"{etiqueta.strip()} [{SEPARADOR_CODIGOS.join(limpios)}]"


def codigos_en_etiqueta(periodo: str) -> tuple[str, ...]:
    """Códigos de partida declarados entre corchetes en la etiqueta de un período.

    Inversa de `etiqueta_con_codigos`. Devuelve una tupla vacía si la etiqueta no los declara.
    """
    return tuple(
        codigo
        for grupo in _CORCHETES.findall(periodo)
        for codigo in (parte.strip() for parte in grupo.split(","))
        if codigo
    )
