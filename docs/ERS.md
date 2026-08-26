# Especificación de Requerimientos de Software (IEEE 830)

**Sistema de generación y auditoría de Análisis de Precios Unitarios multidominio**

> Estado: **esqueleto**. Se completa en la Sesión 0.1 de [PLAN_DESARROLLO.md](../PLAN_DESARROLLO.md).
> Las secciones marcadas `[0.1]` están por redactar; las demás ya tienen contenido definitivo o
> enlazan a su fuente única ([CLAUDE.md](../CLAUDE.md)). Criterio de cierre: al menos 20 RF numerados
> con prioridad y trazabilidad al caso de uso, y matriz de trazabilidad completa.

| Campo | Valor |
|---|---|
| Versión | 0.1 (esqueleto) |
| Fecha | 2026‑08‑26 |
| Autor | [tesista] |
| Revisor | [tutor académico] |

---

## 1. Introducción

### 1.1 Propósito
Definir los requerimientos funcionales y no funcionales del sistema para que el tutor, el jurado y el
equipo de desarrollo compartan una única descripción verificable de lo que se construye.

### 1.2 Alcance
Ver [CLAUDE.md §1](../CLAUDE.md#1-qué-es-este-proyecto). Incluye: derivación trazable de cantidades,
costeo con estructura venezolana, presupuesto y curva, verificación automática, normalización semántica,
detección de anomalías y predicción de precios. Excluye: gemelo digital en sentido estricto,
digitalización automática de planos, evaluación financiera del proyecto de inversión.

### 1.3 Definiciones, acrónimos y abreviaturas

| Término | Definición |
|---|---|
| APU | Análisis de Precios Unitarios: desglose de materiales, equipos y mano de obra por unidad de partida |
| FCAS | Factor de Costos Asociados al Salario (prestaciones); en la línea base, 600 % |
| Bono de alimentación | Cestaticket; monto diario por obrero |
| Rendimiento | Unidades de partida ejecutadas por día |
| BIM‑5D | Modelo paramétrico 3D con cómputo, costo y plan de trabajo asociados |
| IFC | Industry Foundation Classes, formato abierto de intercambio BIM |
| COVENIN 2000 | Codificación venezolana de partidas de construcción |
| ItemComputo | Cantidad de obra trazable (`core.contracts`) |
| Adaptador de dominio | Componente que lee la fuente propia de un dominio y devuelve ItemComputo |
| Línea base | Presupuesto auditado del caso de estudio, [docs/linea_base.md](linea_base.md) |
| `[0.1]` | completar el glosario con LOD, AACE clase 3, MAPE, RMSE, R², CBR, Isolation Forest |

### 1.4 Referencias
IEEE 830‑1998; ISO/IEC 25010; COVENIN 2000; AACE RP 18R‑97; Bases del anteproyecto
(`docs/fuentes/`); [CLAUDE.md](../CLAUDE.md); [docs/metodologia.md](metodologia.md).

### 1.5 Visión general del documento
La sección 2 describe el producto y sus casos de uso; la sección 3 enumera los requerimientos; la
sección 4 los traza a los casos de uso y a las pruebas.

---

## 2. Descripción general

### 2.1 Perspectiva del producto
Sistema de escritorio/servidor local: núcleo Python con base SQLite, interfaz Streamlit y API FastAPI.
Recibe cantidades de obra de adaptadores de dominio (IFC, CSV, tablas) y listas de precios (CSV/Excel);
produce presupuesto, curva de inversión, informe de auditoría y exportación a Excel. Ver
[docs/arquitectura.md](arquitectura.md).

### 2.2 Funciones del producto (casos de uso)

| UC | Nombre | Incremento |
|---|---|---|
| UC‑01 | Elaborar presupuesto nuevo desde una fuente de cantidades | I0.5, I3.1 |
| UC‑02 | Actualizar masivamente los precios de un presupuesto existente | I1 |
| UC‑03 | Reutilizar partidas y desgloses de proyectos anteriores | I2 |
| UC‑04 | Recalcular ante cambio de alcance o dimensiones | I3.2 |
| UC‑05 | Auditar un presupuesto elaborado por un tercero | I4 |
| UC‑06 | Registrar y consultar rendimientos reales de obra ejecutada | I6.2 |
| UC‑07 | Contrastar el precio construido con el precio de mercado | I6.3 |
| UC‑08 | Generar escenarios de sensibilidad | F.1 |

`[0.1]` Redactar cada UC con actor, precondiciones, flujo principal, flujos alternativos y postcondiciones.

### 2.3 Características de los usuarios

| Actor | Descripción | UC principales |
|---|---|---|
| Proyectista / estimador | elabora y actualiza presupuestos | UC‑01, 02, 03, 04, 08 |
| Auditor | revisa presupuestos de terceros | UC‑05, 07 |
| Residente de obra | registra rendimientos medidos | UC‑06 |
| Administrador del catálogo | mantiene partidas, insumos y listas de precios | UC‑02, 03 |

### 2.4 Restricciones
- Todo monto y cantidad en `Decimal` (CLAUDE.md §2).
- El núcleo no depende de ningún dominio; los dominios entran por `AdaptadorDominio` (CLAUDE.md §5).
- Procesamiento sobre IFC 4, no sobre formatos nativos de modelado (independencia tecnológica).
- Codificación de partidas COVENIN 2000; estructura de costos según la Convención Colectiva vigente.
- Ejecución local en Windows/Linux con Python ≥ 3.12.

### 2.5 Suposiciones y dependencias
- Disponibilidad de la línea base auditada (existe) y de un modelo IFC de prueba (`tanquilla.ifc`, pendiente).
- Volumen de registros históricos suficiente para el módulo predictivo (compuerta G2, CLAUDE.md §8.1).
- Autorización de uso académico de una base de precios de referencia, o catálogo reducido propio.

### 2.6 Requisitos futuros
Sombra digital (avance real de obra vs curva planificada); multimoneda con factor de actualización;
reconocimiento de planos.

---

## 3. Requisitos específicos

### 3.1 Interfaces externas
- **Usuario:** interfaz web local (Streamlit) con los ocho casos de uso.
- **Software:** API REST (FastAPI) con esquema OpenAPI en `docs/api.json`.
- **Archivos de entrada:** IFC 4 (dominio civil), CSV de topología (telecom), registro de activos
  (industrial), alcance funcional (sistemas), listas de precios CSV/XLSX.
- **Archivos de salida:** presupuesto y curva en XLSX, informe de auditoría.

### 3.2 Requisitos funcionales `[0.1]`

Numerar RF‑01 en adelante. Cada RF: enunciado verificable, prioridad (Esencial / Deseable / Opcional),
UC de origen, incremento, criterio de aceptación.

| RF | Enunciado | Prioridad | UC | Incremento | Criterio de aceptación |
|---|---|---|---|---|---|
| RF‑01 | El sistema calculará el precio unitario de una partida a partir de su composición y los parámetros de costo según la fórmula de CLAUDE.md §4 | Esencial | UC‑01 | I0.3 | `test_costing.py` en verde (5 APU ± 0,01) |
| RF‑02 | El sistema generará siempre el informe de auditoría al producir o cargar un presupuesto | Esencial | UC‑05 | I4 | 7 de 7 inconsistencias detectadas |
| RF‑03 | Toda cantidad de obra conservará `origen_id`, `origen_tipo` y, si aplica, la regla que la produjo | Esencial | UC‑01, 04 | I0.1 | `test_contracts.py` |
| RF‑… | `[0.1]` | | | | |

Guía de derivación por UC (mínimos esperados): UC‑01 → 4 RF; UC‑02 → 4; UC‑03 → 2; UC‑04 → 3;
UC‑05 → 3 (reglas, informe, severidades); UC‑06 → 3; UC‑07 → 2; UC‑08 → 2. Total ≥ 23.

### 3.3 Requisitos no funcionales (ISO/IEC 25010) `[0.1]`

| Característica | RNF | Métrica | Meta |
|---|---|---|---|
| Adecuación funcional | RNF‑01 exactitud del presupuesto frente a la línea base corregida | desviación % | dentro de clase 3 AACE |
| Fiabilidad | RNF‑02 reproducibilidad: el mismo presupuesto se reconstruye a la fecha de su lista de precios | comparación exacta | 100 % |
| Eficiencia de desempeño | RNF‑03 tiempo de recálculo masivo | segundos para N partidas | `[0.1]` |
| Usabilidad | RNF‑04 el informe de auditoría se entiende sin formación previa | juicio de expertos (Likert) | ≥ 4/5 |
| Mantenibilidad | RNF‑05 agregar un dominio no modifica `core/` | `git diff --stat core/`, `test_arquitectura.py` | vacío / verde |
| Mantenibilidad | RNF‑06 cobertura de pruebas del núcleo | pytest‑cov | ≥ 80 % |
| Portabilidad | RNF‑07 instalación con `uv sync` en Windows y Linux | pasos manuales | 0 |
| Seguridad | RNF‑08 `[0.1]` | | |
| Compatibilidad | RNF‑09 entrada IFC 4 de cualquier modelador | archivos de ≥ 2 herramientas | `[0.1]` |

### 3.4 Reglas de negocio
Fórmula de cálculo: [CLAUDE.md §4](../CLAUDE.md#4-especificación-del-cálculo-y-línea-base).
Reglas de verificación R1–R7: [CLAUDE.md §7](../CLAUDE.md#7-siete-reglas-de-verificación-coreverification-sesión-i4).
Criterios de degradación del módulo predictivo: [CLAUDE.md §8.1](../CLAUDE.md#8-compuertas-y-criterios-de-degradación).

---

## 4. Matriz de trazabilidad `[0.1]`

| UC | RF | Prueba(s) | Incremento | Indicador de la tesis |
|---|---|---|---|---|
| UC‑01 | RF‑01, RF‑03, … | `tests/unit/test_costing.py`, … | I0 | 2 |
| UC‑05 | RF‑02, … | `tests/unit/test_verification.py` (I4) | I4 | 1 |
| … | | | | |

La columna "Indicador" enlaza con [docs/metodologia.md §8](metodologia.md#8-indicadores-de-la-tesis) y
con la matriz de [docs/tesis/esqueleto_tesis.md](tesis/esqueleto_tesis.md).

---

## Apéndices
- A. Caso de estudio y línea base: [docs/linea_base.md](linea_base.md).
- B. Modelo de datos: [docs/modelo_datos.md](modelo_datos.md).
- C. Arquitectura: [docs/arquitectura.md](arquitectura.md).
