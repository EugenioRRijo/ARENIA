# Bitácora — Task 1: Meta del alpha (`scripts/meta_alpha.py`)

**Fecha:** 2026-08-29 · **Rama:** `inc/alpha-meta` · **Base:** `main` (`e783f0c`, etiqueta `sprint-0`)

## Objetivo

Un solo comando, `uv run python scripts/meta_alpha.py`, que el integrador ejecute tras fusionar
cada incremento del sprint alpha para saber si el alpha va bien: tabla de las 12 metas con estado
`OK` / `FALLA` / `PENDIENTE`, código de salida 0 solo si las 12 están en `OK`.

## Qué se hizo

- `scripts/__init__.py`: paquete con docstring de una línea.
- `scripts/meta_alpha.py`: módulo importable con toda la lógica en funciones puras
  (`parsear_junit`, `estado_pruebas`, `estado_nucleo_intacto`, `estado_cobertura`, `estado_ruff`,
  `estado_suite`, `render_tabla`) más `main(argv) -> int`. La orquestación (un solo `pytest` con
  `--junitxml` + `--cov=core --cov-report=json`, `ruff check .`, `ruff format --check .`,
  `git log --no-merges` + `git diff-tree` para el historial) vive en funciones `_ejecutar_*` /
  `_evaluar`, separadas de las funciones puras para que las pruebas nunca disparen procesos reales.
- `tests/unit/test_meta_alpha.py`: 17 pruebas TDD sobre las funciones puras (parseo de JUnit con
  dos archivos y una clase anidada; `estado_pruebas` PENDIENTE/FALLA/OK; `estado_nucleo_intacto`
  FALLA/OK/PENDIENTE; `estado_cobertura` en el umbral; `estado_ruff`, `estado_suite`; `render_tabla`
  con los 12 códigos y la línea `RESULTADO`). Ninguna prueba ejecuta pytest, ruff ni git reales.
- `pyproject.toml`: se añadió `"scripts"` a `[tool.ruff.lint.isort] known-first-party` (única línea
  autorizada por el brief).
- `scripts/README.md`: fila nueva para `meta_alpha.py`.

## Decisiones

| Decisión | Motivo |
|---|---|
| `evidencia` en `Fila`/JSON = el `str` dinámico que devuelve cada `estado_*` (no una descripción estática del brief) | es lo único útil para diagnosticar por qué una meta está en cada estado; la tabla del brief (columna "Evidencia") documenta de qué artefacto sale cada determinación, no el texto literal a imprimir |
| Columna "Meta" de la tabla = `codigo + " " + titulo` | solo hay 3 columnas (`Meta`, `Estado`, `Evidencia`) para 4 campos por fila; fusionar código y título es lo que deja identificable cada fila sin una cuarta columna |
| `--sin-cobertura` omite `--cov=core --cov-report=json` en la invocación de pytest (no solo ignora el resultado) | el nombre de la opción y su objetivo (evitar el costo de instrumentar cobertura) apuntan a no pedirla, no a pedirla y descartarla; con la opción, M10 queda PENDIENTE con detalle explícito |
| `(RAIZ / archivo).exists()` en `estado_pruebas` en vez de `Path(archivo).exists()` | `Path.__truediv__` devuelve el operando derecho tal cual cuando es absoluto, así que la misma expresión funciona con las rutas relativas reales (`tests/unit/test_costing.py`) y con las rutas absolutas de `tmp_path` en las pruebas, sin ramas especiales |
| `M10` usa "Cobertura de core/ >= umbral" en vez de "≥ umbral" | hallazgo, ver abajo |

## Hallazgos

1. **La consola de esta máquina es `cp1252`, no UTF-8.** `print()` de un carácter fuera de esa
   página de códigos (`≥`, U+2265) revienta con `UnicodeEncodeError` y aborta el proceso; se
   verificó con `python -c "print('...≥...')"`. Los acentos y la `ñ` sí están en `cp1252` y se
   imprimen sin error (aunque se ven trocados en esta terminal). Por eso el título de M10 usa
   `>=` en vez de `≥`: es la única desviación textual frente a los valores exactos del brief, y es
   consistente con la advertencia del propio brief sobre `render_tabla` ("la consola de Windows
   puede no ser UTF-8"). `json.dumps` no tiene este problema porque escapa a `\uXXXX` por defecto.
2. **El cierre esperado del brief ("M8/M11 en OK y el resto PENDIENTE") es aproximado para M9,
   M10 y M12.** Hoy pytest sí corre (112 pruebas reales) y sí hay datos de cobertura de `core/`,
   así que M10 y M12 obtienen un estado real y no PENDIENTE: M10 = OK (cobertura de `core/`
   98,48 %, calculada sobre las ~30 líneas de `core/contracts/` y `core/costing/__init__.py`
   existentes hoy; sube cuando `core/costing/` tenga cuerpo) y M12 = FALLA (7 fallidas de 112,
   las mismas de `test_costing.py`). M9 sí queda PENDIENTE porque no hay commits que toquen
   `adapters/` o `ml/` desde `sprint-0`. Salida real verificada, tabla (`uv run python
   scripts/meta_alpha.py`):

   ```
   M1  FALLA      tests/unit/test_costing.py: 0 pasadas / 7 fallidas
   M2  PENDIENTE  falta tests/integration/test_persistencia.py
   M3  PENDIENTE  falta .../test_presupuesto_linea_base.py, .../test_budget.py
   M4  PENDIENTE  falta tests/unit/test_reglas_civil.py
   M5  PENDIENTE  falta .../test_auditoria_7_de_7.py, .../test_verification.py
   M6  PENDIENTE  falta .../test_adapter_industrial.py, .../test_adapter_sistemas.py, .../test_adapter_telecom.py
   M7  PENDIENTE  falta tests/integration/test_actualizacion_precios.py
   M8  OK         tests/unit/test_arquitectura.py: 31 pasadas / 0 fallidas
   M9  PENDIENTE  sin commits que toquen adapters/ o ml/ desde la base
   M10 OK         98.47908745247149% (umbral 80%)
   M11 OK         ruff check y ruff format --check sin hallazgos
   M12 FALLA      7 fallidas / 0 errores de 112 pruebas

   RESULTADO: 3/12 metas OK
   ```
   Código de salida: 1. Coincide con el criterio de cierre del brief en lo esencial (M1 FALLA,
   M8 y M11 OK, código de salida 1); M9/M10/M12 no están en la lista corta del brief pero su
   estado es correcto para hoy.
3. Se probaron manualmente `--json` (JSON válido, mismos 4 campos por objeto), `--sin-cobertura`
   (M10 pasa a PENDIENTE con detalle "cobertura omitida"), `--umbral-cobertura 99` (M10 pasa a
   FALLA) y `--base no-existe-esta-ref` (el `git log` falla en silencio, M9 queda PENDIENTE sin
   abortar el script). No se automatizaron como pruebas unitarias porque disparan procesos reales;
   el brief pide que las pruebas unitarias nunca ejecuten pytest real, y por extensión se aplicó el
   mismo criterio a ruff y git.

## Impedimentos

Ninguno.
