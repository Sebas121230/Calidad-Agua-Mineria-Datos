# Etapa 4 - Pagina 2: preparacion de datos en Power BI

Fuente: `dataset_calidad_agua_limpio.csv`

## 1. Pasos de Power Query sobre la tabla `Agua`

Inicio > Transformar datos. Los pasos se aplican en este orden:

| # | Paso | Detalle |
|---|---|---|
| 1 | Cargar el CSV | Origen UTF-8 (65001), delimitador coma, primera fila como encabezados |
| 2 | Corregir el caracter `@` | En `municipio`: Reemplazar valores, `@` por `A`. Afecta a 29 filas (17 Regional y 12 Nacional) |
| 3 | Tipos de dato con configuracion regional **Ingles (Estados Unidos)** | `fecha` = Fecha; `anio` y `mes` = Numero entero; `irca`, `cobertura_acueducto_pct`, `nivel_almacenamiento_pct`, `afluencias_m3s`, `precipitacion_mm`, `temperatura_c`, `consumo_m3s`, `latitud` y `longitud` = Numero decimal; el resto, Texto |
| 4 | Dejar los vacios de `irca` como nulos | No reemplazar por 0: un IRCA vacio es "no reportado", no un riesgo cero |

El paso 3 es critico: el CSV usa punto decimal. Con la configuracion regional de Colombia
(coma decimal), Power BI puede leer `8.63` como `863`. Para evitarlo, en cada columna numerica
usar Cambiar tipo > Usando configuracion regional > Ingles (Estados Unidos).

Equivalente en lenguaje M (ajustar la ruta del archivo):

```
let
  Origen = Csv.Document(File.Contents("RUTA\dataset_calidad_agua_limpio.csv"),
           [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
  Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),
  Municipio = Table.ReplaceValue(Encabezados, "@", "A", Replacer.ReplaceText, {"municipio"}),
  Tipos = Table.TransformColumnTypes(Municipio,
          {{"fecha", type date}, {"anio", Int64.Type}, {"mes", Int64.Type},
           {"irca", type number}, {"cobertura_acueducto_pct", type number}},
          "en-US")
in
  Tipos
```

Si la consulta `Agua` ya viene del archivo base del equipo, solo hay que agregar el paso 2 y
comprobar el paso 3.

## 2. Tabla de dimension `dim_municipio`

Se crea para que el segmentador y las comparaciones por territorio no dupliquen valores:

1. En Transformar datos, clic derecho sobre `Agua` > Referencia.
2. Renombrar la consulta nueva a `dim_municipio`.
3. Conservar solo las columnas `municipio`, `tipo_region` y `departamento`.
4. Quitar duplicados sobre `municipio`. Debe quedar **una fila por municipio: 29 filas**.
5. Cerrar y aplicar.

## 3. Relaciones del modelo

| Desde (uno) | Hacia (muchos) | Direccion del filtro |
|---|---|---|
| `dim_municipio[municipio]` | `Agua[municipio]` | Unica (de dim_municipio hacia Agua) |
| `Calendario[Date]` | `Agua[fecha]` | Unica (relacion existente del archivo base) |

Los segmentadores y los ejes de las graficas usan los campos de `dim_municipio` y `Calendario`,
no los de `Agua`. Las medidas se calculan siempre sobre `Agua`. Asi cada registro se cuenta una
sola vez: no hay relacion muchos-a-muchos ni tablas con filas repetidas que inflen los totales.

## 4. Verificacion despues de cargar

Estas cifras salen del CSV y deben coincidir exactamente. Se pueden comprobar con una tarjeta
temporal o en la vista de tabla:

| Comprobacion | Valor esperado |
|---|---|
| Filas de `Agua` | 12.680 |
| Filas con `tipo_region` = Regional | 7.606 |
| Filas con `tipo_region` = Nacional | 5.074 |
| Municipios distintos (antes de corregir `@`: 47) | 29 |
| Filas de `dim_municipio` | 29 |
| Filas con `irca` vacio | 262 (166 Regional y 96 Nacional) |
| Promedio de `irca` (todas las filas) | 14,43 (sobre 12.418 registros) |
| Promedio de `cobertura_acueducto_pct` (todas las filas) | 88,03 |

Si el promedio de `irca` da un valor cercano a 1.443, el tipo decimal se leyo mal: repetir el
paso 3 con la configuracion regional en ingles.
