# APU System

Sistema de generación y auditoría de Análisis de Precios Unitarios (APU) multidominio, asistido por
modelo BIM‑5D y aprendizaje automático. Trabajo de grado; caso de estudio: obra civil del sistema de
drenaje de una clínica.

La hipótesis central del trabajo es que **un núcleo de costeo y verificación puede permanecer intacto
mientras se agregan dominios (civil, telecom, industrial, sistemas) mediante adaptadores**. La prueba
empírica es `git diff --stat core/` vacío al terminar los adaptadores (Sesión I5).

## Documentos rectores

| Documento | Para qué |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Constitución del proyecto: principios, cálculo, contratos, estructura, reglas, compuertas |
| [PLAN_DESARROLLO.md](PLAN_DESARROLLO.md) | Las 20 sesiones de trabajo, con prompt, criterio de cierre y commit |
| [docs/metodologia.md](docs/metodologia.md) | Metodología Scrum‑Cascada y principio DRY aplicados al proyecto |
| [docs/README.md](docs/README.md) | Índice de toda la documentación |

## Arranque rápido

```powershell
uv sync                 # crea .venv e instala dependencias base + grupo dev (pytest, ruff)
uv run pytest           # suite de pruebas
uv run ruff check .     # estilo
```

> OneDrive sincroniza todo lo que hay en esta carpeta, incluido `.venv/`. Para evitarlo, antes de
> `uv sync` defina `$env:UV_PROJECT_ENVIRONMENT = "$env:LOCALAPPDATA\apu_system\.venv"` (o fíjelo
> como variable de usuario). `.venv` está en `.gitignore` en cualquier caso.

## Estado de la suite

| Archivo | Estado esperado | Cambia en |
|---|---|---|
| `tests/unit/test_contracts.py` | verde | — (los contratos son estables) |
| `tests/unit/test_arquitectura.py` | verde | — (vigila que adaptadores y ML solo importen `core.contracts`) |
| `tests/unit/test_linea_base.py` | verde | — (integridad del caso auditado) |
| `tests/unit/test_costing.py` | **rojo por `ImportError`** | Sesión I0.3, cuando exista `core/costing/` |

## Mapa del repositorio

```
core/        núcleo cerrado: contracts (estables), costing, models, catalog, budget, verification
adapters/    un paquete por dominio; cada uno implementa AdaptadorDominio y solo importa core.contracts
ml/          normalization, anomaly, prediction
ui/  api/    Streamlit y FastAPI (Fase 6)
tests/       unit, integration, fixtures (la línea base vive en tests/fixtures/apu_linea_base.py)
data/        linea_base (evidencia primaria), samples (IFC, CSV de otros dominios)
docs/        metodología, ERS, modelo de datos, arquitectura, línea base, esqueleto de tesis, bitácora
scripts/     utilidades (seed.py llega en I0.4)
```
