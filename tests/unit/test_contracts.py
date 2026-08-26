"""Los contratos validan sus invariantes. Estas pruebas permanecen verdes todo el proyecto."""

from datetime import date
from decimal import Decimal

import pytest

from core.contracts import (
    AdaptadorDominio,
    ComposicionAPU,
    Dominio,
    Hallazgo,
    ItemComputo,
    LineaEquipo,
    LineaManoObra,
    LineaMaterial,
    OrigenTipo,
    ParametrosCosto,
    PartidaPresupuestada,
    Presupuesto,
    PuntoCurva,
    ReglaVerificacion,
    Rendimiento,
    ResultadoAPU,
    Severidad,
    TipoRendimiento,
    normalizar_unidad,
    unidades_equivalentes,
)


def _item(**cambios):
    base = dict(
        codigo_partida="E-401",
        descripcion="Excavación a mano en tierra",
        unidad="m³",
        cantidad=Decimal("9.74"),
        origen_id="zanja-01",
        origen_tipo=OrigenTipo.TABULAR,
        dominio=Dominio.CIVIL,
    )
    base.update(cambios)
    return ItemComputo(**base)


class TestUnidades:
    @pytest.mark.parametrize(
        ("entrada", "esperada"),
        [
            ("m³", "m3"),
            ("M3", "m3"),
            ("m²", "m2"),
            ("mts", "m"),
            ("  Metros lineales ", "m"),
            ("Pieza", "pieza"),
            ("PZA", "pieza"),
            ("und", "unidad"),
        ],
    )
    def test_alias_conocidos(self, entrada, esperada):
        assert normalizar_unidad(entrada) == esperada

    def test_unidad_desconocida_se_conserva(self):
        assert normalizar_unidad(" Rollo ") == "rollo"

    def test_unidad_vacia_es_error(self):
        with pytest.raises(ValueError):
            normalizar_unidad("   ")

    def test_pieza_y_metro_no_son_equivalentes(self):
        """El hallazgo 4 de la línea base (mts vs Pieza) debe seguir siendo detectable."""
        assert not unidades_equivalentes("mts", "Pieza")
        assert unidades_equivalentes("mts", "m")


class TestItemComputo:
    def test_normaliza_unidad(self):
        assert _item(unidad="M³").unidad == "m3"

    def test_cantidad_negativa(self):
        with pytest.raises(ValueError):
            _item(cantidad=Decimal("-1"))

    def test_cantidad_float_rechazada(self):
        with pytest.raises(TypeError):
            _item(cantidad=9.74)

    def test_origen_obligatorio(self):
        with pytest.raises(ValueError):
            _item(origen_id="  ")

    def test_regla_obligatoria_si_origen_es_regla(self):
        with pytest.raises(ValueError):
            _item(origen_tipo=OrigenTipo.REGLA)

    def test_regla_con_parametros_queda_congelada(self):
        item = _item(
            origen_tipo=OrigenTipo.REGLA,
            regla="(a**2 - (a - 2*e)**2) * h",
            parametros={"a": Decimal("0.80"), "h": Decimal("0.80"), "e": Decimal("0.10")},
            cantidad=Decimal("0.224"),
        )
        assert item.parametros["a"] == Decimal("0.80")
        with pytest.raises(TypeError):
            item.parametros["a"] = Decimal("1")

    def test_es_inmutable(self):
        with pytest.raises(AttributeError):
            _item().cantidad = Decimal("1")

    def test_es_hashable(self):
        assert hash(_item()) == hash(_item())


class TestLineasAPU:
    def test_material_total(self):
        linea = LineaMaterial("Tubería PVC 4 pulg", "m", Decimal("1.05"), Decimal("6"))
        assert linea.total == Decimal("6.30")

    def test_equipo_total_con_depreciacion(self):
        linea = LineaEquipo("Pico", Decimal(2), Decimal(25), Decimal("0.03"))
        assert linea.total == Decimal("1.50")

    @pytest.mark.parametrize("depreciacion", ["0", "1.5", "-0.03"])
    def test_depreciacion_fuera_de_rango(self, depreciacion):
        with pytest.raises(ValueError):
            LineaEquipo("x", Decimal(1), Decimal(1), Decimal(depreciacion))

    def test_mano_obra_total(self):
        assert LineaManoObra("Ayudante", Decimal(2), Decimal(3)).total == Decimal(6)

    def test_precio_negativo(self):
        with pytest.raises(ValueError):
            LineaMaterial("x", "m", Decimal(1), Decimal(-1))


