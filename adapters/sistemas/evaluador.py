"""Evaluador aritmético mínimo para la regla de puntos de función (Sesión I5).

La única regla que declara este dominio (`REGLA_PUNTOS_FUNCION` en `adapters/sistemas/adaptador.py`)
solo necesita sumas y multiplicaciones: los pesos medios IFPUG por la cantidad de transacciones o
archivos de cada tipo. Por eso este evaluador es un subconjunto deliberadamente más pequeño que
`adapters/civil/evaluador.py` (que también acepta resta, división, potencia y negación unaria para
sus reglas geométricas): aquí basta con `ast.Add`, `ast.Mult`, nombres de parámetro y constantes
numéricas. No usa `eval()`.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from decimal import Decimal

_OPERADORES_PERMITIDOS = (ast.Add, ast.Mult)


def evaluar_regla(expresion: str, parametros: Mapping[str, Decimal]) -> Decimal:
    """Evalúa `expresion` (solo sumas y multiplicaciones) con `parametros` y devuelve un `Decimal`.

    Lanza `ValueError` si la expresión contiene un nodo no permitido (por ejemplo una llamada, una
    resta o un acceso a atributo) y `KeyError` si referencia un nombre que no está en `parametros`.
    """
    arbol = ast.parse(expresion, mode="eval")
    return _evaluar_nodo(arbol.body, parametros)


def _evaluar_nodo(nodo: ast.AST, parametros: Mapping[str, Decimal]) -> Decimal:
    if isinstance(nodo, ast.BinOp):
        return _evaluar_binop(nodo, parametros)
    if isinstance(nodo, ast.Name):
        return _evaluar_nombre(nodo, parametros)
    if isinstance(nodo, ast.Constant):
        return _evaluar_constante(nodo)
    raise ValueError(f"nodo no permitido en una regla de puntos de funcion: {type(nodo).__name__}")


def _evaluar_binop(nodo: ast.BinOp, parametros: Mapping[str, Decimal]) -> Decimal:
    if not isinstance(nodo.op, _OPERADORES_PERMITIDOS):
        nombre_operador = type(nodo.op).__name__
        mensaje = f"operador no permitido en la regla de puntos de funcion: {nombre_operador}"
        raise ValueError(mensaje)
    izquierda = _evaluar_nodo(nodo.left, parametros)
    derecha = _evaluar_nodo(nodo.right, parametros)
    return izquierda + derecha if isinstance(nodo.op, ast.Add) else izquierda * derecha


def _evaluar_nombre(nodo: ast.Name, parametros: Mapping[str, Decimal]) -> Decimal:
    if nodo.id not in parametros:
        raise KeyError(f"parametro no definido para la regla: {nodo.id!r}")
    return parametros[nodo.id]


def _evaluar_constante(nodo: ast.Constant) -> Decimal:
    valor = nodo.value
    if isinstance(valor, bool) or not isinstance(valor, int | float):
        raise ValueError(f"constante no numerica en una regla de puntos de funcion: {valor!r}")
    return Decimal(str(valor))
