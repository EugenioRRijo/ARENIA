# Bitácora — Sesión de referencias pendientes

**Fecha:** 2026‑09‑15 · **Rama:** `inc/referencias-pendientes` (worktree
`.claude/worktrees/referencias`) · **Base:** `inc/limpieza-datos-ficticios` (`155b870`, PR #5) ·
**Origen:** pendiente registrado en la [bitácora del Sprint R1](2026-09-15-sprint-r1-capitulos.md).

## Objetivo

Completar las catorce referencias que el Sprint R1 dejó en estado «pendiente», para retirar de los
capítulos las marcas «[verificación pendiente]» que pueda retirarse y dejar el resto con un «Falta»
preciso.

**Resultado:** la lista APA queda con **36 entradas citadas: 32 verificadas y 4 pendientes**. Se
resolvieron diez de las catorce. Las cuatro restantes no dependen de más búsqueda, sino de acceso:
dos repositorios venezolanos no respondieron, una edición no está declarada en ninguna ficha y un
manual solo se distribuye dentro del programa.

## Qué se verificó, y qué corrigió

| Referencia | Resultado |
|---|---|
| Ma et al. (2011) | Crossref invierte apellido y nombre de los cuatro autores chinos. Los apellidos son Ma, Wei, Song y Lou: la cita ya era correcta y la duda queda cerrada |
| Tayefeh Hashemi et al. (2020) | Artículo 1703 de *SN Applied Sciences*. **El resumen no sostiene** lo que le atribuía el capítulo I sobre redes neuronales con conjuntos pequeños: la oración se reescribió para atribuirle solo el repertorio de métodos que la revisión documenta |
| BIMForum (2024) | Especificación LOD 2024, Parte I, PDF oficial de noviembre de 2024; definiciones de LOD 100 a 500 alineadas con AIA E201‑2022 |
| Rozo-Martínez y Tumay-Gamba (2024) | Trabajo de junio de 2024 con enlace al archivo del repositorio. El buscador del repositorio exige verificación antihumana, así que no se obtuvo el identificador persistente |
| Garnica (s.f.) → **Garnica Patiño (2017)** | Tres datos eran erróneos: el título registrado nombraba la metodología GCE, que es el resultado y no el título; la universidad es la **Metropolitana**, no la Católica Andrés Bello; y el año es 2017 (Caracas, noviembre) |
| Colegio de Ingenieros de Venezuela (s.f.) → **(2022)** | Propuesta presentada el 25 de julio de 2022 y publicada el 11 de agosto de 2022 en el sitio del CIV |
| Colegio de Ingenieros de Venezuela (2018) | Comunicado del Departamento de Análisis y Costos, Caracas, 14 de febrero de 2018. Contrastadas sus tres afirmaciones: los factores de las guías «son pura y llanamente ejemplos o referencias», el cálculo «se basa en la Convención Colectiva 2016‑2018 y las Leyes vigentes», y recomienda que cada empresa calcule el suyo para cada obra |
| COVENIN (1999) | El documento de 1999 es el **Suplemento n.º 1** de la norma COVENIN‑MINDUR 2000‑92, firmado en Caracas el 10 de febrero de 1999. **El título registrado estaba cruzado:** «Especificaciones, codificación y mediciones» titula las partes I (carreteras) y III (obras hidráulicas); la de edificaciones es «Mediciones y codificación de partidas para estudios, proyectos y construcción. Parte II.A» |
| Convención colectiva | Gaceta Oficial N.° 6.752 Extraordinario, 6 de julio de 2023. La cláusula 15 fija vigencia desde el depósito y **veinticuatro meses** de duración. Hallazgo: **el texto no menciona el FCAS** |
| AACE International (2020a) → **(2012)** | Se consiguió el texto completo de la 56R‑08 (revisión del 5 de diciembre de 2012). Su clase 3: definición del 10 % al 40 % y exactitud de **−5 % a −15 % / +10 % a +20 %**, más estrecha que la de la 18R‑97. Desaparecen los sufijos «2020a/2020b» |

## El FCAS no está en la convención

Es el hallazgo con más consecuencias. El capítulo I afirmaba que el FCAS «depende» de la convención
colectiva y citaba la convención; el capítulo II decía que la convención «es la base sobre la que se
calcula». La lectura íntegra de la Gaceta Oficial muestra que el texto **no nombra** el factor ni la
expresión «costos asociados al salario». Quien lo calcula y lo publica es el CIV, a partir de las
cláusulas económicas de la convención y de la legislación laboral.

Ambos capítulos se corrigieron para atribuir cada afirmación a su fuente. La decisión D4 —tratar el
FCAS como parámetro declarado del caso de estudio— deja de apoyarse en que faltaba confirmar la
vigencia y pasa a apoyarse en algo verificado: la convención no define ese factor.

## La práctica sectorial de AACE, con cifras

La 56R‑08 ya no es una referencia sin contenido. Su clase 3 admite menos holgura que la 18R‑97
(−5 %/−15 % y +10 %/+20 %, frente a −10 %/−20 % y +10 %/+30 %), de modo que un presupuesto juzgado
con la práctica de edificación tendría un criterio más exigente que el que hoy declara la
especificación de requisitos. El capítulo II lo dice con esas cifras y deja la elección entre ambas
al marco metodológico. Si el tutor opta por la 56R‑08, el cambio alcanza a la ERS y al rango de
`ml/prediction`, no a `core/`.

## Método

- **Crossref** por DOI y por título, con un script local y pausas entre peticiones.
- **Lectura de PDF:** varias fuentes llegan en binario y la herramienta web no las lee. Se extrajo su
  texto con PyMuPDF en un entorno efímero (`uv run --no-project --with pymupdf`), lo que permitió
  leer la Gaceta Oficial, el suplemento de la norma, el comunicado del CIV y la práctica 56R‑08.
- **Descarga por HTTP:** la herramienta web fuerza HTTPS, así que los repositorios que solo sirven
  por HTTP se intentaron con `urllib` desde el script.

## Lo que queda pendiente, y por qué

| Referencia | Por qué sigue pendiente |
|---|---|
| Quiñones y Uzcátegui (2023) | Faltan las páginas. El servidor de la revista (`erevistas.saber.ula.ve`) rechazó HTTPS y agotó el tiempo de espera por HTTP |
| Chacón y Cuervo (s.f.) | Falta el año. El repositorio de la Universidad de Carabobo (`mriuc.bc.uc.edu.ve`) no respondió por ninguna de las dos vías |
| Miranda Miranda (s.f.) | Ninguna ficha declara cuál es la 4.ª edición: hay 3.ª de 1999, una de 2001, 5.ª de 2005 y una de 2010. Falta saber qué edición se consulta y contrastar en ella las dos afirmaciones del capítulo II |
| Lulo Software (s.f.) | El sitio oficial está construido con marcos y no describe las funciones; el manual se distribuye dentro del programa |

Las cuatro se citan con su marca, de modo que ningún capítulo afirma nada sobre ellas sin avisarlo.

## Estado al cierre

- **Metas:** `scripts/meta_redaccion.py` 12/12 y `scripts/meta_datos.py` 3/3.
- **Diagnóstico de la lista:** 62 citas resueltas, ninguna entrada de la lista APA sin citar, y las
  dos entradas consultadas y no citadas siguen fuera de ella.
- **Pruebas negativas sobre los documentos reales:** mover el año de Garnica Patiño hace fallar R5;
  retirar la marca de Quiñones y Uzcátegui hace fallar R6.
