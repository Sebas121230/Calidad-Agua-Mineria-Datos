# Etapa 4 - Pagina 2: comparacion de territorios (especificacion)

## 1. Pregunta de analisis

¿Existen diferencias reales de calidad del agua (IRCA), cobertura de acueducto y continuidad
del servicio entre los territorios del dataset, o la brecha se concentra solo entre la zona
Regional (Sabana de Bogota, area de la EAAB) y la zona Nacional?

Relacion con el proposito del proyecto: identificar donde se concentra el riesgo en la calidad
y la disponibilidad del agua, para saber si una decision territorial debe apuntar a un
municipio concreto o a un grupo de territorios.

## 2. Unidad de analisis

Cada registro es **una observacion diaria de un municipio** (fecha + municipio + sistema de
abastecimiento), con su IRCA, cobertura de acueducto y nivel de servicio ese dia. No son
personas ni muestras unicas: son mediciones repetidas del mismo territorio. Por eso los
promedios se interpretan como "promedio de las observaciones" y los conteos como "numero de
observaciones", nunca como numero de habitantes ni de hogares.

El dataset cubre del 2019-01-01 al 2025-12-31. No hay una observacion por cada dia: hay 2.557
fechas distintas y exactamente un registro por combinacion fecha + municipio.

## 3. Datos de partida y tratamiento previo (Etapa 3)

- Archivo: `dataset_calidad_agua_limpio.csv` (en `main`), generado por `generar_dataset_limpio.py`
  como reproduccion en Python del ETL de SSIS.
- 12.989 registros recibidos -> **12.680 aceptados**, 62 duplicados (P07) y 247 enviados a
  revision (141 de nivel global, P05; 106 con IRCA fuera de 0-100, P08).
- Los vacios de IRCA se conservaron como nulos y se marcaron con `irca_reportado = No`; no se
  imputaron.

### Problemas de calidad que todavia afectan este analisis

| Problema | Efecto | Como se maneja |
|---|---|---|
| Nombres de municipio con `@` en lugar de `A` (p. ej. `CHI@`, `POP@Y@N`); afecta a Regional y a Nacional | Sin corregir, un mismo municipio aparece dividido en dos | Reemplazar `@` por `A` en Power Query; tras corregir quedan 29 municipios (9 Regional + 20 Nacional) |
| 262 registros sin IRCA (2,07 % de 12.680): 166 Regional y 96 Nacional | El denominador del IRCA es menor que el numero de registros | Se excluyen del promedio y se informa el denominador (7.440 Regional, 4.978 Nacional) |
| `nivel_servicio` en Nacional solo tiene Continuo e Intermitente; Regional tambien tiene Racionado y Sin servicio | La mezcla de niveles no es comparable categoria a categoria entre grupos | Se declara como limitacion; no se afirma que Nacional "no raciona" |
| Banda de riesgo calculada con los rangos del propio dataset, no con la Resolucion 2115 de 2007 | Los porcentajes por banda dependen de ese criterio | Se cita el criterio usado en cada indicador |
| El dataset es sintetico: lo genera `generar_dataset.py` a partir de 9 fuentes documentadas | Los resultados describen el dataset, no el sistema real | Se declara en la limitacion del tablero y en el informe |

## 4. Variables

| Variable | Tipo | Uso en la pagina |
|---|---|---|
| `tipo_region` | Categorica (Regional / Nacional) | Grupo principal de comparacion |
| `municipio` | Categorica (29 valores tras homologar) | Comparacion entre territorios |
| `irca` | Numerica 0-100 | Indicador de calidad |
| `clasificacion_riesgo` | Categorica ordenada | Distribucion del riesgo |
| `cobertura_acueducto_pct` | Numerica 0-100 | Indicador de cobertura |
| `nivel_servicio` | Categorica | Continuidad del servicio |
| `anio` | Numerica | Segmentador |
| `sistema_abastecimiento` | Categorica | Segmentador |

## 5. Denominadores

| Indicador | Denominador |
|---|---|
| IRCA promedio | Registros con IRCA reportado (7.440 Regional; 4.978 Nacional) |
| Cobertura promedio | Todos los registros del grupo (7.606 Regional; 5.074 Nacional) |
| % con riesgo alto o inviable | Registros con IRCA reportado del grupo |
| % de servicio continuo | Todos los registros del grupo |

## 6. Periodo y comparabilidad

Ambos grupos cubren los mismos 7 anos completos (2019-2025) y tienen un numero parecido de
registros por ano (Regional entre 1.083 y 1.090; Nacional entre 721 y 728), por lo que los
periodos son equivalentes. Si se filtra un ano, las cifras describen solo ese ano.

## 7. Fuente

Dataset consolidado del proyecto (ver Etapa 1, "Fuentes de datos"), generado con
`generar_dataset.py` a partir de las 9 fuentes documentadas alli.
