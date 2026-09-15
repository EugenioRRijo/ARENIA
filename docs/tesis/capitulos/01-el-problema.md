# Capítulo I — El problema

| Capítulo | Estado | Última revisión |
|---|---|---|
| I. El problema | en redacción (Sesión R1.1: planteamiento y formulación) | 2026-09-15 |

## 1.1 Planteamiento del problema

### 1.1.1 La estimación de costos y la cadena que la sostiene

La estimación de costos articula la formulación técnica de un proyecto con su evaluación financiera. En el ciclo del proyecto, el presupuesto se determina durante la preinversión y se convierte en la referencia de las decisiones posteriores de inversión, contratación y control (Miranda Miranda, s.f.) [verificación pendiente]. Por esa posición en el ciclo, un error del presupuesto no se corrige en las fases siguientes: se propaga hacia el flujo de fondos y hacia los indicadores con los que se decide si el proyecto se ejecuta.

En el procedimiento tradicional, el presupuesto de obra resulta de una cadena de artefactos que deberían derivarse unos de otros: el plano, el cómputo métrico, el análisis de precios unitarios (APU), el presupuesto y el plan de trabajo con su curva de inversión. Cada eslabón se elabora en un soporte distinto, como el plano en un programa de dibujo, el cómputo en una hoja de cálculo y el APU en un programa especializado, y la información pasa de uno a otro por transcripción manual. La literatura que compara la cuantificación tradicional sobre planos bidimensionales con la cuantificación derivada de modelos de información de construcción (BIM) documenta diferencias de tiempo y de exactitud entre ambos procedimientos (Wahab y Wang, 2022) [verificación pendiente], e identifica la falta de estandarización de los elementos del modelo a lo largo del ciclo de vida como un obstáculo principal para automatizar la dimensión de costos (Pishdad et al., 2024) [verificación pendiente].

En Venezuela, la estructura del APU añade condiciones que agravan la situación. El costo de la mano de obra incorpora el factor de costos asociados al salario (FCAS), elevado y variable por su dependencia de la convención colectiva vigente (Convención Colectiva de la Industria de la Construcción, s.f.) [verificación pendiente], a lo que se suman el bono de alimentación, los factores de depreciación de los equipos y, con la dolarización de hecho de la economía, la necesidad de operar en bolívares y en divisas. Los programas de presupuesto de uso regional resuelven estas particularidades del cálculo (DataLaing, s.f.; IP-3, s.f.; Lulo Software, s.f.) [verificación pendiente], pero reciben el cómputo métrico como un dato que el usuario introduce: al no disponer de la geometría del proyecto, no pueden comprobar que las cantidades que costean correspondan a lo que se va a construir.

### 1.1.2 Un caso didáctico: cómo se producen los errores

Para examinar el mecanismo del problema se empleó un caso didáctico: el presupuesto de la obra civil del sistema de drenaje de una clínica, con 24 m de tubería de PVC de 4", cuatro tanquillas de inspección de 0,80 × 0,80 × 0,80 m con paredes de 0,10 m, cinco partidas y un total de 1 586,61 USD. Se trata de un ejercicio académico ficticio: reproduce el contenido y el formato de un presupuesto elaborado por el procedimiento tradicional en Venezuela, pero no corresponde a una obra ejecutada y sus valores no son reales. Su utilidad, por tanto, no es estimar con qué frecuencia se equivoca la práctica, sino mostrar cómo aparecen errores que la revisión del presupuesto final no detecta.

La revisión del caso consistió en recalcular cada cantidad a partir de las dimensiones declaradas en su memoria de cálculo y en contrastar el resultado con los valores empleados en el cómputo, el presupuesto y el plan de trabajo. Se identificaron siete inconsistencias, resumidas en la Tabla 1.1.

**Tabla 1.1**
*Inconsistencias identificadas en el caso didáctico del sistema de drenaje*

| N.º | Elemento | Valor empleado | Valor esperado | Consecuencia |
|---|---|---|---|---|
| 1 | Encofrado | 5,92 m² por tanquilla (23,68 m² en total) | 4,48 m² por tanquilla (17,92 m² en total) | sobreestimación del 32 %; el valor 5,92 no se justifica en la memoria |
| 2 | Concreto | 0,415 m³ por tanquilla (1,66 m³ en total) | 0,224 m³ por tanquilla (0,896 m³ en total) | sobreestimación del 85 % en la partida de mayor precio unitario |
| 3 | Curva de inversión | cierra en 1 575,50 USD (99,30 %) | 1 586,61 USD (100 %) | 11,11 USD sin conciliar entre plan de trabajo y presupuesto |
| 4 | Unidades | cómputo de la tubería en metros | APU de la tubería por pieza | incompatibilidad dimensional entre el cómputo y el APU que lo consume |
| 5 | Diámetro | 3/4" en la memoria de cálculo | 4" en el proyecto y en el APU | error de transcripción que sobrevive sin validación cruzada |
| 6 | Relleno | 1,30 m³ | excavación menos concreto y tubería, ≈ 8,6 m³ | balance volumétrico incoherente |
| 7 | Depreciación | factor 0,03 para el vehículo en un APU y 1,00 en los demás | un factor por equipo con criterio declarado | regla de imputación de equipos no reproducible |

