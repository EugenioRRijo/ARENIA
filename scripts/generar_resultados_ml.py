"""Genera `docs/resultados_ml.md`: compuerta G2 y metricas del modulo predictivo (RF-28, I6.3).

Todo corre sobre una base **en memoria** sembrada con la linea base: el informe es reproducible
con `uv run python scripts/generar_resultados_ml.py`, sin depender de `data/apu.db` ni de estado
previo. El flujo de evaluacion es el mismo del caso UC-02 verificado por las pruebas de
integracion: presupuesto 001 -> lista de muestra del 01/06/2026 -> presupuesto 002; los PU del
motor de costos (funcion pura, la verdad de terreno) se comparan contra la prediccion del sistema
de reglas de `ml.prediction` y las tres metricas obligatorias salen de ahi.

El conteo de la compuerta G2 se hace sobre el catalogo sembrado (partidas por dominio) y la
tecnica la dicta `ml.prediction.tecnica_para` (la tabla de CLAUDE.md §8.1 hecha codigo). La
seccion de texto (`generar_informe`) es pura y la prueba `tests/unit/test_resultados_ml.py` la
cubre; este script solo acopia los datos y escribe el archivo.
"""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from sqlalchemy.orm import Session  # noqa: E402

from core.budget import (  # noqa: E402
    actualizar_precios,
    elaborar,
    generar_presupuesto,
    guardar_presupuesto,
    plan_secuencial,
)
from core.catalog import (  # noqa: E402
    Catalogo,
    abrir_sesion,
    cambios_precio,
    crear_esquema,
    crear_lista_desde_archivo,
    crear_motor,
)
from core.contracts.dominio import Dominio  # noqa: E402
from core.contracts.verificacion import Hallazgo  # noqa: E402
from core.verification.informe import DECIMALES_PRESENTACION  # noqa: E402
from core.verification.texto import formatear_decimal  # noqa: E402
from ml.prediction import (  # noqa: E402
    UMBRAL_CASOS,
    Metricas,
    PrediccionPrecio,
    contrastar_aace,
    metricas,
    predecir_por_reglas,
    tecnica_para,
)
from scripts.seed import NOMBRE_PROYECTO, sembrar  # noqa: E402
from tests.fixtures import apu_linea_base as linea_base  # noqa: E402
from tests.fixtures.computo_auditado import items_auditados  # noqa: E402

MUESTRA_PRECIOS = RAIZ / "data" / "samples" / "precios" / "lista_2026-06-01.csv"
RUTA_INFORME = RAIZ / "docs" / "resultados_ml.md"
FECHA_LISTA_NUEVA = date(2026, 6, 1)
_CIEN = Decimal(100)


def conteo_por_dominio(sesion: Session) -> dict[str, int]:
    """Registros de APU disponibles por dominio: partidas del catalogo (compuerta G2)."""
    catalogo = Catalogo(sesion)
    return {dominio.value: len(catalogo.partidas(dominio)) for dominio in Dominio}


def evaluar_sobre_linea_base(
    sesion: Session,
) -> tuple[Metricas, list[PrediccionPrecio], list[Hallazgo]]:
    """Predice los PU del presupuesto 002 con la regla y los mide contra el motor de costos."""
    proyecto = sembrar(sesion)
    catalogo = Catalogo(sesion)
    items = items_auditados()
    codigos = [apu.codigo_partida for apu in linea_base.APUS_LINEA_BASE]
    composiciones = catalogo.composiciones(codigos, fecha=linea_base.FECHA_LINEA_BASE)
    argumentos = dict(
        codigo=linea_base.CODIGO_PRESUPUESTO,
        fecha=linea_base.FECHA_LINEA_BASE,
        moneda=linea_base.MONEDA,
    )
    borrador = generar_presupuesto(
        items, composiciones, linea_base.PARAMETROS_LINEA_BASE, **argumentos
    )
    resultado = elaborar(
        items,
        composiciones,
        linea_base.PARAMETROS_LINEA_BASE,
        plan=plan_secuencial(borrador),
        **argumentos,
    )
    guardar_presupuesto(
        sesion,
        resultado.presupuesto,
        resultado.informe,
        proyecto=proyecto,
        lista=catalogo.lista_vigente(linea_base.FECHA_LINEA_BASE),
        parametros=linea_base.PARAMETROS_LINEA_BASE,
    )

    resumen = crear_lista_desde_archivo(
        sesion,
        MUESTRA_PRECIOS,
        nombre="Lista de precios 01/06/2026",
        moneda=linea_base.MONEDA,
        fecha_vigencia=FECHA_LISTA_NUEVA,
        origen=MUESTRA_PRECIOS.name,
    )
    _, comparativo = actualizar_precios(
        sesion,
        NOMBRE_PROYECTO,
        linea_base.CODIGO_PRESUPUESTO,
        resumen.lista,
        "002",
        plan=plan_secuencial(resultado.presupuesto),
    )

    pus_base = {
        fila.codigo_partida: fila.pu_anterior for fila in comparativo.tabla.itertuples(index=False)
    }
    reales = {
        fila.codigo_partida: fila.pu_nuevo for fila in comparativo.tabla.itertuples(index=False)
    }
    variaciones = [cambio.variacion for cambio in cambios_precio(sesion)]

    predicciones = predecir_por_reglas(pus_base, variaciones)
    estimados = {prediccion.codigo_partida: prediccion.pu_estimado for prediccion in predicciones}
    hallazgos = [
        hallazgo
        for codigo in sorted(reales)
        if (hallazgo := contrastar_aace(codigo, reales[codigo], estimados[codigo])) is not None
    ]
    return metricas(estimados=estimados, reales=reales), predicciones, hallazgos


