# Bitácora — Plan de redacción de los capítulos

**Fecha:** 2026‑08‑31 · **Rama:** `inc/tesis-plan-redaccion` (fusionada a `main` con `--no-ff`) ·
**Base:** `77bb2ce` (dossier G0) · **Origen:** pedido del usuario («haz un md para redactar los
capítulos»), continuación natural tras el dossier.

## Qué se hizo

**[docs/tesis/plan_redaccion.md](../tesis/plan_redaccion.md)**: el guión operativo que convierte
el esqueleto en capítulos escribibles.

1. **Convenciones de redacción** (voz, cifras con coma decimal, terminología BIM‑5D/D8, DRY
   documental: los capítulos citan, los anexos cargan).
2. **Orden de escritura** del material más consolidado al menos: IV → V → III → II → I →
   Conclusiones → Introducción. La única dependencia dura con G0 es D3 (objetivos); se neutraliza
   redactando las dos variantes.
3. **Guión por capítulo**: qué contar en cada sección, con qué evidencia y qué figura; el IV en
   el orden causal del PLAN (11 secciones), el V con la redacción propuesta para cada uno de los
   cinco indicadores (incluidos los hallazgos adicionales 8 y 9), y las conclusiones respondiendo
   pregunta por pregunta contra la tabla §4 del esqueleto.
4. **Dependencias con G0** (qué decisión bloquea qué capítulo y qué hacer mientras tanto).
5. **Tabla de cifras citables** con su comando de regeneración: ninguna cifra entra al texto si
   no puede reproducirse con un comando (extiende a la redacción el principio de
   `generar_resultados_ml.py`).
6. **Tablero de avance** por capítulo (`docs/tesis/capitulos/`, un archivo por capítulo; se crean
   al redactarse, no vacíos).

El esqueleto enlaza ahora al plan (referencia cruzada única); el índice de docs tiene su fila.

## Decisiones

| Decisión | Motivo |
|---|---|
| Plan separado del esqueleto, que no se toca | El esqueleto es la matriz de trazabilidad (única, estable); el plan es operativo y cambiará con cada sesión de redacción. Mezclarlos degradaría la fuente de verdad |
| Orden de escritura por consolidación, no por índice | El capítulo IV no depende de nadie; los objetivos (cap. I) dependen de D3. Empezar por la introducción es el error clásico |
| Cifras solo desde la tabla §5, con comando | Una tesis con cifras que no cuadran entre capítulos es indefendible; la tabla es el único origen y se actualiza primero |
| Los archivos de capítulos se crean al redactarse | Siete esqueletos vacíos serían ruido; el tablero §6 ya reserva nombre y estado |

## Estado al cierre

```
uv run pytest -W error  -> 395 passed en 63,0 s (sesion solo de documentos)
uv run ruff check .     -> limpio
git diff --stat core/   -> vacio
```

## Próximos pasos

1. **Primera sesión de redacción: capítulo IV** (`docs/tesis/capitulos/04-desarrollo.md`),
   siguiendo el guión §3 — sin dependencias externas.
2. Reunión de G0 con el dossier; al volver, volcar D3/D4/D8 al plan (§1 y §4) y al capítulo I.
3. G1 (exports reales), RNF‑04 (anexo A), RNF‑07 (Linux) — dueño externo.
