# `data/telecom/fuentes/` — presupuestos ARENAZA estructurados

Sesión M1.1 del [PLAN_MULTIDOMINIO.md](../../../PLAN_MULTIDOMINIO.md). Esta carpeta guarda la
estructuración renglón a renglón de los dos presupuestos reales de ARENAZA (telecom), la
segunda línea base real de la tesis (la primera es el caso civil de la clínica,
`data/linea_base/`).

A diferencia de la carpeta `data/<dominio>/fuentes/` que describe
[`docs/protocolo_precios.md`](../../../docs/protocolo_precios.md) §1.3 (evidencia de campo de
cotizaciones sueltas: facturas, capturas, cotizaciones escaneadas), lo que se archiva aquí es la
transcripción completa de un presupuesto ya existente en el repositorio como evidencia primaria
(`data/samples/telecom/`), no una cotización nueva levantada en campo.

## Archivos

| Archivo | Contenido | Generado por |
|---|---|---|
| `presupuesto_1_arenaza.csv` | Los 14 renglones de la tabla "Presupuesto" de `Presupuesto_1_ARENAZA.pdf` (presupuesto 001) | `scripts/extraer_arenaza.py` |
| `presupuesto_2_arenaza.csv` | Los 26 renglones de la tabla "Presupuesto" de `Presupuesto_2_ARENAZA.pdf` (presupuesto 002) | `scripts/extraer_arenaza.py` |

**Cabecera exacta:** `renglon,descripcion,unidad,cantidad,precio_unitario,total,origen`, con
`origen = <pdf>:<pagina>:<renglon>` (página 1‑indexada: 1 = "Computos métricos", 2 =
"Presupuesto"; ambos PDF traen esas dos tablas por presupuesto).

**Vigencia:** ambos presupuestos están fechados **18/05/2026** en el propio PDF (presupuesto
001 y 002, "Computos métricos" 001 y 002). Es la fecha declarada de la fuente, no la fecha en
que se estructuró (2026‑09‑02).

**Totales verificados:** la suma de la columna `total` de `presupuesto_1_arenaza.csv` es
exactamente **1 109,29 USD**; la de `presupuesto_2_arenaza.csv`, exactamente **5 410,73 USD**.
Ambos coinciden con el renglón "TOTAL PRESUPUESTO" impreso en cada PDF. Ninguna fila fue omitida
ni ajustada para forzar el cierre: las 14 y 26 filas transcritas ya suman el total exacto (ver
`scripts/extraer_arenaza.py`, que además verifica programáticamente que cada total de renglón y
el total impreso aparecen en el texto extraído del PDF con PyMuPDF antes de escribir el CSV).

## Por qué se usa la tabla "Presupuesto" y no "Computos métricos"

Cada PDF trae dos tablas: "Computos métricos" (página 1: ítem, unidad, cantidad, sin precio) y
"Presupuesto" (página 2: ítem, unidad, cantidad, precio unitario, total). La cabecera exigida
por esta sesión (`...,precio_unitario,total,...`) solo la puede llenar la tabla "Presupuesto";
"Computos métricos" se usa exclusivamente para (a) completar una descripción que la tabla
"Presupuesto" trunca por ancho fijo de columna (por ejemplo "Switch Escritorio Gigabit De 10
Puertos" sin su sufijo "Con Poe De") y (b) registrar la discrepancia del tubo corrugado (ver
abajo).

`precio_unitario` viene vacío en el PDF cuando `cantidad = 1` (el precio unitario es idéntico al
total y el autor no lo repite): en ese caso el CSV completa `precio_unitario` con el mismo
importe de `total` (dividir entre 1 no cambia el valor; no es un precio inventado, es el mismo
dato ya impreso en la otra columna).

## La inconsistencia registrada: 80 m vs 90 m del tubo corrugado (presupuesto 2, ítem 5)

El renglón "Tubo Corrugado Flexible 1 Pulgada" del **presupuesto 2** trae:

