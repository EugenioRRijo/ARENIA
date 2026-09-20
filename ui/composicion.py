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


def _fila_vacia(valores: Sequence[str]) -> bool:
    """Una fila dinámica sin ningún dato todavía no es un error: es una fila que el usuario no
    llenó. Se descarta antes de intentar convertir nada.
    """
    return all(not valor.strip() for valor in valores)


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


def _material_desde_fila(fila: Mapping[str, str]) -> LineaMaterial | None:
    descripcion = str(fila.get("descripcion", ""))
    unidad = str(fila.get("unidad", ""))
    cantidad_texto = str(fila.get("cantidad", ""))
    precio_texto = str(fila.get("precio", ""))
    if _fila_vacia((descripcion, unidad, cantidad_texto, precio_texto)):
        return None

    descripcion = descripcion.strip()
    cantidad = decimal_desde_texto(cantidad_texto, f"cantidad ({descripcion})")
    precio = decimal_desde_texto(precio_texto, f"precio ({descripcion})")
    try:
        return LineaMaterial(
            descripcion=descripcion, unidad=unidad, cantidad=cantidad, precio=precio
        )
    except ValueError as error:
        raise ComposicionInvalida(str(error)) from error


def _equipo_desde_fila(fila: Mapping[str, str]) -> LineaEquipo | None:
    descripcion = str(fila.get("descripcion", ""))
    cantidad_texto = str(fila.get("cantidad", ""))
    precio_texto = str(fila.get("precio", ""))
    depreciacion_texto = str(fila.get("depreciacion", ""))
    if _fila_vacia((descripcion, cantidad_texto, precio_texto, depreciacion_texto)):
        return None

    descripcion = descripcion.strip()
    cantidad = decimal_desde_texto(cantidad_texto, f"cantidad ({descripcion})")
    precio = decimal_desde_texto(precio_texto, f"precio ({descripcion})")
    depreciacion = decimal_desde_texto(depreciacion_texto, f"depreciacion ({descripcion})")
    try:
        return LineaEquipo(
            descripcion=descripcion, cantidad=cantidad, precio=precio, depreciacion=depreciacion
        )
    except ValueError as error:
        raise ComposicionInvalida(str(error)) from error


def _mano_obra_desde_fila(fila: Mapping[str, str]) -> LineaManoObra | None:
    descripcion = str(fila.get("descripcion", ""))
    cantidad_texto = str(fila.get("cantidad", ""))
    sueldo_texto = str(fila.get("sueldo", ""))
    modalidad_texto = str(fila.get("modalidad", ""))
    if _fila_vacia((descripcion, cantidad_texto, sueldo_texto, modalidad_texto)):
        return None

    descripcion = descripcion.strip()
    cantidad = decimal_desde_texto(cantidad_texto, f"cantidad ({descripcion})")
    sueldo = decimal_desde_texto(sueldo_texto, f"sueldo ({descripcion})")
    modalidad = _modalidad_desde_texto(modalidad_texto, descripcion)
    try:
        return LineaManoObra(
            descripcion=descripcion, cantidad=cantidad, sueldo=sueldo, modalidad=modalidad
        )
    except ValueError as error:
        raise ComposicionInvalida(str(error)) from error


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
    materiales = tuple(
        linea for fila in filas_materiales if (linea := _material_desde_fila(fila)) is not None
    )
    equipos = tuple(
        linea for fila in filas_equipos if (linea := _equipo_desde_fila(fila)) is not None
    )
    mano_obra = tuple(
        linea for fila in filas_mano_obra if (linea := _mano_obra_desde_fila(fila)) is not None
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
