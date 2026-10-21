# Etapa 4 - Pagina 2: medidas DAX (comparacion de territorios)

Todas las medidas tienen el prefijo `Terr_` para no chocar con las de otras paginas cuando se
unifique el informe. Se crean en la tabla `Agua` (Nueva medida) y se agrupan en la carpeta de
presentacion `Territorial` (Propiedades > Carpeta de presentacion).

Las medidas usan `dim_municipio[tipo_region]` para separar Regional y Nacional, y las columnas de
`Agua` para los calculos. Si Power BI marca error de sintaxis, cambiar las comas por punto y coma.

## 1. Medidas base

```
Terr_Registros = COUNTROWS ( Agua )

Terr_Registros con IRCA = COUNT ( Agua[irca] )

Terr_IRCA promedio = AVERAGE ( Agua[irca] )

Terr_Cobertura promedio = AVERAGE ( Agua[cobertura_acueducto_pct] )
```

`COUNT` ignora los vacios, por eso `Terr_Registros con IRCA` es el denominador correcto para el
IRCA y para los porcentajes de riesgo.

## 2. Medidas por grupo y brechas (indicadores 1 y 2)

```
Terr_IRCA Regional =
CALCULATE ( [Terr_IRCA promedio], dim_municipio[tipo_region] = "Regional" )

Terr_IRCA Nacional =
CALCULATE ( [Terr_IRCA promedio], dim_municipio[tipo_region] = "Nacional" )

Terr_Cobertura Regional =
CALCULATE ( [Terr_Cobertura promedio], dim_municipio[tipo_region] = "Regional" )

Terr_Cobertura Nacional =
CALCULATE ( [Terr_Cobertura promedio], dim_municipio[tipo_region] = "Nacional" )

Terr_Brecha IRCA =
IF (
    NOT ISBLANK ( [Terr_IRCA Nacional] ) && NOT ISBLANK ( [Terr_IRCA Regional] ),
    [Terr_IRCA Nacional] - [Terr_IRCA Regional]
)

Terr_Brecha cobertura pp =
IF (
    NOT ISBLANK ( [Terr_Cobertura Regional] ) && NOT ISBLANK ( [Terr_Cobertura Nacional] ),
    [Terr_Cobertura Regional] - [Terr_Cobertura Nacional]
)
```

El `IF` evita que, cuando un grupo no tiene registros con el filtro elegido, el vacio se tome como
cero y la brecha salga falsa. En ese caso la tarjeta queda en blanco.

## 3. Riesgo alto o inviable (indicador 3)

```
Terr_Registros riesgo alto o inviable =
CALCULATE (
    COUNT ( Agua[irca] ),
    Agua[clasificacion_riesgo] IN { "Alto riesgo (28-40)", "Inviable sanitariamente (>40)" }
)

Terr_% Riesgo alto o inviable =
DIVIDE ( [Terr_Registros riesgo alto o inviable], [Terr_Registros con IRCA] )

Terr_% Riesgo alto o inviable Nacional =
CALCULATE ( [Terr_% Riesgo alto o inviable], dim_municipio[tipo_region] = "Nacional" )
```

Denominador: registros del grupo con IRCA reportado. Las bandas son las del propio dataset (no las
de la Resolucion 2115 de 2007).

## 4. Columna de orden para las bandas de riesgo

Las bandas se ordenarian alfabeticamente si no se les da un orden. En `Agua`, Nueva columna:

```
Terr_Orden riesgo =
SWITCH (
    Agua[clasificacion_riesgo],
    "Sin riesgo (0-5)", 1,
    "Bajo riesgo (5-14)", 2,
    "Riesgo medio (14-28)", 3,
    "Alto riesgo (28-40)", 4,
    "Inviable sanitariamente (>40)", 5
)
```

Luego seleccionar `clasificacion_riesgo` > Herramientas de columna > Ordenar por columna >
`Terr_Orden riesgo`.

## 5. Uso en la pagina

| Elemento | Campos |
|---|---|
| Tarjeta 1 | `Terr_Brecha IRCA` |
| Tarjeta 2 | `Terr_Brecha cobertura pp` |
| Tarjeta 3 | `Terr_% Riesgo alto o inviable Nacional` |
| Visual 1: columnas, IRCA promedio por region | Eje `dim_municipio[tipo_region]`; valor `Terr_IRCA promedio` |
| Visual 2: barras 100 % apiladas, riesgo por region | Eje `dim_municipio[tipo_region]`; leyenda `Agua[clasificacion_riesgo]`; valor `Terr_Registros con IRCA` |
| Visual 3: dispersion por municipio | Detalles `dim_municipio[municipio]`; X `Terr_Cobertura promedio`; Y `Terr_IRCA promedio`; leyenda `dim_municipio[tipo_region]` |
| Segmentador 1 | `Calendario[Año]` |
| Segmentador 2 | `Agua[nivel_servicio]` |

## 6. Valores esperados (calculados sobre el CSV)

### Indicadores segun el filtro

| Filtro | Brecha IRCA | Brecha cobertura (pp) | % riesgo alto o inviable Nacional |
|---|---|---|---|
| Sin filtros | 19,52 (26,13 - 6,61) | 17,11 (94,88 - 77,77) | 46,42 % (2.311 de 4.978) |
| Año 2024 | 20,00 (26,65 - 6,65) | 17,77 (95,00 - 77,23) | 49,09 % (351 de 715) |
| Año 2024 y nivel Continuo | 20,24 (26,59 - 6,35) | 17,04 (94,84 - 77,80) | 49,19 % (183 de 372) |
| Nivel Racionado | en blanco | en blanco | en blanco |

Con nivel de servicio Racionado (o Sin servicio) no hay registros Nacional, porque esa categoria
solo existe en Regional. Las tarjetas deben quedar en blanco, no en cero.

### Visual 2: distribucion de bandas (sin filtros, sobre registros con IRCA)

| Banda | Regional (n = 7.440) | Nacional (n = 4.978) |
|---|---|---|
| Sin riesgo (0-5) | 37,59 % | 6,69 % |
| Bajo riesgo (5-14) | 58,20 % | 17,74 % |
| Riesgo medio (14-28) | 4,21 % | 29,15 % |
| Alto riesgo (28-40) | 0 % | 25,63 % |
| Inviable sanitariamente (>40) | 0 % | 20,79 % |

### Visual 3: 29 puntos (sin filtros)

| Grupo | Puntos | IRCA promedio (minimo - maximo) | Cobertura promedio (minimo - maximo) |
|---|---|---|---|
| Regional | 9 | 6,52 - 6,72 | 94,73 - 95,04 |
| Nacional | 20 | 24,29 - 27,54 | 76,50 - 79,83 |
