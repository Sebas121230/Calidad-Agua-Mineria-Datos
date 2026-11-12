# Calidad y Accesibilidad del Agua - Minería de Datos

Aplicación Flask y scripts del proyecto de Minería de Datos sobre la disponibilidad y
continuidad del servicio de agua potable en Bogotá, la Sabana y otros municipios del país
(2019-2025).

**Universidad de Cundinamarca** - Ingeniería de Sistemas y Computación

## Integrantes

- Diego Armando Guzmán Garzón
- Andrés Felipe Beltrán Barrera
- Juan Sebastián Rodríguez Riveros
- John Sebastián Rodríguez Domínguez

## Estructura

```text
Calidad-Agua-Mineria-Datos/
├── app.py
├── requirements.txt
├── README.md
├── scripts/                 # Generación, limpieza y auditoría
├── datos/                   # CSV de entrada, salidas y evidencias
├── etapa3/                  # ETL SSIS y SQL
│   ├── ETL_CalidadAgua/
│   └── sql/
├── etapa5/                  # Modelo estrella en SQLite
│   ├── cargar_modelo.py
│   ├── consultas_slice_dice.py
│   ├── calidad_agua_dw.db
│   ├── diagrama_modelo.png
│   └── sql/
├── etapa6/                  # Modelos de Orange y comentarios
│   ├── preparar_supervisado.py
│   ├── datos/
│   ├── orange/
│   └── capturas/
├── templates/
└── static/
```

## Ejecución

```bash
python -m venv venv
source venv/bin/activate          # Linux/macOS
# .\venv\Scripts\Activate         # Windows
pip install -r requirements.txt
python app.py
```

Abrir <http://127.0.0.1:5000>.

La aplicación Flask solo necesita Flask; pandas se usa en algunos scripts. Si el entorno usa
Python 3.14, `pandas==2.2.3` puede no instalar: en ese caso ejecuta `pip install "pandas>=2.3"`.

## Etapas 1 y 2

Se definió el problema, las preguntas, las fuentes y la calidad inicial de un conjunto
consolidado de mediciones diarias de calidad y servicio de agua. La Etapa 2 documentó el
perfilamiento, las dimensiones de calidad, el inventario de problemas y el plan de tratamiento
que se ejecutó en la Etapa 3.

## Etapa 3: limpieza con SSIS

El paquete `etapa3/ETL_CalidadAgua/ETL_CalidadAgua/Package.dtsx` se ejecuta sobre
`datos/dataset_calidad_agua.csv` (12.989 registros) y deja 12.680 mediciones válidas, 62
duplicados y 247 registros en revisión. Los scripts SQL están en `etapa3/sql/`.

- Resultado reproducible: `datos/resultados_iteraciones.csv`.
- Video: ruta `/etapa3/video`.
- Para reconstruir el dataset limpio sin SQL Server: `python scripts/generar_dataset_limpio.py`.

## Etapa 4: conocimiento evidente

La sección `/etapa4/conocimiento-evidente` integra el informe publicado de Power BI y sus cuatro
páginas. Los tableros de apoyo están en:

- `/etapa4/territorial`
- `/etapa4/temporal`
- `/etapa4/multivariable`

Hallazgos principales: el IRCA de Nacional (26,13) es muy superior al de Regional (6,61); la
continuidad de la Sabana cayó de 100 % (2019-2023) a 43,91 % (2024) y 23,76 % (2025); la cobertura
alta no garantiza continuidad y el servicio continuo no garantiza calidad.

## Etapa 5: análisis multidimensional

El modelo estrella está en `etapa5/calidad_agua_dw.db`:

- Hechos: `fact_medicion`, una fila por fecha y municipio.
- Dimensiones: `dim_tiempo`, `dim_geografia`, `dim_sistema`, `dim_riesgo` y `dim_servicio`.

Para recrear la base:

```bash
python etapa5/cargar_modelo.py
```

La sección `/etapa5/multidimensional` reúne cinco vistas en tarjetas desplegables: sistemas y
cambio de régimen, prioridades por departamento, cobertura y continuidad, recuperación hídrica y
Slice/Dice. Cada vista recalcula sus indicadores desde la tabla de hechos.

