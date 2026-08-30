"""El presupuesto de la línea base, de extremo a extremo y con base de datos (Sesión I0.5).

Cierra el flujo completo: SQLite sembrada → `Catalogo.composiciones` → `elaborar` → 1 586,61 USD con
la curva al 100 % y su informe → `guardar_presupuesto` → `cargar_presupuesto` devuelve el **mismo**
`Presupuesto`.

La ida y vuelta se comprueba por igualdad de los contratos, no campo a campo: si un `Decimal` pierde
un dígito al pasar por JSON o por SQLite, la igualdad falla. Es la comprobación que exige
`docs/modelo_datos.md` §4.3 (los `Decimal` dentro de JSON se serializan como texto) y §7.1.
"""

from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal

import pytest

from core import models
from core.budget import (
    cargar_presupuesto,
    elaborar,
    generar_presupuesto,
    guardar_presupuesto,
    plan_secuencial,
)
from core.catalog import Catalogo
from core.contracts import ParametrosCosto
from scripts.seed import NOMBRE_PROYECTO, sembrar
from tests.fixtures import apu_linea_base as linea_base
from tests.fixtures.computo_auditado import items_auditados
from tests.fixtures.presupuesto_auditado import items_con_trazas

TOLERANCIA = Decimal("0.01")
CODIGOS = [apu.codigo_partida for apu in linea_base.APUS_LINEA_BASE]


def _elaborado(sesion, items):
    """Elabora el presupuesto del caso con las composiciones reconstruidas desde SQLite."""
    composiciones = Catalogo(sesion).composiciones(CODIGOS, fecha=linea_base.FECHA_LINEA_BASE)
    borrador = generar_presupuesto(
        items,
        composiciones,
        linea_base.PARAMETROS_LINEA_BASE,
        codigo=linea_base.CODIGO_PRESUPUESTO,
        fecha=linea_base.FECHA_LINEA_BASE,
        moneda=linea_base.MONEDA,
    )
    return elaborar(
        items,
        composiciones,
        linea_base.PARAMETROS_LINEA_BASE,
        codigo=linea_base.CODIGO_PRESUPUESTO,
        fecha=linea_base.FECHA_LINEA_BASE,
        moneda=linea_base.MONEDA,
        plan=plan_secuencial(borrador),
    )


def _guardado(sesion, items=None):
    """Elabora y persiste el presupuesto; devuelve (resultado, modelo, catalogo)."""
    resultado = _elaborado(sesion, items if items is not None else items_con_trazas())
    catalogo = Catalogo(sesion)
    modelo = guardar_presupuesto(
        sesion,
        resultado.presupuesto,
        resultado.informe,
        proyecto=sembrar(sesion),
        lista=catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE),
        parametros=linea_base.PARAMETROS_LINEA_BASE,
    )
    return resultado, modelo, catalogo


def test_elaborar_desde_el_catalogo_reproduce_1586_61(sesion):
    resultado = _elaborado(sesion, items_auditados())

    assert abs(resultado.presupuesto.total - linea_base.TOTAL_PRESUPUESTO_AUDITADO) <= TOLERANCIA
    assert resultado.presupuesto.total_curva == resultado.presupuesto.total
    assert resultado.informe.codigo_presupuesto == linea_base.CODIGO_PRESUPUESTO


def test_guardar_y_cargar_reproduce_el_presupuesto(sesion):
    resultado, modelo, catalogo = _guardado(sesion)

    cargado = cargar_presupuesto(sesion, NOMBRE_PROYECTO, linea_base.CODIGO_PRESUPUESTO, catalogo)

    assert modelo.codigo == linea_base.CODIGO_PRESUPUESTO
    assert cargado.total == resultado.presupuesto.total
    assert cargado.curva == resultado.presupuesto.curva
    assert cargado == resultado.presupuesto


def test_guardar_persiste_renglones_curva_y_hallazgos(sesion):
    resultado, modelo, _ = _guardado(sesion)

    assert len(modelo.partidas) == len(resultado.presupuesto.partidas)
    assert len(modelo.curva) == len(resultado.presupuesto.curva)
    assert len(modelo.hallazgos) == len(resultado.informe.hallazgos)
    assert [renglon.orden for renglon in modelo.partidas] == list(range(len(modelo.partidas)))
    assert modelo.fcas == linea_base.PARAMETROS_LINEA_BASE.fcas
    assert modelo.utilidad == linea_base.PARAMETROS_LINEA_BASE.utilidad

    hallazgo = modelo.hallazgos[0]
    assert isinstance(hallazgo.severidad, int)
    assert isinstance(json.loads(hallazgo.origen_ids), list)


