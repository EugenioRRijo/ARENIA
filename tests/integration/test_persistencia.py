"""Persistencia y catálogo (Sesión I0.4).

Criterio de cierre: los cinco APU de la línea base se reconstruyen desde SQLite **idénticos** al
fixture `tests/fixtures/apu_linea_base.py`, que es la única copia de esos datos (CLAUDE.md §2).
Las comparaciones son por igualdad de dataclass del contrato; no interviene el motor de costos.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from core import contracts, models
from core.catalog import Catalogo, CatalogoIncompleto, abrir_sesion, crear_motor
from scripts.seed import main, sembrar
from tests.fixtures import apu_linea_base as linea_base

CODIGOS = [apu.codigo_partida for apu in linea_base.APUS_LINEA_BASE]
TABLAS_SEMBRADAS = (
    models.Proyecto,
    models.ListaPrecios,
    models.Partida,
    models.Insumo,
    models.PrecioInsumo,
    models.ComposicionAPU,
    models.Rendimiento,
)


def _contar(sesion, entidad) -> int:
    return sesion.scalar(select(func.count()).select_from(entidad))


def test_seed_carga_cinco_partidas_y_una_lista(sesion):
    assert _contar(sesion, models.Proyecto) == 1
    assert _contar(sesion, models.Partida) == len(linea_base.APUS_LINEA_BASE)
    assert _contar(sesion, models.ListaPrecios) == 1
    # Dos por partida: el estimado sin condiciones de cargar_composicion y el de la siembra con
    # las condiciones del caso didactico (CONDICIONES_LINEA_BASE, scripts/seed.py).
    assert _contar(sesion, models.Rendimiento) == 2 * len(linea_base.APUS_LINEA_BASE)

    lista = sesion.scalars(select(models.ListaPrecios)).one()
    assert lista.moneda == linea_base.MONEDA
    assert lista.fecha_vigencia == linea_base.FECHA_LINEA_BASE

    catalogo = Catalogo(sesion)
    assert [partida.codigo for partida in catalogo.partidas()] == sorted(CODIGOS)
    assert catalogo.partida("LB-01-EXC").dominio == contracts.Dominio.CIVIL
    with pytest.raises(KeyError):
        catalogo.partida("NO-EXISTE")


@pytest.mark.parametrize("apu", linea_base.APUS_LINEA_BASE, ids=CODIGOS)
def test_composicion_reconstruye_cada_apu_identico(sesion, apu):
    assert Catalogo(sesion).composicion(apu.codigo_partida) == apu


def test_precios_se_reconstruyen_a_fecha(sesion):
    catalogo = Catalogo(sesion)
    base = catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE)

    nueva = models.ListaPrecios(
        nombre="Junio 2026",
        moneda=linea_base.MONEDA,
        fecha_vigencia=date(2026, 6, 1),
        origen="prueba",
    )
    sesion.add(nueva)
    sesion.flush()
    for precio in base.precios:
        subido = precio.insumo.descripcion == "Cemento Portland"
        sesion.add(
            models.PrecioInsumo(
                lista_id=nueva.id,
                insumo_id=precio.insumo_id,
                precio=Decimal("18") if subido else precio.precio,
            )
        )
    sesion.flush()

    def cemento(fecha: date) -> Decimal:
        composicion = catalogo.composicion("LB-04-CON", fecha=fecha)
        return next(
            linea.precio
            for linea in composicion.materiales
            if linea.descripcion == "Cemento Portland"
        )

    assert catalogo.lista_vigente(date(2026, 5, 1)).id == base.id
    assert catalogo.lista_vigente(date(2026, 6, 15)).id == nueva.id
    assert cemento(date(2026, 5, 1)) == Decimal("15")
    assert cemento(date(2026, 6, 15)) == Decimal("18")


def test_un_material_sin_unidad_es_un_catalogo_incompleto(sesion):
    """La frontera modelo → contrato debe nombrar el insumo que falta, como sus ramas vecinas.

    `insumo.unidad or ""` mandaba la cadena vacía a `normalizar_unidad`, que lanza el `ValueError`
    del contrato: un error sin código ni descripción, que no dice cuál de los insumos del catálogo
    hay que completar (revisión final, ítem 7).
    """
    codigo_partida = linea_base.APU_CONCRETO.codigo_partida
    linea = sesion.scalars(
        select(models.ComposicionAPU)
        .join(models.Partida, models.Partida.id == models.ComposicionAPU.partida_id)
        .join(models.Insumo, models.Insumo.id == models.ComposicionAPU.insumo_id)
        .where(
            models.Partida.codigo == codigo_partida,
            models.Insumo.tipo == models.TipoInsumo.MATERIAL.value,
        )
        .order_by(models.ComposicionAPU.orden)
    ).first()
    linea.insumo.unidad = None
    sesion.flush()

    with pytest.raises(CatalogoIncompleto) as error:
        Catalogo(sesion).composicion(codigo_partida)

    assert linea.insumo.codigo in str(error.value)
    assert linea.insumo.descripcion in str(error.value)


def test_rendimiento_medido_exige_ejecucion(sesion):
    catalogo = Catalogo(sesion)
    partida = catalogo.partida("LB-01-EXC")

    sesion.add(
        models.Rendimiento(
            partida_id=partida.id,
            valor=Decimal("95"),
            tipo=contracts.TipoRendimiento.MEDIDO.value,
            fecha=date(2026, 7, 1),
            condiciones="sin ejecución declarada",
            ejecucion_id=None,
        )
    )
    with pytest.raises(IntegrityError):
        sesion.flush()
    sesion.rollback()

    sesion.add(
        models.Ejecucion(
            referencia="EJ-001",
            fecha_inicio=date(2026, 7, 1),
            descripcion="Drenaje de la clínica, tramo ejecutado",
        )
    )
    sesion.flush()
    medido = Catalogo(sesion).registrar_rendimiento(
        contracts.Rendimiento(
            codigo_partida="LB-01-EXC",
            valor=Decimal("95"),
            tipo=contracts.TipoRendimiento.MEDIDO,
            fecha=date(2026, 7, 1),
            condiciones="suelo blando",
            referencia_ejecucion="EJ-001",
        )
    )
    sesion.flush()
    assert medido.ejecucion.referencia == "EJ-001"
    assert medido.tipo == contracts.TipoRendimiento.MEDIDO.value

    rendimientos = Catalogo(sesion).rendimientos("LB-01-EXC")
    # Dos estimados de la siembra (sin condiciones el de cargar_composicion, con condiciones el
    # del caso didactico) mas el medido que acaba de registrar esta prueba.
    assert [rendimiento.tipo for rendimiento in rendimientos] == [
        contracts.TipoRendimiento.ESTIMADO,
        contracts.TipoRendimiento.ESTIMADO,
        contracts.TipoRendimiento.MEDIDO,
    ]
    assert rendimientos[-1].referencia_ejecucion == "EJ-001"


def test_el_vehiculo_es_un_solo_insumo_con_cinco_lineas(sesion):
    """El precio del vehículo es 50,00 en los cinco APU: un solo insumo, cinco líneas.

    Lo que varía es la depreciación (1,00 en cuatro APU y 0,03 en tubería: hallazgo 7), y eso es
    atributo de la línea, no del insumo. Es la contraparte del hallazgo de datos de §6 del modelo.
    """
    insumos = sesion.scalars(
        select(models.Insumo).where(models.Insumo.descripcion == "Vehículo de transporte")
    ).all()
    assert len(insumos) == 1

    lineas = insumos[0].lineas
    assert len(lineas) == len(linea_base.APUS_LINEA_BASE)
    assert {linea.depreciacion for linea in lineas} == {Decimal("1.00"), Decimal("0.03")}


def test_insumos_homonimos_con_precio_distinto_se_cargan_como_variantes(sesion):
    """Hallazgo de datos: cuatro insumos de la línea base cuestan dos cosas distintas el mismo día.

    El esquema no admite dos precios por (lista, insumo), así que la carga crea una variante con la
    misma descripción y un código con sufijo. Candidata a regla R8 (docs/modelo_datos.md §6).
    """
    duplicados = sesion.execute(
        select(models.Insumo.descripcion, func.count(models.Insumo.id))
        .group_by(models.Insumo.tipo, models.Insumo.descripcion)
        .having(func.count(models.Insumo.id) > 1)
    ).all()

    assert {descripcion for descripcion, _ in duplicados} == {
        "Agua",
        "Pala",
        "Cinta métrica",
        "Nivel de mano",
    }
    assert all(cuantos == 2 for _, cuantos in duplicados)

    lista = Catalogo(sesion).lista_vigente()
    for descripcion, _ in duplicados:
        variantes = sesion.scalars(
            select(models.Insumo)
            .where(models.Insumo.descripcion == descripcion)
            .order_by(models.Insumo.id)
        ).all()
        precios = {
            sesion.scalar(
                select(models.PrecioInsumo.precio).where(
                    models.PrecioInsumo.lista_id == lista.id,
                    models.PrecioInsumo.insumo_id == insumo.id,
                )
            )
            for insumo in variantes
        }
        assert len(precios) == 2, f"{descripcion} debería tener dos precios distintos"
        assert variantes[1].codigo.startswith(f"{variantes[0].codigo}-")


def test_sembrar_es_idempotente(sesion):
    antes = {entidad.__name__: _contar(sesion, entidad) for entidad in TABLAS_SEMBRADAS}
    sembrar(sesion)
    despues = {entidad.__name__: _contar(sesion, entidad) for entidad in TABLAS_SEMBRADAS}

    assert antes == despues
    assert Catalogo(sesion).composicion("LB-03-ENC") == linea_base.APU_ENCOFRADO


def test_cargar_composicion_dos_veces_lanza_valueerror(sesion):
    """Recargar una partida ya compuesta duplicaría sus líneas: el catálogo lo rechaza.

    `cargar_composicion` no es reentrante y no debe fingir que lo es: reemplazar en silencio
    dejaría un APU con las líneas repetidas y un segundo rendimiento estimado de la misma fecha.
    """
    catalogo = Catalogo(sesion)
    lista = catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE)
    lineas_antes = _contar(sesion, models.ComposicionAPU)
    rendimientos_antes = _contar(sesion, models.Rendimiento)

    with pytest.raises(ValueError, match="LB-05-REL"):
        catalogo.cargar_composicion(
            linea_base.APU_RELLENO,
            lista,
            contracts.Dominio.CIVIL,
            linea_base.FECHA_LINEA_BASE,
        )

    assert _contar(sesion, models.ComposicionAPU) == lineas_antes
    assert _contar(sesion, models.Rendimiento) == rendimientos_antes
    assert Catalogo(sesion).composicion("LB-05-REL") == linea_base.APU_RELLENO


def test_reemplazar_composicion_permite_corregir_una_partida(sesion):
    catalogo = Catalogo(sesion)
    lista = catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE)
    corregido = replace(
        linea_base.APU_RELLENO,
        rendimiento=linea_base.APU_RELLENO.rendimiento + Decimal("1"),
    )

    resumen = catalogo.reemplazar_composicion(
        corregido, lista, contracts.Dominio.CIVIL, linea_base.FECHA_LINEA_BASE
    )

    assert resumen.partida.codigo == "LB-05-REL"
    assert Catalogo(sesion).composicion("LB-05-REL") == corregido


def test_reemplazar_conserva_el_rendimiento_anterior_en_el_historico(sesion):
    catalogo = Catalogo(sesion)
    lista = catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE)
    original = linea_base.APU_RELLENO.rendimiento
    corregido = replace(linea_base.APU_RELLENO, rendimiento=original + Decimal("1"))

    catalogo.reemplazar_composicion(
        corregido, lista, contracts.Dominio.CIVIL, linea_base.FECHA_LINEA_BASE
    )

    valores = [rendimiento.valor for rendimiento in catalogo.rendimientos("LB-05-REL")]
    assert original in valores
    assert corregido.rendimiento in valores


def test_reemplazar_una_partida_inexistente_lanza_lookuperror(sesion):
    catalogo = Catalogo(sesion)
    lista = catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE)
    inventada = replace(linea_base.APU_RELLENO, codigo_partida="LB-99-NADA")

    with pytest.raises(LookupError, match="LB-99-NADA"):
        catalogo.reemplazar_composicion(
            inventada, lista, contracts.Dominio.CIVIL, linea_base.FECHA_LINEA_BASE
        )


def test_script_seed_crea_la_base(tmp_path):
    ruta = tmp_path / "apu.db"
    assert main(["--db", str(ruta)]) == 0
    assert ruta.exists()

    motor = crear_motor(f"sqlite:///{ruta.as_posix()}")
    try:
        with abrir_sesion(motor) as sesion:
            catalogo = Catalogo(sesion)
            assert _contar(sesion, models.Partida) == len(linea_base.APUS_LINEA_BASE)
            composiciones = catalogo.composiciones(CODIGOS)
            assert composiciones == {apu.codigo_partida: apu for apu in linea_base.APUS_LINEA_BASE}
    finally:
        motor.dispose()


def test_la_siembra_deja_rendimientos_estimados_con_condiciones(sesion):
    """Sin condiciones declaradas, un rendimiento estimado no tiene procedencia que auditar.

    La pagina de composicion (fase P2) exige declararlas; la siembra de la linea base tiene que
    dar el ejemplo, y ademas es lo que permite que proponer_rendimiento sugiera algo.
    """
    catalogo = Catalogo(sesion)

    for codigo in CODIGOS:
        registrados = catalogo.rendimientos(codigo)
        assert registrados, codigo
        assert any(rendimiento.condiciones for rendimiento in registrados), codigo
