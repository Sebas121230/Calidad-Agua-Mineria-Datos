# Calidad y Accesibilidad del Agua - Mineria de Datos

Aplicacion Flask que documenta la **Etapa 1** del proyecto de Mineria de Datos sobre la
disponibilidad y continuidad del servicio de agua potable en Bogota D.C. (2019-2025).

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
├── .gitignore
├── static/
│   ├── css/estilos.css     # Estilos propios (complementan Bootstrap)
│   └── img/logo_udec.png
└── templates/
    ├── base.html           # Plantilla base con el menu lateral
    ├── inicio.html         # Portada
    └── etapa1/             # Los 8 submenus de la Etapa 1
        ├── problema.html
        ├── preguntas.html
        ├── necesidades.html
        ├── fuentes.html
        ├── dataset.html
        ├── diccionario.html
        ├── calidad.html
        └── limitaciones.html
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
identificados en la Etapa 2 sobre `dataset_calidad_agua.csv` (12.989 registros), en tres
iteraciones documentadas en la tabla `etl_log`.

### Contenido

```
Calidad-Agua-Mineria-Datos/
├── ETL_CalidadAgua/                 # Proyecto de Visual Studio (SSIS)
│   ├── ETL_CalidadAgua.slnx         # Abrir este archivo
│   └── ETL_CalidadAgua/Package.dtsx # Paquete: Control Flow y Data Flows
├── sql/
│   ├── 01_crear_staging.sql         # Zona staging (datos originales, todo texto)
│   ├── 02_crear_destino.sql         # Datos limpios con tipos reales y llave UNIQUE
│   ├── 03_crear_revision.sql        # Registros rechazados con valor original y motivo
│   ├── 04_crear_log.sql             # Una fila por ejecucion con los conteos
│   ├── 05_consultas_verificacion.sql# Evidencias y verificacion de resultados
│   └── 06_sql_del_paquete.sql       # SQL que ejecuta SSIS internamente
├── dataset_calidad_agua.csv         # Datos originales
└── resultados_iteraciones.csv       # Log exportado de las tres iteraciones
```

### Como reproducir el proceso

Requisitos: SQL Server 2025 (Developer), SSMS y Visual Studio con la extension
*SQL Server Integration Services Projects 2022+*.

1. En SSMS, crear la base de datos `CalidadAgua_ETL` y ejecutar `sql/01` a `sql/04` en orden.
2. Abrir `ETL_CalidadAgua/ETL_CalidadAgua.slnx` en Visual Studio.
3. En *Administradores de conexiones*, editar `CSV_CalidadAgua` y seleccionar la ruta local
   de `dataset_calidad_agua.csv`. La conexion a `localhost` usa autenticacion de Windows
   (el repositorio no contiene contrasenas).
4. Fijar la variable `vIteracion` (1, 2 o 3) y `vObservacion`, y ejecutar el paquete.
5. Revisar los resultados con `sql/05_consultas_verificacion.sql`.

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

El menu de la Etapa 4 incluye dos tableros: la **Dimension territorial** en
`/etapa4/territorial` y el **Analisis multivariable** en `/etapa4/multivariable`.
El tablero multivariable relaciona IRCA, cobertura de acueducto, nivel de servicio,
municipio, region y periodo. Incluye indicadores, dispersion por registro, comparacion
de grupos y las combinaciones trimestrales mas frecuentes, con filtros interactivos de
año y region. Sus agregaciones se calculan sobre el dataset limpio; las relaciones son
descriptivas y no implican causalidad.

```
Calidad-Agua-Mineria-Datos/
├── generar_dataset_limpio.py          # Reproduce en Python el resultado del ETL (SSIS)
├── dataset_calidad_agua_limpio.csv    # Salida: equivalente a dst_calidad_agua
├── dataset_calidad_agua_revision.csv  # Salida: equivalente a rev_calidad_agua
└── templates/etapa4/
    ├── territorial.html               # Tablero de la dimension territorial
    └── Multivariada.html               # Tablero de analisis multivariable
```

**Por que un script en Python y no la tabla `dst_calidad_agua` de SQL Server:** el
paquete SSIS de la Etapa 3 corre contra una base de datos local que no se exporta ni
se versiona en el repositorio. `generar_dataset_limpio.py` aplica, en Python puro,
las mismas reglas documentadas en `Informe_Etapa3_Calidad_Agua.pdf` (normalizacion,
validacion P05/P09/P08, clasificacion de riesgo y llave unica fecha+municipio+sistema
para los duplicados P07), para que el tablero de Flask tenga un dataset limpio sin
depender de SQL Server. Se valido que coincide **exactamente** con la iteracion 2 del
ETL real registrada en `resultados_iteraciones.csv`: 12.680 aceptados, 62 duplicados y
247 en revision sobre 12.989 recibidos.

Para regenerar los archivos limpios:

```bash
python generar_dataset_limpio.py
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
de agregacion del tablero (`app.py`), sin modificar `dataset_calidad_agua_limpio.csv`,
para no alterar el resultado ya validado de la Etapa 3.

El desarrollo de la Etapa 4 (dimension territorial) se realiza en la rama
`feature/dim-territorial`.

### Dimension poblacional

Tablero en `/etapa4/poblacional`.

**Pregunta de analisis:** ¿cuantas personas estan expuestas a riesgo en la calidad del
agua o viven sin cobertura de acueducto, y cambia la conclusion cuando cada municipio
pesa segun su poblacion y no segun su numero de registros?

**Fuente externa (decision sustentada):** el dataset no trae ninguna variable de
poblacion, y cada municipio tiene una cantidad parecida de registros sin importar su
tamaño (Bogota y Sopo pesan casi igual en un promedio por registro). Por eso se
incorporo la *Serie municipal de poblacion por area, periodo 2018-2042* del DANE
(CNPV 2018, publicada el 8 de agosto de 2025):
<https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion>

```
Calidad-Agua-Mineria-Datos/
├── fuentes/PPED-AreaMun-2018-2042_VP.xlsx   # Archivo original del DANE, sin modificar
├── generar_poblacion.py                     # Filtra area "Total", años 2019-2025 y los 29 municipios
├── poblacion_municipios.csv                 # Salida: 203 filas (29 municipios x 7 años)
└── templates/etapa4/poblacional.html        # Tablero de la dimension poblacional
```

El cruce se hace por codigo DIVIPOLA y no por nombre, porque el DANE escribe con tildes
("Cajicá", "Bogotá, D.C.", "San José de Cúcuta") y el dataset no. El script usa
`openpyxl` (Python puro) en lugar de pandas. Para regenerar el CSV:

```bash
python generar_poblacion.py
```

**Hallazgos principales:**

- Ponderado por poblacion, el IRCA total sube de 14,43 a 18,46 y pasa de "Bajo riesgo" a
  "Riesgo medio": la Sabana tiene el 59,98% de los registros pero solo el 38,96% de la
  poblacion.
- Cerca de 3,74 millones de personas por año viven sin cobertura de acueducto (87% en
  ciudades del nivel Nacional). Bogota, con 94,82% de cobertura, es el tercer municipio
  con mas personas sin acueducto (404.014).
- El tamaño del municipio no explica el IRCA; lo que separa el riesgo es la region.

**Limitacion:** el IRCA del dataset es sintetico y se genera por region
(`generar_dataset.py`), por lo que los patrones dentro de cada region no deben leerse
como evidencia sobre municipios reales. La poblacion es una proyeccion anual que se
asigna a registros diarios.

El desarrollo de la dimension poblacional se realiza en la rama `feature/dim-poblacional`.
