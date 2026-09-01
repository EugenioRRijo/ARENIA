# Bitácora — Cierre UC‑08: escenarios de sensibilidad (RF‑30, RF‑31)

**Fecha:** 2026‑08‑31 · **Rama:** `inc/UC08-escenarios` (fusionada a `main` con `--no-ff`) ·
**Base:** `8dede1a` (Sesión F.2) · **Origen:** hallazgo 1 de la bitácora de F.2, resuelto por
decisión del usuario («UC‑08 necesita pruebas») antes de abrir F.3.

## Qué se hizo

**`core/budget/escenarios.py`** (TDD, RED observado por `ImportError`): UC‑08 según el flujo de
la ERS §2.2, «usa el mecanismo de UC‑02 sin persistir» (diseño de F.1):

1. **`generar_escenario(nombre, base, composiciones, parametros, *, precios=None)`** (RF‑30):
   recalcula el presupuesto completo con `ParametrosCosto` nuevos y/o precios de insumos nuevos
   (por descripción: material y equipo por `precio`, mano de obra por `sueldo`). Todo en memoria;
   el base y las composiciones quedan intactos (contratos congelados, aquí solo se crean copias).
   `elaborar` audita siempre: cada escenario trae su informe.
2. **`comparar_escenarios(base, escenarios)`** (RF‑31): tabla con el base en la primera fila y
   una fila por escenario — total, variación absoluta y porcentual — con celdas `Decimal`
   (dtype `object`, como el comparativo de UC‑02); exportable con `to_csv`/`to_excel`.
3. **`comparar_por_partida(base, escenario)`** (paso 3 del flujo): reutiliza `_comparar` de
   `actualizacion` — la tabla por renglón tiene una sola definición (DRY).

**`tests/unit/test_escenarios.py`** (6 pruebas, primero en RED): cada partida del escenario de
parámetros se verifica contra `calcular_apu` (el motor como verdad de terreno, no el propio
mecanismo); el escenario de precios del caso UC‑02 (cemento 18, arena 33) sube **solo** el
vaciado de concreto y exactamente en los 30,17025 USD/m3 calculados a mano para
`test_actualizacion_precios`; base y composiciones idénticos antes y después; tabla, exportación
y detalle por partida.

## Decisiones

| Decisión | Motivo |
|---|---|
| El módulo vive en `core/budget`, y este incremento **sí** toca `core/` | Igual que I6.2: es una sesión de funcionalidad del núcleo, no un adaptador. La hipótesis central («agregar un *dominio* no cambia `core/`») no está en juego; `test_arquitectura.py` sigue en verde |
| Nada se persiste; promover un escenario (flujo 4a) no se implementa | La ERS lo resuelve sola: promover = UC‑02 con la lista nueva, y ese camino ya existe (`actualizar_precios`). Duplicarlo sería una segunda escritura del mismo flujo |
| `insumos_variados` cuenta solo precios que **difieren** de los vigentes | Un precio declarado igual al vigente no varía nada; misma semántica que `insumos_afectados` en UC‑02 (hallazgo de la ronda 1 de I1: distinguir «nada cambió» de «cambió algo que no afecta») |
| Importes esperados tomados de las constantes calculadas a mano para UC‑02 | La prueba no puede validar el mecanismo con el mecanismo: 30,17025 = (7,5 × 3 + 0,45 × 3) × 1,15 × 1,10 viene del papel, como toda la línea base |
| Reutilización de `_comparar`/`_porcentaje` (privados del módulo hermano) | Patrón ya establecido (`actualizacion` importa ayudantes de `persistencia`); la alternativa era duplicar la única definición de la tabla por renglón |

## Hallazgos

1. **UC‑08 no tiene página en la UI ni ruta en la API.** La ERS §3.1 promete la interfaz web con
   los ocho casos de uso; los escenarios operan hoy desde `core.budget`. Cablearlo es mecánico
   (la página del simulador ya ejercita UC‑02); queda para F.3 o como salvedad en G0.
2. La postcondición de UC‑08 («escenarios guardados con sus parámetros») se satisface en memoria
   (el `Escenario` lleva sus `ParametrosCosto` y su conteo de precios variados), no en base de
   datos — coherente con «sin persistir», pero conviene decirlo en G0 con esta referencia.

## Estado al cierre

```
uv run pytest tests/unit/test_escenarios.py -W error -> 6 passed (RED -> GREEN observados)
uv run pytest -W error --cov=...                     -> 392 passed en 96,7 s (385 + 6 nuevas + 1
                                                        de arquitectura parametrizada por el
                                                        modulo nuevo); core 98,05 %
uv run ruff check .                                  -> limpio
git diff --stat core/ (en la rama)                   -> core/budget: modulo nuevo + exportacion
                                                        (legitimo: incremento de nucleo, como I6.2)
```

## Próximos pasos

1. **Sesión F.3** (última del PLAN): manuales de usuario y técnico; decidir allí si el manual
   documenta UC‑08 por API de `core` o si se cablea la página primero (hallazgo 1).
2. G0 (tutor), G1 (IFC real), RNF‑04 (Likert) y RNF‑07 (Linux) sin cambios.
