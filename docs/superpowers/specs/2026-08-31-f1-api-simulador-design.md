# Diseño — F.1 adelantada: API FastAPI, simulador de mercado, front de prueba y gestión 3D (I3.1)

**Fecha:** 2026‑08‑31 · **Estado:** aprobado en conversación (enfoque B, «aprobado tal cual») ·
**Rama prevista:** `inc/F1-api` · **Spec de autoridad:** [CLAUDE.md](../../../CLAUDE.md),
[PLAN_DESARROLLO.md](../../../PLAN_DESARROLLO.md) (Sesión F.1), [docs/ERS.md](../../ERS.md)

## 1. Contexto y alcance

El usuario necesita «sacar y mantener actualizados los precios» y un banco de pruebas del sistema.
Según el plan original, el mecanismo de precios es **UC‑02** (listas CSV/XLSX → carga masiva →
`CambioPrecio` como histórico, que después alimenta I6.3) — ya construido en el sprint alpha — y el
backend que el plan manda es la **Sesión F.1**: `api/main.py` en FastAPI exponiendo las operaciones
del núcleo con esquema OpenAPI exportado a `docs/api.json`.

**Alcance** (F.1 parcial, adelantada; desviación de la cascada documentada en bitácora, igual que el
alpha): API HTTP sobre el núcleo existente, un simulador de listas de precios para ejercitar el ciclo
de actualización, la UI Streamlit extendida a multipágina y **la gestión del sistema 3D**
(Sesión I3.1 del plan, compuerta G1): adaptador civil IFC, modelo de muestra generado
programáticamente y visor 3D en la UI (añadido 2026‑08‑31 a pedido del usuario). Casos de uso cubiertos: UC‑01 (elaborar
desde cómputo de muestra por dominio), UC‑02 (actualización masiva vía API), UC‑05 (informe de
auditoría, que se genera siempre), más consulta de catálogo e histórico.

**Fuera de alcance:** UC‑03/06/07 (los bloquean las compuertas de ML), UC‑08 (escenarios; usa el
mecanismo de UC‑02 sin persistir, se añade después), autenticación (herramienta local de tesis),
conectores a fuentes externas reales de precios (si algún día se quieren, cada conector *produce una
lista de precios* que entra por UC‑02 — el núcleo intacto).

## 2. API (`api/`)

**Estructura:** `api/main.py` (aplicación y arranque), `api/esquemas.py` (modelos Pydantic espejo de
los contratos), `api/rutas/` (un módulo por recurso: `catalogo.py`, `listas.py`, `computos.py`,
`presupuestos.py`), `api/dependencias.py` (sesión por petición).

**Decisiones técnicas:**

- **`Decimal` viaja como texto en el JSON**, en ambas direcciones — nunca float (regla 3 del
  proyecto). Los modelos Pydantic declaran los montos como `str` y la conversión a `Decimal` ocurre
  en la frontera, construyendo siempre desde texto.
- Base de datos: `data/apu.db` por defecto; variable de entorno `APU_BASE` para otra ruta. Sesión
  SQLAlchemy por petición vía dependencia de FastAPI; la transacción la confirma el endpoint que
  representa la decisión del usuario (mismo criterio que la UI: `insumos_afectados`).
- `api/` importa `core` y `adapters` (capa de composición, como `ui/`); `core` sigue sin conocer a
  nadie; `tests/unit/test_arquitectura.py` sigue verde.
- Errores: excepciones del núcleo (`CatalogoIncompleto`, `ValueError`, `PlanInvalido`…) →
  respuestas 4xx con el mensaje original; nunca traza cruda.

**Endpoints v1:**

