"""Consulta y carga de partidas, insumos, precios y rendimientos.

`Catalogo` es la única puerta de entrada al catálogo persistido. Devuelve **contratos** cuando el
resultado va a cruzar una frontera de paquete (`ComposicionAPU`, `Rendimiento`) y **modelos** cuando
el llamador va a seguir trabajando con la sesión (`Partida`, `Insumo`, `ListaPrecios`).
"""

from __future__ import annotations

import string
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from core import models
from core.catalog.errores import CatalogoIncompleto
from core.catalog.mapeo import a_composicion, a_rendimiento
from core.contracts.apu import ComposicionAPU, Rendimiento, TipoRendimiento
from core.contracts.dominio import Dominio

#: Sufijos de variante de insumo: el segundo homónimo es «-B», el tercero «-C»…
SUFIJOS_VARIANTE = string.ascii_uppercase[1:]


@dataclass(slots=True)
class ResumenCarga:
    """Qué produjo una carga: la partida y los insumos creados, separando las variantes.

    `variantes` son los insumos creados porque ya existía uno con la misma descripción y unidad
    pero con **otro precio** en la misma lista: el hallazgo de datos de docs/modelo_datos.md §6.
    """

    partida: models.Partida
    insumos_nuevos: list[models.Insumo] = field(default_factory=list)
    variantes: list[models.Insumo] = field(default_factory=list)


