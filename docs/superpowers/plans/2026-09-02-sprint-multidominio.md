# Sprint Multidominio (M0–M4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ejecutar las 11 sesiones del PLAN_MULTIDOMINIO (M0.1–M4.2) más la meta del sprint: telecom, industrial y sistemas entran por la misma puerta que civil — catálogo, presupuesto auditado y lista de precios real y fechada — sin tocar `core/`.

**Architecture:** Trabajo de datos y adaptadores sobre un núcleo cerrado: evidencia primaria en `data/`, un fixture único por dominio en `tests/fixtures/`, capa de catálogo/seed por dominio en `scripts/`, verificación con las reglas R1–R7 existentes, listas de precios por UC‑02 (`core.catalog.precios`). Compuertas GM1–GM4 con degradaciones declaradas (GM2 usa la referencia MaPreX como proxy; GM3 usa el tabulador CIV ya en el repo).

**Tech Stack:** Python 3.12 + uv, pytest (`-W error`), ruff, SQLAlchemy/SQLite (catálogo), PyMuPDF solo en scripts de extracción (vía `uv run --with pymupdf`), Decimal en todo número.

**Spec:** `PLAN_MULTIDOMINIO.md` (sesiones y compuertas) + `CLAUDE.md` (constitución: §2 principios, §4 cálculo, §5 contratos, §7 reglas). Ante conflicto, manda CLAUDE.md.

## Global Constraints

- `Decimal` para todo lo monetario y dimensional; nunca `float`; redondear solo al presentar (CLAUDE.md §2.3).
- `git diff m-base --stat -- core/` DEBE estar vacío al cierre de cada tarea; los adaptadores solo importan `core.contracts` (lo vigila `tests/unit/test_arquitectura.py`).
- Prohibido modificar pruebas existentes para ponerlas en verde.
- **Prohibido editar estos archivos en todo el sprint** (tienen cambios sin commitear del usuario en el checkout principal): `CLAUDE.md`, `README.md`, `docs/README.md`, `docs/linea_base.md`, `docs/tesis/**`. Si una sesión pide tocarlos, se anota el pendiente en la bitácora de la sesión y NO se edita.
- Ningún precio ni cita inventados: cada precio lleva `origen` (archivo + Ref/renglón) y `fecha_vigencia`; todo supuesto sin fuente se marca literalmente `SUPUESTO (pendiente validacion del autor)` en el archivo que lo use.
- Tasa única de conversión: `Decimal("633.3644")` Bs/USD, fecha 01/07/2026 (declarada dentro del listado MO de MaPreX). `precio_usd = (precio_bs / tasa)` cuantizado a `Decimal("0.0001")` con `ROUND_HALF_UP`.
- Anclas numéricas exactas: presupuesto ARENAZA 1 = `Decimal("1109.29")` (14 renglones); ARENAZA 2 = `Decimal("5410.73")` (26 renglones); tubo corrugado: 80 m en cómputos vs 90 m en presupuesto (presupuesto 2); tabulador CIV = 43 filas; tolerancia de reproducción de totales ± `Decimal("0.01")`.
- Fechas de vigencia MaPreX: materiales y equipos `2026-07-09`; mano de obra `2026-07-01`.
- PyMuPDF no es dependencia del proyecto: los scripts de extracción se ejecutan con `uv run --with pymupdf python scripts/<script>.py` y lo documentan en su docstring; NINGUNA prueba importa `fitz`/`pymupdf`.
- Código, docstrings y commits en español; identificadores y asuntos de commit sin tildes; Conventional Commits.
- Cada sesión M cierra con: `uv run pytest` verde, `uv run ruff check .` limpio, bitácora `docs/bitacora/2026-09-02-<id>.md` y el commit indicado en su tarea.
- Idioma de todo lo generado: español.

---

### Task 1: Meta del sprint multidominio

**Files:**
- Create: `scripts/meta_multidominio.py`
- Test: ninguno nuevo (el script ES el verificador; se ejecuta a mano)

**Interfaces:**
- Consumes: `scripts/meta_alpha.py` (función `_evaluar(metas=...)` parametrizable) y `scripts/meta_i6.py` (el patrón a espejar).
- Produces: `uv run python scripts/meta_multidominio.py` imprime N/12 metas y sale con código 0 solo si 12/12.

**Lecturas obligatorias antes de escribir:** `scripts/meta_i6.py`, `scripts/meta_alpha.py`, `PLAN_MULTIDOMINIO.md` (secciones 2 y Resumen).

