# Capítulo II — Marco teórico

| Capítulo | Estado | Última revisión |
|---|---|---|
| II. Marco teórico | en redacción (Sesión R1.4: antecedentes) | 2026-09-15 |

## 2.1 Antecedentes de la investigación

La revisión de antecedentes se organizó en tres ámbitos, internacional, latinoamericano y nacional, y dentro del ámbito internacional en líneas temáticas: la cuantificación y la estimación de costos a partir de modelos BIM, el aprendizaje automático aplicado a costos, el procesamiento de lenguaje natural en textos técnicos de construcción y los modelos digitales con realimentación del activo. De cada trabajo se indica qué hizo y qué aporta a esta investigación. Las referencias se contrastaron con sus fuentes; las que conservan datos por confirmar llevan la marca correspondiente.

### 2.1.1 Ámbito internacional

#### Cuantificación y estimación de costos a partir de modelos BIM

Ma et al. (2011) [verificación pendiente] aplicaron y extendieron el estándar IFC para la estimación de costos en licitaciones de obra en China. Su aporte a esta investigación es mostrar que el formato abierto IFC puede adaptarse a las reglas de un sistema nacional de estimación, que es la decisión que aquí se adopta al tomar IFC como frontera entre el modelado y el cálculo del presupuesto venezolano.

Khosakitchalert et al. (2019) abordaron la mejora de la exactitud de la cuantificación basada en BIM para elementos compuestos. La necesidad misma de mejorar esa exactitud advierte, para esta investigación, que el uso de un modelo no garantiza por sí solo cantidades correctas: la exactitud depende de cómo se modelan los elementos, lo que justifica contrastar las cantidades extraídas con el cálculo manual antes de confiar en ellas.

Wahab y Wang (2021) compararon, elemento por elemento, la cuantificación basada en BIM con la cuantificación tradicional en dos dimensiones, a partir de la constatación de que la literatura no contaba con estudios suficientes para confirmar la superioridad de la primera. Para esta investigación el aporte es metodológico: la ventaja de automatizar el cómputo no se da por supuesta, se mide.

Yang et al. (2022) desarrollaron un modelo de estimación del costo de construcción basado en BIM y en un método paramétrico para la etapa de planificación arquitectónica, tras observar que las estimaciones por unidad de área no consideran otros factores y producen error. Aporta el antecedente de estimar a partir de los parámetros del modelo y no solo del área; esta investigación lleva ese principio a las cantidades de obra de cada partida.

Pishdad y Onungwa (2024) analizaron el uso de BIM‑5D para la estimación de costos, el control de costos y los pagos, y señalaron la falta de integración entre los modelos 5D, el seguimiento del avance y los sistemas de pago, así como la falta de estandarización en el uso de los elementos del modelo. Esas carencias fundamentan dos decisiones de la propuesta: conservar la procedencia de cada cantidad a lo largo de toda la cadena y asociar cada objeto del modelo con un código de partida normalizado.

#### Aprendizaje automático aplicado a costos de construcción

Elmousalami (2020) revisó el estado del arte de la inteligencia artificial y del modelado paramétrico en la estimación de costos de construcción. Su valor para esta investigación es servir de mapa de las técnicas disponibles, a partir del cual se justifica que la técnica se seleccione según los datos existentes.

Tayefeh Hashemi et al. (2020) [verificación pendiente] realizaron una revisión sistemática de las técnicas de aprendizaje automático empleadas para estimar y predecir costos de proyectos de construcción. Aporta el panorama contra el que se contrasta la decisión de degradar la técnica predictiva cuando los datos son escasos.

Kim et al. (2004) compararon modelos de estimación de costos de construcción basados en análisis de regresión, redes neuronales y razonamiento basado en casos. El antecedente respalda que la elección entre esas técnicas es una decisión empírica, dependiente de los datos disponibles, y no una preferencia previa; esta investigación formaliza esa dependencia como un criterio declarado antes de medir.

Huang y Hsieh (2020) predijeron el costo de la mano de obra asociada a BIM con bosques aleatorios y regresión lineal simple. El trabajo muestra la aplicación de un método de ensamble a un costo vinculado con proyectos BIM, familia de técnicas que la propuesta prevé cuando el volumen de datos lo permita.

#### Procesamiento de lenguaje natural en textos técnicos de construcción

Moon et al. (2022) desarrollaron un sistema automatizado de revisión de especificaciones de construcción mediante procesamiento de lenguaje natural. Para esta investigación, confirma que el texto técnico de la construcción puede tratarse de forma automática; aquí el mismo tipo de técnica se aplica a las descripciones de partidas para asociarlas con las del catálogo.

