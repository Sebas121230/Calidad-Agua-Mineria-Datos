# Calidad y Accesibilidad del Agua - Mineria de Datos

Aplicacion Flask y scripts que documentan las **etapas 1 a 5** del proyecto de Mineria
de Datos sobre la disponibilidad y continuidad del servicio de agua potable en Bogota D.C.
(2019-2025).

**Universidad de Cundinamarca** - Ingenieria de Sistemas y Computacion

## Integrantes

- Diego Armando Guzman Garzon
- Andres Felipe Beltran Barrera
- Juan Sebastian Rodriguez Rivero
- John Sebastian Rodriguez Dominguez

## Estructura del proyecto

```
Calidad-Agua-Mineria-Datos/
├── app.py                  # Rutas de la aplicacion Flask
├── requirements.txt        # Dependencias
├── README.md
├── scripts/                # Scripts de generacion, limpieza y auditoria
├── datos/                  # CSV de entrada, salidas y evidencias
├── docs/                   # Documentacion de las etapas
│   └── etapa5/             # Modelo estrella y diagrama
├── etapa3/                 # ETL SSIS y scripts SQL de la Etapa 3
│   ├── ETL_CalidadAgua/    # Proyecto de Visual Studio
│   └── sql/
├── etapa5/                 # Modelo multidimensional en SQLite
│   ├── cargar_modelo.py
│   ├── calidad_agua_dw.db
│   └── sql/
├── static/                 # CSS e imagenes
└── templates/              # Vistas Flask por etapa
```

## Como ejecutar el proyecto

```bash
# 1. Crear el entorno virtual
python -m venv venv

# 2. Activarlo
#    Windows:
.\venv\Scripts\Activate
#    Linux / macOS:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python app.py
```

Luego abrir <http://127.0.0.1:5000> en el navegador.

## Contenido de la Etapa 1

| # | Submenu | Estado |
|---|---------|--------|
| 1 | Problema y contexto | Completo |
| 2 | Pregunta principal y preguntas secundarias | Completo |
| 3 | Necesidades de informacion | Completo |
| 4 | Fuentes de datos | Completo |
| 5 | Dataset | Estructura lista, pendiente consolidar datos |
| 6 | Diccionario de datos | Estructura lista, pendiente consolidar datos |
| 7 | Calidad inicial de los datos | Estructura lista, pendiente perfilado |
| 8 | Limitaciones y consideraciones | Completo |

## Flujo de trabajo con Git

El desarrollo de la Etapa 1 se realiza en la rama `feature/etapa-1`.
Una vez validada, se integra a `main` mediante merge.

## Etapa 3 - Limpieza de datos con SSIS

Proceso ETL en SQL Server Integration Services que trata los problemas de calidad
identificados en la Etapa 2 sobre `datos/dataset_calidad_agua.csv` (12.989 registros), en tres
iteraciones documentadas en la tabla `etl_log`.

### Contenido

```
Calidad-Agua-Mineria-Datos/
├── etapa3/
│   ├── ETL_CalidadAgua/                    # Proyecto de Visual Studio (SSIS)
│   │   ├── ETL_CalidadAgua.slnx            # Abrir este archivo
│   │   └── ETL_CalidadAgua/Package.dtsx    # Paquete: Control Flow y Data Flows
│   └── sql/
│       ├── 01_crear_staging.sql            # Zona staging (datos originales, todo texto)
│       ├── 02_crear_destino.sql            # Datos limpios con tipos reales y llave UNIQUE
│       ├── 03_crear_revision.sql           # Registros rechazados con valor original y motivo
│       ├── 04_crear_log.sql                # Una fila por ejecucion con los conteos
│       ├── 05_consultas_verificacion.sql   # Evidencias y verificacion de resultados
│       └── 06_sql_del_paquete.sql          # SQL que ejecuta SSIS internamente
├── datos/
│   ├── dataset_calidad_agua.csv            # Datos originales
│   └── resultados_iteraciones.csv          # Log exportado de las tres iteraciones
```