- [ ] **Step 1: Escribir `scripts/meta_multidominio.py`** espejo de `meta_i6.py`, con estas 12 metas (cada una una función que devuelve bool + descripción):
  1. `docs/protocolo_precios.md` existe y contiene las cuatro secciones de dominio (civil, telecom, industrial, sistemas).
  2. Las cuatro plantillas `data/<dominio>/plantilla_precios.csv` existen (dominios: civil, telecom, industrial, sistemas).
  3. Los cuatro CSV de referencia MaPreX existen en `data/precios/maprex_2026-07/` (`referencia_civil.csv`, `referencia_telecom.csv`, `referencia_industrial.csv`, `referencia_sistemas.csv`) y toda fila tiene `ref_maprex` y `archivo` no vacíos.
  4. `data/telecom/fuentes/presupuesto_1_arenaza.csv` y `presupuesto_2_arenaza.csv` existen y sus totales suman exactamente 1109.29 y 5410.73.
  5. `tests/fixtures/presupuestos_arenaza.py` existe y registra la discrepancia 80/90 del tubo corrugado.
  6. `tests/integration/test_presupuesto_arenaza.py` pasa (reproducción ± 0.01).
  7. La auditoría telecom detecta el hallazgo 80/90 (pasa `tests/integration/test_auditoria_arenaza.py`).
  8. Presupuesto industrial: fixture `tests/fixtures/mantenimiento_industrial.py` con ≥ 3 partidas MNT-* y su prueba de integración verde.
  9. Presupuesto sistemas: fixture `tests/fixtures/tarifas_sistemas.py` y su prueba de integración verde.
  10. `docs/resultados_ml.md` contiene conteos por dominio regenerados (busca la cadena `telecom` y una tabla de conteos).
  11. `git diff m-base --stat -- core/` vacío.
  12. `uv run ruff check .` limpio.
  Para las metas que ejecutan pytest, invocar pytest por subproceso sobre el archivo concreto (como haga `meta_i6.py`; espejar su mecánica exacta).
- [ ] **Step 2: Ejecutarlo** — `uv run python scripts/meta_multidominio.py`. Esperado: la mayoría de metas en rojo (0–2/12): el sprint recién empieza. El script corre sin excepciones.
- [ ] **Step 3: `uv run ruff check .` limpio.**
- [ ] **Step 4: Commit**

```bash
git add scripts/meta_multidominio.py docs/superpowers/plans/2026-09-02-sprint-multidominio.md
git commit -m "feat(scripts): meta del sprint multidominio"
```

---

### Task 2: Sesión M0.1 — Protocolo de levantamiento de precios

**Files:**
- Create: `docs/protocolo_precios.md`
- Create: `data/civil/plantilla_precios.csv`, `data/telecom/plantilla_precios.csv`, `data/industrial/plantilla_precios.csv`, `data/sistemas/plantilla_precios.csv`

**Interfaces:**
- Consumes: catálogos existentes — insumos civil en `tests/fixtures/apu_linea_base.py`; telecom en `data/samples/telecom/` (los dos PDF ARENAZA y `topologia_arenaza.csv`); industrial en `data/samples/industrial/activos_planta.csv`; sistemas en `data/samples/sistemas/alcance_funcional.csv`.
- Produces: plantillas con columnas `tipo,insumo,unidad,precio,fecha,fuente,evidencia` listas para llenar en campo; el protocolo que M0.2–M3.2 citan.

**Lecturas obligatorias:** `PLAN_MULTIDOMINIO.md` (Sesión M0.1 y principios 1–5), `data/precios/maprex_2026-07/README.md`, `data/samples/*/README.md`, `docs/dossier_g0.md` (solo la decisión sobre fuente del FCAS).

- [ ] **Step 1: Escribir `docs/protocolo_precios.md`** con: (a) procedimiento común (mínimo 2 fuentes por insumo cuando sea posible; qué evidencia se guarda y dónde — `data/<dominio>/fuentes/`, transversal en `data/precios/`; registro de fecha y tasa BCV del día; formato canónico de salida de UC‑02 `tipo,insumo,unidad,precio`); (b) catálogo de fuentes por dominio con forma de acceso y cita (civil: MaPreX/Lulowin, cotizaciones, convención colectiva; telecom: distribuidores + ARENAZA + MaPreX; industrial: cotizaciones de repuestos/servicios + MaPreX como proxy; sistemas: tabulador CIV vía MaPreX + encuesta TI + ISBSG para HH/PF); (c) anexo: borrador de carta de solicitud de acceso académico continuo a MaPreX/Lulowin para firma del tutor (los listados de julio 2026 ya están en el repo; la carta pide la serie mensual).
- [ ] **Step 2: Crear las cuatro plantillas** `data/<dominio>/plantilla_precios.csv` con cabecera `tipo,insumo,unidad,precio,fecha,fuente,evidencia` y una fila por insumo que ese dominio necesita (civil: los insumos exactos de `apu_linea_base.py`; telecom: los renglones de los PDF ARENAZA; industrial: repuestos/servicios plausibles por activo de `activos_planta.csv`, marcados como lista tentativa; sistemas: roles del APU por punto de función), con las columnas de precio VACÍAS (se llenan en campo).
- [ ] **Step 3: Verificar** — `uv run pytest` verde (nada de código tocado), `uv run ruff check .` limpio.
- [ ] **Step 4: Escribir bitácora** `docs/bitacora/2026-09-02-M0.1-protocolo.md` (qué se creó, decisiones, siguiente sesión).
- [ ] **Step 5: Commit**

```bash
git add docs/protocolo_precios.md data/civil/ data/telecom/plantilla_precios.csv data/industrial/plantilla_precios.csv data/sistemas/plantilla_precios.csv docs/bitacora/2026-09-02-M0.1-protocolo.md
git commit -m "docs(datos): protocolo de levantamiento de precios multidominio"
```

---

### Task 3: Sesión M0.2 — Referencia MaPreX estructurada por dominio

**Files:**
- Create: `scripts/extraer_maprex.py` (extracción asistida; se ejecuta con `uv run --with pymupdf python scripts/extraer_maprex.py`)
- Create: `data/precios/maprex_2026-07/referencia_civil.csv`, `referencia_telecom.csv`, `referencia_industrial.csv`, `referencia_sistemas.csv`
- Modify: `data/precios/maprex_2026-07/README.md` (añadir: tabla de factores de depreciación de los equipos de la línea base + par jornal/bono del tabulador construcción + descripción de los CSV)
- Test: `tests/unit/test_referencia_maprex.py`

