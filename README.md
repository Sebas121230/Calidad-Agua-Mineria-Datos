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

El desarrollo de la Etapa 3 se realiza en la rama `feature/limpieza_de_datos`.
