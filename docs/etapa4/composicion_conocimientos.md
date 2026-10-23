# Etapa 4 - Página 1: conocimientos evidentes (composición y distribución)

Página de Power BI: `1. Composición` (archivo `powerbi/conocimiento_evidente.pbix`).
Responsable: Diego Armando Guzmán Garzón.

Las cifras salen del conjunto de datos limpio (12.680 mediciones diarias de municipios entre
2019 y 2025). Si no se dice otra cosa, son de todo el periodo y sin filtros.

**Unidad de análisis:** cada registro es una medición diaria de un municipio.

## Pregunta de la página

¿Cómo se distribuyen las mediciones diarias por nivel de riesgo IRCA, nivel de servicio y tipo
de región, y qué grupos predominan o son minoritarios?

## Medidas DAX usadas

| Medida | Fórmula | Denominador |
|---|---|---|
| Registros | `COUNTROWS ( Agua )` | — |
| % Riesgo bajo o nulo | Sin riesgo + Bajo riesgo / registros con IRCA | 12.418 registros con IRCA |
| % Servicio continuo | registros Continuo / Registros | registros del filtro |
| % de la selección | `DIVIDE ( [Registros], CALCULATE ( [Registros], ALLSELECTED ( Agua ) ) )` | registros del filtro |

---

## Conocimiento 1: la mayoría de las mediciones tiene riesgo bajo o nulo

| Elemento | Contenido |
|---|---|
| Pregunta | ¿Qué proporción de las mediciones tiene agua apta para el consumo? |
| Variables | clasificacion_riesgo, irca_reportado |
| Procedimiento | Conteo de registros por categoría de riesgo; porcentaje sobre los 12.418 registros con IRCA (se excluyen los 262 sin dato) |
| Evidencia | Tarjeta % Riesgo bajo o nulo y gráfico de anillo |
| Hallazgo | El 67,18 % (8.343 de 12.418) está en Sin riesgo o Bajo riesgo; el 18,61 % (2.311) en Alto riesgo o Inviable |
| Interpretación | En la mayoría de las mediciones el agua tiene niveles aceptables, pero casi una de cada cinco tiene riesgo alto |
| Utilidad | Dimensiona cuántas mediciones requieren seguimiento sanitario |
| Limitación | Son mediciones, no personas; no indica cuánta población está expuesta |

---

## Conocimiento 2: el servicio continuo bajó en 2024 y 2025

| Elemento | Contenido |
|---|---|
| Pregunta | ¿La composición del nivel de servicio es igual todos los años? |
| Variables | nivel_servicio, Año (tabla Calendario) |
| Procedimiento | % de registros por nivel de servicio filtrando cada año (denominador: registros del año, unos 1.810) |
| Evidencia | Gráfico de barras y tarjeta % Servicio continuo con el segmentador de Año |
| Hallazgo | Entre 2019 y 2023 el servicio continuo estuvo cerca del 80 %; bajó a 47,19 % en 2024 y a 34,03 % en 2025. Racionado y Sin servicio solo aparecen en 2024 y 2025 |
| Interpretación | Hipótesis: el cambio coincide con el racionamiento de agua en Bogotá; los datos muestran la coincidencia, no la causa |
| Utilidad | Identifica el periodo crítico para planear la continuidad del servicio |
| Limitación | Sin datos operativos no se puede afirmar que el racionamiento sea la causa |

---

## Conocimiento 3: los datos sin IRCA son pocos y están repartidos

| Elemento | Contenido |
|---|---|
| Pregunta | ¿Los registros sin IRCA reportado se concentran en algún grupo? |
| Variables | irca_reportado, tipo_region, Año |
| Procedimiento | Conteo de registros con irca_reportado = "No", filtrando por región y por año |
| Evidencia | Sección "Sin dato de IRCA" del anillo con los segmentadores |
| Hallazgo | Son 262 registros (2,07 %): 2,18 % en Regional (166 de 7.606) y 1,89 % en Nacional (96 de 5.074); por año van de 31 a 43 registros |
| Interpretación | Hipótesis: el faltante es disperso y no se concentra en una región ni en un año |
| Utilidad | Permite excluir los faltantes de los indicadores de riesgo sin sesgar la comparación |
| Limitación | No se sabe si el dato falta porque no se midió o porque no se reportó |

---

## Limitación del análisis

Los porcentajes describen mediciones diarias por municipio, no personas ni hogares. Los 262
registros sin IRCA (2,07 %) se excluyen de los indicadores de riesgo.

## Decisión sustentada

Calcular los indicadores de riesgo solo sobre los registros con IRCA reportado (12.418) y mostrar
aparte el 2,07 % sin dato, para no confundir un dato faltante con agua sin riesgo.