**Interfaces:**
- Consumes: los tres PDF de `data/precios/maprex_2026-07/`; los insumos de `tests/fixtures/apu_linea_base.py`; los renglones ARENAZA (PDFs en `data/samples/telecom/`); activos de `data/samples/industrial/activos_planta.csv`.
- Produces: CSV de referencia con cabecera EXACTA `tipo,insumo,unidad,precio_bs,bono_bs,factor_depreciacion,precio_usd,fecha_vigencia,archivo,ref_maprex,notas` (columnas no aplicables vacías). `referencia_sistemas.csv` = las 43 filas del tabulador CIV. Tarea 6 usa `referencia_telecom.csv` como lista 2; Tareas 7–8 usan `referencia_industrial.csv`; Tareas 9–10 usan `referencia_sistemas.csv`.

**Lecturas obligatorias:** `data/precios/maprex_2026-07/README.md` (reglas de uso), `PLAN_MULTIDOMINIO.md` (Sesión M0.2), `tests/fixtures/apu_linea_base.py`.

- [ ] **Step 1: Escribir la prueba** `tests/unit/test_referencia_maprex.py` (fallará: los CSV no existen):

```python
"""Verifica los CSV de referencia MaPreX: formato, conversion y procedencia."""
import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

CARPETA = Path("data/precios/maprex_2026-07")
ARCHIVOS = ["referencia_civil.csv", "referencia_telecom.csv",
            "referencia_industrial.csv", "referencia_sistemas.csv"]
TASA = Decimal("633.3644")
CABECERA = ["tipo", "insumo", "unidad", "precio_bs", "bono_bs", "factor_depreciacion",
            "precio_usd", "fecha_vigencia", "archivo", "ref_maprex", "notas"]


def _filas(nombre):
    with open(CARPETA / nombre, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        assert lector.fieldnames == CABECERA
        return list(lector)


def test_archivos_existen_y_no_vacios():
    for nombre in ARCHIVOS:
        assert len(_filas(nombre)) > 0


def test_conversion_usd_con_tasa_declarada():
    for nombre in ARCHIVOS:
        for fila in _filas(nombre):
            esperado = (Decimal(fila["precio_bs"]) / TASA).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP)
            assert Decimal(fila["precio_usd"]) == esperado, f"{nombre}: {fila['insumo']}"


def test_procedencia_completa():
    for nombre in ARCHIVOS:
        for fila in _filas(nombre):
            assert fila["ref_maprex"], f"{nombre}: {fila['insumo']} sin ref"
            assert fila["archivo"] in {"materiales.pdf", "equipos.pdf", "mano_de_obra.pdf"}
            assert fila["fecha_vigencia"] in {"2026-07-09", "2026-07-01"}
            assert fila["tipo"] in {"material", "equipo", "mano_obra"}


def test_tabulador_civ_completo():
    assert len(_filas("referencia_sistemas.csv")) == 43


def test_equipos_llevan_factor_de_depreciacion():
    for nombre in ARCHIVOS:
        for fila in _filas(nombre):
            if fila["archivo"] == "equipos.pdf":
                factor = Decimal(fila["factor_depreciacion"])
                assert Decimal("0") < factor <= Decimal("1")
```

- [ ] **Step 2: Correr la prueba** — `uv run pytest tests/unit/test_referencia_maprex.py -v`. Esperado: FAIL (archivos inexistentes).
- [ ] **Step 3: Escribir `scripts/extraer_maprex.py`** — busca en los PDF por términos/Ref y emite candidatos de fila; el docstring documenta `uv run --with pymupdf python scripts/extraer_maprex.py`. Alcance de cada CSV: civil = solo insumos que aparecen en `apu_linea_base.py` (buscar equivalentes MaPreX de cada material, equipo y rol de MO de las 5 partidas; si un insumo no tiene equivalente claro, fila en `notas` con `sin equivalente claro` y precio del candidato más cercano NO incluido — mejor omitir que adivinar); telecom = renglones comparables con los de ARENAZA (cable UTP, fibra, tubo corrugado, conectores, racks, etc.); industrial = repuestos/servicios aplicables a los activos de `activos_planta.csv` (rodamientos, correas, válvulas, aceites, servicio de mecánico); sistemas = las 43 filas del tabulador CIV (agrupación `TAB CIV`), tipo `mano_obra`, `precio_bs` = jornal, `bono_bs` = bono.
- [ ] **Step 4: Generar los CSV y VERIFICAR CADA FILA** contra el texto del PDF (releer la página con el script y comparar Ref, descripción, unidad y precio dígito a dígito). Toda fila dudosa se elimina o se marca en `notas`. Registrar en la bitácora cuántas filas por CSV y cuáles requieren revisión del autor.
- [ ] **Step 5: Correr la prueba** — `uv run pytest tests/unit/test_referencia_maprex.py -v`. Esperado: PASS.
- [ ] **Step 6: Actualizar el README de la carpeta** — sección nueva «CSV de referencia» (cabecera y alcance de cada CSV), tabla «Depreciación MaPreX de los equipos de la línea base» (equipo ↔ Ref ↔ factor) y párrafo «Jornal + bono del tabulador construcción» (valores exactos, para la decisión FCAS del dossier G0).
- [ ] **Step 7: Suite completa + ruff** — `uv run pytest` y `uv run ruff check .`. Verde/limpio.
- [ ] **Step 8: Bitácora** `docs/bitacora/2026-09-02-M0.2-referencia-maprex.md` (conteos por CSV, filas dudosas para el autor, decisiones).
- [ ] **Step 9: Commit**

