-- =====================================================================
-- Etapa 5 - Modelo multidimensional (estrella) - Calidad del agua
-- Base: SQLite (archivo etapa5/calidad_agua_dw.db)
-- Granularidad de la tabla de hechos: una medición diaria de un municipio
-- Se ejecuta desde cargar_modelo.py; se puede correr varias veces.
-- =====================================================================

-- Activa la revisión de claves foráneas (en SQLite viene apagada)
PRAGMA foreign_keys = ON;

-- Se borran las tablas para que el script sea reproducible.
-- Primero la de hechos, porque depende de las dimensiones.
DROP TABLE IF EXISTS fact_medicion;
DROP TABLE IF EXISTS dim_tiempo;
DROP TABLE IF EXISTS dim_geografia;
DROP TABLE IF EXISTS dim_sistema;
DROP TABLE IF EXISTS dim_riesgo;
DROP TABLE IF EXISTS dim_servicio;

-- ---------------------------------------------------------------------
-- DIMENSIÓN TIEMPO
-- Jerarquía: anio -> trimestre -> mes -> dia
-- ---------------------------------------------------------------------
CREATE TABLE dim_tiempo (
    fecha_key        INTEGER PRIMARY KEY,   -- AAAAMMDD, ej. 20240315 (0 = desconocida)
    fecha            TEXT    NOT NULL,      -- 'AAAA-MM-DD'
    anio             INTEGER NOT NULL,
    trimestre        INTEGER NOT NULL,      -- 1 a 4
    anio_trimestre   TEXT    NOT NULL,      -- '2024-T1'
    mes              INTEGER NOT NULL,      -- 1 a 12
    nombre_mes       TEXT    NOT NULL,      -- 'Enero', 'Febrero', ...
    anio_mes         TEXT    NOT NULL,      -- '2024-03'
    dia              INTEGER NOT NULL
);

-- Miembro "Desconocido" para mediciones sin fecha válida
INSERT INTO dim_tiempo VALUES
    (0, 'Desconocida', 0, 0, 'Desconocido', 0, 'Desconocido', 'Desconocido', 0);

-- ---------------------------------------------------------------------
-- DIMENSIÓN GEOGRAFÍA
-- Jerarquía: tipo_region -> departamento -> municipio
-- (2 regiones, 21 departamentos, 29 municipios)
-- ---------------------------------------------------------------------
CREATE TABLE dim_geografia (
    municipio_key    INTEGER PRIMARY KEY,   -- 1, 2, 3... (0 = desconocido)
    municipio        TEXT    NOT NULL UNIQUE,
    departamento     TEXT    NOT NULL,
    tipo_region      TEXT    NOT NULL       -- 'Regional' (Bogotá y Sabana) o 'Nacional'
);

-- Miembro "Desconocido" para mediciones sin municipio válido
INSERT INTO dim_geografia VALUES (0, 'Desconocido', 'Desconocido', 'Desconocido');

-- ---------------------------------------------------------------------
-- DIMENSIÓN SISTEMA DE ABASTECIMIENTO
-- Valores: Chingaza, Sur, Tibitoc (EAAB) y Fuera de cobertura EAAB
-- ---------------------------------------------------------------------
CREATE TABLE dim_sistema (
    sistema_key      INTEGER PRIMARY KEY,   -- 1, 2, 3... (0 = desconocido)
    sistema          TEXT    NOT NULL UNIQUE,
    cubierto_eaab    INTEGER NOT NULL       -- 1 = sistema de la EAAB, 0 = fuera de cobertura
                     CHECK (cubierto_eaab IN (0, 1))
);

-- Miembro "Desconocido" para mediciones sin sistema válido
INSERT INTO dim_sistema VALUES (0, 'Desconocido', 0);

-- ---------------------------------------------------------------------
-- DIMENSIÓN RIESGO (clasificación del IRCA)
-- Jerarquía: grupo_riesgo -> clasificacion
-- "Sin dato de IRCA" = valor faltante; "Desconocido" = categoría no reconocida
-- ---------------------------------------------------------------------
CREATE TABLE dim_riesgo (
    riesgo_key       INTEGER PRIMARY KEY,
    clasificacion    TEXT    NOT NULL UNIQUE,
    grupo_riesgo     TEXT    NOT NULL,      -- 'Bajo o nulo', 'Medio', 'Alto o inviable', 'Sin dato'
    rango_min        REAL,                  -- límite del IRCA (vacío si no aplica)
    rango_max        REAL,
    orden            INTEGER NOT NULL       -- para ordenar en tablas y gráficos
);

INSERT INTO dim_riesgo VALUES
    (0, 'Desconocido',                   'Desconocido',     NULL, NULL, 0),
    (1, 'Sin riesgo (0-5)',              'Bajo o nulo',     0,    5,    1),
    (2, 'Bajo riesgo (5-14)',            'Bajo o nulo',     5,    14,   2),
    (3, 'Riesgo medio (14-28)',          'Medio',           14,   28,   3),
    (4, 'Alto riesgo (28-40)',           'Alto o inviable', 28,   40,   4),
    (5, 'Inviable sanitariamente (>40)', 'Alto o inviable', 40,   100,  5),
    (6, 'Sin dato de IRCA',              'Sin dato',        NULL, NULL, 6);

-- ---------------------------------------------------------------------
-- DIMENSIÓN NIVEL DE SERVICIO
-- ---------------------------------------------------------------------
CREATE TABLE dim_servicio (
    servicio_key     INTEGER PRIMARY KEY,
    nivel_servicio   TEXT    NOT NULL UNIQUE,
    es_continuo      INTEGER NOT NULL CHECK (es_continuo IN (0, 1)),
    orden            INTEGER NOT NULL
);

INSERT INTO dim_servicio VALUES
    (0, 'Desconocido',  0, 0),
    (1, 'Continuo',     1, 1),
    (2, 'Intermitente', 0, 2),
    (3, 'Racionado',    0, 3),
    (4, 'Sin servicio', 0, 4);

-- ---------------------------------------------------------------------
-- TABLA DE HECHOS: una medición diaria de un municipio
-- ---------------------------------------------------------------------
CREATE TABLE fact_medicion (
    id_medicion              INTEGER PRIMARY KEY,
    fecha_key                INTEGER NOT NULL REFERENCES dim_tiempo(fecha_key),
    municipio_key            INTEGER NOT NULL REFERENCES dim_geografia(municipio_key),
    sistema_key              INTEGER NOT NULL REFERENCES dim_sistema(sistema_key),
    riesgo_key               INTEGER NOT NULL REFERENCES dim_riesgo(riesgo_key),
    servicio_key             INTEGER NOT NULL REFERENCES dim_servicio(servicio_key),
    irca                     REAL,          -- vacío cuando no se reportó (no se pone 0)
    irca_reportado           INTEGER NOT NULL CHECK (irca_reportado IN (0, 1)),
    cobertura_acueducto_pct  REAL,
    nivel_almacenamiento_pct REAL,
    precipitacion_mm         REAL,
    consumo_m3s              REAL,
    UNIQUE (fecha_key, municipio_key)       -- garantiza la granularidad: sin duplicados
);

-- Índices para que las consultas de Flask sean rápidas
CREATE INDEX ix_fact_fecha     ON fact_medicion(fecha_key);
CREATE INDEX ix_fact_municipio ON fact_medicion(municipio_key);
CREATE INDEX ix_fact_sistema   ON fact_medicion(sistema_key);
CREATE INDEX ix_fact_riesgo    ON fact_medicion(riesgo_key);
CREATE INDEX ix_fact_servicio  ON fact_medicion(servicio_key);