### Como reproducir el proceso

Requisitos: SQL Server 2025 (Developer), SSMS y Visual Studio con la extension
*SQL Server Integration Services Projects 2022+*.

1. En SSMS, crear la base de datos `CalidadAgua_ETL` y ejecutar `etapa3/sql/01` a `etapa3/sql/04` en orden.
2. Abrir `etapa3/ETL_CalidadAgua/ETL_CalidadAgua.slnx` en Visual Studio.
3. En *Administradores de conexiones*, editar `CSV_CalidadAgua` y seleccionar la ruta local
   de `datos/dataset_calidad_agua.csv`. La conexion a `localhost` usa autenticacion de Windows
   (el repositorio no contiene contrasenas).
4. Fijar la variable `vIteracion` (1, 2 o 3) y `vObservacion`, y ejecutar el paquete.
5. Revisar los resultados con `etapa3/sql/05_consultas_verificacion.sql`.

### Resultados

| Iteracion | Recibidos | Aceptados | Duplicados | Revision | Ya cargados |
|---|---|---|---|---|---|
| 1 | 12.989 | 1.732 | 12 | 11.245 | 0 |
| 2 | 12.989 | 12.680 | 62 | 247 | 0 |
| 3 (1.a ejecucion) | 12.989 | 12.680 | 62 | 247 | 0 |
| 3 (re-ejecucion del mismo lote) | 12.989 | 0 | 0 | 247 | 12.742 |

En todas las ejecuciones: recibidos = aceptados + duplicados + revision + ya cargados.
La re-ejecucion del mismo lote no genera duplicados.

### Video de demostracion

El video de la entrega se incrusta en la pagina `/etapa3/video` con un `<iframe>` a
`https://www.youtube-nocookie.com/embed/wH8ADSF4i8c` (`youtube-nocookie` no guarda
cookies de seguimiento). Para cambiarlo basta con definir la variable de entorno
`ETAPA3_VIDEO_URL` o editar `VIDEO_URL` y `VIDEO_WATCH` en `app.py`; el archivo de
video no se versiona en el repositorio.

El desarrollo de la Etapa 3 se realiza en la rama `feature/limpieza_de_datos`.

## Etapa 4 - Mineria para Descubrimiento de Conocimiento Evidente

### Tableros

El menu de la Etapa 4 incluye tres tableros: la **Dimension territorial** en
`/etapa4/territorial`, la **Dimension temporal** en `/etapa4/temporal` y el **Analisis
multivariable** en `/etapa4/multivariable`.
El tablero multivariable relaciona IRCA, cobertura de acueducto, nivel de servicio,
municipio, region y periodo. Incluye indicadores, dispersion por registro, comparacion
de grupos y las combinaciones trimestrales mas frecuentes, con filtros interactivos de
año y region. Sus agregaciones se calculan sobre el dataset limpio; las relaciones son
descriptivas y no implican causalidad.

El tablero temporal sigue la serie 2019-2025 trimestre a trimestre: continuidad del
servicio por año y region, IRCA promedio por año, almacenamiento y precipitacion por año, con
filtros de año, periodo y tipo de region. Sus cifras se recalculan sobre el dataset limpio.

```
Calidad-Agua-Mineria-Datos/
├── scripts/
│   ├── generar_dataset_limpio.py          # Reproduce en Python el resultado del ETL (SSIS)
│   └── calcular_indicadores_temporal.py   # Recalcula los indicadores por año y trimestre
├── datos/
│   ├── dataset_calidad_agua_limpio.csv    # Salida: equivalente a dst_calidad_agua
│   └── dataset_calidad_agua_revision.csv  # Salida: equivalente a rev_calidad_agua
└── templates/etapa4/
    ├── territorial.html                   # Tablero de la dimension territorial
    ├── temporal.html                      # Tablero de la dimension temporal
    └── Multivariada.html                  # Tablero de analisis multivariable
```