```bash
git add scripts/extraer_maprex.py data/precios/maprex_2026-07/ tests/unit/test_referencia_maprex.py docs/bitacora/2026-09-02-M0.2-referencia-maprex.md
git commit -m "feat(datos): referencia maprex julio 2026 estructurada por dominio"
```

---

### Task 4: Sesión M1.1 — Fuentes ARENAZA estructuradas

**Files:**
- Create: `data/telecom/fuentes/presupuesto_1_arenaza.csv`, `data/telecom/fuentes/presupuesto_2_arenaza.csv`, `data/telecom/fuentes/README.md`
- Create: `tests/fixtures/presupuestos_arenaza.py`
- Create: `scripts/extraer_arenaza.py` (mismo contrato PyMuPDF que Task 3)
- Test: `tests/unit/test_fuentes_arenaza.py`

**Interfaces:**
- Consumes: `data/samples/telecom/Presupuesto_1_ARENAZA.pdf` y `Presupuesto_2_ARENAZA.pdf` (evidencia primaria, 14 + 26 renglones).
- Produces: CSV con cabecera EXACTA `renglon,descripcion,unidad,cantidad,precio_unitario,total,origen` (origen = `<pdf>:<pagina>:<renglon>`); fixture `presupuestos_arenaza.py` que expone `PRESUPUESTO_1`, `PRESUPUESTO_2` (listas de dataclasses o dicts con Decimal), `TOTAL_1 = Decimal("1109.29")`, `TOTAL_2 = Decimal("5410.73")` y `TUBO_CORRUGADO = {"cantidad_computos": Decimal("80"), "cantidad_presupuesto": Decimal("90")}` — la inconsistencia REGISTRADA tal cual, no corregida. Task 5 importa este fixture.

**Lecturas obligatorias:** `docs/bitacora/2026-08-29-I5-telecom.md` (los hallazgos, en especial el 1 y el de 80/90 m), `tests/fixtures/apu_linea_base.py` (el patrón de fixture), `PLAN_MULTIDOMINIO.md` (Sesión M1.1).

- [ ] **Step 1: Escribir la prueba** `tests/unit/test_fuentes_arenaza.py` (falla: nada existe):

```python
"""Los CSV ARENAZA suman exactamente los totales de cada PDF y registran el 80/90."""
import csv
from decimal import Decimal
from pathlib import Path

from tests.fixtures.presupuestos_arenaza import (
    PRESUPUESTO_1, PRESUPUESTO_2, TOTAL_1, TOTAL_2, TUBO_CORRUGADO)

CARPETA = Path("data/telecom/fuentes")


def _total_csv(nombre):
    with open(CARPETA / nombre, newline="", encoding="utf-8") as f:
        return sum(Decimal(fila["total"]) for fila in csv.DictReader(f))


def test_totales_exactos():
    assert TOTAL_1 == Decimal("1109.29")
    assert TOTAL_2 == Decimal("5410.73")
    assert _total_csv("presupuesto_1_arenaza.csv") == TOTAL_1
    assert _total_csv("presupuesto_2_arenaza.csv") == TOTAL_2


def test_conteo_renglones():
    assert len(PRESUPUESTO_1) == 14
    assert len(PRESUPUESTO_2) == 26


def test_inconsistencia_80_90_registrada():
    assert TUBO_CORRUGADO["cantidad_computos"] == Decimal("80")
    assert TUBO_CORRUGADO["cantidad_presupuesto"] == Decimal("90")


def test_fixture_coincide_con_csv():
    for renglones, nombre in [(PRESUPUESTO_1, "presupuesto_1_arenaza.csv"),
                              (PRESUPUESTO_2, "presupuesto_2_arenaza.csv")]:
        assert sum(r.total for r in renglones) == _total_csv(nombre)
```

(Si el fixture usa dicts en vez de dataclasses, ajustar `r.total` a `r["total"]` — decisión del implementador, documentada en el fixture.)

- [ ] **Step 2: Correr y ver FAIL.**
- [ ] **Step 3: Escribir `scripts/extraer_arenaza.py`**, volcar los renglones, y VERIFICAR CADA FILA contra el PDF (dígito a dígito: descripción, unidad, cantidad, precio, total). Si la suma de renglones no da el total del PDF, investigar antes de seguir (renglón omitido o redondeo del PDF); documentar en el README de la carpeta lo encontrado.
- [ ] **Step 4: Escribir el fixture** `tests/fixtures/presupuestos_arenaza.py` (única copia estructurada; el CSV es la forma tabular de la MISMA información y se genera desde el fixture o se verifica contra él — elegir una dirección y documentarla en el docstring).
- [ ] **Step 5: Correr la prueba — PASS. Suite completa + ruff.**
- [ ] **Step 6: Bitácora** `docs/bitacora/2026-09-02-M1.1-fuentes-arenaza.md`.
- [ ] **Step 7: Commit**

```bash
git add data/telecom/fuentes/ tests/fixtures/presupuestos_arenaza.py tests/unit/test_fuentes_arenaza.py scripts/extraer_arenaza.py docs/bitacora/2026-09-02-M1.1-fuentes-arenaza.md
git commit -m "feat(telecom): fuentes arenaza estructuradas con su inconsistencia registrada"
```

