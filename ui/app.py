"""Interfaz mínima de UC‑02: cargar una lista de precios y ver el presupuesto revalorado (I1).

Solo presentación. Toda la lógica vive en `core`: esta capa abre la sesión, llama a
`crear_lista_desde_archivo` y a `actualizar_precios`, muestra el comparativo y el informe de
auditoría —que se genera siempre, sin pedirlo (principio 7 de CLAUDE.md §2)— y ofrece el libro de
Excel. No calcula ni redondea nada por su cuenta: los dos decimales de la tabla son los de
`core.verification.informe.DECIMALES_PRESENTACION`, la única definición de presentación del
sistema.

La transacción se confirma aquí porque el núcleo la deja abierta a propósito: es esta pantalla la
que representa al usuario que acepta o descarta la versión nueva (UC‑02, flujos 3a y 7a).

Uso::

    uv sync --extra ui
    uv run streamlit run ui/app.py
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import streamlit as st
from pandas import DataFrame
from sqlalchemy.orm import Session

from core.budget import Comparativo, actualizar_precios, exportar_excel
from core.catalog import (
    Catalogo,
    abrir_sesion,
    crear_esquema,
    crear_lista_desde_archivo,
    crear_motor,
)
from core.verification.informe import DECIMALES_PRESENTACION
from core.verification.texto import formatear_decimal
from scripts.seed import NOMBRE_PROYECTO, sembrar

TITULO = "Actualizacion masiva de precios (UC-02)"
RUTA_BASE_POR_DEFECTO = "data/apu.db"
CODIGO_BASE_POR_DEFECTO = "001"
CODIGO_NUEVO_POR_DEFECTO = "002"
MONEDA_POR_DEFECTO = "USD"
TIPOS_ACEPTADOS = ["csv", "xlsx"]
CLAVE_RESULTADO = "resultado_uc02"
CERO = Decimal(0)

#: Columnas del comparativo que se presentan redondeadas; el resto va como texto tal cual.
COLUMNAS_NUMERICAS = (
    "cantidad",
    "pu_anterior",
    "pu_nuevo",
    "variacion_pct",
    "total_anterior",
    "total_nuevo",
    "incidencia_pct",
)


# `eq=False` por el mismo motivo que en `Comparativo`: lleva un `DataFrame` dentro.
@dataclass(frozen=True, slots=True, eq=False)
class Presentacion:
    """Lo que la pantalla necesita mostrar después de confirmar (o descartar) la actualización."""

    tabla: DataFrame
    resumen: str
    informe: str
    desconocidos: tuple[str, ...]
    libro: bytes
    nombre_libro: str


def main() -> None:
    """Pantalla única: parámetros en la barra lateral, archivo y resultados en el cuerpo."""
    st.set_page_config(page_title=TITULO, layout="wide")
    st.title(TITULO)
    st.caption(
        "Carga una lista de precios nueva (CSV o XLSX con las columnas tipo, insumo, unidad y "
        "precio) y el sistema revalora el presupuesto guardado, registra que cambio y audita la "
        "version nueva."
    )

    parametros = _barra_lateral()
    archivo = st.file_uploader("Lista de precios", type=TIPOS_ACEPTADOS)

    if st.button("Revalorar presupuesto", type="primary", disabled=archivo is None):
        with st.spinner("Revalorando..."):
            _ejecutar(parametros, archivo)

    _mostrar(st.session_state.get(CLAVE_RESULTADO))


# ---------------------------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------------------------


def _barra_lateral() -> dict[str, object]:
    """Los datos que necesita `actualizar_precios`, con la línea base como valor por defecto."""
    with st.sidebar:
        st.header("Base de datos")
        ruta = st.text_input("Archivo SQLite", value=RUTA_BASE_POR_DEFECTO)
        if st.button("Sembrar la linea base"):
            _sembrar(Path(ruta))

        st.header("Presupuesto")
        proyecto = st.text_input("Proyecto", value=NOMBRE_PROYECTO)
        codigo = st.text_input("Codigo del presupuesto base", value=CODIGO_BASE_POR_DEFECTO)
        codigo_nuevo = st.text_input("Codigo de la version nueva", value=CODIGO_NUEVO_POR_DEFECTO)

        st.header("Lista de precios")
        vigencia = st.date_input("Fecha de vigencia", value=date.today())
        moneda = st.text_input("Moneda", value=MONEDA_POR_DEFECTO)
        nombre = st.text_input("Nombre de la lista", value=f"Lista {vigencia:%d/%m/%Y}")

    return {
        "ruta": Path(ruta),
        "proyecto": proyecto,
        "codigo": codigo,
        "codigo_nuevo": codigo_nuevo,
        "vigencia": vigencia,
        "moneda": moneda,
        "nombre": nombre,
    }


def _sembrar(ruta: Path) -> None:
    """Crea el esquema y carga la línea base en la base indicada, si aún no está."""
    motor = crear_motor(f"sqlite:///{ruta.as_posix()}")
    try:
        crear_esquema(motor)
        with abrir_sesion(motor) as sesion:
            sembrar(sesion)
            partidas = len(Catalogo(sesion).partidas())
        st.sidebar.success(f"Base lista en {ruta} con {partidas} partidas.")
    finally:
        motor.dispose()


# ---------------------------------------------------------------------------------------------
# Caso de uso
# ---------------------------------------------------------------------------------------------


def _ejecutar(parametros: dict[str, object], archivo) -> None:
    """Corre UC‑02 completo y deja en la sesión de Streamlit lo que hay que mostrar."""
    motor = crear_motor(f"sqlite:///{parametros['ruta'].as_posix()}")
    try:
        crear_esquema(motor)
        with tempfile.TemporaryDirectory() as carpeta, abrir_sesion(motor) as sesion:
            ruta_archivo = Path(carpeta) / archivo.name
            ruta_archivo.write_bytes(archivo.getvalue())
            st.session_state[CLAVE_RESULTADO] = _actualizar(
                sesion, parametros, ruta_archivo, Path(carpeta)
            )
    except (LookupError, ValueError) as error:
        st.session_state[CLAVE_RESULTADO] = None
        st.error(str(error))
    finally:
        motor.dispose()


def _actualizar(
    sesion: Session, parametros: dict[str, object], archivo: Path, carpeta: Path
) -> Presentacion:
    """Crea la lista, revalora, confirma si algo cambió y arma la presentación."""
    resumen = crear_lista_desde_archivo(
        sesion,
        archivo,
        nombre=str(parametros["nombre"]),
        moneda=str(parametros["moneda"]),
        fecha_vigencia=parametros["vigencia"],
        origen=archivo.name,
    )
    nuevo, comparativo = actualizar_precios(
        sesion,
        str(parametros["proyecto"]),
        str(parametros["codigo"]),
        resumen.lista,
        str(parametros["codigo_nuevo"]),
    )
    libro = exportar_excel(
        nuevo.presupuesto, nuevo.informe, carpeta / f"presupuesto_{nuevo.presupuesto.codigo}.xlsx"
    )
    presentacion = Presentacion(
        tabla=_para_presentar(comparativo.tabla),
        resumen=_resumen(comparativo, nuevo.presupuesto.moneda),
        informe=nuevo.informe.a_markdown(),
        desconocidos=tuple(
            f"{precio.descripcion} ({precio.tipo.value})" for precio in resumen.desconocidos
        ),
        libro=libro.read_bytes(),
        nombre_libro=libro.name,
    )

    if comparativo.variacion == CERO:
        st.warning("Ningun precio cambio: no se guardo una version nueva (UC-02, flujo 3a).")
    else:
        sesion.commit()
    return presentacion


# ---------------------------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------------------------


def _para_presentar(tabla: DataFrame) -> DataFrame:
    """El comparativo con sus `Decimal` a dos decimales, ya como texto: la tabla es de lectura."""
    presentada = tabla.copy()
    for columna in COLUMNAS_NUMERICAS:
        presentada[columna] = [
            formatear_decimal(valor, DECIMALES_PRESENTACION) for valor in tabla[columna]
        ]
    return presentada


def _resumen(comparativo: Comparativo, moneda: str) -> str:
    anterior = formatear_decimal(comparativo.total_anterior, DECIMALES_PRESENTACION)
    nuevo = formatear_decimal(comparativo.total_nuevo, DECIMALES_PRESENTACION)
    variacion = formatear_decimal(comparativo.variacion, DECIMALES_PRESENTACION)
    porcentaje = formatear_decimal(comparativo.variacion_pct, DECIMALES_PRESENTACION)
    return f"{anterior} -> {nuevo} {moneda}  ({variacion} {moneda}, {porcentaje} %)"


def _mostrar(presentacion: Presentacion | None) -> None:
    if presentacion is None:
        return

    st.subheader("Comparativo por partida")
    st.metric("Total del presupuesto", presentacion.resumen)
    st.dataframe(presentacion.tabla, hide_index=True)

    if presentacion.desconocidos:
        st.warning(
            "Insumos del archivo que no estan en el catalogo (no se crearon ni intervienen en el "
            "recalculo): " + ", ".join(presentacion.desconocidos)
        )

    st.download_button(
        "Exportar a Excel",
        data=presentacion.libro,
        file_name=presentacion.nombre_libro,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.subheader("Informe de auditoria de la version nueva")
    st.markdown(presentacion.informe)


if __name__ == "__main__":
    main()