| Método y ruta | UC | Núcleo que llama |
|---|---|---|
| `GET /salud` | — | ping + versión del paquete |
| `GET /partidas` | — | `Catalogo` (código, descripción, unidad) |
| `GET /insumos` | — | `Catalogo` + precio vigente por insumo |
| `GET /listas-precios` | UC‑02 | listas registradas (nombre, moneda, vigencia) |
| `POST /listas-precios` (multipart CSV/XLSX + nombre, moneda, fecha_vigencia) | UC‑02 | `crear_lista_desde_archivo` → devuelve la lista creada y los insumos desconocidos |
| `GET /cambios-precio` (filtros insumo, desde, hasta) | UC‑02 | histórico `CambioPrecio` |
| `POST /computos/{dominio}` (archivo de muestra) | UC‑01 | el adaptador del dominio → `ItemComputo` trazables serializados |
| `POST /presupuestos` (cómputo + código + fecha [+ plan]) | UC‑01/05 | `elaborar` (audita siempre) + `guardar_presupuesto` |
| `GET /presupuestos` | — | códigos y totales |
| `GET /presupuestos/{codigo}` | — | `cargar_presupuesto` (renglones, curva, parámetros) |
| `GET /presupuestos/{codigo}/informe` | UC‑05 | informe de auditoría en markdown |
| `GET /presupuestos/{codigo}/excel` | — | `exportar_excel` como descarga |
| `POST /presupuestos/{codigo}/actualizacion` (lista + codigo_nuevo) | UC‑02 | `actualizar_precios` → comparativo; confirma por `insumos_afectados` |

**OpenAPI:** `scripts/exportar_openapi.py` escribe `docs/api.json` desde `app.openapi()`; una prueba
valida que el esquema contiene las rutas clave; el archivo se regenera en el cierre de la sesión.

## 3. Simulador de mercado (`scripts/simular_lista.py`)

Toma la lista vigente de la base y emite un CSV con el formato canónico de `data/samples/precios/`
(`tipo,insumo,unidad,precio`), aplicando variaciones parametrizadas y **deterministas**:

```
uv run python scripts/simular_lista.py --salida lista.csv \
    --variacion-max 10 --insumos "Cemento Portland,Arena lavada" --semilla 42
```

- `--variacion-max` (porcentaje, `Decimal`), `--insumos` (opcional: solo esos; por defecto todos),
  `--semilla` (obligatoria para reproducibilidad), `--base` (ruta de la BD, por defecto
  `data/apu.db`).
- Los precios nuevos se construyen con `Decimal` y cuantización de dos decimales (es un precio de
  lista, no un cálculo intermedio).
- No toca `core/`: sus listas entran por UC‑02, la puerta única de precios, y van llenando el
  histórico que I6 necesitará.

## 4. Front de prueba (`ui/app.py` multipágina)

La UI sigue llamando a `core` directamente (patrón actual aprobado). Páginas: (1) UC‑02 tal cual
está hoy; (2) catálogo — partidas, insumos, precios vigentes; (3) elaborar presupuesto desde muestra
por dominio (UC‑01: dominio + archivo → cómputo → presupuesto + informe); (4) histórico de cambios
de precio; (5) generar lista de prueba (invoca el simulador). Solo presentación; los dos decimales
siguen siendo los de `DECIMALES_PRESENTACION`.

**El front de prueba de la API es Swagger UI** (`/docs`, incluido en FastAPI): ahí se ejercita cada
endpoint a mano. La UI no consume la API por HTTP (decisión del usuario, 2026‑08‑31).

## 5. Pruebas

TDD. `tests/integration/test_api.py` con `TestClient` (httpx, ya resuelto en `uv.lock`) sobre SQLite
en memoria sembrada con la línea base (override de la dependencia de sesión):

- elaborar el presupuesto 001 vía API → total `1586.61` **exacto como texto**;
- cargar la lista de muestra y actualizar → el comparativo reproduce los mismos `Decimal` exactos
  del caso UC‑02 (solo LB‑04‑CON cambia; total `1636.70`);
- informe de auditoría presente; Excel descargable con bytes no vacíos y libro abrible;
- desconocidos reportados; errores 4xx con mensaje del núcleo;
- `POST /computos/{dominio}` devuelve los `ItemComputo` de la muestra civil (6 ítems, con regla y
  balance).

`tests/unit/test_simulador.py`: determinismo con semilla, formato de columnas, respeto de
`--insumos`, precios `Decimal` no negativos. Suite completa y ruff en verde, cero advertencias;
`meta_alpha.py` sigue 12/12 (la meta no cubre la API: es post‑alpha).