def test_los_decimal_del_json_van_y_vuelven_como_texto(sesion):
    resultado, modelo, catalogo = _guardado(sesion)
    codigo = linea_base.APU_ENCOFRADO.codigo_partida

    persistido = next(item for item in modelo.items_computo if item.codigo_partida == codigo)
    crudo = json.loads(persistido.parametros)
    assert crudo, "el ítem de encofrado declara los parámetros de su regla"
    assert all(isinstance(valor, str) for valor in crudo.values()), crudo

    cargado = cargar_presupuesto(sesion, NOMBRE_PROYECTO, linea_base.CODIGO_PRESUPUESTO, catalogo)
    item = next(p.item for p in cargado.partidas if p.item.codigo_partida == codigo)
    original = next(
        p.item for p in resultado.presupuesto.partidas if p.item.codigo_partida == codigo
    )

    assert all(isinstance(valor, Decimal) for valor in item.parametros.values())
    assert dict(item.parametros) == dict(original.parametros)
    assert dict(item.especificaciones) == dict(original.especificaciones)
    assert item.regla == original.regla


def test_cargar_verifica_el_snapshot_contra_la_reconstruccion(sesion):
    _, modelo, catalogo = _guardado(sesion)
    renglon = modelo.partidas[0]
    renglon.precio_unitario = renglon.precio_unitario + Decimal("0.001")
    sesion.flush()

    with pytest.raises(ValueError, match=renglon.partida.codigo):
        cargar_presupuesto(sesion, NOMBRE_PROYECTO, linea_base.CODIGO_PRESUPUESTO, catalogo)


def test_cargar_reconstruye_los_parametros_de_costo(sesion):
    parametros = ParametrosCosto(
        fcas=Decimal("5.50"),
        bono_alimentacion=Decimal("2.00"),
        administracion=Decimal("0.12"),
        utilidad=Decimal("0.08"),
    )
    composiciones = Catalogo(sesion).composiciones(CODIGOS, fecha=linea_base.FECHA_LINEA_BASE)
    resultado = elaborar(
        items_auditados(),
        composiciones,
        parametros,
        codigo="002",
        fecha=linea_base.FECHA_LINEA_BASE,
        moneda=linea_base.MONEDA,
    )
    catalogo = Catalogo(sesion)
    guardar_presupuesto(
        sesion,
        resultado.presupuesto,
        resultado.informe,
        proyecto=sembrar(sesion),
        lista=catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE),
        parametros=parametros,
    )

    cargado = cargar_presupuesto(sesion, NOMBRE_PROYECTO, "002", catalogo)

    assert cargado == resultado.presupuesto
    assert cargado.curva == ()


def test_informe_de_otro_presupuesto_lanza_valueerror(sesion):
    resultado = _elaborado(sesion, items_auditados())
    catalogo = Catalogo(sesion)
    ajeno = replace(resultado.informe, codigo_presupuesto="999")

    with pytest.raises(ValueError, match="999"):
        guardar_presupuesto(
            sesion,
            resultado.presupuesto,
            ajeno,
            proyecto=sembrar(sesion),
            lista=catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE),
            parametros=linea_base.PARAMETROS_LINEA_BASE,
        )


def test_presupuesto_inexistente_lanza_keyerror(sesion):
    with pytest.raises(KeyError, match="NO-EXISTE"):
        cargar_presupuesto(sesion, NOMBRE_PROYECTO, "NO-EXISTE", Catalogo(sesion))


def test_los_renglones_referencian_la_partida_del_catalogo(sesion):
    _, modelo, _ = _guardado(sesion)

    for renglon, esperado in zip(modelo.partidas, CODIGOS, strict=True):
        assert renglon.partida.codigo == esperado
        assert renglon.item_computo.codigo_partida == esperado
        assert isinstance(renglon.item_computo, models.ItemComputo)