**Por que un script en Python y no la tabla `dst_calidad_agua` de SQL Server:** el
paquete SSIS de la Etapa 3 corre contra una base de datos local que no se exporta ni
se versiona en el repositorio. `scripts/generar_dataset_limpio.py` aplica, en Python puro,
las mismas reglas documentadas en `Informe_Etapa3_Calidad_Agua.pdf` (normalizacion,
validacion P05/P09/P08, clasificacion de riesgo y llave unica fecha+municipio+sistema
para los duplicados P07), para que el tablero de Flask tenga un dataset limpio sin
depender de SQL Server. Se valido que coincide **exactamente** con la iteracion 2 del
ETL real registrada en `datos/resultados_iteraciones.csv`: 12.680 aceptados, 62 duplicados y
247 en revision sobre 12.989 recibidos.

Para regenerar los archivos limpios:

```bash
python scripts/generar_dataset_limpio.py
```

**Pregunta de analisis:** ¿la calidad (IRCA) y la disponibilidad del servicio de
agua varian de forma real entre los municipios de la Sabana de Bogota, o la
diferencia territorial que realmente importa es otra?

**Hallazgo principal:** no hay una diferencia real entre los 9 municipios de la
Sabana (rango de 0.2 puntos de IRCA frente a una desviacion estandar intra-municipio
de ~4.1 a 4.3 puntos: la diferencia es ruido estadistico). La diferencia territorial
real y grande esta entre **Regional (Sabana) vs Nacional**: 19.52 puntos de brecha en
IRCA y 17.11 puntos porcentuales en cobertura de acueducto.

**Limitacion conocida:** 8 de los 9 municipios de la Sabana llegan con una variante
corrupta del nombre (la letra "A" aparece como "@", p. ej. "CHI@" junto a "CHIA").
Esta corrupcion ya viene del dataset original y el ETL de la Etapa 3 no la corrige
(su regla P10 solo hace `UPPER(TRIM(...))`). Se homologa unicamente dentro de la capa
de agregacion del tablero (`app.py`), sin modificar `datos/dataset_calidad_agua_limpio.csv`,
para no alterar el resultado ya validado de la Etapa 3.

El desarrollo de la Etapa 4 (dimension territorial) se realiza en la rama
`feature/dim-territorial`.


## Etapa 4 - Conocimiento evidente en Power BI

La Etapa 4 se entrega como un informe de Power BI con cuatro paginas (una por integrante) y una
seccion de la aplicacion Flask que lo presenta. Esta parte documenta la **pagina 2: comparacion de
territorios**.

Responsable: John Sebastian Rodriguez Dominguez.

**Pregunta de la pagina:** ¿hay diferencias reales en la calidad del agua, la cobertura de
acueducto y la continuidad del servicio entre los municipios, o la diferencia esta solo entre los
de la Sabana de Bogota (Regional) y los del resto del pais (Nacional)?

**Resultados principales** (todo el periodo 2019-2025, sin filtros):

- El IRCA promedio de Nacional (26,13) es casi cuatro veces el de Regional (6,61).
- En Regional no hay mediciones de riesgo alto ni inviable; en Nacional son el 46,42 %.
- Dentro de cada grupo los municipios son casi iguales: la diferencia esta entre los dos grupos.

### Contenido

El archivo `.pbix` y las fichas de `docs/etapa4/` no se versionan en esta rama; el informe
publicado se incrusta en la aplicacion. Los archivos que si acompañan esta pagina son:

```
Calidad-Agua-Mineria-Datos/
├── scripts/
│   └── generar_dataset_limpio.py          # Reproduce en Python el resultado del ETL (SSIS)
├── datos/
│   ├── dataset_calidad_agua_limpio.csv    # Salida: equivalente a dst_calidad_agua
│   ├── dataset_calidad_agua_revision.csv  # Salida: equivalente a rev_calidad_agua
│   └── resultados_iteraciones.csv         # Log de las iteraciones del ETL
└── templates/etapa4/
    └── conocimiento_evidente.html         # Seccion "Conocimiento evidente" de la aplicacion
```

