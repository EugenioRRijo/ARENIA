"""Funciones puras de composición de un APU a mano (Sesión P2.1, UC-10 y UC-11).

La lógica de convertir las tres tablas de la futura pantalla (`ui/paginas/componer.py`, Sesión
P2.2) en un `ComposicionAPU` del contrato vive aquí, fuera de `render()`, porque hoy el repositorio
no tiene ninguna prueba de interfaz: lo único verificable es lo que se puede llamar sin Streamlit
(spec de diseño §4, `docs/superpowers/specs/2026-09-16-prototipo-composicion-apu-design.md`). Por
eso este módulo no importa `streamlit` ni `pandas`: `st.data_editor` devuelve un `DataFrame`, pero
convertirlo a las listas de diccionarios que aquí se reciben es trabajo de la página, no de esta
capa de dominio.

Las filas son diccionarios de texto (las claves que produce cada tabla de la pantalla), nunca
`Decimal` ni objetos del contrato: el usuario escribe texto y esta capa es la única que decide qué
significa "vacío" y qué mensaje de error señala la fila y el campo culpables.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation

from core.contracts.apu import (
    ComposicionAPU,
    LineaEquipo,
    LineaManoObra,
    LineaMaterial,
    ModalidadManoObra,
)
from core.contracts.dominio import Dominio
from core.contracts.item_computo import ItemComputo, OrigenTipo


class ComposicionInvalida(ValueError):  # noqa: N818
    """Una tabla de la pantalla no se puede convertir en un APU del contrato.

    El nombre no lleva el sufijo `Error` que pide la convención inglesa de N818: el proyecto
    escribe sus identificadores en español (CLAUDE.md §3), igual que `ExpresionInvalida`
    (`core/verification/expresiones.py`) y `PlanInvalido` (`core/budget/curva.py`).
    """


def decimal_desde_texto(texto: str, campo: str) -> Decimal:
    """`Decimal` desde el texto del formulario, con el campo culpable en el mensaje.

    Movido de `ui/paginas/escenarios.py` (antes `_decimal`, privado): un nombre privado importado
    desde otro módulo era una contradicción, y P2.2/P2.3 lo necesitan igual que UC-08.
    """
    try:
        valor = Decimal(texto.strip())
    except InvalidOperation as error:
        raise ComposicionInvalida(f"{campo}: {texto!r} no es un numero decimal valido") from error
    if not valor.is_finite():
        raise ComposicionInvalida(f"{campo}: {texto!r} no es un monto finito")
    return valor


def _texto(fila: Mapping[str, str], clave: str) -> str:
    """Extrae y normaliza una celda, incluida la frontera con el productor real de las filas.

    El tipo declarado de `fila` es `Mapping[str, str]`, pero `st.data_editor` con
    `num_rows="dynamic"` (docstring líneas 6-8) entrega `None` o NaN en las celdas de una fila
    recién añadida en blanco: `str(None)` es `"None"` y `str(float("nan"))` es `"nan"`, y ninguno
    de los dos es vacío para `str.strip()`. Esta es la frontera donde ambos se normalizan a
    cadena vacía, antes de que lleguen a `_fila_vacia` o a cualquier conversión.
    """
    valor = fila.get(clave)
    if valor is None:
        return ""
    texto = str(valor).strip()
    return "" if texto.lower() == "nan" else texto


def _fila_vacia(valores: Sequence[str]) -> bool:
    """Una fila dinámica sin ningún dato todavía no es un error: es una fila que el usuario no
    llenó. Se descarta antes de intentar convertir nada.
    """
    return all(not valor.strip() for valor in valores)


def _exigir_descripcion(tabla: str, indice: int, descripcion: str) -> None:
    """Una fila con algún dato pero sin descripción no es "vacía": es un error (spec §4, plan P2.2).

    Sin este control, `Catalogo._resolver_insumo` (core/catalog/repositorio.py) identifica los
    insumos por (tipo, descripcion, unidad): varias líneas sin nombre con la misma unidad y precio
    colapsarían calladamente en un solo insumo, y la regla R6 (`CriterioDepreciacion`) las
    confundiría con "el mismo insumo" entre APU distintos.
    """
    if not descripcion:
        raise ComposicionInvalida(f"{tabla}, fila {indice}: la descripcion no puede estar vacia")


def _modalidad_desde_texto(texto: str, descripcion: str) -> ModalidadManoObra:
    """Vacía es JORNAL (el caso por defecto del contrato); cualquier otra debe ser válida.

    `ModalidadManoObra(texto)` deja escapar un `ValueError` del `StrEnum` sin decir de qué fila
    viene; con tres tablas y filas dinámicas eso no basta para ubicar el error.
    """
    texto = texto.strip()
    if not texto:
        return ModalidadManoObra.JORNAL
    try:
        return ModalidadManoObra(texto)
    except ValueError as error:
        raise ComposicionInvalida(
            f"modalidad ({descripcion}): {texto!r} no es una modalidad de mano de obra valida"
        ) from error


def _material_desde_fila(fila: Mapping[str, str], indice: int) -> LineaMaterial | None:
    descripcion = _texto(fila, "descripcion")
    unidad = _texto(fila, "unidad")
    cantidad_texto = _texto(fila, "cantidad")
    precio_texto = _texto(fila, "precio")
    if _fila_vacia((descripcion, unidad, cantidad_texto, precio_texto)):
        return None
    _exigir_descripcion("materiales", indice, descripcion)

    cantidad = decimal_desde_texto(cantidad_texto, f"cantidad ({descripcion})")
    precio = decimal_desde_texto(precio_texto, f"precio ({descripcion})")
    try:
        return LineaMaterial(
            descripcion=descripcion, unidad=unidad, cantidad=cantidad, precio=precio
        )
    except ValueError as error:
        raise ComposicionInvalida(
            f"materiales, fila {indice} ({descripcion}): {error}"
        ) from error


def _equipo_desde_fila(fila: Mapping[str, str], indice: int) -> LineaEquipo | None:
    descripcion = _texto(fila, "descripcion")
    cantidad_texto = _texto(fila, "cantidad")
    precio_texto = _texto(fila, "precio")
    depreciacion_texto = _texto(fila, "depreciacion")
    if _fila_vacia((descripcion, cantidad_texto, precio_texto, depreciacion_texto)):
        return None
    _exigir_descripcion("equipos", indice, descripcion)

    cantidad = decimal_desde_texto(cantidad_texto, f"cantidad ({descripcion})")
    precio = decimal_desde_texto(precio_texto, f"precio ({descripcion})")
    depreciacion = decimal_desde_texto(depreciacion_texto, f"depreciacion ({descripcion})")
    try:
        return LineaEquipo(
            descripcion=descripcion, cantidad=cantidad, precio=precio, depreciacion=depreciacion
        )
    except ValueError as error:
        raise ComposicionInvalida(
            f"equipos, fila {indice} ({descripcion}): {error}"
        ) from error


def _mano_obra_desde_fila(fila: Mapping[str, str], indice: int) -> LineaManoObra | None:
    descripcion = _texto(fila, "descripcion")
    cantidad_texto = _texto(fila, "cantidad")
    sueldo_texto = _texto(fila, "sueldo")
    modalidad_texto = _texto(fila, "modalidad")
    if _fila_vacia((descripcion, cantidad_texto, sueldo_texto, modalidad_texto)):
        return None
    _exigir_descripcion("mano de obra", indice, descripcion)

    cantidad = decimal_desde_texto(cantidad_texto, f"cantidad ({descripcion})")
    sueldo = decimal_desde_texto(sueldo_texto, f"sueldo ({descripcion})")
    modalidad = _modalidad_desde_texto(modalidad_texto, descripcion)
    try:
        return LineaManoObra(
            descripcion=descripcion, cantidad=cantidad, sueldo=sueldo, modalidad=modalidad
        )
    except ValueError as error:
        raise ComposicionInvalida(
            f"mano de obra, fila {indice} ({descripcion}): {error}"
        ) from error


def composicion_desde_tablas(
    codigo: str,
    descripcion: str,
    unidad: str,
    rendimiento: str,
    filas_materiales: Sequence[Mapping[str, str]],
    filas_equipos: Sequence[Mapping[str, str]],
    filas_mano_obra: Sequence[Mapping[str, str]],
) -> ComposicionAPU:
    """Arma la `ComposicionAPU` que compone la pantalla a partir de sus tres tablas de texto.

    Claves esperadas por fila (una ausente se trata como cadena vacía):
    materiales `descripcion`, `unidad`, `cantidad`, `precio`; equipos `descripcion`, `cantidad`,
    `precio`, `depreciacion`; mano de obra `descripcion`, `cantidad`, `sueldo`, `modalidad`.
    """
    # El indice empieza en 1 y cuenta las filas tal como llegaron (antes de descartar las
    # vacias), para que el mensaje de error coincida con lo que la persona ve en pantalla.
    materiales = tuple(
        linea
        for indice, fila in enumerate(filas_materiales, start=1)
        if (linea := _material_desde_fila(fila, indice)) is not None
    )
    equipos = tuple(
        linea
        for indice, fila in enumerate(filas_equipos, start=1)
        if (linea := _equipo_desde_fila(fila, indice)) is not None
    )
    mano_obra = tuple(
        linea
        for indice, fila in enumerate(filas_mano_obra, start=1)
        if (linea := _mano_obra_desde_fila(fila, indice)) is not None
    )
    valor_rendimiento = decimal_desde_texto(rendimiento, "rendimiento")

    try:
        return ComposicionAPU(
            codigo_partida=codigo,
            descripcion=descripcion,
            unidad=unidad,
            rendimiento=valor_rendimiento,
            materiales=materiales,
            equipos=equipos,
            mano_obra=mano_obra,
        )
    except ValueError as error:
        # `rendimiento > 0` y `codigo_partida` no vacío ya los valida el contrato; aquí solo se
        # traduce la excepción, sin duplicar la invariante.
        raise ComposicionInvalida(str(error)) from error


def item_desde_cantidad(
    codigo: str,
    descripcion: str,
    unidad: str,
    cantidad: str,
    origen_id: str,
    dominio: Dominio,
) -> ItemComputo:
    """Un `ItemComputo` de origen MANUAL: la cantidad que el proyectista escribe a mano al
    componer el APU (no viene de IFC, regla ni CSV). `dominio` es el sexto parámetro porque
    `ItemComputo` lo exige sin valor por defecto (`core/contracts/item_computo.py`).
    """
    valor_cantidad = decimal_desde_texto(cantidad, "cantidad")
    try:
        return ItemComputo(
            codigo_partida=codigo,
            descripcion=descripcion,
            unidad=unidad,
            cantidad=valor_cantidad,
            origen_id=origen_id,
            origen_tipo=OrigenTipo.MANUAL,
            dominio=dominio,
        )
    except ValueError as error:
        # `origen_id` no vacío ya lo exige el contrato (toda cantidad debe ser trazable); aquí
        # solo se traduce la excepción.
        raise ComposicionInvalida(str(error)) from error