---

### Task 5: Sesión M1.2 — Catálogo y costeo telecom (reproducción ± 0,01)

**Files:**
- Create: `scripts/seed_telecom.py` (la capa que arma composiciones vive en el script/fixture — NADA se crea en `core/`)
- Test: `tests/integration/test_presupuesto_arenaza.py`

**Interfaces:**
- Consumes: `tests/fixtures/presupuestos_arenaza.py` (Task 4); `core.contracts.apu` (`ComposicionAPU`, `LineaMaterial`, `LineaManoObra`, `ParametrosCosto`); `core.costing.calcular_apu`; el patrón de `scripts/seed.py` y `core/catalog/` para persistir.
- Produces: catálogo telecom en SQLite (partidas TC-*) y la función/es del seed que Task 6 reutiliza para armar el `Presupuesto` telecom.

**Lecturas obligatorias:** `docs/bitacora/2026-08-29-I5-telecom.md` **hallazgo 1, opción 1** (política «mano de obra = 50 % del total» → `LineaManoObra` sintética que arma la capa de catálogo ANTES de llamar al motor; el motor puro NO cambia — espejar exactamente esa opción), `scripts/seed.py`, `core/catalog/` (API de carga/consulta), `tests/integration/` (patrón de pruebas con SQLite).

- [ ] **Step 1: Escribir la prueba de integración** `tests/integration/test_presupuesto_arenaza.py`: carga el catálogo telecom (vía el seed), arma el presupuesto de cada PDF desde el catálogo y afirma `abs(total_reproducido - TOTAL_N) <= Decimal("0.01")` para ambos presupuestos, más una aserción por partida TC-* de que su precio unitario coincide con el del fixture ± 0.01. Correr: FAIL.
- [ ] **Step 2: Escribir `scripts/seed_telecom.py`** importando el fixture (DRY: los números viven SOLO en el fixture). Composiciones TC-*: materiales con precios reales ARENAZA; equipos según los renglones que correspondan; la MO del 50 % como línea sintética construida por la capa de catálogo (opción 1). Documentar en docstring el mapeo renglón→composición y todo supuesto.
- [ ] **Step 3: Correr la prueba — PASS (± 0.01 exacto).** Si no reproduce, el error está en el mapeo o la política de MO; NO tocar `core/`, NO aflojar la tolerancia.
- [ ] **Step 4: Suite completa + ruff + `git diff m-base --stat -- core/` vacío.**
- [ ] **Step 5: Bitácora** `docs/bitacora/2026-09-02-M1.2-catalogo-telecom.md` (mapeo, supuestos, momento clave del plan: segunda línea base reproducida).
- [ ] **Step 6: Commit**

```bash
git add scripts/seed_telecom.py tests/integration/test_presupuesto_arenaza.py docs/bitacora/2026-09-02-M1.2-catalogo-telecom.md
git commit -m "feat(telecom): catalogo y presupuesto arenaza reproducido desde sqlite"
```

---

### Task 6: Sesión M1.3 — Auditoría telecom + UC‑02 real (compuerta GM1)

**Files:**
- Create: `data/telecom/fuentes/lista_arenaza.csv` (lista 1, canónica UC‑02: `tipo,insumo,unidad,precio`; fecha del PDF ARENAZA declarada en el README) y `data/telecom/fuentes/lista_maprex_2026-07.csv` (lista 2, derivada de `referencia_telecom.csv` de Task 3, solo columnas canónicas)
- Test: `tests/integration/test_auditoria_arenaza.py`
- Modify: `data/telecom/fuentes/README.md` (documentar ambas listas y su vigencia)

**Interfaces:**
- Consumes: el presupuesto telecom armado en Task 5; `core/verification/` (las siete reglas y el informe); `core.catalog.precios.leer_lista_precios` y el flujo UC‑02 existente (ver `tests/integration/test_actualizacion_precios.py` como patrón).
- Produces: GM1 CRUZADA — el hallazgo 80/90 con sus `origen_id`; primer histórico de `CambioPrecio` real fuera de civil.

**Lecturas obligatorias:** `core/verification/` (qué regla corresponde a una cantidad de cómputos que no coincide con el presupuesto — se espera R1 o R7; usar la que las reglas existentes dicten SIN modificarlas), `tests/unit/test_reglas_civil.py` (patrón de aserción de hallazgos), `tests/integration/test_actualizacion_precios.py`.

- [ ] **Step 1: Escribir la prueba** `tests/integration/test_auditoria_arenaza.py`: (a) auditar el presupuesto telecom completo; (b) afirmar que existe EXACTAMENTE un hallazgo cuya descripción u origen involucra el tubo corrugado con 80 vs 90 y que sus `origen_id` no están vacíos; (c) afirmar que R5 (balance volumétrico civil) reporta INFO/sin datos y NO un error (comportamiento RF‑23 correcto); (d) cargar `lista_arenaza.csv` y luego `lista_maprex_2026-07.csv` por UC‑02 y afirmar que se genera al menos un `CambioPrecio` con las dos fechas correctas. Correr: FAIL.
- [ ] **Step 2: Generar las dos listas canónicas** (lista 2 derivada por script corto o a mano desde `referencia_telecom.csv`; documentar correspondencia insumo ARENAZA ↔ insumo MaPreX en el README — solo insumos con equivalencia defendible; los demás quedan fuera y anotados).
- [ ] **Step 3: Hacer pasar la prueba** ajustando SOLO datos, seed o la prueba de detalles (nunca `core/`). Si ninguna regla existente detecta el 80/90, NO crear reglas nuevas en core: registrar el hallazgo en la bitácora como limitación y ajustar la aserción (b) a lo que las reglas sí reportan, dejando el hallazgo documental. — Esto es un fallback; el resultado esperado es que R1/R7 lo detecten.
- [ ] **Step 4: Suite + ruff + core intacto.**
- [ ] **Step 5: Bitácora** `docs/bitacora/2026-09-02-M1.3-auditoria-telecom.md`: declarar **GM1 CRUZADA** (o qué faltó), qué reglas aplican y cuáles reportan INFO, el histórico UC‑02.
- [ ] **Step 6: Commit**

