"""Exporta el esquema OpenAPI de la aplicacion FastAPI a `docs/api.json`.

Entregable del plan de desarrollo (Sesion F.1): el esquema se regenera cada vez que cambian las
rutas de la API, para que `docs/api.json` quede siempre al dia con `api.main.app`.

Uso:
    uv run python scripts/exportar_openapi.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ejecutado como `python scripts/exportar_openapi.py`, sys.path[0] es scripts/, no el raiz del repo.
RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from api.main import app  # noqa: E402

RUTA_SALIDA = RAIZ / "docs" / "api.json"


def exportar(ruta: Path = RUTA_SALIDA) -> Path:
    """Escribe el esquema OpenAPI de `app` en `ruta` y la devuelve."""
    esquema = app.openapi()
    ruta.write_text(json.dumps(esquema, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def main() -> int:
    ruta = exportar()
    print(f"Esquema OpenAPI exportado a {ruta} ({len(ruta.read_text(encoding='utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
