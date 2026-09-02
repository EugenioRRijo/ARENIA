# Listados MaPreX — julio 2026 (referencia de precios)

Evidencia primaria transversal a los cuatro dominios, aportada por el autor el 02/09/2026.
Son los tres listados oficiales del software **MaPreX v26.0.0.1** (base de datos
`BDLaing08072026.mdb` del 08/07/2026, zona predeterminada), impresos el 13/07/2026. Los archivos
originales se llamaban «Materiales Julio 2026.pdf», «Equipos Julio 2026.pdf» y «Mano de Obra
Julio 2026.pdf»; aquí se renombran sin cambiar su contenido.

**Papel: referencia y contexto de precios, no lista vigente.** Los listados son de julio 2026
(un mes pasado respecto de su incorporación). Sirven para contrastar, componer proxies fechados y
declarar criterios; una ronda vigente de precios sigue pendiente como trabajo de campo
([PLAN_MULTIDOMINIO.md](../../../PLAN_MULTIDOMINIO.md), Fase M0).

## Moneda y tasa

Todos los precios están en **bolívares**. La tasa declarada dentro del propio listado de mano de
obra (agrupaciones «01JUL @ 633,3644 BS/$») es **633,3644 Bs/USD al 01/07/2026**. Toda conversión
a USD que se derive de estos PDF debe registrar esa tasa y esa fecha; nunca convertir con una tasa
de otro día sin declararlo.

## Los tres archivos

| Archivo | Págs. | Renglones (aprox.) | Columnas | Fecha de precio |
|---|---|---|---|---|
| `materiales.pdf` | 190 | ≈ 12 500 | Ref, Descripción, Und, Fecha, Precio, Proveedor | 09/07/2026 |
| `equipos.pdf` | 51 | ≈ 2 850 | Ref, Descripción, Precio/Alq., **Cop/Depr.**, Total, Proveedor, Fecha | 09/07/2026 |
| `mano_de_obra.pdf` | 13 | ≈ 790 | Ref, Descripción, Jornal, Bono, Agrupación, Nivel/Oficio, Fecha | 01/07/2026 |

Particularidades que importan a la tesis:

- **`equipos.pdf` trae el factor de depreciación por equipo** (columna Cop/Depr.;
  Total = Precio × factor). Es un criterio de mercado externo y fechado para la regla **R6**
  (`CriterioDepreciacion`): permite declarar el criterio en vez de heredarlo del APU manual.
- **`mano_de_obra.pdf` agrupa por tabulador**: construcción («SAL CONST» del 25/03/2026 + bono
  equivalente a 240 USD/mes), **tabulador CIV al 01/07/2026 (43 filas, escalafón P-1…P-10**, con
  ingeniero computista, analista de telecomunicaciones, ingeniero de mantenimiento y gerente de
  proyectos**)**, sector petrolero, PEQUIVEN, METOR, petroquímica y profesionales/TSU. El par
  jornal + bono del tabulador de la construcción es evidencia para la decisión de fuente del FCAS
  del [dossier G0](../../../docs/dossier_g0.md).

## Cobertura por dominio

| Dominio | Qué hay | Qué NO hay |
|---|---|---|
| civil | Los insumos de la línea base: PVC (≈ 829 menciones), cemento, arena, encofrado; retroexcavadoras (49) y compactadoras (44) en equipos; tabulador de la construcción en MO | — |
| telecom | Fibra óptica (≈ 58), UTP, patch panels, racks, telefonía, coaxial; fusionadoras y equipos de red | precios de distribuidores específicos como los de ARENAZA (sirven de contraste, no de reemplazo) |
| industrial | Válvulas (≈ 172), rodamientos, compresores, correas; herramientas y equipos de taller; mecánicos y electricistas por tabulador | cotizaciones reales de repuestos/servicios de los activos concretos de `activos_planta.csv` |
| sistemas | El tabulador CIV (roles de ingeniería, incluido computista y analistas) | tarifas TI de mercado (programadores/desarrolladores) y productividad HH/PF — esta última siempre sale de benchmark declarado (ISBSG) |

## Reglas de uso

1. Nada de estos PDF entra al catálogo directamente. Primero se estructura en CSV canónico
   (Sesión M0.2 del PLAN_MULTIDOMINIO), **verificando cada fila a mano contra el PDF**, con
   columnas de `origen` (archivo + Ref MaPreX) y `fecha_vigencia` (2026-07-09; mano de obra
   2026-07-01), y la conversión Bs→USD con la tasa declarada arriba.
2. Solo se extraen los insumos que los catálogos necesitan; jamás el volcado completo de
   ≈ 16 000 renglones.
3. Cualquier precio citado en la tesis referencia archivo, Ref y fecha.
