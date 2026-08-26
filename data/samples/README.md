# Muestras de datos por dominio

| Ruta | Dominio | Estado | Sesión |
|---|---|---|---|
| `tanquilla.ifc` | civil | **pendiente**: modelar una sola tanquilla (0,80 × 0,80 × 0,80 m, pared 0,10 m) en Revit o Bonsai, con el Pset `Pset_APU` (`COVENIN_Codigo`, `Partida_Descripcion`, `Unidad`) y exportar a IFC 4 | antes de I3.1 |
| `telecom/Presupuesto_1_ARENAZA.pdf` | telecom / sistemas | presupuesto real de puntos WiFi (14 renglones, 1 109,29 USD) | I5 |
| `telecom/Presupuesto_2_ARENAZA.pdf` | telecom / sistemas | presupuesto real de red y CCTV con rack (26 renglones, 5 410,73 USD) | I5 |

Nota para I5: los presupuestos ARENAZA usan una política de mano de obra distinta ("50 % del total")
en lugar del APU por rendimiento. Cómo la representa el adaptador sin tocar `core/` es una decisión
de diseño registrada en la bitácora del sprint 0.

La evidencia primaria del caso civil (los cinco APU) está en `../linea_base/APUS_CLINICA.pdf`; su
versión ejecutable es `tests/fixtures/apu_linea_base.py`.
