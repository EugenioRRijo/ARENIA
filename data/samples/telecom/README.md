# Muestra telecom: `topologia_arenaza.csv`

Entrada del adaptador `AdaptadorTelecom` (`adapters/telecom/adaptador.py`, Sesión I5): una topología
de red pequeña (rack, dos switches, cinco puntos de acceso WiFi, un UPS, cinco enlaces de cable UTP),
derivada de `data/samples/telecom/Presupuesto_1_ARENAZA.pdf` (presupuesto real de instalación de
puntos WiFi, 14 renglones, 1 109,29 USD; leído con `python -c "import fitz; ..."`, PyMuPDF global).

## Columnas

`tipo,id,descripcion,codigo_partida,unidad,cantidad,origen,destino,longitud_m,reserva,especificaciones`

- `tipo` ∈ {`nodo`, `enlace`}. Una fila `nodo` solo llena `cantidad`; una fila `enlace` solo llena
  `origen,destino,longitud_m,reserva`. Las columnas que no aplican a la fila se dejan vacías.
- `id`: clave de la fila, usada tal cual como `origen_id` del `ItemComputo` (trazabilidad total,
  CLAUDE.md sección 2).
- `codigo_partida`: prefijo `TC-` (partidas propias del dominio telecom; no reutiliza códigos `LB-`
  de la línea base civil).
- `cantidad` (solo `nodo`): cantidad tabular directa, tomada tal cual del CSV.
- `origen`, `destino` (solo `enlace`): extremos del tramo de cable, como `id` de dos filas `nodo`.
  No se validan como referencias existentes en esta sesión (fuera del alcance del adaptador); quedan
  en `ItemComputo.especificaciones["origen"/"destino"]` para que una regla de verificación futura los
  use si hace falta.
- `longitud_m`, `reserva` (solo `enlace`): la cantidad del enlace es
  `longitud_m * (1 + reserva)` (`ItemComputo.regla`), evaluada por
  `adapters/telecom/evaluador.py`. `reserva` es la fracción adicional de cable por curvas, empalmes
  y holgura de servicio; vacía equivale a 0.
- `especificaciones`: pares `clave=valor` separados por `;` (por ejemplo `categoria=cat6;tipo_cable=utp`),
  trazables hacia la regla R4.

## Origen y supuestos declarados

`Presupuesto_1_ARENAZA.pdf` es una lista de materiales (piezas y una bobina de 90 m de cable UTP
CAT6), no una topología con nodos y tramos identificados: el PDF no dice cuántos metros van entre
cada switch y cada punto de acceso, solo el total de cable comprado. Los nueve nodos de esta muestra
(`RACK-01`, `SW-CORE`, `SW-DIST`, `AP-01`..`AP-05`, `UPS-01`) reproducen el tipo y la cantidad de
equipos de los renglones del PDF (un switch de escritorio, cinco puntos WiFi/decodificadores mesh, un
rack y un UPS, estos dos últimos coherentes con el alcance de `Presupuesto_2_ARENAZA.pdf`, que sí
incluye rack). Las longitudes y la fracción de reserva por tramo (`ENL-01`..`ENL-05`, que suman 95 m,
cerca de los 90 m de la bobina) son **supuestos de esta muestra**, igual que el sobreancho y el
espesor de fondo lo son en `data/samples/civil/README.md`: el PDF no discrimina el cableado por
tramo, así que se distribuye la longitud total entre una topología plausible (rack -> switch núcleo
-> switch de distribución -> puntos de acceso) para que la regla del enlace sea evaluable.

## Política de mano de obra "50 % del total"

Ambos PDF de ARENAZA (`Presupuesto_1_ARENAZA.pdf`, `Presupuesto_2_ARENAZA.pdf`) fijan la mano de obra
como "el equivalente al 50 % del presupuesto total", no un jornal por rendimiento como en el dominio
civil (CLAUDE.md sección 4). Esta muestra y el adaptador **no representan esa política**: el
adaptador solo extrae `ItemComputo` (cantidades de obra), no `ComposicionAPU` ni costeo; la política
de mano de obra pertenece a la capa de costeo (`core.costing`, `core.contracts.apu`), fuera del
alcance de esta sesión. El análisis de cómo representarla sin tocar `core/` está en
`docs/bitacora/2026-08-29-I5-telecom.md`.
