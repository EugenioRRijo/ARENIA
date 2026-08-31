# Resultados del modulo predictivo (Sesion I6.3, RF-28)

Generado por `scripts/generar_resultados_ml.py` sobre una base en memoria sembrada con
la linea base; reproducible con `uv run python scripts/generar_resultados_ml.py`.

## Compuerta G2: conteo de registros y tecnica (CLAUDE.md §8.1)

| Dominio | Registros de APU | Tecnica que dicta la tabla |
|---|---|---|
| civil | 5 | reglas |
| industrial | 0 | reglas |
| sistemas | 0 | reglas |
| telecom | 0 | reglas |

Todos los dominios estan por debajo de los 50 registros: la tecnica de
`ml/prediction/` es el **sistema de reglas con analisis de sensibilidad**, y se declara
como **limitacion** del trabajo, no como logro: no hay datos suficientes para entrenar
ni validar un modelo de aprendizaje (la tabla de degradacion existe exactamente para
este caso). La compuerta G2 queda cruzada con esta evidencia.

## Regla declarada

PU estimado = PU base x (1 + media de las variaciones del historico de cambios de
precio). Sensibilidad: el rango recorre la variacion minima y la maxima observadas.
La regla no conoce la composicion del APU: el motor de costos (`core.costing`) es la
verdad de terreno contra la que se mide.

## Metricas (RF-28)

| Metrica | Valor |
|---|---|
| MAPE | 12.46 % |
| RMSE | 5.10 USD |
| R2 | 0.9974 |

## Predicciones sobre el caso UC-02 de la linea base

| Partida | PU base | PU estimado | Rango de sensibilidad |
|---|---|---|---|
| LB-01-EXC | 8.60 | 9.89 | [9.46, 10.32] |
| LB-02-TUB | 10.19 | 11.72 | [11.21, 12.23] |
| LB-03-ENC | 33.24 | 38.22 | [36.56, 39.89] |
| LB-04-CON | 242.64 | 279.04 | [266.90, 291.17] |
| LB-05-REL | 52.58 | 60.46 | [57.83, 63.09] |

## Contraste AACE clase 3 (RF-29)

Ningun precio construido se desvia del estimado fuera del rango declarado (-20 % / +30 %): sin hallazgos.
