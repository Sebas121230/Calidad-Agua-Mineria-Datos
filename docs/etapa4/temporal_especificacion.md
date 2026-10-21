# Etapa 4 - Página 3: evolución en el tiempo

Página de Power BI: `3. Evolución en el tiempo` (archivo `powerbi/temporal.pbix`).
Responsable: John Sebastian Rodriguez Dominguez.

## 1. Pregunta de análisis

¿La calidad del agua y la disponibilidad del servicio cambiaron a lo largo del periodo 2019-2025,
o el servicio se comportó igual los siete años?

Relación con el propósito del proyecto: la página 2 mostró **dónde** está concentrado el riesgo
(Regional contra Nacional). Esta página responde **cuándo** apareció el problema, qué magnitud
tuvo y si la red de agua se recuperó, para saber si la vigilancia debe mirar la disponibilidad
del servicio y no solo la calidad.

## 2. Unidad de análisis

Cada registro es **una observación diaria de un municipio** (fecha + municipio + sistema de
abastecimiento). No son personas ni muestras únicas: son mediciones repetidas del mismo
territorio. Por eso los promedios se leen como "promedio de las observaciones" y los conteos como
"número de observaciones", nunca como número de habitantes.

El dataset cubre del 2019-01-01 al 2025-12-31 con 2.557 fechas distintas y exactamente un
registro por combinación fecha + municipio.

## 3. Datos de partida y tratamiento previo (Etapa 3)

- Archivo: `dataset_calidad_agua_limpio.csv` (en `main`), generado por `generar_dataset_limpio.py`
  como reproducción en Python del ETL de SSIS.
- 12.989 registros recibidos -> **12.680 aceptados**, 62 duplicados (P07) y 247 enviados a
  revisión (141 de nivel global, P05; 106 con IRCA fuera de 0-100, P08).
- El modelo de Power BI es el mismo de las páginas 1 y 2: tabla `Agua` (12.680 filas),
  `dim_municipio` (29 municipios) y `Calendario` (2.557 fechas).

### Problemas de calidad que todavía afectan este análisis

| Problema | Efecto | Cómo se maneja |
|---|---|---|
| Antes de 2024-T2 no existe ningún registro con nivel `Racionado` ni `Sin servicio` | La serie de servicio antes de 2024 solo tiene dos categorías y el 100 % continuo del Regional es una consecuencia del registro, no de una operación sin incidentes | Se declara en la limitación general y en el Conocimiento 1; no se lee como comparación de calidad pura |
| Nombres de municipio con `@` en lugar de `A`; afecta a Regional y a Nacional | Sin corregir, un mismo municipio aparece dividido en dos | Reemplazar `@` por `A` en Power Query (paso ya hecho en las páginas 1 y 2); quedan 29 municipios |
| 262 registros sin IRCA (2,07 % de 12.680) | El denominador del IRCA es menor que el número de registros | Se excluyen del promedio de IRCA y de los porcentajes de riesgo, y se informa el denominador (12.418) |
| El dataset es sintético: lo genera `generar_dataset.py` y el generador **simula una crisis ENSO en 2024** (`crisis_dip` entre abril y septiembre de 2024) | Los resultados describen el dataset, no el sistema real; y la coincidencia entre la crisis simulada y el quiebre observado no es una prueba de causa | Se declara como limitación y la causa (ENSO, operación o ambas) se presenta siempre como hipótesis |
| El IRCA se registra por el mismo operador regional en cada municipio | Puede no captar el efecto de la racionación sobre la calidad | Se declara como limitación del Conocimiento 2 |
| Banda de riesgo calculada con los rangos del propio dataset, no con la Resolución 2115 de 2007 | Los porcentajes por banda dependen de ese criterio | Se cita el criterio usado en cada indicador |

## 4. Variables

| Variable | Tipo | Uso en la página |
|---|---|---|
| `anio` | Numérica (entero) | Eje de los gráficos 1, 3, 4 y 5; segmentador |
| `periodo` | Categórica (`AAAA-Tn`) | Eje del gráfico 2 (trimestre comparable); segmentador |
| `tipo_region` | Categórica (Regional / Nacional) | Serie del gráfico 1; segmentador |
| `nivel_servicio` | Categórica | Indicadores de continuidad y racionamiento |
| `irca` | Numérica 0-100 | Gráfico 3 y medida de variación |
| `clasificacion_riesgo` | Categórica ordenada | Porcentaje de riesgo alto o inviable |
| `nivel_almacenamiento_pct` | Numérica 0-100 | Gráfico 4 |
| `precipitacion_mm` | Numérica | Gráfico 5 |

## 5. Denominadores

| Indicador | Denominador |
|---|---|
| % de servicio continuo | Todos los registros del periodo seleccionado |
| % de racionamiento o sin servicio | Todos los registros del periodo seleccionado |
| % de riesgo alto o inviable | Registros del periodo con IRCA reportado |
| IRCA promedio | Registros del periodo con IRCA reportado |
| Nivel de almacenamiento promedio | Registros del periodo con dato de almacenamiento |
| Precipitación promedio | Registros del periodo con dato de precipitación |

Ningún indicador suma observaciones de municipios distintos como si fueran personas: cada
registro cuenta una sola vez porque la única relación del modelo es `dim_municipio[municipio]` ->
`Agua[municipio]` (muchos a uno).

## 6. Periodo y comparabilidad

Los siete años son comparables entre sí: cada año tiene los cuatro trimestres completos, 365 o
366 fechas distintas y entre 1.809 y 1.814 observaciones (Regional entre 1.083 y 1.090;
Nacional entre 721 y 728). Por eso se comparan trimestres contra trimestres y años contra años.

Cuando el segmentador de año o de trimestre deja una sola categoría, la medida de variación del
IRCA compara contra el **mismo trimestre del año anterior**; sin filtro de trimestre, compara
contra el año completo anterior.

## 7. Segmentadores

| Segmentador | Campo | Para qué sirve |
|---|---|---|
| Año | `Agua[anio]` | Ver el quiebre en 2024 y el comportamiento de 2025 |
| Periodo | `Agua[periodo]` | Localizar el trimestre exacto del quiebre (2024-T2) |
| Tipo de región | `Agua[tipo_region]` | Separar la Sabana del resto del país en todos los gráficos |

## 8. Fuente

Dataset consolidado del proyecto (ver Etapa 1, "Fuentes de datos"), generado con
`generar_dataset.py` a partir de las 9 fuentes documentadas allí.