class Catalogo:
    """Operaciones de consulta y carga sobre una sesión abierta."""

    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    # -- consulta ------------------------------------------------------------------------------

    def partidas(self, dominio: Dominio | str | None = None) -> list[models.Partida]:
        """Partidas del catálogo, ordenadas por código; filtradas por dominio si se indica."""
        consulta = select(models.Partida).order_by(models.Partida.codigo)
        if dominio is not None:
            consulta = consulta.where(models.Partida.dominio == str(dominio))
        return list(self._sesion.scalars(consulta))

    def partida(self, codigo: str) -> models.Partida:
        """La partida de ese código. `KeyError` si no está en el catálogo."""
        partida = self._sesion.scalars(
            select(models.Partida).where(models.Partida.codigo == codigo)
        ).one_or_none()
        if partida is None:
            raise KeyError(f"no hay ninguna partida con código {codigo!r} en el catálogo")
        return partida

    def insumos(self, tipo: models.TipoInsumo | str | None = None) -> list[models.Insumo]:
        """Insumos del catálogo, ordenados por código; filtrados por tipo si se indica."""
        consulta = select(models.Insumo).order_by(models.Insumo.codigo)
        if tipo is not None:
            consulta = consulta.where(models.Insumo.tipo == str(tipo))
        return list(self._sesion.scalars(consulta))

    def rendimientos(self, codigo_partida: str) -> list[Rendimiento]:
        """Todos los rendimientos de una partida, del más antiguo al más reciente."""
        self.partida(codigo_partida)
        consulta = (
            select(models.Rendimiento)
            .join(models.Partida)
            .where(models.Partida.codigo == codigo_partida)
            .order_by(models.Rendimiento.fecha, models.Rendimiento.id)
        )
        return [a_rendimiento(modelo) for modelo in self._sesion.scalars(consulta)]

    def lista_vigente(self, fecha: date | None = None) -> models.ListaPrecios:
        """La lista de mayor `fecha_vigencia` menor o igual a `fecha`; hoy si `fecha` es None."""
        limite = fecha if fecha is not None else date.today()
        lista = self._sesion.scalars(
            select(models.ListaPrecios)
            .where(models.ListaPrecios.fecha_vigencia <= limite)
            .order_by(models.ListaPrecios.fecha_vigencia.desc(), models.ListaPrecios.id.desc())
            .limit(1)
        ).one_or_none()
        if lista is None:
            raise CatalogoIncompleto(f"no hay ninguna lista de precios vigente al {limite}")
        return lista

    def composicion(
        self,
        codigo_partida: str,
        fecha: date | None = None,
        lista: models.ListaPrecios | None = None,
    ) -> ComposicionAPU:
        """Reconstruye el APU de una partida a una fecha (docs/modelo_datos.md §5).

        Precios: los de `lista`, o los de la lista vigente a esa fecha.
        Rendimiento: el ESTIMADO más reciente con `fecha` menor o igual a la pedida.
        """
        limite = fecha if fecha is not None else date.today()
        partida = self.partida(codigo_partida)
        if lista is None:
            lista = self.lista_vigente(limite)
        return a_composicion(partida, lista, self._rendimiento_estimado(partida, limite))

    def composiciones(
        self, codigos: Iterable[str], fecha: date | None = None
    ) -> dict[str, ComposicionAPU]:
        """Reconstruye varios APU con una sola resolución de lista de precios."""
        limite = fecha if fecha is not None else date.today()
        lista = self.lista_vigente(limite)
        return {codigo: self.composicion(codigo, fecha=limite, lista=lista) for codigo in codigos}

    # -- carga ---------------------------------------------------------------------------------

    def cargar_composicion(
        self,
        composicion: ComposicionAPU,
        lista: models.ListaPrecios,
        dominio: Dominio,
        fecha_rendimiento: date,
    ) -> ResumenCarga:
        """Persiste un APU del contrato: partida, insumos, precios, líneas y rendimiento estimado.

        Reutiliza los insumos que ya existen con el mismo (tipo, descripción, unidad) y el mismo
        precio en la lista; si el precio difiere, crea una variante (§6 del modelo de datos).
        """
        partida = self._sesion.scalars(
            select(models.Partida).where(models.Partida.codigo == composicion.codigo_partida)
        ).one_or_none()
        if partida is None:
            partida = models.Partida(
                codigo=composicion.codigo_partida,
                descripcion=composicion.descripcion,
                unidad=composicion.unidad,
                dominio=str(dominio),
            )
            self._sesion.add(partida)
            self._sesion.flush()

        resumen = ResumenCarga(partida=partida)
        orden = 0
        for material in composicion.materiales:
            insumo = self._resolver_insumo(
                models.TipoInsumo.MATERIAL,
                material.descripcion,
                material.unidad,
                material.precio,
                lista,
                resumen,
            )
            self._agregar_linea(partida, insumo, material.cantidad, None, orden)
            orden += 1
        for equipo in composicion.equipos:
            insumo = self._resolver_insumo(
                models.TipoInsumo.EQUIPO, equipo.descripcion, None, equipo.precio, lista, resumen
            )
            self._agregar_linea(partida, insumo, equipo.cantidad, equipo.depreciacion, orden)
            orden += 1
        for obrero in composicion.mano_obra:
            insumo = self._resolver_insumo(
                models.TipoInsumo.MANO_OBRA, obrero.descripcion, None, obrero.sueldo, lista, resumen
            )
            self._agregar_linea(partida, insumo, obrero.cantidad, None, orden)
            orden += 1

        self._sesion.add(
            models.Rendimiento(
                partida_id=partida.id,
                valor=composicion.rendimiento,
                tipo=TipoRendimiento.ESTIMADO.value,
                fecha=fecha_rendimiento,
                condiciones="",
            )
        )
        self._sesion.flush()
        return resumen

    def registrar_rendimiento(self, rendimiento: Rendimiento) -> models.Rendimiento:
        """Persiste un rendimiento del contrato. Un MEDIDO exige una `Ejecucion` ya registrada."""
        partida = self.partida(rendimiento.codigo_partida)
        ejecucion = None
        if rendimiento.referencia_ejecucion:
            ejecucion = self._sesion.scalars(
                select(models.Ejecucion).where(
                    models.Ejecucion.referencia == rendimiento.referencia_ejecucion
                )
            ).one_or_none()
            if ejecucion is None:
                raise CatalogoIncompleto(
                    f"no hay ninguna ejecución con referencia {rendimiento.referencia_ejecucion!r}"
                )
        modelo = models.Rendimiento(
            partida_id=partida.id,
            valor=rendimiento.valor,
            tipo=rendimiento.tipo.value,
            fecha=rendimiento.fecha,
            condiciones=rendimiento.condiciones,
            ejecucion_id=ejecucion.id if ejecucion is not None else None,
        )
        self._sesion.add(modelo)
        self._sesion.flush()
        return modelo

    # -- interno -------------------------------------------------------------------------------

    def _rendimiento_estimado(self, partida: models.Partida, limite: date) -> models.Rendimiento:
        rendimiento = self._sesion.scalars(
            select(models.Rendimiento)
            .where(
                models.Rendimiento.partida_id == partida.id,
                models.Rendimiento.tipo == TipoRendimiento.ESTIMADO.value,
                models.Rendimiento.fecha <= limite,
            )
            .order_by(models.Rendimiento.fecha.desc(), models.Rendimiento.id.desc())
            .limit(1)
        ).one_or_none()
        if rendimiento is None:
            raise CatalogoIncompleto(
                f"la partida {partida.codigo} no tiene rendimiento estimado al {limite}"
            )
        return rendimiento

    def _agregar_linea(
        self,
        partida: models.Partida,
        insumo: models.Insumo,
        cantidad: Decimal,
        depreciacion: Decimal | None,
        orden: int,
    ) -> None:
        self._sesion.add(
            models.ComposicionAPU(
                partida_id=partida.id,
                insumo_id=insumo.id,
                cantidad=cantidad,
                depreciacion=depreciacion,
                orden=orden,
            )
        )

    def _resolver_insumo(
        self,
        tipo: models.TipoInsumo,
        descripcion: str,
        unidad: str | None,
        precio: Decimal,
        lista: models.ListaPrecios,
        resumen: ResumenCarga,
    ) -> models.Insumo:
        candidatos = list(
            self._sesion.scalars(
                select(models.Insumo)
                .where(
                    models.Insumo.tipo == tipo.value,
                    models.Insumo.descripcion == descripcion,
                    models.Insumo.unidad == unidad,
                )
                .order_by(models.Insumo.id)
            )
        )
        for candidato in candidatos:
            vigente = self._precio_en_lista(lista, candidato)
            if vigente is None:
                self._fijar_precio(lista, candidato, precio)
                return candidato
            if vigente == precio:
                return candidato

        insumo = models.Insumo(
            codigo=(
                self._codigo_variante(candidatos[0].codigo)
                if candidatos
                else self._codigo_nuevo(tipo)
            ),
            tipo=tipo.value,
            descripcion=descripcion,
            unidad=unidad,
        )
        self._sesion.add(insumo)
        self._sesion.flush()
        self._fijar_precio(lista, insumo, precio)
        destino = resumen.variantes if candidatos else resumen.insumos_nuevos
        destino.append(insumo)
        return insumo

    def _precio_en_lista(self, lista: models.ListaPrecios, insumo: models.Insumo) -> Decimal | None:
        return self._sesion.scalar(
            select(models.PrecioInsumo.precio).where(
                models.PrecioInsumo.lista_id == lista.id,
                models.PrecioInsumo.insumo_id == insumo.id,
            )
        )

    def _fijar_precio(
        self, lista: models.ListaPrecios, insumo: models.Insumo, precio: Decimal
    ) -> None:
        self._sesion.add(models.PrecioInsumo(lista_id=lista.id, insumo_id=insumo.id, precio=precio))
        self._sesion.flush()

    def _codigo_nuevo(self, tipo: models.TipoInsumo) -> str:
        prefijo = models.PREFIJO_CODIGO_INSUMO[tipo]
        numeros = [
            int(partes[1])
            for codigo in self._sesion.scalars(
                select(models.Insumo.codigo).where(models.Insumo.tipo == tipo.value)
            )
            if len(partes := codigo.split("-")) > 1 and partes[1].isdigit()
        ]
        return f"{prefijo}-{max(numeros, default=0) + 1:03d}"

    def _codigo_variante(self, codigo_base: str) -> str:
        raiz = "-".join(codigo_base.split("-")[:2])
        for sufijo in SUFIJOS_VARIANTE:
            candidato = f"{raiz}-{sufijo}"
            if not self._existe_codigo(candidato):
                return candidato
        raise CatalogoIncompleto(f"se agotaron los sufijos de variante para {raiz}")

    def _existe_codigo(self, codigo: str) -> bool:
        return (
            self._sesion.scalar(select(models.Insumo.id).where(models.Insumo.codigo == codigo))
            is not None
        )