```bash
git add data/telecom/fuentes/ tests/integration/test_auditoria_arenaza.py docs/bitacora/2026-09-02-M1.3-auditoria-telecom.md
git commit -m "feat(telecom): auditoria arenaza y actualizacion de precios reales"
```

---

### Task 7: Sesión M2.1 — Catálogo industrial con referencia MaPreX (degradación GM2)

**Files:**
- Create: `tests/fixtures/mantenimiento_industrial.py`, `data/industrial/fuentes/README.md`, `data/industrial/fuentes/lista_maprex_2026-07.csv` (canónica UC‑02)
- Test: `tests/unit/test_mantenimiento_industrial.py`

**Interfaces:**
- Consumes: `data/samples/industrial/activos_planta.csv` (elegir ≥ 3 activos); `referencia_industrial.csv` (Task 3) como fuente de precios; `core.contracts.apu`.
- Produces: fixture con ≥ 3 composiciones MNT-* (repuestos = materiales, servicio/herramienta = equipos, técnico = mano de obra con tarifa del tabulador MaPreX), cada línea con nota de origen (Ref MaPreX). Task 8 lo importa.

**Lecturas obligatorias:** `docs/bitacora/2026-08-29-I5-industrial.md`, `adapters/industrial/adaptador.py` (qué produce el adaptador: códigos de partida, unidades), `tests/fixtures/apu_linea_base.py` (patrón), `PLAN_MULTIDOMINIO.md` (GM2 y su degradación).

- [ ] **Step 1: DECLARAR LA DEGRADACIÓN** primero, en `data/industrial/fuentes/README.md`: «No llegaron cotizaciones de campo; los precios provienen de la referencia nacional MaPreX julio 2026 (proxy fechado, degradación GM2 declarada según PLAN_MULTIDOMINIO §2). Cada precio cita archivo + Ref. Supuestos de alcance de cada intervención listados abajo.»
- [ ] **Step 2: Escribir la prueba** `tests/unit/test_mantenimiento_industrial.py`: el fixture expone ≥ 3 composiciones MNT-*; toda línea tiene precio > 0 con `Decimal`; `calcular_apu(composicion, ParametrosCosto())` devuelve un precio unitario > 0 y estable (aserción de regresión: fijar el valor exacto tras el primer cálculo verificado a mano — el implementador calcula una composición a mano con la fórmula de CLAUDE.md §4 y fija ese número como esperado). Correr: FAIL.
- [ ] **Step 3: Escribir el fixture** con los precios de `referencia_industrial.csv` (importar/leer el CSV o transcribir con Ref citada en comentario — elegir y documentar; DRY: si transcribe, una prueba compara fixture vs CSV).
- [ ] **Step 4: PASS + lista canónica** `lista_maprex_2026-07.csv` industrial para UC‑02 (Task 8 la usa).
- [ ] **Step 5: Suite + ruff + core intacto.**
- [ ] **Step 6: Bitácora** `docs/bitacora/2026-09-02-M2.1-catalogo-industrial.md` (degradación declarada, activos elegidos, supuestos).
- [ ] **Step 7: Commit**

```bash
git add tests/fixtures/mantenimiento_industrial.py tests/unit/test_mantenimiento_industrial.py data/industrial/ docs/bitacora/2026-09-02-M2.1-catalogo-industrial.md
git commit -m "feat(industrial): catalogo de mantenimiento con referencia maprex declarada"
```

---

### Task 8: Sesión M2.2 — Presupuesto industrial de extremo a extremo (compuerta GM2)

**Files:**
- Create: `scripts/seed_industrial.py`
- Test: `tests/integration/test_presupuesto_industrial.py`

**Interfaces:**
- Consumes: `adapters.industrial` (`AdaptadorIndustrial.extraer()` → `ItemComputo` con `frecuencia_anual × horizonte_anios`); fixture de Task 7; `core/budget/` (armar presupuesto), `core/verification/` (auditar), UC‑02 con la lista industrial de Task 7.
- Produces: GM2 declarada CRUZADA-CON-DEGRADACIÓN en la bitácora; presupuesto de mantenimiento auditado con ≥ 3 activos.

**Lecturas obligatorias:** `adapters/industrial/adaptador.py` y su prueba `tests/unit/test_adapter_industrial.py`; `tests/integration/` (patrón de flujo completo civil); `core/budget/` API.

