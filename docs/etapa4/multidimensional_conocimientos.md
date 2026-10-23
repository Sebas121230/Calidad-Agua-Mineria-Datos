# Etapa 4 - Página 4: conocimientos evidentes (análisis multivariado)

Página de análisis multivariado (archivo `powerbi/multivariado.pbix`).

Las cifras se calcularon con `dataset_calidad_agua_limpio.csv`: 12.680 mediciones diarias
de municipios entre 2019 y 2025. Si no se indica otra cosa, corresponden a todo el periodo
y sin filtros. La unidad de análisis es una medición diaria de un municipio; no representa
una persona ni un hogar.

## Pregunta de la página

¿Cómo se relacionan la calidad del agua (IRCA), la cobertura de acueducto y la continuidad
del servicio al compararlas simultáneamente por región, municipio y periodo?

## Variables y medidas

| Variable o medida | Uso |
|---|---|
| IRCA | Resume el riesgo de calidad del agua en una escala de 0 a 100 |
| Cobertura de acueducto (%) | Se compara con el IRCA y con los grupos territoriales |
| Nivel de servicio | Distingue Continuo, Intermitente, Racionado y Sin servicio |
| Tipo de región, municipio y año | Permite cruzar los resultados por territorio y periodo |
| Correlación de Pearson | Resume la asociación lineal entre IRCA y cobertura en registros con ambos datos |

El conjunto tiene 12.680 registros. Hay 12.418 con IRCA y cobertura disponibles, que son
los usados para calcular la correlación global. Para comparaciones de IRCA se excluyen los
registros sin ese valor; cada evidencia informa su denominador.

---

## Conocimiento 1: la relación global entre IRCA y cobertura cambia al separar por región

| Elemento | Contenido |
|---|---|
| Pregunta | ¿La asociación entre cobertura e IRCA se mantiene cuando se comparan municipios de la misma región? |
| Variables | IRCA, cobertura de acueducto y tipo de región |
| Procedimiento | Se calcula la correlación de Pearson para los registros con ambos valores, primero en todo el conjunto y luego por región |
| Evidencia | Para los 12.418 pares completos, la correlación global es `r = -0,522`. Al separar los grupos, es `r = -0,002` en Regional (7.440 pares) y `r = -0,002` en Nacional (4.978 pares) |
| Hallazgo | La asociación inversa aparece en el conjunto combinado, pero prácticamente desaparece al comparar dentro de cada región |
| Interpretación | La diferencia global coincide principalmente con la separación entre regiones: Regional tiene mayor cobertura y menor IRCA promedio que Nacional. No se observa una relación lineal apreciable dentro de cada grupo |
| Utilidad | Evita interpretar la correlación global como evidencia de que aumentar cobertura, por sí solo, reduzca el IRCA |
| Limitación | La correlación mide asociación lineal, no causalidad; los resultados describen un conjunto sintético y pueden variar al aplicar filtros |

---

## Conocimiento 2: territorio y nivel de servicio, vistos junto con IRCA y cobertura

| Elemento | Contenido |
|---|---|
| Pregunta | ¿Se mantiene la diferencia entre regiones al comparar registros con el mismo nivel de servicio? |
| Variables | Tipo de región, nivel de servicio, IRCA y cobertura de acueducto |
| Procedimiento | Se agrupan los registros por región y nivel de servicio y se calculan el IRCA y la cobertura promedio de cada grupo |
| Evidencia | Con servicio Continuo, Regional tiene IRCA promedio de 6,59 (6.034 registros con IRCA) y cobertura de 94,86 % (6.170 registros); Nacional, 25,94 (2.495 con IRCA) y 77,62 % (2.554 registros). Con servicio Intermitente, Regional tiene IRCA de 6,58 (485 con IRCA) y cobertura de 95,23 % (493 registros); Nacional, IRCA de 26,32 (2.483 con IRCA) y cobertura de 77,91 % (2.520 registros) |
| Hallazgo | Tanto para el servicio Continuo como para el Intermitente, Nacional registra un IRCA promedio más alto y menor cobertura que Regional |
| Interpretación | En estos datos, la diferencia entre regiones se mantiene dentro de los niveles de servicio comparables; no parece explicarse únicamente por la continuidad |
| Utilidad | Orienta a revisar conjuntamente calidad, cobertura y territorio, sin resumir el desempeño con una sola variable |
| Limitación | Los promedios describen grupos y no todos sus municipios. Los tamaños de los grupos difieren y Nacional agrupa territorios heterogéneos |