### Como abrir el informe

El informe se consulta en `/etapa4/conocimiento-evidente`, donde se incrustan sus cuatro
paginas. Si se abre una copia local del `.pbix` en Power BI Desktop y aparece
`DataSource.NotFound`, se cambia el origen de datos a `datos/dataset_calidad_agua_limpio.csv`.

### Datos y periodo

Fuente: `datos/dataset_calidad_agua_limpio.csv` (resultado de la limpieza de la Etapa 3), 12.680
mediciones diarias de municipios entre 2019-01-01 y 2025-12-31. Es un conjunto de datos sintetico.

### Seccion en la aplicacion

Con la aplicacion en marcha, el menu lateral tiene la entrada **Conocimiento evidente (Power BI)**
(`/etapa4/conocimiento-evidente`), con el proposito, las cuatro preguntas, el informe y la fuente
de los datos.

La pagina ya trae el identificador del informe publicado y arma una vista por pagina con
`pageName`. Se puede cambiar con las variables de entorno `POWER_BI_REPORT_ID` y
`POWER_BI_GROUP_ID`; el enlace de apertura se ajusta con `CONOCIMIENTO_EVIDENTE_URL`.

El desarrollo de la pagina territorial en Power BI se realiza en la rama
`feature/conocimiento-territorial`.


## Etapa 4 - Conocimiento evidente en Power BI (pagina 3: evolucion en el tiempo)

Esta parte documenta la **pagina 3: evolucion en el tiempo** del informe de Power BI y el tablero
correspondiente de la aplicacion (`/etapa4/temporal`).

Responsable: John Sebastian Rodriguez Dominguez.

**Pregunta de la pagina:** ¿la calidad del agua y la disponibilidad del servicio cambiaron a lo
largo del periodo 2019-2025, o el servicio se comporto igual los siete años?

**Resultados principales** (todo el periodo 2019-2025, sin filtros):

- El servicio de la Sabana dejo de ser continuo en un trimestre exacto (**2024-T2**, primer registro
  no continuo el 2024-04-01) y no se recupero en los siete trimestres siguientes: la continuidad
  Regional pasa de 100 % (2019-2023) a 43,91 % (2024) y 23,76 % (2025), mientras el Nacional se
  mantiene entre 48,76 % y 52,06 %.
- El IRCA no se movio: entre 14,22 y 14,69 por año, con variaciones de 0,34 puntos como maximo
  entre años consecutivos, en el mismo periodo en que el servicio continuo caia de 80,30 % a
  47,19 %. Un tablero construido solo con calidad no habria detectado el quiebre.
- El almacenamiento de la Sabana se deterioro un año antes del quiebre (70,79 % en 2022, 50,84 % en
  2023 y 37,98 % en 2024) y sirve de alerta temprana, pero su recuperacion en 2025 (61,11 %) no
  devolvio el servicio.

### Contenido

El archivo `.pbix` y las fichas de `docs/etapa4/` no se versionan en esta rama; el informe
publicado se incrusta en la aplicacion. Los archivos que si acompañan esta pagina son:

```
Calidad-Agua-Mineria-Datos/
├── scripts/
│   └── calcular_indicadores_temporal.py   # Recalcula las tablas citadas
├── datos/
│   └── dataset_calidad_agua_limpio.csv    # Fuente de los indicadores
└── templates/etapa4/
    └── temporal.html                      # Tablero de la dimension temporal
```

### Como abrir el informe

El informe se consulta en `/etapa4/conocimiento-evidente`, donde se incrustan sus cuatro
paginas. Si se abre una copia local del `.pbix` en Power BI Desktop y aparece
`DataSource.NotFound`, se cambia el origen de datos a `datos/dataset_calidad_agua_limpio.csv`.

### Datos y periodo

Fuente: `datos/dataset_calidad_agua_limpio.csv` (resultado de la limpieza de la Etapa 3), 12.680
mediciones diarias de municipios entre 2019-01-01 y 2025-12-31. Es un conjunto de datos sintetico:
el generador simula una crisis ENSO en 2024, por lo que la causa del quiebre se presenta siempre
como hipotesis.