- [ ] **Step 1: Escribir la prueba de integración**: adaptador extrae ítems de `activos_planta.csv` → presupuesto costeado desde el catálogo (seed de Task 7 vía `scripts/seed_industrial.py`) → (a) total > 0 y estable (regresión con valor fijado tras verificación manual); (b) la auditoría corre y R1 verifica la cantidad = `frecuencia_anual × horizonte_anios` (si los ítems traen la regla declarada — espejar cómo civil declara `regla` en `ItemComputo`); (c) UC‑02 carga la lista industrial y genera histórico. Correr: FAIL.
- [ ] **Step 2: Escribir `scripts/seed_industrial.py`** (patrón de `seed_telecom.py`).
- [ ] **Step 3: PASS. Suite + ruff + core intacto.**
- [ ] **Step 4: Bitácora** `docs/bitacora/2026-09-02-M2.2-presupuesto-industrial.md`: **GM2 CRUZADA con degradación declarada** (proxy MaPreX; qué falta para cruzarla con cotizaciones: la ronda de campo del autor).
- [ ] **Step 5: Commit**

```bash
git add scripts/seed_industrial.py tests/integration/test_presupuesto_industrial.py docs/bitacora/2026-09-02-M2.2-presupuesto-industrial.md
git commit -m "feat(industrial): presupuesto de mantenimiento auditado con degradacion gm2 declarada"
```

---

### Task 9: Sesión M3.1 — Tarifas sistemas con el tabulador CIV

**Files:**
- Create: `tests/fixtures/tarifas_sistemas.py`, `data/sistemas/fuentes/README.md`, `data/sistemas/fuentes/lista_tarifas_2026-07.csv` (canónica UC‑02)
- Test: `tests/unit/test_tarifas_sistemas.py`

**Interfaces:**
- Consumes: `referencia_sistemas.csv` (Task 3, las 43 filas TAB CIV); `core.contracts.apu`.
- Produces: fixture con tarifas HH por rol y composiciones SI-* (APU de un punto de función por módulo = horas de cada rol × tarifa). Task 10 lo importa.

**Lecturas obligatorias:** `docs/bitacora/2026-08-29-I5-sistemas.md`, `adapters/sistemas/adaptador.py` (regla IFPUG, unidad `pf`), `data/samples/sistemas/README.md`.

- [ ] **Step 1: Documentar los supuestos en `data/sistemas/fuentes/README.md`** ANTES del código: (a) conversión jornal→HH: `tarifa_hh = jornal_bs / 8` horas, convertida a USD con la tasa única (supuesto declarado: jornada de 8 h); (b) correspondencia rol del APU ↔ fila del tabulador (p. ej. analista ↔ `INGENIERO P-5 CIV ANALISTA...`, desarrollador ↔ `INGENIERO COMPUTISTA P-9...`, líder ↔ `GERENTE DE PROYECTOS...` — el implementador elige filas EXISTENTES en el CSV y las cita por Ref); (c) productividad HH/PF: valor de benchmark declarado con esta redacción literal: «SUPUESTO (pendiente validacion del autor): X HH/PF, rango tipico reportado por benchmarks de la industria (ISBSG); la cita definitiva la fija el autor en el marco teorico» — elegir X dentro de 6–12 HH/PF y NO citar un paper concreto (prohibido inventar citas).
- [ ] **Step 2: Escribir la prueba** `tests/unit/test_tarifas_sistemas.py`: fixture expone tarifas por rol (Decimal, USD, > 0, con Ref del tabulador) y ≥ 1 composición SI-* cuyo `calcular_apu` da un precio unitario fijado por regresión (verificado a mano con la fórmula §4). Correr: FAIL.
- [ ] **Step 3: Escribir el fixture — PASS.**
- [ ] **Step 4: Lista canónica** `lista_tarifas_2026-07.csv` para UC‑02.
- [ ] **Step 5: Suite + ruff + core intacto.**
- [ ] **Step 6: Bitácora** `docs/bitacora/2026-09-02-M3.1-tarifas-sistemas.md`.
- [ ] **Step 7: Commit**

```bash
git add tests/fixtures/tarifas_sistemas.py tests/unit/test_tarifas_sistemas.py data/sistemas/ docs/bitacora/2026-09-02-M3.1-tarifas-sistemas.md
git commit -m "feat(sistemas): tarifas del tabulador civ y apu por punto de funcion"
```

---

### Task 10: Sesión M3.2 — Presupuesto de sistemas de extremo a extremo (compuerta GM3)

**Files:**
- Create: `scripts/seed_sistemas.py`
- Test: `tests/integration/test_presupuesto_sistemas.py`

**Interfaces:**
- Consumes: `adapters.sistemas` (PF por caso de uso, regla IFPUG trazable); fixture de Task 9; `core/budget/`, `core/verification/`, UC‑02.
- Produces: GM3 CRUZADA (tarifas con fuente: tabulador CIV jul‑2026).

**Lecturas obligatorias:** `adapters/sistemas/adaptador.py` + `tests/unit/test_adapter_sistemas.py`; Task 8 como patrón de flujo.

- [ ] **Step 1: Prueba de integración**: adaptador extrae PF de `alcance_funcional.csv` → presupuesto costeado → (a) total estable por regresión (verificado a mano); (b) auditoría: R1 reevalúa la regla de puntos de función y R3 acepta la unidad `pf` (documentada — verificar cómo `core.contracts.unidades` la trata; si `pf` no es unidad conocida, usar la unidad que el adaptador YA emite; nunca tocar `core/contracts/unidades.py`); (c) UC‑02 con `lista_tarifas_2026-07.csv`. Correr: FAIL.
- [ ] **Step 2: `scripts/seed_sistemas.py`** (patrón de los seeds anteriores).
- [ ] **Step 3: PASS. Suite + ruff + core intacto.**
- [ ] **Step 4: Bitácora** `docs/bitacora/2026-09-02-M3.2-presupuesto-sistemas.md`: **GM3 CRUZADA** (tarifas con fuente; productividad = supuesto declarado pendiente de cita del autor).
- [ ] **Step 5: Commit**

