# Etapa 4 - Página 3: medidas DAX (evolución en el tiempo)

Todas las medidas tienen el prefijo `Temp_`. Se crean en la tabla `Agua` (Nueva medida) y se
agrupan en la carpeta de presentación `Temporal` (Propiedades > Carpeta de presentación).

Las medidas se calculan siempre sobre `Agua`. Los segmentadores (año, periodo, tipo de región)
filtran esa misma tabla, así que todas las cifras de la página se recalculan con los filtros.

## 1. Indicadores de la página (tarjetas)

```
Temp_% Servicio continuo =
DIVIDE (
    CALCULATE ( COUNTROWS ( Agua ), Agua[nivel_servicio] = "Continuo" ),
    COUNTROWS ( Agua )
)
```

```
Temp_% Racionamiento o sin servicio =
DIVIDE (
    CALCULATE (
        COUNTROWS ( Agua ),
        Agua[nivel_servicio] IN { "Racionado", "Sin servicio" }
    ),
    COUNTROWS ( Agua )
)
```

Denominador de las dos: **todos los registros del periodo**, con o sin IRCA. Son porcentajes de
observaciones, no de personas.

## 2. Calidad del agua y denominadores

```
Temp_Observaciones con IRCA =
COUNT ( Agua[irca] )
```

`COUNT` ignora los vacíos, por eso esta medida es el denominador correcto para el IRCA y para los
porcentajes de riesgo.

```
Temp_% Riesgo alto o inviable =
DIVIDE (
    CALCULATE (
        COUNTROWS ( Agua ),
        Agua[clasificacion_riesgo] IN { "Alto riesgo (28-40)", "Inviable sanitariamente (>40)" }
    ),
    CALCULATE ( COUNTROWS ( Agua ), Agua[irca_reportado] = "Si" )
)
```

```
Temp_% sin IRCA reportado =
DIVIDE (
    CALCULATE ( COUNTROWS ( Agua ), Agua[irca_reportado] = "No" ),
    COUNTROWS ( Agua )
)
```

Las bandas de riesgo son las del propio dataset (no las de la Resolución 2115 de 2007) y el
denominador de `Temp_% Riesgo alto o inviable` son los registros con IRCA reportado.

## 3. Indicadores físicos (almacenamiento y precipitación)

```
Temp_Nivel almacenamiento promedio =
AVERAGE ( Agua[nivel_almacenamiento_pct] )
```

```
Temp_Precipitacion promedio =
AVERAGE ( Agua[precipitacion_mm] )
```

Son promedios de las observaciones del periodo, no acumulados. `AVERAGE` ignora los registros sin
dato, así que el denominador de cada promedio son las observaciones con dato.

## 4. Variación del IRCA frente al periodo comparable

```
Temp_Variacion IRCA (pp) =
VAR AnioActual = MAXX ( Agua[anio], Agua[anio] )
VAR PeriodoUnico = MAXX ( VALUES ( Agua[periodo] ), VALUES ( Agua[periodo] ) )
VAR IRCAAnterior =
    IF (
        COUNTROWS ( VALUES ( Agua[periodo] ) ) = 1,
        CALCULATE (
            [IRCA promedio],
            REMOVEFILTERS ( Agua[periodo] ),
            Agua[periodo] = STR ( AnioActual - 1 ) & "-" & RIGHT ( PeriodoUnico, 2 )
        ),
        CALCULATE (
            [IRCA promedio],
            REMOVEFILTERS ( Agua[periodo] ),
            Agua[anio] = AnioActual - 1
        )
    )
RETURN
    IF ( NOT ISBLANK ( IRCAAnterior ), [IRCA promedio] - IRCAAnterior )
```

Cómo se lee:

- Si el segmentador de periodo deja **un solo trimestre** (por ejemplo 2024-T2), la comparación es
  contra el **mismo trimestre del año anterior** (2023-T2): es la comparación de equivalentes que
  pide la rúbrica y evita comparar un trimestre seco con uno lluvioso.
- Si el filtro deja varios trimestres o el año completo, la comparación es contra el **año
  anterior completo**.
- `REMOVEFILTERS ( Agua[periodo] )` quita el filtro de trimestre antes de reimponer el del año
  anterior; `REMOVEFILTERS` sobre `Agua[periodo]` no toca el filtro de `Agua[anio]`, así que el
  año anterior queda acotado.
- El `IF ( NOT ISBLANK ( ... ) )` evita que la tarjeta muestre una variación falsa cuando el
  año anterior no tiene datos en el filtro elegido (por ejemplo 2019, que no tiene 2018): en ese
  caso la tarjeta queda en blanco.

El resultado se expresa en **puntos porcentuales** (diferencia de dos promedios de IRCA), no en
porcentaje de variación relativa.

## 5. Medidas heredadas que no se usan en esta página

El archivo base trae `% Servicio continuo`, `% sin IRCA reportado`, `% Riesgo bajo o nulo` y las
23 medidas `Terr_` de la página 2. En esta página se usan las medidas `Temp_` porque:

1. su formato es el especificador estándar `0.00%`, que aplica el factor ×100 (las medidas
   heredadas usan `0.00\ %;-0.00\ %;0.00\ %`, que muestra el porcentaje como texto literal);
2. `Temp_% Riesgo alto o inviable` deja explícito el denominador (registros con IRCA reportado) en
   la propia medida, sin depender de `Terr_Registros con IRCA`;
3. `Temp_Variacion IRCA (pp)` necesita la comparación contra el periodo equivalente, que no
   existía en el archivo base.

Las medidas heredadas no se modificaron, para no cambiar lo que muestra la página 2.

## 6. Comprobación rápida

Con los filtros en "Todos" y sin segmentador de periodo:

| Medida | Valor esperado |
|---|---|
| `Temp_% Servicio continuo` | 68,80 % |
| `Temp_% Racionamiento o sin servicio` | 7,44 % |
| `Temp_% Riesgo alto o inviable` | 18,61 % (2.311 de 12.418) |
| `Temp_% sin IRCA reportado` | 2,07 % |
| `Temp_Observaciones con IRCA` | 12.418 |
| `Temp_Nivel almacenamiento promedio` | 59,84 |
| `Temp_Precipitacion promedio` | 3,14 |
| `Temp_Variacion IRCA (pp)` | -0,23 (2025 contra 2024) |
