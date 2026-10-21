# Etapa 4 - Página 3: preparación de datos en Power BI

Fuente: `dataset_calidad_agua_limpio.csv`

La página 3 **no crea un modelo nuevo**: reutiliza el modelo de las páginas 1 y 2 (tabla `Agua`,
tabla `dim_municipio`, tabla `Calendario` y las relaciones entre ellas) y solo agrega lo que
necesita para leer el tiempo.

## 1. Lo que ya estaba (no se toca)

| Objeto | Estado |
|---|---|
| Consulta `Agua` | 12.680 filas, con los pasos de Power Query de la página 2 (reemplazo de `@` por `A` y tipos de dato con configuración regional en inglés) |
| Tabla `dim_municipio` | 29 filas, una por municipio, sin duplicados |
| Tabla `Calendario` | 2.557 fechas, ligada a `Agua[fecha]` |
| Relaciones | `dim_municipio[municipio]` -> `Agua[municipio]` (muchos a uno, filtro único) y `Calendario[Date]` -> `Agua[fecha]` |
| Medidas base | `Registros`, `% del total`, `Municipios`, `IRCA promedio`, `% sin IRCA reportado`, `% Riesgo bajo o nulo`, `% Servicio continuo`, `% de la selección` y las 23 medidas `Terr_` de la página 2 |

## 2. Lo que agrega esta página

### 2.1 Ocho medidas nuevas (prefijo `Temp_`)

Se crean en la tabla `Agua` (Nueva medida) y se agrupan en la carpeta de presentación
`Temporal` (Propiedades > Carpeta de presentación). El DAX completo está en
`docs/etapa4/temporal_medidas_dax.md`:

| Medida | Qué calcula | Formato |
|---|---|---|
| `Temp_% Servicio continuo` | % de observaciones con nivel de servicio `Continuo` | `0.00%` |
| `Temp_% Racionamiento o sin servicio` | % de observaciones con nivel `Racionado` o `Sin servicio` | `0.00%` |
| `Temp_% Riesgo alto o inviable` | % de observaciones con IRCA reportado en banda alta o inviable | `0.00%` |
| `Temp_% sin IRCA reportado` | % de observaciones sin IRCA (dato faltante) | `0.00%` |
| `Temp_Observaciones con IRCA` | Número de observaciones con IRCA (denominador de los porcentajes de riesgo) | `#,0` |
| `Temp_Nivel almacenamiento promedio` | Nivel de almacenamiento medio del periodo | `0.00` |
| `Temp_Precipitacion promedio` | Precipitación media del periodo en mm | `0.00` |
| `Temp_Variacion IRCA (pp)` | Variación del IRCA promedio frente al periodo comparable del año anterior, en puntos porcentuales | `0.00` |

Nota sobre el formato: las medidas de porcentaje heredadas del archivo base usan la cadena
`0.00\ %;-0.00\ %;0.00\ %`, que muestra el símbolo de porcentaje **literal** y no aplica el factor
×100 (un valor de 0,8 se vería como "0.80 %" en vez de "80.00 %"). Las medidas `Temp_` usan el
especificador estándar `0.00%`, que sí aplica el factor. En esta página solo se usan las medidas
`Temp_`, de modo que los porcentajes se leen correctamente; las medidas heredadas no se modifican
para no afectar la página 2.

### 2.2 Formato de dos columnas

Para que las etiquetas de los gráficos 4 y 5 no muestren decimales largos:

| Columna | Formato |
|---|---|
| `Agua[nivel_almacenamiento_pct]` | `0.00` |
| `Agua[precipitacion_mm]` | `0.00` |

Es un cambio de presentación: no altera ni los valores ni las medidas.

## 3. Ejes y segmentadores de la página

| Elemento | Campo | Por qué |
|---|---|---|
| Segmentador Año | `Agua[anio]` | El eje temporal principal |
| Segmentador Periodo | `Agua[periodo]` | El formato `AAAA-Tn` ordena cronológicamente y permite comparar trimestres |
| Segmentador Tipo de región | `Agua[tipo_region]` | Separa la Sabana del resto del país |
| Eje de los gráficos 1, 3, 4 y 5 | `Agua[anio]` | Columna de la propia tabla de hechos: no depende de la tabla `Calendario` |
| Eje del gráfico 2 | `Agua[periodo]` | 28 periodos (7 años × 4 trimestres) |

Se usan las columnas de `Agua` y no las de `Calendario` para que el eje no dependa de la
relación con el calendario y para que los filtros de la página acts sobre la misma tabla que
calcula las medidas.

## 4. Verificación después de cargar

Estas cifras salen del CSV y deben coincidir exactamente con lo que muestra la página:

| Comprobación | Valor esperado |
|---|---|
| Filas de `Agua` | 12.680 |
| Filas con `tipo_region` = Regional | 7.606 |
| Filas con `tipo_region` = Nacional | 5.074 |
| Filas con IRCA | 12.418 (262 vacías) |
| Municipios distintos (tras corregir `@`) | 29 |
| Fechas distintas en `Calendario` | 2.557 |
| Periodos (`AAAA-Tn`) | 28 |
| Promedio de `irca` (todas las filas) | 14,43 |
| `%` de servicio continuo en todo el periodo | 68,80 % (8.724 de 12.680) |
| `%` de racionamiento o sin servicio en todo el periodo | 7,44 % |
| `%` continuo de Regional en 2024 | 43,91 % |
| `%` continuo de Regional en 2025 | 23,76 % |
| `%` continuo de Nacional en 2024 | 52,06 % |
| Almacenamiento promedio de Regional en 2024 | 37,98 % |
| Almacenamiento promedio de Regional en 2025 | 61,11 % |
| IRCA promedio por año | entre 14,22 y 14,69 (variación máxima entre años consecutivos: 0,34 puntos) |

Si el promedio de `irca` da un valor cercano a 1.443, el tipo decimal se leyó mal: hay que repetir
el paso de Power Query con la configuración regional en inglés (Estados Unidos).

## 5. Cómo se recalculan las cifras

El script `calcular_indicadores_temporal.py` (en la raíz del repositorio) recalcula sobre el CSV
limpio todas las tablas que se citan en los documentos y en los textos de la página:

```
python calcular_indicadores_temporal.py
```

Imprime la serie anual, la continuidad por año y tipo de región, la continuidad por trimestre (la
base del Conocimiento 1), el punto de quiebre con las fechas exactas, la variación del IRCA frente
al año anterior, la cobertura de la serie, el almacenamiento y la precipitación por región y la
homologación de nombres de municipio.