```bash
git add scripts/seed_sistemas.py tests/integration/test_presupuesto_sistemas.py docs/bitacora/2026-09-02-M3.2-presupuesto-sistemas.md
git commit -m "feat(sistemas): presupuesto por puntos de funcion con tarifas del tabulador"
```

---

### Task 11: Sesión M4.1 — Recuento G2 y resultados ML multidominio (compuerta GM4)

**Files:**
- Modify: `scripts/generar_resultados_ml.py` (iterar dominios si aún no lo hace)
- Modify: `docs/resultados_ml.md` (REGENERADO por el script, no a mano)
- Modify: `docs/plan_pruebas.md` (solo el registro de ejecución: fecha, conteo de pruebas, cobertura) y `docs/calidad_iso25010.md` (solo si algún veredicto cambia)

**Interfaces:**
- Consumes: los catálogos/fixtures de los cuatro dominios (Tasks 3–10); `ml/prediction/reglas.py` (G2: < 50 registros por dominio → reglas).
- Produces: GM4 (informativa) — conteos nuevos por dominio en `docs/resultados_ml.md`.

**Lecturas obligatorias:** `scripts/generar_resultados_ml.py`, `docs/resultados_ml.md` actual, `docs/bitacora/2026-08-31-sprint-i6.md` (cómo se generó la primera vez), `PLAN_MULTIDOMINIO.md` (GM4: la técnica SIGUE siendo reglas; el documento declara la limitación con los conteos NUEVOS).

- [ ] **Step 1: Extender el script** para contar registros de APU por dominio (civil, telecom, industrial, sistemas) desde los fixtures/catálogos y volcar la tabla al documento; donde el histórico de variaciones lo permita (telecom tras Task 6), reportar métricas por dominio.
- [ ] **Step 2: Regenerar** `docs/resultados_ml.md` con el script. Verificar que declara: todos los dominios < 50 → técnica = reglas con análisis de sensibilidad, limitación declarada.
- [ ] **Step 3: Actualizar el registro de ejecución** de `docs/plan_pruebas.md` (número de pruebas y fecha de esta corrida) y revisar si algún veredicto de `docs/calidad_iso25010.md` cambia (si ninguno cambia, no tocarlo).
- [ ] **Step 4: Suite + ruff + core intacto.**
- [ ] **Step 5: Bitácora** `docs/bitacora/2026-09-02-M4.1-recuento-g2.md` (conteos antes/después, GM4).
- [ ] **Step 6: Commit**

```bash
git add scripts/generar_resultados_ml.py docs/resultados_ml.md docs/plan_pruebas.md docs/calidad_iso25010.md docs/bitacora/2026-09-02-M4.1-recuento-g2.md
git commit -m "feat(ml): resultados multidominio con conteos g2 regenerados"
```

---

### Task 12: Sesión M4.2 — Documentación de cierre del sprint

**Files:**
- Modify: `docs/manual_usuario.md` y `docs/manual_tecnico.md` (sección: fuentes de precios por dominio y cómo cargar cada catálogo — los seeds nuevos)
- Modify: `PLAN_MULTIDOMINIO.md` (marcar el estado de las compuertas GM1–GM4 en la tabla de §2, una palabra por fila: CRUZADA / CRUZADA‑CON‑DEGRADACIÓN)
- Create: `docs/bitacora/2026-09-02-sprint-multidominio.md` (bitácora FINAL del sprint)

**Interfaces:**
- Consumes: todas las bitácoras de sesión del sprint; `scripts/meta_multidominio.py`.
- Produces: cierre documental; meta del sprint 12/12.

**RESTRICCIÓN REFORZADA:** la sesión M4.2 del spec pide actualizar `docs/tesis/plan_redaccion.md` — en este sprint está PROHIBIDO (cambios sin commitear del usuario). En su lugar, la bitácora final lista ese pendiente textualmente: «actualizar plan_redaccion (cap. IV §9 y cap. V) cuando el usuario commitee su sesión de redacción».

- [ ] **Step 1: Actualizar los dos manuales** (fuentes por dominio, comando de cada seed, dónde vive cada evidencia).
- [ ] **Step 2: Marcar compuertas** en `PLAN_MULTIDOMINIO.md` §2.
- [ ] **Step 3: Ejecutar `uv run python scripts/meta_multidominio.py`** — esperado 12/12. Si alguna meta falla, arreglar lo que falte (o documentar por qué no aplica) antes de cerrar.
- [ ] **Step 4: Bitácora final** `docs/bitacora/2026-09-02-sprint-multidominio.md`: estado de las cuatro compuertas, conteos, pendientes del autor (ronda de cotizaciones, cita ISBSG, verificación manual de filas MaPreX marcadas, plan_redaccion), salida de la meta.
- [ ] **Step 5: Suite + ruff + core intacto. Commit**

```bash
git add docs/manual_usuario.md docs/manual_tecnico.md PLAN_MULTIDOMINIO.md docs/bitacora/2026-09-02-sprint-multidominio.md
git commit -m "docs: cierre del sprint multidominio"
```
