# Muestras de listas de precios (UC‑02)

Archivos de entrada de `core.catalog.precios.leer_lista_precios`. Columnas obligatorias:
`tipo` (`material`, `equipo` o `mano_obra`), `insumo` (descripción), `unidad` (vacía para equipos y
mano de obra, que no la llevan en el catálogo) y `precio` (punto como separador decimal).

| Archivo | Vigencia | Qué contiene |
|---|---|---|
| `lista_2026-06-01.csv` | 01/06/2026 | Nueve insumos de la línea base. Solo suben dos: cemento Portland 15 → 18 USD/saco y arena lavada 30 → 33 USD/m3; los otros siete repiten su precio y no generan `CambioPrecio` |

Los dos insumos que suben participan únicamente en `LB-04-CON` (vaciado de concreto), así que la
muestra revalora una sola partida: es el caso mínimo que demuestra el registro de cambios, la
incidencia por partida y el comparativo de la Sesión I1.
