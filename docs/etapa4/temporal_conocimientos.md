# Etapa 4 - Página 3: conocimientos evidentes (evolución en el tiempo)

Página de Power BI: `3. Evolución en el tiempo` (archivo `powerbi/temporal.pbix`).
Responsable: John Sebastian Rodriguez Dominguez.

Las cifras salen del conjunto de datos limpio del proyecto (12.680 mediciones diarias de
municipios entre 2019 y 2025) y coinciden con lo que muestra la página de Power BI. Si no se dice
otra cosa, son de todo el periodo y sin filtros. Se pueden recalcular con
`python calcular_indicadores_temporal.py`.

**Cómo leer el IRCA:** es un índice de 0 a 100 que resume qué tan riesgosa es el agua. Entre más
alto, peor es la calidad.

**Cómo leer los denominadores:** los porcentajes de servicio (continuo, racionamiento o sin
servicio) se calculan sobre todas las mediciones del periodo. El IRCA promedio y el porcentaje de
riesgo alto o inviable usan solo las 12.418 mediciones con IRCA reportado (las 262 sin IRCA quedan
fuera). Todos los porcentajes son de mediciones, no de personas.

## Pregunta de la página

¿La calidad del agua y la disponibilidad del servicio cambiaron a lo largo del periodo 2019-2025,
o el servicio se comportó igual los siete años?

---

## Conocimiento 1: el servicio de la Sabana dejó de ser continuo en un trimestre exacto (2024-T2) y no se recuperó

| Elemento | Contenido |
|---|---|
| Pregunta | ¿En qué momento dejó de ser continuo el servicio de agua en la Sabana y ese cambio fue general o fue solo regional? |
| Variables | El trimestre (`periodo`), el año, el nivel del servicio (`nivel_servicio`) y el tipo de región |
| Procedimiento | Calculamos el porcentaje de mediciones con nivel de servicio "Continuo" en cada trimestre y en cada año, separando por tipo de región, y revisamos la fecha del primer registro no continuo de la Sabana. Se ve en el gráfico 2 y en la primera tarjeta |
| Evidencia | El primer registro Regional no continuo es del 2024-04-01 (FUNZA, Intermitente); ese mismo día aparece "Sin servicio" en MOSQUERA y el primer "Racionado" es del 2024-04-04 en MADRID. Antes de esa fecha los 1.887 registros no continuos del dataset son todos del nivel Nacional y en estado Intermitente, y el Regional registra 100 % continuo en cada trimestre de 2019 a 2024-T1. En 2024-T2 la continuidad Regional cae a 26,39 % y se mueve entre 21,93 % y 25,46 % hasta 2025-T4, mientras el Nacional se mantiene entre 44,81 % y 56,35 % en todo el periodo. Por año: 100 % en 2019-2023, 43,91 % en 2024 y 23,76 % en 2025 |
| Hallazgo | El quiebre no es gradual ni general: ocurre en un trimestre exacto, en la Sabana, y no se recupera en los siete trimestres siguientes |
| Interpretación | La discontinuidad se concentró en la operación regional desde el segundo trimestre de 2024; el resto del país no registra un cambio comparable, así que el dato apunta a una causa operativa regional y no a un fenómeno general del país |
| Utilidad | Acota la ventana de intervención (desde el 2024-04-01) y el responsable operativo, y evita diluir el problema promediando el país entero |
| Limitación | Antes de 2024-T2 no existe ningún registro con nivel "Racionado" ni "Sin servicio", así que la comparación entre periodos mezcla un cambio del servicio con un cambio de las categorías de registro; y los datos son sintéticos, por lo que la causa real debe confirmarse con la operación |

---

## Conocimiento 2: la calidad del agua no se movió mientras el servicio se caía

| Elemento | Contenido |
|---|---|
| Pregunta | ¿La restricción del servicio se ve también en la calidad del agua (IRCA)? |
| Variables | El IRCA, la banda de riesgo (`clasificacion_riesgo`), el año y el nivel del servicio |
| Procedimiento | Calculamos el IRCA promedio y el porcentaje de riesgo alto o inviable de cada año y los contrastamos con el porcentaje de servicio continuo del mismo año. Se ve en el gráfico 3 y en la tercera tarjeta |
| Evidencia | El IRCA promedio por año va de 14,22 (2020 y 2022) a 14,69 (2024): la variación entre años consecutivos nunca pasa de 0,34 puntos. El porcentaje de riesgo alto o inviable se mantiene entre 17,90 % y 19,74 %. En el mismo 2024 en que el servicio continuo cae de 80,30 % a 47,19 %, el IRCA sube solo 0,13 puntos y el riesgo alto sube 0,97 puntos. En Regional el IRCA promedio es 6,61 y en Nacional 26,13, igual que en la página 2 |
| Hallazgo | La disponibilidad se desplomó en 2024 y 2025, pero ningún indicador de calidad acompaña el movimiento |
| Interpretación | El IRCA y las bandas de riesgo no son sensibles a la restricción del servicio: seguir solo el IRCA habría dado por normal todo el periodo en que la Sabana estuvo sin agua continua |
| Utilidad | Obliga a que el tablero de vigilancia incluya indicadores de disponibilidad (continuidad y racionamiento) y no solo de calidad, y define qué se revisa cuando la disponibilidad cae |
| Limitación | El IRCA se registra por el mismo operador regional en cada municipio, así que puede no captar el efecto de la racionación sobre la calidad; además, las 262 mediciones sin IRCA (2,07 %) quedan fuera de los promedios y el denominador cambia levemente entre años |

---

## Conocimiento 3: el almacenamiento avisó un año antes, y su recuperación no devolvió el servicio