## 6. Mecánica y tareas

Misma mecánica del sprint alpha (subagentes con revisión por tarea, fusión `--no-ff`, ledger).
Tareas previstas: **T1** API núcleo (esquemas, dependencias, rutas de catálogo/listas/cambios),
**T2** rutas de cómputo y presupuestos, **T3** simulador + su prueba, **T4** UI multipágina,
**T5** generador de `tanquilla.ifc`, **T6** adaptador civil IFC + entrada .ifc en la API (compuerta
G1), **T7** visor 3D, **T8** OpenAPI a `docs/api.json` + bitácora + integración. Dependencias:
T2 tras T1; T4 tras T3; T6 y T7 tras T5 (T7 además tras T4); T8 al final. Oleadas: (T1, T3, T5) →
(T2, T4, T6) → (T7, T8). Commits convencionales en español sin tildes (`feat(api): …`, `feat(scripts): …`,
`feat(ui): …`).

## 7. Gestión del sistema 3D (Sesión I3.1, compuerta G1) — añadido 2026‑08‑31

- **`scripts/generar_tanquilla_ifc.py`** construye `data/samples/tanquilla.ifc` (IFC 4) con
  ifcopenshell: una tanquilla de a = 0,80 m, h = 0,80 m, e = 0,10 m como sólido real (extrusión del
  anillo de paredes), con el conjunto de propiedades `Pset_APU` (`COVENIN_Codigo`,
  `Partida_Descripcion`, `Unidad`) y un `IfcElementQuantity` cuyo volumen sale de la fórmula de
  I3.2 — `(a² − (a−2e)²)·h = 0,224 m3​` — calculada con `Decimal`, no de una constante suelta.
  El archivo es reemplazable por un export de Revit/Bonsai: el extractor no distingue el productor.
- **`adapters/civil/ifc.py`**: `AdaptadorCivilIFC(AdaptadorDominio)` lee el IFC con ifcopenshell,
  recorre los elementos que llevan `Pset_APU`, toma la cantidad del `IfcElementQuantity` acorde a
  la unidad declarada y devuelve `ItemComputo` con `origen_id` = GlobalId y
  `origen_tipo = OrigenTipo.IFC`. Solo importa `core.contracts` (e ifcopenshell, terceros).
- **Compuerta G1:** la prueba de aceptación compara lo extraído contra el cálculo manual
  (0,224 m3, la misma cifra de `test_reglas_civil`). Si no coincidiera, el adaptador tabular sigue
  siendo la entrada civil y se documenta la pérdida (CLAUDE.md §8.2); el resto del sistema no cambia.
- **API:** `POST /computos/civil` acepta `.csv` (tabular) o `.ifc` (IFC), decidido por la
  extensión del archivo.
- **Visor 3D:** `ui/visor3d.py` tesela el IFC con `ifcopenshell.geom` a mallas por elemento
  (vértices, caras, GlobalId) y la página del visor las renderiza con three.js (CDN) junto a la
  tabla elemento ↔ partida ↔ cantidad extraída. La teselación se prueba con pytest; la página no
  (sin pruebas de UI, por diseño del proyecto).
- **Dependencias:** el extra `civil` ya declara `ifcopenshell>=0.8` (verificado: 0.8.5 instala en
  Python 3.13/Windows). Entorno del sprint: `uv sync --extra ui --extra api --extra civil`. Las
  pruebas que requieren ifcopenshell usan `pytest.importorskip` para no romper entornos sin el
  extra, pero el sprint corre con el extra instalado y su evidencia debe mostrarlas pasando.

## 8. Riesgos y decisiones abiertas

- **G0 sigue pendiente** (tutor): la API expone lo ya construido; si G0 pide cambios, la API los
  hereda vía el núcleo, no los absorbe.
- La serialización de `Decimal` como texto es un contrato de la API: se documenta en OpenAPI
  (`format: "decimal"` en la descripción de los campos) para consumidores futuros.
- El simulador es una herramienta de prueba, no una fuente de mercado: se declara así en su
  docstring y en el README de `scripts/`, para que la tesis no lo confunda con UC‑07.
