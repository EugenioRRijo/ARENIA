# Esqueleto del trabajo de grado y matriz de trazabilidad

Título propuesto: *Modelo BIM‑5D asistido por aprendizaje automático para la generación y validación
de Análisis de Precios Unitarios en proyectos de instalaciones sanitarias. Caso: obra civil del sistema
de drenaje de una clínica* (Bases del anteproyecto, `docs/fuentes/`). El PLAN de desarrollo amplía el
sistema a **multidominio** (civil, telecom, industrial, sistemas); ver la nota de la sección 3.

Este archivo es la **única** matriz que relaciona objetivos, fases, sesiones, productos, indicadores y
capítulos. Los demás documentos la enlazan. El guión operativo para escribir los capítulos —
orden, convenciones, cifras citables y tablero de avance — está en
[plan_redaccion.md](plan_redaccion.md).

## 1. Estructura de capítulos

| Capítulo | Contenido | Fuente ya disponible |
|---|---|---|
| Introducción | contexto, problema en una página, aporte, estructura del documento | Bases §1.1 |
| I. El problema | planteamiento, evidencia empírica (siete inconsistencias), formulación, objetivos, justificación, alcance y delimitación | Bases §2–5; [docs/linea_base.md](../linea_base.md) |
| II. Marco teórico | antecedentes (internacional, latinoamericano, nacional), bases teóricas (ciclo del proyecto, BIM‑5D, sombra/gemelo digital, ML para costos, NLP para normalización), bases normativas (COVENIN 2000, convención colectiva, AACE 18R‑97), definición de términos | Bases §6–7; `docs/fuentes/Estado_del_Arte_BIM5D_ML_APU.pdf` |
| III. Marco metodológico | tipo y diseño, fases, técnicas e instrumentos, fuentes de datos, criterios de validación, **metodología de desarrollo de software (Scrum‑Cascada, DRY)** | Bases §8; [docs/metodologia.md](../metodologia.md) |
| IV. Desarrollo de la propuesta | requerimientos (ERS), modelo de datos, arquitectura 4+1, núcleo y motor de costos, adaptador civil (IFC y reglas paramétricas), verificación, adaptadores adicionales, módulos ML, interfaz y API | [docs/ERS.md](../ERS.md), [docs/modelo_datos.md](../modelo_datos.md), [docs/arquitectura.md](../arquitectura.md), código |
| V. Resultados y evaluación | indicadores 1–5, contraste con la línea base y con AACE clase 3, juicio de expertos, evaluación ISO/IEC 25010, plan de pruebas IEEE 829 | `docs/resultados_ml.md`, `docs/calidad_iso25010.md`, `docs/plan_pruebas.md` (Fase 6) |
| Conclusiones y recomendaciones | respuesta a la pregunta principal y a las secundarias; limitaciones declaradas (compuertas no cruzadas); líneas futuras (sombra digital, planos) | bitácoras |
| Referencias | norma institucional | Bases §12 |
| Anexos | A ERS · B modelo de datos · C arquitectura · D plan de pruebas · E manuales · F `api.json` · G línea base (`APUS_CLINICA.pdf`) · H bitácoras de sprint | `docs/` |

## 2. Matriz de trazabilidad

| Objetivo específico (Bases §3.2) | Fase (Bases §8.2) | Fase / sesiones (PLAN) | Producto verificable | Indicador | Capítulo |
|---|---|---|---|---|---|
| OE1 Diagnosticar las inconsistencias del proceso manual y establecer la línea base | I Diagnóstico | Sprint 0; fixture de I4 | `docs/linea_base.md`, `tests/fixtures/apu_linea_base.py` | base del 1 y del 2 | I, IV |
| OE2 Estructurar el modelo paramétrico y la extracción automática en IFC | II Modelado y extracción | I3.1 (G1) | `adapters/civil`, `data/samples/tanquilla.ifc` | 3 (tiempo) | IV |
| OE3 Diseñar la base de datos bajo COVENIN con FCAS, bono y depreciación explícitos | III Base de datos y motor | 0.2, I0.3, I0.4, I0.5, I1 | `docs/modelo_datos.md`, `core/costing`, `core/models`, `core/budget` | 2 | IV |
| OE4 Implementar normalización, predicción y detección de anomalías | IV Aprendizaje automático | I2, I6.1, I6.3 (G2) | `ml/*`, `docs/resultados_ml.md` | 5 | IV, V |
| OE5 Desarrollar la verificación automática de consistencia | V Verificación | I3.2, I4 | `core/verification`, informe de auditoría | 1 (7/7) | IV, V |
| OE6 Evaluar exactitud y desempeño frente a la línea base y al mercado (AACE) | VI Evaluación | F.2, I6.3 | `docs/calidad_iso25010.md`, `docs/plan_pruebas.md`, juicio de expertos | 2, 3, 5 | V |
| **Transversal:** extensibilidad multidominio sin modificar el núcleo | — | I0.1, I5 | `core/contracts`, `adapters/{telecom,industrial,sistemas}`, `test_arquitectura.py` | 4 | IV, V |

## 3. Nota sobre el alcance multidominio

Las Bases del anteproyecto formulan seis objetivos específicos para el dominio sanitario. El PLAN de
desarrollo incorpora la hipótesis central de extensibilidad (núcleo intacto al agregar telecom,
industrial y sistemas), que no aparece como objetivo en las Bases. Antes de redactar el anteproyecto
formal hay que decidir con el tutor una de dos opciones:

1. Incorporarla como **OE7** ("Validar la extensibilidad del modelo a otros dominios mediante
   adaptadores que no modifiquen el núcleo") y ajustar título y alcance; o
2. Mantenerla como **resultado complementario** dentro de OE3 (diseño del núcleo), sin cambiar el
   título, y presentar los adaptadores adicionales en el capítulo V como evidencia de mantenibilidad.

Las muestras de `data/samples/telecom/` (presupuestos ARENAZA) permiten cualquiera de las dos.

## 4. Correspondencia entre preguntas de investigación y evidencia

| Pregunta (Bases §2.4) | Dónde se responde |
|---|---|
| ¿Qué LOD necesita el modelo para una extracción confiable? | I3.1, compuerta G1; capítulo IV |
| ¿Qué reglas paramétricas derivan las cantidades de la geometría? | I3.2 (`adapters/civil/reglas.py`); capítulo IV |
| ¿Qué técnica de ML conviene con datos escasos? | I6.3, compuerta G2, `docs/resultados_ml.md`; capítulo V |
| ¿Qué verificaciones automáticas aporta el conocimiento geométrico? | R1–R7, I4; capítulos IV y V |
| ¿Qué exactitud alcanza el presupuesto generado (AACE)? | indicador 2, F.2; capítulo V |