| Elemento | Contenido |
|---|---|
| Pregunta | ¿El almacenamiento y la precipitación anticiparon el quiebre, y la recuperación de esos indicadores se tradujo en volver al servicio continuo? |
| Variables | El nivel de almacenamiento (`nivel_almacenamiento_pct`), la precipitación (`precipitacion_mm`), el año, el trimestre y el nivel del servicio |
| Procedimiento | Calculamos el almacenamiento y la precipitación promedio por año y por trimestre y los comparamos con el porcentaje de servicio continuo del mismo periodo. Se ve en los gráficos 4 y 5 |
| Evidencia | El almacenamiento promedio de la Sabana pasa de 70,79 % (2022) a 50,84 % (2023) y a 37,98 % (2024), con la precipitación media de la región cayendo de 2,97 mm (2022) a 1,81 mm (2023) y 1,56 mm (2024), mientras el servicio seguía continuo hasta 2024-T1. En 2025 el almacenamiento se recupera a 61,11 % y la precipitación sube a 2,39 mm, pero la continuidad sigue en 23,76 % anual (entre 21,93 % y 25,46 % por trimestre), peor que el 43,91 % de 2024. En el nivel Nacional el almacenamiento no se mueve (entre 56,66 % y 58,37 % en los siete años) y la precipitación se mantiene entre 3,97 mm y 4,34 mm |
| Hallazgo | El almacenamiento y la precipitación se deterioraron un año antes del quiebre del servicio, y su recuperación en 2025 no devolvió la continuidad |
| Interpretación | El almacenamiento sirve como señal temprana (adelantó un año el problema), pero la relación con el servicio no es mecánica: con 61,11 % de almacenamiento el servicio siguió intermitente, lo que apunta a que la restricción no es solo de oferta hídrica |
| Utilidad | Permite construir una alerta temprana con el almacenamiento y define una verificación adicional (continuidad y racionamiento) antes de declarar resuelta una recuperación |
| Limitación | La coincidencia entre el deterioro de la precipitación y el quiebre es una hipótesis de causa (el generador del dataset simula una crisis ENSO en 2024), no una demostración: habría que contrastarla con los registros del operador y con la serie oficial de precipitación |

---

## Limitación de la página

La serie permite comparar bien los periodos entre sí (siete años completos con los cuatro
trimestres y 365 o 366 fechas por año), pero no permite leer el antes y el después del quiebre como
si fueran la misma medición: hasta 2024-T1 no existe ninguna categoría "Racionado" ni "Sin
servicio", así que el 100 % continuo del Regional antes de 2024 es consecuencia de cómo se
registraron los datos y no de una operación sin incidentes. A eso se suma que el dataset es
sintético (incluye una crisis ENSO simulada en 2024), que hay 262 mediciones sin IRCA (2,07 %) y
que cada registro es un día-municipio, no una persona. Los porcentajes son de observaciones: no se
pueden leer como cobertura de población.

## Decisión sustentada

La vigilancia de la calidad del agua de la Sabana no puede seguir apoyándose solo en el IRCA: la
decisión es incorporar la continuidad del servicio a la agenda de seguimiento y abrir una revisión
operativa de la Sabana con fecha de arranque en 2024-04-01. Se sustenta en tres hallazgos: el
quiebre es de un trimestre exacto, de alcance regional y sin recuperación en siete trimestres
(Conocimiento 1); el IRCA no se movió, con variaciones de 0,34 puntos como máximo, así que un
tablero construido solo con calidad no lo habría detectado (Conocimiento 2); y el almacenamiento se
deterioró un año antes, lo que sirve como alerta temprana, pero su recuperación en 2025 no devolvió
el servicio, así que esa señal por sí sola no basta para cerrar el caso (Conocimiento 3). La causa
(ENSO, operación o ambas) queda como hipótesis y debe confirmarse con los registros del operador
antes de reasignar responsabilidades.

---

## Cuidados que tuvimos con los datos

| Cuidado | Qué hicimos |
|---|---|
| Decir con cuántas mediciones se calcula cada cifra | Los porcentajes de servicio usan todas las mediciones del periodo (12.680 en total). El IRCA promedio y el porcentaje de riesgo alto o inviable usan solo las 12.418 mediciones con IRCA reportado |
| Comparar periodos equivalentes | Los siete años tienen los cuatro trimestres completos y entre 1.809 y 1.814 mediciones. El Conocimiento 1 compara trimestre contra trimestre (2024-T2 contra 2024-T1) y el Conocimiento 3 compara años completos |
| No confundir un dato vacío con un cero | Las 262 mediciones sin IRCA se dejaron vacías y no se convirtieron en cero |
| No sumar mediciones como si fueran personas | Todas las cifras son proporciones de observaciones. Las medidas se calculan sobre `Agua` con una sola relación muchos-a-uno desde `dim_municipio`, así que ningún registro se cuenta dos veces |
| Separar hipótesis de hechos | La causa del quiebre (ENSO, operación o ambas) se presenta como hipótesis en el Conocimiento 3 y en la decisión, apoyada en que el generador del dataset simula la crisis de 2024 |
| No confundir asociación con causa | La comparación entre almacenamiento, precipitación y servicio es una coincidencia en el tiempo; el documento no afirma que una variable cause la otra |
| Revisar datos atípicos | En la Etapa 3 se enviaron 247 registros a revisión (141 por la regla P05 y 106 con IRCA fuera de rango); no entran en este análisis |
| Distinguir datos del ETL de simulación | Las cifras vienen del ETL (12.680 aceptados de 12.989 recibidos); lo que el generador simula es la crisis de 2024, no la serie medida |