Hallazgos principales:

- El quiebre de 2024 es un cambio de régimen: la mezcla de niveles de servicio se repite en los
  tres sistemas de la EAAB y en los nueve municipios de la Sabana.
- Hay tres perfiles de prioridad: intervención conjunta de calidad y continuidad, prioridad de
  calidad y recuperación de continuidad.
- La cobertura está desacoplada de la continuidad y del riesgo dentro de cada región.
- En 2025 el consumo y el almacenamiento se recuperaron, pero el servicio siguió restringido.

## Etapa 6: conocimiento oculto

La sección `/etapa6/conocimiento-oculto` reúne los flujos de Orange, las capturas y los
resultados de aprendizaje supervisado, clustering y comentarios de YouTube.

### Aprendizaje supervisado

La pregunta es si las condiciones hidrológicas y climáticas permiten anticipar una restricción
del servicio. Se compararon árbol de decisión, Random Forest, regresión logística y una constante
con validación cruzada de 10 pliegues.

- Random Forest obtiene el mejor desempeño en la validación aleatoria: AUC 0,915, CA 0,884 y F1
  0,878.
- La clase con restricción (640 de 2.557 días) es minoritaria: el bosque detecta 63,3 % y deja
  235 falsos negativos.
- La validación temporal cambia la lectura: 2019-2023 no tiene días restringidos y 2025 tiene
  365 de 365. La restricción es un cambio de régimen operativo o de política, no una predicción
  hidrológica que el modelo pueda anticipar con estos datos.

### Clustering

Se aplicó k-Means con k = 3 sobre las variables normalizadas de almacenamiento, afluencias,
precipitación y temperatura, sin usar la restricción ni el consumo.

- C1: almacenamiento alto y clima cálido; 891 días.
- C2: estrés hídrico, baja precipitación y menores afluencias; 838 días y 43,3 % de días
  restringidos.
- C3: recarga hídrica, clima frío y consumo alto; 828 días.
- En el holdout 2024-2025 los tres grupos tienen entre 83,2 % y 100 % de restricción y la silueta
  baja a 0,190: los clusters describen contextos meteorológicos, no el estado del servicio.

### Comentarios de YouTube

Se analizaron 500 comentarios extraídos mediante la API de YouTube (texto, fecha y likes). El
corpus se centra en consumo y ahorro (76 comentarios), empresas e industria (59), clima y ambiente
(48), escasez y “día cero” (42), crítica al contenido (33) y gobierno y política (25). El
sentimiento es mayoritariamente crítico.

La conversación complementa la dimensión operativa/política de los modelos, pero no valida la
percepción local: solo 3 comentarios mencionan Bogotá y 2 Colombia. El corpus es global y no es una
muestra representativa.

## Origen de los datos

| Archivo | Origen y transformación |
|---|---|
| `datos/dataset_calidad_agua_limpio.csv` | Resultado de la limpieza de la Etapa 3 sobre el dataset original. |
| `etapa5/calidad_agua_dw.db` | Modelo estrella cargado desde el dataset limpio con `etapa5/cargar_modelo.py`. |
| `etapa6/datos/dataset_supervisado_dia.csv` | Una fila por día de la región Regional, generada por `etapa6/preparar_supervisado.py`. |
| `etapa6/datos/dias_clusters.csv` | Exportación de la asignación de clusters y la silueta del flujo de k-Means. |
| `etapa6/datos/comentarios_youtube.csv` | 500 comentarios públicos extraídos de YouTube; sin credenciales ni datos personales. |

Los flujos de Orange están en `etapa6/orange/` y las capturas en `etapa6/capturas/`.

## Rutas principales

| Ruta | Contenido |
|---|---|
| `/` | Inicio |
| `/etapa3/video` | Video de la Etapa 3 |
| `/etapa4/conocimiento-evidente` | Informe de Power BI |
| `/etapa4/territorial` | Dimensión territorial |
| `/etapa4/temporal` | Dimensión temporal |
| `/etapa4/multivariable` | Análisis multivariable |
| `/etapa5/multidimensional` | Análisis multidimensional |
| `/etapa6/conocimiento-oculto` | Conocimiento oculto |