### Seccion en la aplicacion

El menu lateral tiene la entrada **Dimension temporal** (`/etapa4/temporal`), con los indicadores,
las cuatro graficas, los tres conocimientos evidentes, la limitacion y la decision sustentada. Los
filtros de año, periodo y tipo de region recalculan todo el tablero sobre el dataset limpio.

El desarrollo de la pagina temporal en Power BI se realiza en la rama
`feature/conocimiento-temporal`.
## Etapa 5 - Analisis multidimensional

### Modelo estrella

Modelo multidimensional en SQLite construido a partir de `datos/dataset_calidad_agua_limpio.csv`
(12.680 mediciones diarias de 29 municipios, 2019-2025).

- Tabla de hechos: `fact_medicion` (una medicion diaria de un municipio).
- Dimensiones: `dim_tiempo`, `dim_geografia`, `dim_sistema`, `dim_riesgo` y `dim_servicio`.
- Jerarquias: anio > trimestre > mes > dia; tipo_region > departamento > municipio;
  grupo_riesgo > clasificacion.
- Diagrama y diccionario: [docs/etapa5/modelo_estrella.md](docs/etapa5/modelo_estrella.md).

### Archivos

| Archivo | Contenido |
|---|---|
| `etapa5/sql/01_crear_modelo.sql` | Creacion de tablas, claves y relaciones |
| `etapa5/cargar_modelo.py` | Carga reproducible del CSV a las dimensiones y la tabla de hechos |
| `etapa5/sql/02_validaciones.sql` | Claves unicas, claves foraneas, duplicados, faltantes y comparacion con el CSV |
| `etapa5/calidad_agua_dw.db` | Base SQLite ya cargada, lista para consultar |

### Como crear y cargar la base

Requisitos: Python 3.10 o superior. No necesita librerias adicionales (usa `csv` y `sqlite3`).

```
python etapa5/cargar_modelo.py
```

El script borra la base si existe, la vuelve a crear, carga los datos e imprime las comprobaciones
contra el CSV (todas deben salir `OK`). Para consultar la base desde Flask:

```python
import sqlite3
con = sqlite3.connect("etapa5/calidad_agua_dw.db")
```

### Operaciones Slice y Dice

Responsable: John Sebastian Rodriguez D.

Vista interactiva en la aplicacion: menu **Etapa 5 - Analisis multidimensional > Slice y Dice:
riesgo y continuidad** (ruta `/etapa5/slice-dice`). Todos los indicadores, tablas, matrices y
graficas se calculan con consultas a `etapa5/calidad_agua_dw.db`; al cambiar un filtro las medidas se
recalculan desde la tabla de hechos (no se suman ni se promedian porcentajes de otros grupos).

**Pregunta de la vista:** que subconjuntos del territorio y del tiempo concentran el riesgo sanitario
del agua y la perdida de continuidad del servicio, y como cambian al combinar region, periodo y
sistema de abastecimiento.

| Archivo | Contenido |
|---|---|
| `etapa5/sql/03_consultas_slice_dice.sql` | Consultas de los ejemplos (S0-S2 slice, D1-D3 dice) y validaciones V1-V3 |
| `etapa5/consultas_slice_dice.py` | Modulo con las consultas parametrizadas que usa Flask |
| `app.py` | Rutas `/etapa5/slice-dice` (vista) y `/etapa5/slice-dice/datos` (API JSON) |
| `templates/etapa5/slice_dice.html` | Vista: indicadores, filtros, matrices, 2 graficas y 2 conocimientos |
| `templates/base.html` | Enlace en el menu de la Etapa 5 |

#### Ejemplos implementados

