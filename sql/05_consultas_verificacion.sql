-- =============================================================
-- 05 - Consultas de verificacion y analisis de resultados
--      (ejecutar despues de correr el paquete)
-- =============================================================
USE CalidadAgua_ETL;
GO

-- -------------------------------------------------------------
-- A. Estructura
-- -------------------------------------------------------------
-- A1. Tablas creadas en la base
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA, TABLE_NAME;

-- A2. Carga a staging: debe dar 12989 (igual que el CSV)
SELECT COUNT(*) AS registros_staging FROM stg_calidad_agua;

-- -------------------------------------------------------------
-- B. Resultados por iteracion
-- -------------------------------------------------------------
-- B1. Log de todas las ejecuciones
SELECT * FROM etl_log ORDER BY log_id;

-- B2. Verificacion de la ecuacion de control (cuadra = 'Si')
SELECT log_id, iteracion, recibidos,
       aceptados + duplicados + revision + ya_cargados AS suma,
       CASE WHEN recibidos = aceptados + duplicados + revision + ya_cargados
            THEN 'Si' ELSE 'No' END AS cuadra
FROM etl_log ORDER BY log_id;

-- B3. Registros en destino por iteracion
SELECT iteracion, COUNT(*) AS registros_destino
FROM dst_calidad_agua GROUP BY iteracion ORDER BY iteracion;

-- B4. Registros en revision por iteracion
SELECT iteracion, COUNT(*) AS registros_revision
FROM rev_calidad_agua GROUP BY iteracion ORDER BY iteracion;

-- B5. Motivos de revision comparando iteraciones
SELECT iteracion, regla_id, COUNT(*) AS cantidad
FROM rev_calidad_agua
GROUP BY iteracion, regla_id
ORDER BY iteracion, regla_id;

-- -------------------------------------------------------------
-- C. Hallazgos de la iteracion 1 (justifican la iteracion 2)
-- -------------------------------------------------------------
-- C1. IRCA validos enviados a revision (problema de LocaleID)
SELECT TOP 15 irca, motivo
FROM rev_calidad_agua
WHERE iteracion = 1 AND regla_id = 'P08';

-- C2. Formatos de fecha alternos
SELECT TOP 20 fecha, anio, mes
FROM rev_calidad_agua
WHERE iteracion = 1 AND regla_id = 'P09';

-- C3. Columna que causo los errores de conversion (sin motivo)
SELECT
  SUM(CASE WHEN TRY_CAST(anio AS SMALLINT) IS NULL THEN 1 ELSE 0 END) AS anio,
  SUM(CASE WHEN TRY_CAST(mes AS TINYINT) IS NULL THEN 1 ELSE 0 END) AS mes,
  SUM(CASE WHEN TRY_CAST(nivel_almacenamiento_pct AS DECIMAL(5,2)) IS NULL THEN 1 ELSE 0 END) AS nivel,
  SUM(CASE WHEN TRY_CAST(afluencias_m3s AS DECIMAL(8,2)) IS NULL THEN 1 ELSE 0 END) AS afluencias,
  SUM(CASE WHEN TRY_CAST(consumo_m3s AS DECIMAL(8,2)) IS NULL THEN 1 ELSE 0 END) AS consumo,
  SUM(CASE WHEN TRY_CAST(latitud AS DECIMAL(9,6)) IS NULL THEN 1 ELSE 0 END) AS latitud,
  SUM(CASE WHEN TRY_CAST(longitud AS DECIMAL(9,6)) IS NULL THEN 1 ELSE 0 END) AS longitud,
  SUM(CASE WHEN TRY_CAST(cobertura_acueducto_pct AS DECIMAL(5,2)) IS NULL THEN 1 ELSE 0 END) AS cobertura
FROM rev_calidad_agua
WHERE iteracion = 1 AND regla_id IS NULL;

-- C4. Ejemplos de los registros sin motivo (resultaron ser tipo Global)
SELECT TOP 10 * FROM rev_calidad_agua
WHERE iteracion = 1 AND regla_id IS NULL;

-- C5. Confirmar que son de tipo Global
SELECT tipo_region, COUNT(*) AS cantidad
FROM rev_calidad_agua
WHERE iteracion = 1 AND regla_id IS NULL
GROUP BY tipo_region;

-- -------------------------------------------------------------
-- D. Evidencias para el informe y el video
-- -------------------------------------------------------------
-- D1. Dato corregido: fecha original vs fecha en destino
SELECT TOP 5 s.fecha AS fecha_original, d.fecha AS fecha_corregida, d.municipio
FROM stg_calidad_agua s
JOIN dst_calidad_agua d
  ON d.iteracion = 3 AND d.municipio = UPPER(TRIM(s.municipio))
 AND d.fecha = TRY_CONVERT(DATE, s.fecha, 103)
WHERE s.fecha LIKE '%/%';

-- D2. Registro enviado a revision con su valor original y motivo
SELECT TOP 5 irca, municipio, regla_id, motivo
FROM rev_calidad_agua
WHERE iteracion = 3 AND regla_id = 'P08';

-- D3. Municipios normalizados (espacios / mayusculas)
SELECT TOP 10
  '[' + municipio + ']' AS municipio_original,
  UPPER(LTRIM(RTRIM(municipio))) AS municipio_destino
FROM stg_calidad_agua
WHERE municipio <> UPPER(LTRIM(RTRIM(municipio))) COLLATE Latin1_General_CS_AS;

-- D4. Completitud final en el destino (iteracion 3)
SELECT
  COUNT(*) AS total,
  CAST(100.0 * COUNT(precipitacion_mm) / COUNT(*) AS DECIMAL(5,2)) AS pct_precipitacion,
  CAST(100.0 * COUNT(temperatura_c)    / COUNT(*) AS DECIMAL(5,2)) AS pct_temperatura,
  CAST(100.0 * COUNT(irca)             / COUNT(*) AS DECIMAL(5,2)) AS pct_irca
FROM dst_calidad_agua
WHERE iteracion = 3;

-- -------------------------------------------------------------
-- E. Exportacion para Flask
-- -------------------------------------------------------------
-- E1. Resultados de las iteraciones (Guardar resultados como...
--     resultados_iteraciones.csv)
SELECT iteracion, recibidos, aceptados, duplicados, revision, ya_cargados, observacion
FROM etl_log ORDER BY log_id;