*Nota.* Elaboración propia a partir del ejercicio académico de la clínica; el detalle de cada valor está en el documento de línea base del sistema.

Ninguna de las siete inconsistencias se aprecia leyendo el presupuesto final: el total cuadra con la suma de sus partidas y cada precio unitario es aritméticamente correcto. Todas exigen rehacer el cómputo desde la geometría o contrastar entre sí documentos que el procedimiento tradicional mantiene separados. La transcripción del ejercicio mostró, además, dos hechos que refuerzan esa lectura: el encofrado se computó en metros cúbicos cuando su APU está expresado en metros cuadrados, y cada monto diario del plan de trabajo es menor que el de su partida, de modo que la suma de esas diferencias explica la brecha de 11,11 USD de la curva de inversión.

El fenómeno no es exclusivo de un tipo de obra. Un segundo ejercicio académico, correspondiente a una red de telecomunicaciones, presenta la misma patología en un solo documento: el tubo corrugado figura con 80 m en el cómputo métrico y con 90 m en el presupuesto. En ambos casos la discrepancia nace del mismo lugar, la transcripción manual entre dos tablas que deberían describir la misma cantidad.

### 1.1.3 Naturaleza del problema

Las inconsistencias del caso didáctico no se atribuyen a la impericia de quien elaboró el presupuesto. Comparten un origen estructural: la información se transfiere manualmente entre soportes que no se comunican, y no existe una instancia que verifique que el cómputo derive de la geometría del proyecto, que las unidades del cómputo coincidan con las del APU, que el criterio de depreciación de un equipo sea el mismo en todas las partidas ni que el presupuesto cierre contra su plan de trabajo.

El problema, en consecuencia, no es de cálculo sino de trazabilidad. La cadena que va del plano al presupuesto está interrumpida en varios puntos, y esa interrupción hace que los errores sean indetectables por los medios de revisión habituales, que examinan el documento final y no su procedencia. Los programas de presupuesto disponibles resuelven con solvencia la aritmética del APU; lo que ninguno de ellos puede hacer, al no conocer la geometría, es comprobar que las cantidades que reciben sean las del proyecto.

Resolver este problema requiere un procedimiento en el que cada cantidad del presupuesto conserve su procedencia, de modo que pueda reevaluarse desde su origen; en el que las verificaciones de consistencia entre geometría, cómputo, APU, presupuesto y plan de trabajo se ejecuten de forma automática; y en el que el precio construido por estructura de costos pueda contrastarse con precios de referencia del mercado. La prevalencia de estos errores en obras reales no puede establecerse con casos didácticos y queda declarada como limitación de la investigación: los casos muestran el mecanismo, no su frecuencia.

## 1.2 Formulación del problema

A partir del planteamiento anterior, la investigación se orienta por la siguiente pregunta principal:

¿Cómo automatizar la cadena de trazabilidad desde el modelo geométrico tridimensional hasta el presupuesto de obra, de manera que los análisis de precios unitarios resultantes sean verificables en su consistencia interna y contrastables con precios de referencia del mercado venezolano?

De ella se derivan las siguientes preguntas secundarias:

1. ¿Qué nivel de desarrollo debe alcanzar el modelo tridimensional para que la extracción automática de cantidades sea confiable a efectos presupuestarios?
2. ¿Qué reglas paramétricas permiten derivar las cantidades de obra de las instalaciones sanitarias directamente de la geometría, sin intervención manual?
3. ¿Qué técnica de aprendizaje automático resulta más adecuada para clasificar partidas y estimar precios unitarios cuando la disponibilidad de datos es limitada?
4. ¿Qué verificaciones automáticas de consistencia pueden implementarse a partir del conocimiento geométrico que un programa de presupuesto convencional no posee?
5. ¿Qué grado de exactitud alcanza el presupuesto generado automáticamente frente al elaborado por el procedimiento tradicional, medido según las clases de estimación de AACE International?
6. ¿Puede extenderse el modelo a otros dominios de la ingeniería, como las telecomunicaciones, el mantenimiento industrial y los sistemas de información, sin modificar su núcleo de cálculo y de verificación? *(Esta pregunta corresponde a la variante A de los objetivos; en la variante B, la extensibilidad se examina como resultado complementario y no como pregunta de investigación.)*