#### Gemelo digital y sombra digital en la construcción

Sacks et al. (2020) formularon la construcción con sistemas de información de gemelo digital a partir de BIM y de la producción lean, y observaron que en edificación e infraestructura el concepto sigue poco definido. Sepasgozar (2021) se propuso diferenciar el gemelo digital de la sombra digital y de otros modelos tridimensionales avanzados. Ambos trabajos aportan el marco con el que se delimita el alcance de esta investigación, desarrollado en las bases teóricas.

#### Síntesis del ámbito internacional

En los trabajos revisados, la cuantificación a partir de modelos BIM y el aprendizaje automático para costos se desarrollan como líneas separadas, y ninguno de ellos incorpora la verificación automática de consistencia entre el cómputo, el presupuesto y el plan de trabajo, ni la estructura de costos derivada de la normativa laboral venezolana. Ese es el espacio que ocupa esta investigación.

### 2.1.2 Ámbito latinoamericano

Rozo-Martínez y Tumay-Gamba (2024) [verificación pendiente] aplicaron la metodología BIM en su dimensión 5D a la gestión del costo de un proyecto de vivienda y compararon los presupuestos elaborados por el método tradicional con los obtenidos a partir del modelo, con el propósito de mostrar sus beneficios económicos para empresas pequeñas. Es el antecedente metodológico más próximo a esta investigación en cuanto a la comparación entre el presupuesto tradicional y el derivado del modelo; a diferencia de él, esta investigación incorpora la verificación automática de consistencia y la estructura de costos venezolana.

Carbonell Charchabal et al. (2026) estudiaron la integración de BIM en el sistema presupuestario cubano para el sector de la construcción. Encontraron que su implementación se encuentra en una fase inicial, limitada principalmente al modelado tridimensional por la complejidad del sistema presupuestario nacional, y destacan que asociar cada componente del modelo con su valor económico favorece la automatización del proceso presupuestario, la trazabilidad de los costos y la coherencia entre el diseño técnico y la estimación financiera. Su aporte es doble: muestra que un sistema presupuestario nacional con reglas propias exige adaptar BIM en lugar de adoptar los flujos internacionales tal como se ofrecen, situación análoga a la venezolana, y respalda la trazabilidad de los costos como beneficio central de la integración.

**Síntesis.** Los trabajos latinoamericanos revisados documentan la aplicación de BIM‑5D a la gestión del costo y la necesidad de adaptarlo a los sistemas presupuestarios nacionales, pero ninguno de ellos automatiza la verificación de consistencia del presupuesto.

### 2.1.3 Ámbito nacional

Quiñones y Uzcátegui (2023) [verificación pendiente] analizaron, en una revista de la Universidad de Los Andes, los beneficios de aplicar la metodología BIM a la optimización de recursos y de los procesos creativos y constructivos de un proyecto de edificación, con base en las buenas prácticas del Project Management Institute y a partir del caso de un conjunto residencial desarrollado en Múnich, Alemania. Su aporte es vincular BIM con la gestión del costo en el marco de la gerencia de proyectos, aunque su caso de estudio no corresponde al contexto normativo venezolano.

Chacón y Cuervo (s.f.) [verificación pendiente] elaboraron, en la Universidad de Carabobo, una guía multimedia para el modelado paramétrico de edificaciones con Revit, en la que comparan la metodología BIM con la metodología CAD tradicional desde la interoperabilidad y la parametrización. Aporta el antecedente nacional de la parametrización como ventaja del modelado BIM, que es la base del motor de reglas paramétricas con el que esta investigación deriva las cantidades de obra.

Garnica (s.f.) [verificación pendiente] propuso una metodología integral de gestión de construcción eficiente coordinada mediante BIM. Aporta el antecedente de concebir BIM como eje de coordinación de la gestión de la construcción, y no solo como herramienta de modelado.

En el plano institucional, el Colegio de Ingenieros de Venezuela presentó una propuesta de ley marco para un plan nacional de adopción de BIM (Colegio de Ingenieros de Venezuela, s.f.) [verificación pendiente], lo que sitúa la incorporación de BIM como un asunto de interés gremial en el país.

**Síntesis y conclusión de la revisión.** En los trabajos revisados en los tres ámbitos no se localizó ninguno que aplique BIM‑5D a la generación y validación de análisis de precios unitarios con la estructura de costos venezolana, ni que integre el modelo geométrico, el aprendizaje automático, la codificación de partidas y la verificación automática de consistencia. Este vacío, acotado al conjunto revisado, es el que ocupa la investigación. La revisión se ampliará con los trabajos cuya referencia no pudo completarse, registrados como pendientes en la lista de referencias.