---

## Conocimiento 3: el nivel de servicio cambia con el año de forma distinta por región

| Elemento | Contenido |
|---|---|
| Pregunta | ¿La evolución del nivel de servicio entre 2019 y 2025 es igual en Regional y Nacional? |
| Variables | Año, tipo de región y nivel de servicio |
| Procedimiento | Se calcula el porcentaje de registros de cada nivel de servicio dentro de cada combinación de año y región |
| Evidencia | En Regional, el servicio Continuo representa el 100 % de los registros de cada año entre 2019 y 2023 (entre 1.083 y 1.090 registros anuales); baja a 43,9 % en 2024 (476 de 1.084) y a 23,8 % en 2025 (258 de 1.086). “Sin servicio” representa 17,7 % en 2024 y 25,7 % en 2025. En Nacional, el servicio Continuo representa 52,1 % en 2024 y 49,4 % en 2025 |
| Hallazgo | El cambio de composición del servicio se observa con fuerza en Regional, mientras la proporción Nacional de servicio Continuo permanece cerca de la mitad |
| Interpretación | El periodo y la región, considerados juntos, permiten ver un patrón que se pierde al mirar solo el promedio de todos los municipios |
| Utilidad | Ayuda a identificar qué combinación de territorio y periodo conviene revisar primero y a hacer comparaciones anuales |
| Limitación | Los registros son sintéticos y no explican las causas de los cambios. Las proporciones describen registros, no personas ni hogares sin agua |

---

## Conocimiento 4: el servicio continuo no distingue por sí solo los registros con IRCA superior a 40

| Elemento | Contenido |
|---|---|
| Pregunta | ¿La proporción de registros con IRCA superior a 40 cambia entre servicio Continuo e Intermitente dentro de cada región? |
| Variables | Tipo de región, nivel de servicio e IRCA |
| Procedimiento | Se cuentan los registros con IRCA superior a 40 dentro de cada combinación de región y servicio y se divide por los registros de esa combinación que sí tienen IRCA |
| Evidencia | En Nacional, el IRCA supera 40 en 521 de 2.495 registros con servicio Continuo (20,9 %) y en 514 de 2.483 con servicio Intermitente (20,7 %). En Regional no hay registros con IRCA superior a 40 entre los 7.440 valores de IRCA disponibles |
| Hallazgo | En Nacional, las proporciones de IRCA superior a 40 son muy parecidas para el servicio Continuo y el Intermitente; Regional presenta un patrón diferente |
| Interpretación | En este conjunto, la región distingue más estos resultados que la diferencia entre esos dos niveles de servicio. Tener servicio Continuo no permite asumir que el IRCA sea menor |
| Utilidad | Recomienda comprobar la calidad del agua aunque el registro indique servicio Continuo |
| Limitación | IRCA superior a 40 es el corte numérico de esta comparación y no debe confundirse con una clasificación normativa oficial. Los resultados no demuestran causas |

---

## Limitaciones del análisis

El conjunto es sintético; por tanto, los hallazgos describen sus registros y no necesariamente
la situación real de los territorios. Hay distintos tamaños de grupo, faltan algunos valores
de IRCA o cobertura y no se controlan otros factores. Las asociaciones y diferencias no
prueban causalidad ni deben interpretarse como resultados de personas o poblaciones.

## Decisión sustentada

Examinar la calidad y la cobertura dentro de cada región antes de interpretar una asociación
global, revisar la evolución del servicio por territorio y periodo y mantener la vigilancia
de IRCA incluso cuando el servicio se registra como Continuo. Contrastar estos patrones con
fuentes oficiales antes de tomar decisiones sobre territorios reales.