- **80 m** en la tabla "Computos métricos" (página 1, ítem 5, unidad "Metros").
- **90 m** en la tabla "Presupuesto" (página 2, ítem 5: "Tubo Corrugado Flexible 1 Pulgada 30
  MTS", precio unitario 99,75, total 299,25).

Es la misma discrepancia dentro del **mismo PDF**, no un desacuerdo entre dos fuentes distintas.
Esta sesión la **registra tal cual, sin corregirla**: es la segunda inconsistencia de fuente
primaria que documenta la tesis (la primera son las siete de la línea base civil,
`docs/linea_base.md`). `presupuesto_2_arenaza.csv` usa 90 (el valor de la tabla "Presupuesto",
la única con precio y total); el fixture `tests/fixtures/presupuestos_arenaza.py` expone ambos
valores en `TUBO_CORRUGADO` (`cantidad_computos = 80`, `cantidad_presupuesto = 90`) para que la
Sesión M1.3 (auditoría telecom) los compare con una regla de verificación.

**Nota:** el **presupuesto 1** no tiene esta inconsistencia — su propio tubo corrugado trae 90 m
en ambas tablas (ítem 3 de "Computos métricos" e ítem 3 de "Presupuesto"). Solo el presupuesto 2
la presenta.

En ambos presupuestos, el precio unitario del tubo corrugado (99,75 USD) está cotizado **por
tubo de 30 m**, no por metro: el propio PDF anota el cálculo como "3\*99,75" (3 tubos × 30 m = 90
m = 299,25 USD). Por eso `cantidad × precio_unitario` no reproduce `total` con una
multiplicación literal en ese renglón (90 × 99,75 ≠ 299,25): es una unidad de precio compuesta,
no un error de transcripción de esta sesión, y se conserva tal cual en el CSV y el fixture.

## Reconciliación de la suma: sin renglones omitidos ni ajustados

Antes de estructurar el CSV se verificó que la suma de los renglones de la tabla "Presupuesto"
de cada PDF, tal como se imprimen (sin recalcular ningún `total`), cierra exactamente con el
"TOTAL PRESUPUESTO" del PDF:

- Presupuesto 1: 82,68 + 157,99 + 299,25 + 5,00 + 10,00 + 90,00 + 211,21 + 9,99 + 10,00 + 25,25
  + 7,92 + 90,00 + 10,00 + 100,00 (renglón "Micelaneos") = **1 109,29** ✓
- Presupuesto 2: suma de los 26 renglones de la tabla "Presupuesto" = **5 410,73** ✓

No hizo falta omitir ni ajustar ningún renglón: la cifra cuadra con las 14 y 26 filas completas.
Sí se encontraron, al verificar dígito a dígito, dos discrepancias **internas** de renglón (no
relacionadas con el cierre del total, que sí cuadra) en el presupuesto 2:

| Renglón | Descripción | Cantidad × precio unitario | Total impreso | Diferencia |
|---|---|---|---|---|
| 14 | Camara Bullet Ip 4mp Intemperie | 5 × 289,00 = 1 445,00 | 1 446,65 | 1,65 |
| 18 | Conector Jack Coupler Ubiquiti Rj45 | 7 × 42,99 = 300,93 | 303,93 | 3,00 |

Ninguna de las dos se corrige: se transcriben los tres valores (`cantidad`, `precio_unitario`,
`total`) tal como los imprime el PDF, y es `total` el que entra en la suma verificada (no una
recomputación de `cantidad × precio_unitario`). No son la inconsistencia que esta sesión debe
registrar (esa es el 80/90 del tubo corrugado), pero tampoco se ocultan: quedan anotadas aquí y
en el docstring de `scripts/extraer_arenaza.py` y de
`tests/fixtures/presupuestos_arenaza.py`, con el mismo criterio de trazabilidad total de
CLAUDE.md §2 que ya aplican las siete inconsistencias de la línea base civil.

## Otras diferencias entre "Computos métricos" y "Presupuesto" (presupuesto 2)

Ya señaladas, en general, por `docs/bitacora/2026-08-29-I5-telecom.md` y
`docs/bitacora/2026-09-02-M0.1-protocolo.md`.

Además del tubo corrugado, el presupuesto 2 tiene otras dos filas cuya cantidad no coincide
entre ambas tablas del mismo PDF ("Protector De Voltaje Exceline": 3 en Computos métricos vs 4
en Presupuesto; "Cajetin Superficial 4x2...": 10 en Computos métricos vs 5 en Presupuesto), y
dos ítems que solo aparecen en Computos métricos ("Face Plate Blanco 4x2 2 Puertos", "Keystone
Jack Coupler Inserto Cat6") sin renglón equivalente en la tabla "Presupuesto". No se investigan
ni corrigen en esta sesión (fuera de su alcance, que es registrar el 80/90 del tubo corrugado);
quedan anotadas para quien trabaje la Sesión M1.3 (auditoría telecom) o revise la fuente
primaria con más detalle.

## Regenerar los CSV

```
uv run --with pymupdf python scripts/extraer_arenaza.py
```

El script relee los dos PDF, vuelve a verificar cada total contra el texto extraído y sobre-
escribe ambos CSV. Si algún total no aparece en el texto de la página correspondiente (el PDF
cambió, o hay un error en la transcripción curada del script), se detiene con un error explícito
en vez de escribir un CSV no verificado.
