# Etapa 4 - Página 2: conocimientos evidentes (comparación de territorios)

Página de Power BI: `2. Comparación territorial` (archivo `powerbi/territorial.pbix`).
Responsable: John Sebastian Rodriguez Dominguez.

Las cifras salen del conjunto de datos limpio del proyecto (12.680 mediciones diarias de
municipios entre 2019 y 2025) y coinciden con lo que muestra la página de Power BI. Si no se dice
otra cosa, son de todo el periodo y sin filtros.

**Cómo leer el IRCA:** es un índice de 0 a 100 que resume qué tan riesgosa es el agua. Entre más
alto, peor es la calidad.

## Pregunta de la página

¿Hay diferencias reales en la calidad del agua, la cobertura de acueducto y la continuidad del
servicio entre los municipios, o la diferencia está solo entre los de la Sabana de Bogotá
(Regional) y los del resto del país (Nacional)?

---

## Conocimiento 1: el agua de Nacional tiene un IRCA casi cuatro veces mayor que la de Regional

| Elemento | Contenido |
|---|---|
| Pregunta | ¿El agua tiene la misma calidad en los dos grupos de municipios? |
| Variables | El IRCA (calidad del agua) y el grupo del municipio (Regional o Nacional) |
| Procedimiento | Sacamos el promedio del IRCA de cada grupo, usando solo las mediciones que sí tienen IRCA, y restamos: Nacional menos Regional. Se ve en el primer gráfico y en la primera tarjeta de la página |
| Evidencia | Nacional: 26,13 (4.978 mediciones). Regional: 6,61 (7.440 mediciones). La diferencia es de 19,52 puntos. Mirando solo 2024: Nacional 26,65, Regional 6,65 y diferencia de 20,00 |
| Hallazgo | El IRCA promedio de Nacional es casi cuatro veces el de Regional, y la diferencia se repite al mirar un solo año |
| Interpretación | En estos datos, el agua de los municipios Nacional es de peor calidad que la de los Regional |
| Utilidad | Ayuda a decidir a qué grupo darle prioridad cuando se vigila la calidad del agua |
| Limitación | Los datos son sintéticos, así que esto describe este conjunto de datos y no la situación real. Muestra que hay una diferencia entre grupos, pero no explica por qué |

---

## Conocimiento 2: en Regional no hay riesgo alto y en Nacional casi la mitad de las mediciones lo tiene

| Elemento | Contenido |
|---|---|
| Pregunta | ¿Qué tan arriesgada es el agua en cada grupo? |
| Variables | La banda de riesgo del IRCA (sin riesgo, bajo, medio, alto e inviable) y el grupo del municipio |
| Procedimiento | Calculamos qué porcentaje de las mediciones cae en cada banda dentro de cada grupo, contando solo las que tienen IRCA. Se ve en el segundo gráfico y en la tercera tarjeta |
| Evidencia | Regional: 37,59 % sin riesgo, 58,20 % riesgo bajo, 4,21 % riesgo medio y 0 % riesgo alto o inviable. Nacional: 6,69 % sin riesgo (333 mediciones), 17,74 % bajo (883), 29,15 % medio (1.451), 25,63 % alto (1.276) y 20,79 % inviable (1.035). Riesgo alto o inviable en Nacional: 2.311 de 4.978 mediciones, es decir, 46,42 % (49,09 % en 2024: 351 de 715) |
| Hallazgo | Regional no tiene mediciones de riesgo alto ni inviable. En Nacional, casi la mitad de las mediciones con IRCA está en esas dos bandas |
| Interpretación | El riesgo alto se concentra en el grupo Nacional; no está repartido por igual |
| Utilidad | Sirve para ubicar dónde están los casos más críticos y refuerza la prioridad del Conocimiento 1 |
| Limitación | Las bandas usan los rangos del propio conjunto de datos, no los de la norma oficial (Resolución 2115 de 2007). Las 262 mediciones sin IRCA no cuentan en los porcentajes |

---

## Conocimiento 3: la cobertura también cambia entre grupos, y los municipios de cada grupo son casi iguales

