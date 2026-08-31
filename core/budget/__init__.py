"""Presupuesto, curva de inversión (cierra al 100 % por construcción) y exportación a Excel.

Sesiones I0.5 e I1.

Flujo completo de la Sesión I0.5::

    from core.budget import elaborar, exportar_excel, plan_secuencial

    resultado = elaborar(items, composiciones, parametros, codigo="001", fecha=hoy)
    exportar_excel(resultado.presupuesto, resultado.informe, Path("presupuesto.xlsx"))

`elaborar` audita siempre: no existe forma de obtener el presupuesto sin su informe (principio 7 de
CLAUDE.md §2).

`guardar_presupuesto` y `cargar_presupuesto` implementan el versionado híbrido de
`docs/modelo_datos.md` §5: el renglón guardado congela su `ResultadoAPU` y al cargar se comprueba
que el catálogo sigue reproduciéndolo.
"""

from core.budget.actualizacion import COLUMNAS_COMPARATIVO, Comparativo, actualizar_precios
from core.budget.curva import (
    PeriodoPlan,
    PlanInvalido,
    con_curva,
    generar_curva,
    plan_secuencial,
)
from core.budget.excel import exportar_excel
from core.budget.persistencia import cargar_presupuesto, guardar_presupuesto
from core.budget.presupuesto import ResultadoElaboracion, elaborar, generar_presupuesto

__all__ = [
    "COLUMNAS_COMPARATIVO",
    "Comparativo",
    "PeriodoPlan",
    "PlanInvalido",
    "ResultadoElaboracion",
    "actualizar_precios",
    "cargar_presupuesto",
    "con_curva",
    "elaborar",
    "exportar_excel",
    "generar_curva",
    "generar_presupuesto",
    "guardar_presupuesto",
    "plan_secuencial",
]
