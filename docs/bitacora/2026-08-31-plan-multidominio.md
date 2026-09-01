# Bitácora — Plan de desarrollo multidominio (datos reales)

**Fecha:** 2026‑08‑31 · **Rama:** `inc/PLAN-multidominio` (fusionada a `main` con `--no-ff`) ·
**Base:** `eae65ee` (plan de redacción) · **Origen:** pedido del usuario («necesito armar un plan
de desarrollo para cubrir las demás ingenierías»), tras la conversación sobre fuentes de precios
por dominio.

## Qué se hizo

**[PLAN_MULTIDOMINIO.md](../../PLAN_MULTIDOMINIO.md)** (raíz, junto al PLAN original, que ahora
lo enlaza en su sección «Continuación»): 10 sesiones en 5 fases (M0–M4) con compuertas GM1–GM4 y
criterios de degradación declarados, para que telecom, industrial y sistemas dejen de tener cero
registros y entren por la misma puerta que civil — catálogo, presupuesto auditado y lista de
precios real y fechada, cada uno desde su fuente natural.

Ideas rectoras del plan:

1. **La generalización que se demuestra es doble y simétrica:** el PLAN original probó que el
   núcleo no cambia al agregar un dominio; este prueba que el protocolo de datos no cambia al
   cambiar la fuente. Ninguna sesión toca `core/`.
2. **Telecom primero y sin dependencias externas:** los dos presupuestos ARENAZA ya están en el
   repo con precios reales por renglón (1 109,29 y 5 410,73 USD) y traen su propia inconsistencia
   documentada (tubo corrugado: 80 m en cómputos vs 90 m en presupuesto del mismo PDF). M1
   convierte eso en la **segunda línea base** de la tesis y en el segundo caso de auditoría
   (momento clave: M1.3, cuando R1–R7 marquen los 80/90 con sus `origen_id`).
3. **La política «mano de obra = 50 % del total» se resuelve con la opción 1 del hallazgo 1 de la
   bitácora I5‑telecom** (línea de mano de obra sintética armada por la capa de catálogo antes de
   llamar al motor): el análisis existía desde I5, el plan solo lo adopta.
4. **El trabajo de campo (cotizaciones, tarifario, carta MaPreX/Lulowin) corre en paralelo** y
   solo bloquea M2/M3, nunca M1; cada compuerta GM tiene su degradación declarada para no
   inventar precios si el campo no llega.
5. **G2 no se promete revertir:** los dominios seguirán < 50 registros y la técnica seguirá
   siendo reglas; GM4 regenera los conteos para que la limitación quede declarada con números
   nuevos, no con ausencia de intento.

## Decisiones

| Decisión | Motivo |
|---|---|
| Plan nuevo en la raíz, no sesiones añadidas al PLAN original | El PLAN de 20 sesiones es un documento cerrado y citado por la metodología; extenderlo reescribiría historia. La sección «Continuación» lo enlaza |
| R5 reportando INFO en dominios no civiles se documenta como comportamiento correcto | Es exactamente RF‑23 (regla sin datos → INFO sin abortar); «arreglarlo» sería tocar el núcleo por un no‑defecto |
| Fixture único por dominio en `tests/fixtures/` | El mismo DRY que `apu_linea_base.py`: una sola copia estructurada de cada evidencia primaria |
| El protocolo de precios (M0.1) es una sesión del plan, no un documento suelto | Así queda con Definition of Done, commit y bitácora como todo lo demás |

## Estado al cierre

```
uv run pytest -W error  -> 395 passed (sesion solo de documentos)
uv run ruff check .     -> limpio
git diff --stat core/   -> vacio
```

## Próximos pasos

1. **Sesión M0.1** (protocolo + plantillas + carta) o directamente **M1.1** (fuentes ARENAZA
   estructuradas), que no depende de nada externo — a elección del usuario.
2. El trabajo de campo del autor (cotizaciones civil e industrial, tarifario CIV, carta) puede
   arrancar apenas exista M0.1.
3. La redacción de capítulos (plan_redaccion) sigue pausada por decisión del usuario; cuando se
   retome, el capítulo V se beneficiará de cada compuerta GM cruzada.