def generar_informe(
    conteos: dict[str, int],
    metricas: Metricas,
    predicciones: list[PrediccionPrecio],
    hallazgos: list[Hallazgo],
) -> str:
    """El texto de `docs/resultados_ml.md`. Puro: todo lo que presenta viene por parametro."""

    def dos(valor: Decimal) -> str:
        return formatear_decimal(valor, DECIMALES_PRESENTACION)

    def cuatro(valor: Decimal) -> str:
        # R2 va con cuatro decimales: a dos, un 0.9974 se presentaria como "1.00", que enganna.
        return formatear_decimal(valor, 4)

    lineas = [
        "# Resultados del modulo predictivo (Sesion I6.3, RF-28)",
        "",
        "Generado por `scripts/generar_resultados_ml.py` sobre una base en memoria sembrada con",
        "la linea base; reproducible con `uv run python scripts/generar_resultados_ml.py`.",
        "",
        "## Compuerta G2: conteo de registros y tecnica (CLAUDE.md §8.1)",
        "",
        "| Dominio | Registros de APU | Tecnica que dicta la tabla |",
        "|---|---|---|",
    ]
    for dominio, registros in sorted(conteos.items()):
        lineas.append(f"| {dominio} | {registros} | {tecnica_para(registros).value} |")
    lineas += [
        "",
        f"Todos los dominios estan por debajo de los {UMBRAL_CASOS} registros: la tecnica de",
        "`ml/prediction/` es el **sistema de reglas con analisis de sensibilidad**, y se declara",
        "como **limitacion** del trabajo, no como logro: no hay datos suficientes para entrenar",
        "ni validar un modelo de aprendizaje (la tabla de degradacion existe exactamente para",
        "este caso). La compuerta G2 queda cruzada con esta evidencia.",
        "",
        "## Regla declarada",
        "",
        "PU estimado = PU base x (1 + media de las variaciones del historico de cambios de",
        "precio). Sensibilidad: el rango recorre la variacion minima y la maxima observadas.",
        "La regla no conoce la composicion del APU: el motor de costos (`core.costing`) es la",
        "verdad de terreno contra la que se mide.",
        "",
        "## Metricas (RF-28)",
        "",
        "| Metrica | Valor |",
        "|---|---|",
        f"| MAPE | {dos(metricas.mape * _CIEN)} % |",
        f"| RMSE | {dos(metricas.rmse)} USD |",
        f"| R2 | {'sin varianza en los reales' if metricas.r2 is None else cuatro(metricas.r2)} |",
        "",
        "## Predicciones sobre el caso UC-02 de la linea base",
        "",
        "| Partida | PU base | PU estimado | Rango de sensibilidad |",
        "|---|---|---|---|",
    ]
    for prediccion in predicciones:
        lineas.append(
            f"| {prediccion.codigo_partida} | {dos(prediccion.pu_base)} | "
            f"{dos(prediccion.pu_estimado)} | "
            f"[{dos(prediccion.pu_minimo)}, {dos(prediccion.pu_maximo)}] |"
        )
    lineas += [
        "",
        "## Contraste AACE clase 3 (RF-29)",
        "",
    ]
    if hallazgos:
        lineas.append(f"{len(hallazgos)} hallazgo(s) de severidad ADVERTENCIA:")
        lineas.append("")
        lineas += [f"- {hallazgo.descripcion}" for hallazgo in hallazgos]
    else:
        lineas.append(
            "Ningun precio construido se desvia del estimado fuera del rango declarado "
            "(-20 % / +30 %): sin hallazgos."
        )
    lineas.append("")
    return "\n".join(lineas)


def main() -> int:
    motor = crear_motor("sqlite://")
    try:
        crear_esquema(motor)
        with abrir_sesion(motor) as sesion:
            resultado_metricas, predicciones, hallazgos = evaluar_sobre_linea_base(sesion)
            conteos = conteo_por_dominio(sesion)
            informe = generar_informe(conteos, resultado_metricas, predicciones, hallazgos)
    finally:
        motor.dispose()

    RUTA_INFORME.write_text(informe, encoding="utf-8")
    print(f"Informe escrito en: {RUTA_INFORME}")
    print(
        f"MAPE {resultado_metricas.mape * _CIEN:.2f} % | RMSE {resultado_metricas.rmse:.2f} | "
        f"R2 {resultado_metricas.r2 if resultado_metricas.r2 is not None else 'n/a'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