| Operacion | Filtros | Nivel / matriz | Resultado principal |
|---|---|---|---|
| **Slice** | `tipo_region = 'Nacional'` (una dimension, un valor) | departamento; nivel de servicio x grupo de riesgo | 46,4 % de mediciones en riesgo alto o inviable (total: 18,6 %); los 19 departamentos entre 38,6 % y 52,5 %; continuo 45,4 % vs. intermitente 47,5 % |
| **Dice** | `tipo_region = 'Regional'` + `anio IN (2024, 2025)` + `sistema IN ('Chingaza', 'Sur', 'Tibitoc')` (tres dimensiones) | trimestre; sistema x nivel de servicio; comparacion con 2022-2023 | Servicio continuo de 100 % a 33,8 % (-66,2 p.p.); quiebre desde 2024-T2; en 2025 el almacenamiento (61,1 %) supera al de 2022-2023 y las interrupciones suben a 50,5 % |

#### Medidas y denominadores

| Medida | Calculo | Denominador |
|---|---|---|
| % riesgo alto o inviable | mediciones "Alto o inviable" / mediciones con IRCA | Mediciones con IRCA reportado |
| % servicio continuo | promedio de `es_continuo` | Todas las mediciones del grupo |
| % racionado o sin servicio | mediciones Racionado o Sin servicio / mediciones | Todas las mediciones del grupo |
| IRCA y almacenamiento promedio | `AVG` sobre la tabla de hechos | Mediciones con dato (los NULL no cuentan) |

#### Como probar

```
python etapa5/consultas_slice_dice.py
python app.py
```

El primer comando imprime los ejemplos del slice y el dice (deben salir 5074 mediciones y 46,4 % para el
slice; 2170 mediciones y 33,8 % de servicio continuo para el dice). Luego se abre
`http://127.0.0.1:5000/etapa5/slice-dice`.

La API tambien se puede consultar directamente, por ejemplo:

```
/etapa5/slice-dice/datos?op=slice&dimension=region&valor=Nacional&nivel=departamento&filas=servicio&columnas=riesgo
/etapa5/slice-dice/datos?op=dice&region=Regional&anio=2024&anio=2025&sistema=Chingaza&sistema=Sur&sistema=Tibitoc&nivel=trimestre&filas=sistema&columnas=servicio
```

El slice exige una sola dimension con un solo valor y el dice exige filtros sobre al menos dos
dimensiones diferentes; si no se cumple, la API responde con un mensaje de error (codigo 400).

### Operacion Pivot

Vista interactiva en el menu **Etapa 5 - Analisis multidimensional > Pivot: rotar la matriz**
(ruta `/etapa5/pivot`). Permite intercambiar filas y columnas, elegir otras dimensiones y ubicar
varias medidas en uno de los ejes. Cada celda y cada total se recalculan desde la tabla de hechos;
los totales no son la suma ni el promedio de las celdas.

| Archivo | Contenido |
|---|---|
| `etapa5/sql/04_consultas_pivot.sql` | Consultas de los ejemplos y validaciones del pivot |
| `etapa5/consultas_pivot.py` | Consultas parametrizadas, matrices y validaciones |
| `app.py` | Rutas `/etapa5/pivot` (vista) y `/etapa5/pivot/datos` (API JSON) |
| `templates/etapa5/pivot.html` | Controles, matriz, visualizaciones, validaciones y conocimientos |
| `templates/base.html` | Enlace en el menu de la Etapa 5 |

#### Como probar

```
python etapa5/consultas_pivot.py
python app.py
```

Abre `http://127.0.0.1:5000/etapa5/pivot`. La API permite consultar la orientacion inicial,
rotarla o mostrar medidas por trimestre:

```
/etapa5/pivot/datos?filas=region&columnas=anio&medida=pct_continuo
/etapa5/pivot/datos?filas=anio&columnas=region&medida=pct_continuo
/etapa5/pivot/datos?filas=trimestre&columnas=medidas&region=Regional&anio=2022&anio=2023&anio=2024&anio=2025&medidas=almacenamiento&medidas=precipitacion&medidas=pct_continuo
```

Filas y columnas deben ser ejes diferentes; de lo contrario, la API responde con un mensaje de error
(codigo 400).