class TestComposicionAPU:
    def test_rendimiento_cero(self):
        with pytest.raises(ValueError):
            ComposicionAPU("E-401", "Excavación", "m3", Decimal(0))

    def test_convierte_listas_en_tuplas_y_cuenta_obreros(self):
        apu = ComposicionAPU(
            "E-401",
            "Excavación",
            "m3",
            Decimal(80),
            mano_obra=[
                LineaManoObra("Ayudante", Decimal(2), Decimal(3)),
                LineaManoObra("Chofer de 4ta", Decimal(1), Decimal("3.5")),
            ],
        )
        assert isinstance(apu.mano_obra, tuple)
        assert apu.total_obreros == Decimal(3)


class TestParametrosCosto:
    def test_valores_por_defecto_son_los_de_la_linea_base(self):
        p = ParametrosCosto()
        assert (p.fcas, p.bono_alimentacion, p.administracion, p.utilidad) == (
            Decimal("6.00"),
            Decimal("1.00"),
            Decimal("0.15"),
            Decimal("0.10"),
        )

    def test_negativo(self):
        with pytest.raises(ValueError):
            ParametrosCosto(fcas=Decimal("-1"))


class TestRendimiento:
    def test_medido_exige_referencia(self):
        with pytest.raises(ValueError):
            Rendimiento("E-401", Decimal(80), TipoRendimiento.MEDIDO, date(2026, 4, 28))

    def test_estimado_no_la_exige(self):
        r = Rendimiento("E-401", Decimal(80), TipoRendimiento.ESTIMADO, date(2026, 4, 28))
        assert r.referencia_ejecucion is None


class TestPresupuesto:
    @staticmethod
    def _partida(cantidad="9.74", precio_unitario="8.60", codigo_apu="E-401"):
        pu = Decimal(precio_unitario)
        resultado = ResultadoAPU(Decimal(0), Decimal(0), Decimal(0), pu, pu, pu)
        apu = ComposicionAPU(codigo_apu, "Excavación", "m3", Decimal(80))
        return PartidaPresupuestada(_item(cantidad=Decimal(cantidad)), apu, resultado)

    def test_total_partida(self):
        assert self._partida().total == Decimal("9.74") * Decimal("8.60")

    def test_item_y_apu_deben_ser_la_misma_partida(self):
        with pytest.raises(ValueError):
            self._partida(codigo_apu="E-402")

    def test_total_y_curva(self):
        presupuesto = Presupuesto(
            "001",
            date(2026, 4, 28),
            "USD",
            [self._partida()],
            curva=[PuntoCurva("Día 1", Decimal("82.98"), Decimal("82.98"))],
        )
        assert presupuesto.total == Decimal("83.764")
        assert presupuesto.total_curva == Decimal("82.98")
        # La regla R2 (Sesión I4) convertirá esta diferencia en un Hallazgo.
        assert presupuesto.total != presupuesto.total_curva


class TestVerificacion:
    def test_severidad_ordenada(self):
        assert Severidad.INFO < Severidad.ADVERTENCIA < Severidad.ERROR < Severidad.CRITICO

    def test_hallazgo_exige_regla_y_descripcion(self):
        with pytest.raises(ValueError):
            Hallazgo("", Severidad.ERROR, "x")
        with pytest.raises(ValueError):
            Hallazgo("R2", Severidad.ERROR, " ")

    def test_hallazgo_origenes_en_tupla(self):
        hallazgo = Hallazgo("R2", Severidad.ERROR, "x", origen_ids=["a", "b"])
        assert hallazgo.origen_ids == ("a", "b")

    def test_regla_sin_evaluar_no_se_instancia(self):
        class Incompleta(ReglaVerificacion):
            codigo = "R0"
            nombre = "incompleta"

        with pytest.raises(TypeError):
            Incompleta()

    def test_regla_sin_codigo_falla_al_definirse(self):
        with pytest.raises(TypeError):

            class SinCodigo(ReglaVerificacion):
                def evaluar(self, presupuesto):
                    return []


class TestAdaptadorDominio:
    def test_sin_extraer_no_se_instancia(self):
        class Incompleto(AdaptadorDominio):
            dominio = Dominio.TELECOM

        with pytest.raises(TypeError):
            Incompleto()

    def test_sin_dominio_falla_al_definirse(self):
        with pytest.raises(TypeError):

            class SinDominio(AdaptadorDominio):
                def extraer(self, fuente):
                    return []

    def test_adaptador_minimo_cumple_el_contrato(self):
        class Tabular(AdaptadorDominio):
            dominio = Dominio.CIVIL

            def extraer(self, fuente):
                return [_item(origen_id=str(fuente))]

        items = Tabular().extraer("fila-1")
        assert items[0].origen_id == "fila-1"
        assert items[0].dominio is Dominio.CIVIL
