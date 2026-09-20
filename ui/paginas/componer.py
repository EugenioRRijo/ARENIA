"""Pagina de UC-10 (componer) y UC-11 (editar) una partida a mano (`docs/ERS.md`).

Es la novena pantalla y la que da sentido al prototipo: hasta esta sesion, solo los scripts de
siembra llamaban a `Catalogo.cargar_composicion`
(`docs/superpowers/specs/2026-09-16-prototipo-composicion-apu-design.md` §1) y ninguna de las ocho
paginas existentes permitia armar una partida desde cero.

No contiene logica de dominio: toda vive en `ui/composicion.py`, que es lo unico verificable sin
Streamlit porque el repositorio todavia no tiene pruebas de interfaz (spec §4). Esta pagina solo
pinta: abre la sesion, arma las tres tablas con `st.data_editor`, llama a `composicion_desde_tablas`
y a `calcular_apu` para el desglose en vivo, y decide entre `Catalogo.cargar_composicion` (la
partida no existe, UC-10) y `Catalogo.reemplazar_composicion` (ya existe, UC-11).

El vocabulario de los dos campos de "rendimiento" no se comparte a proposito (spec §3.2): la nota de
campo que origino este trabajo llama "rendimiento" tanto al consumo de material por unidad de obra
como a la produccion diaria de la cuadrilla, y ahi es exactamente donde se produce el error. Por eso
la columna de materiales dice "Consumo por unidad" y el campo de la partida dice "Rendimiento -
unidades por dia": nunca la misma palabra para las dos cosas.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st
from pandas import DataFrame
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.catalog import (
    Catalogo,
    DispersionRendimiento,
    PropuestaRendimiento,
    abrir_sesion,
    advertencia_rendimiento,
    crear_esquema,
    crear_motor,
    dispersion_rendimientos,
    proponer_rendimiento,
)
from core.contracts import ComposicionAPU, Dominio, ModalidadManoObra, ParametrosCosto
from core.costing import calcular_apu
from ui.composicion import ComposicionInvalida, composicion_desde_tablas, decimal_desde_texto

TITULO = "Componer partida (UC-10 / UC-11)"
RUTA_BASE_POR_DEFECTO = "data/apu.db"
RENDIMIENTO_ETIQUETA = "Rendimiento — unidades por día"
CONSUMO_ETIQUETA = "Consumo por unidad"

#: Columnas de cada tabla de insumos: la clave interna que espera `composicion_desde_tablas`
#: (contrato), no el rotulo que se ve en pantalla (presentacion).
COLUMNAS_MATERIALES = ("descripcion", "unidad", "cantidad", "precio")
COLUMNAS_EQUIPOS = ("descripcion", "cantidad", "precio", "depreciacion")
COLUMNAS_MANO_OBRA = ("descripcion", "cantidad", "sueldo", "modalidad")


def render() -> None:
    """Cabecera de la partida, tres tablas de insumos, desglose en vivo y boton de guardado."""
    st.title(TITULO)
    st.caption(
        "Componga una partida a mano: declare su cabecera y sus tres tablas de insumos, vea el "
        "precio unitario desglosarse en vivo (sin necesidad de guardar) y guarde la composicion. "
        "Si la partida ya existe, guardar reemplaza su composicion vigente (UC-11); si no existe, "
        "la crea (UC-10)."
    )

    ruta = Path(st.sidebar.text_input("Archivo SQLite", value=RUTA_BASE_POR_DEFECTO))
    motor = crear_motor(f"sqlite:///{ruta.as_posix()}")
    try:
        crear_esquema(motor)
        with abrir_sesion(motor) as sesion:
            _pagina(sesion)
    except (LookupError, ValueError, ArithmeticError, SQLAlchemyError) as error:
        # Mismo criterio que las demas paginas que escriben en la base
        # (`ui/paginas/actualizacion.py`, `ui/paginas/escenarios.py`): un dato invalido o una base
        # inaccesible es un mensaje, no una traza cruda. `ComposicionInvalida` es un `ValueError`
        # y queda cubierta aqui.
        st.error(str(error))
    finally:
        motor.dispose()


# ---------------------------------------------------------------------------------------------
# Orquestacion de la pagina
# ---------------------------------------------------------------------------------------------


def _pagina(sesion: Session) -> None:
    codigo, descripcion, unidad, dominio, fecha = _cabecera()
    catalogo = Catalogo(sesion)

    rendimiento_texto = _rendimiento(sesion, codigo)
    condiciones = st.text_area(
        "Condiciones del rendimiento",
        help="Obligatorio (RF-33): el sistema no persiste una composicion cuyo rendimiento no se "
        "declare junto con las condiciones en que se obtuvo.",
    )
    condiciones_vacias = not condiciones.strip()
    if condiciones_vacias:
        st.caption(
            "Las condiciones del rendimiento son obligatorias para guardar (RF-33): el boton de "
            "guardar permanece deshabilitado hasta que se declaren."
        )

    filas_materiales, filas_equipos, filas_mano_obra = _tablas_de_insumos()

    composicion = _desglose_en_vivo(
        codigo,
        descripcion,
        unidad,
        rendimiento_texto,
        filas_materiales,
        filas_equipos,
        filas_mano_obra,
    )

    st.subheader("Guardar")
    if st.button("Guardar composicion", type="primary", disabled=condiciones_vacias):
        if composicion is None:
            st.warning(
                "La composicion todavia no es valida (revise el aviso del desglose en vivo, "
                "arriba): corrija las tablas antes de guardar."
            )
        else:
            _guardar(sesion, catalogo, composicion, dominio, fecha, condiciones)


def _cabecera() -> tuple[str, str, str, Dominio, date]:
    """Codigo, descripcion, unidad, dominio y fecha de la partida (UC-10, paso 1)."""
    st.subheader("Cabecera de la partida")
    columnas = st.columns(3)
    codigo = columnas[0].text_input("Codigo")
    descripcion = columnas[1].text_input("Descripcion")
    unidad = columnas[2].text_input("Unidad")

    columnas_dominio = st.columns(2)
    dominio = columnas_dominio[0].selectbox(
        "Dominio", list(Dominio), format_func=lambda d: d.value
    )
    fecha = columnas_dominio[1].date_input("Fecha", value=date.today())
    return codigo, descripcion, unidad, dominio, fecha


def _rendimiento(sesion: Session, codigo: str) -> str:
    """El campo de rendimiento de la partida: precargado, con su advertencia si corresponde.

    `proponer_rendimiento` y `dispersion_rendimientos` exigen que la partida ya exista en el
    catalogo (`Catalogo.partida`, `KeyError` si no); una partida nueva (UC-10) no tiene historial
    todavia, asi que ese `KeyError` se trata igual que "sin historial": el campo queda vacio y el
    aviso lo dice, sin ser un error.
    """
    propuesta: PropuestaRendimiento | None = None
    dispersion: DispersionRendimiento | None = None
    if codigo.strip():
        try:
            propuesta = proponer_rendimiento(sesion, codigo)
            dispersion = dispersion_rendimientos(sesion, codigo)
        except KeyError:
            propuesta = None
            dispersion = None

    valor_precargado = str(propuesta.rendimiento.valor) if propuesta is not None else ""
    rendimiento_texto = st.text_input(RENDIMIENTO_ETIQUETA, value=valor_precargado)

    if propuesta is None:
        st.caption(
            "Todavia no hay historial de rendimientos registrado para esta partida: es el "
            "comportamiento correcto, no un error. Declare el rendimiento con sus condiciones."
        )

    _advertir_si_corresponde(dispersion, rendimiento_texto)
    return rendimiento_texto


def _advertir_si_corresponde(
    dispersion: DispersionRendimiento | None, rendimiento_texto: str
) -> None:
    """RF-27: avisa si el valor tecleado se aparta de lo observado, sin bloquear nunca."""
    if not rendimiento_texto.strip():
        return
    try:
        valor = decimal_desde_texto(rendimiento_texto, "rendimiento")
    except ComposicionInvalida:
        return  # el valor todavia no es un decimal valido: nada que advertir aun
    advertencia = advertencia_rendimiento(dispersion, valor)
    if advertencia:
        st.warning(advertencia)


def _tablas_de_insumos() -> tuple[list[dict], list[dict], list[dict]]:
    """Las tres tablas dinamicas de insumos (UC-10, pasos 2 a 4), como listas de diccionarios."""
    st.subheader("Materiales")
    materiales = st.data_editor(
        DataFrame(columns=COLUMNAS_MATERIALES).astype(str),
        num_rows="dynamic",
        hide_index=True,
        column_config={"cantidad": st.column_config.TextColumn(CONSUMO_ETIQUETA)},
        key="componer_materiales",
    )

    st.subheader("Equipos")
    equipos = st.data_editor(
        DataFrame(columns=COLUMNAS_EQUIPOS).astype(str),
        num_rows="dynamic",
        hide_index=True,
        key="componer_equipos",
    )

    st.subheader("Mano de obra")
    mano_obra = st.data_editor(
        DataFrame(columns=COLUMNAS_MANO_OBRA).astype(str),
        num_rows="dynamic",
        hide_index=True,
        column_config={
            # Sin `default`: una fila nueva debe quedar en blanco en las cuatro columnas (igual
            # que materiales y equipos) para que `_fila_vacia` (`ui/composicion.py`) la descarte
            # sin error mientras el proyectista no haya escrito nada. Con un valor por defecto
            # aqui, la celda de modalidad dejaria de estar en blanco y esa fila se trataria como
            # "con datos", disparando "la descripcion no puede estar vacia" al solo agregar la
            # fila. El contrato ya asume JORNAL cuando el texto viene vacio.
            "modalidad": st.column_config.SelectboxColumn(
                "modalidad",
                options=[modalidad.value for modalidad in ModalidadManoObra],
            )
        },
        key="componer_mano_obra",
    )

    return (
        materiales.to_dict("records"),
        equipos.to_dict("records"),
        mano_obra.to_dict("records"),
    )


def _desglose_en_vivo(
    codigo: str,
    descripcion: str,
    unidad: str,
    rendimiento_texto: str,
    filas_materiales: list[dict],
    filas_equipos: list[dict],
    filas_mano_obra: list[dict],
) -> ComposicionAPU | None:
    """El `ResultadoAPU` en vivo (UC-10, paso 6): nunca hace falta guardar para verlo.

    Una tabla a medio llenar es el estado normal mientras se teclea, no un fallo: por eso
    `ComposicionInvalida` se muestra con `st.info`, no con `st.error`, y no se pinta nada mas.
    """
    st.subheader("Desglose en vivo")
    try:
        composicion = composicion_desde_tablas(
            codigo,
            descripcion,
            unidad,
            rendimiento_texto,
            filas_materiales,
            filas_equipos,
            filas_mano_obra,
        )
    except ComposicionInvalida as error:
        st.info(str(error))
        return None

    resultado = calcular_apu(composicion, ParametrosCosto())
    columnas = st.columns(6)
    columnas[0].metric("Materiales", str(resultado.materiales))
    columnas[1].metric("Equipos", str(resultado.equipos))
    columnas[2].metric("Mano de obra", str(resultado.mano_obra))
    columnas[3].metric("Costo directo", str(resultado.costo_directo))
    columnas[4].metric("Con administracion", str(resultado.con_administracion))
    columnas[5].metric("Precio unitario", str(resultado.precio_unitario))
    return composicion


def _guardar(
    sesion: Session,
    catalogo: Catalogo,
    composicion: ComposicionAPU,
    dominio: Dominio,
    fecha: date,
    condiciones: str,
) -> None:
    """Persiste la composicion (UC-10 si la partida no existe, UC-11 si ya existe) y confirma."""
    lista = catalogo.lista_vigente(fecha)
    try:
        catalogo.partida(composicion.codigo_partida)
    except KeyError:
        catalogo.cargar_composicion(composicion, lista, dominio, fecha, condiciones)
    else:
        catalogo.reemplazar_composicion(composicion, lista, dominio, fecha, condiciones)
    sesion.commit()

    resultado = calcular_apu(composicion, ParametrosCosto())
    st.success(
        f"Composicion guardada para la partida {composicion.codigo_partida}: precio unitario "
        f"{resultado.precio_unitario}."
    )