| Elemento | Contenido |
|---|---|
| Pregunta | ¿La cobertura de acueducto también cambia entre grupos? ¿Hay municipios que se salgan del patrón de su grupo? |
| Variables | La cobertura de acueducto (en %), el IRCA, el municipio y el grupo |
| Procedimiento | Sacamos el promedio de cobertura de cada grupo con todas sus mediciones y restamos: Regional menos Nacional. Luego pusimos cada municipio como un punto según su cobertura y su IRCA promedio. Se ve en el tercer gráfico y en la segunda tarjeta |
| Evidencia | Cobertura: Regional 94,88 % (7.606 mediciones) y Nacional 77,77 % (5.074 mediciones), una diferencia de 17,12 puntos porcentuales (17,77 en 2024). Los 9 municipios Regional tienen IRCA entre 6,52 y 6,72 y cobertura entre 94,73 % y 95,04 %. Los 20 municipios Nacional tienen IRCA entre 24,29 y 27,54 y cobertura entre 76,50 % y 79,83 % |
| Hallazgo | Nacional tiene menos cobertura que Regional, y dentro de cada grupo los municipios quedan casi en el mismo punto |
| Interpretación | La diferencia está entre los dos grupos, no entre un municipio y otro del mismo grupo |
| Utilidad | Indica que actuar sobre un solo municipio no resolvería el problema: conviene pensar por grupo |
| Limitación | Que los municipios se parezcan tanto puede deberse a cómo se creó el conjunto de datos sintético. Es una hipótesis, no un hecho comprobado: con datos reales se esperaría ver más variación |

---

## Limitación de la página

Los datos son sintéticos (creados para el proyecto), así que los resultados describen este
conjunto de datos y no la situación real. Además, la continuidad del servicio no se puede comparar
de forma justa: en Nacional solo aparecen los niveles Continuo e Intermitente, por eso al filtrar
Racionado o Sin servicio las diferencias quedan en blanco. Las bandas de riesgo no siguen la norma
oficial, y lo que se ve es una diferencia entre grupos, no la causa de esa diferencia.

## Decisión sustentada

Pensar las acciones para mejorar la calidad del agua por grupos de municipios y no uno por uno, y
empezar por el grupo Nacional, donde el 46,42 % de las mediciones con IRCA está en riesgo alto o
inviable. Se sustenta en tres hallazgos: el IRCA de Nacional es casi cuatro veces el de Regional
(Conocimiento 1), el riesgo alto se concentra en Nacional (Conocimiento 2) y dentro de cada grupo
los municipios son casi iguales, así que escoger uno solo no cambiaría el resultado
(Conocimiento 3).

---

## Cuidados que tuvimos con los datos

| Cuidado | Qué hicimos |
|---|---|
| Decir con cuántas mediciones se calcula cada cifra | El IRCA y los porcentajes de riesgo usan solo las mediciones con IRCA (7.440 Regional y 4.978 Nacional). La cobertura usa todas las mediciones del grupo (7.606 y 5.074) |
| Comparar periodos iguales | Los dos grupos cubren 2019-2025 con una cantidad parecida de mediciones por año (Regional entre 1.083 y 1.090; Nacional entre 721 y 728). Repetimos la comparación solo para 2024 y el resultado fue el mismo |
| No confundir un dato vacío con un cero | Las 262 mediciones sin IRCA se dejaron vacías y no se convirtieron en cero. Las 106 con IRCA fuera de 0 a 100 ya estaban en revisión desde la Etapa 3 |
| Separar hipótesis de hechos | En el Conocimiento 3, la explicación de por qué los municipios se parecen se presenta como hipótesis |
| No confundir asociación con causa | Las conclusiones dicen dónde hay diferencias, no por qué ocurren |
| Revisar datos atípicos | En la Etapa 3 se enviaron 247 registros a revisión (141 por la regla P05 y 106 por IRCA fuera de rango); no entran en este análisis |
| No contar dos veces lo mismo | Usamos una lista con cada municipio una sola vez (29 municipios), conectada a las mediciones, para que ninguno se cuente doble. Antes corregimos un error de escritura en los nombres, donde la letra A aparecía como @ |
