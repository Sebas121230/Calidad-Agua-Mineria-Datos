-- =====================================================================
-- Etapa 5 - Validaciones del modelo estrella (SQLite)
-- Se ejecutan sobre etapa5/calidad_agua_dw.db después de correr
-- cargar_modelo.py. Cada consulta indica el resultado esperado.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. UNICIDAD DE LAS CLAVES DE LAS DIMENSIONES
-- Esperado: 0 filas en cada consulta (ninguna clave ni nombre repetido)
-- ---------------------------------------------------------------------
SELECT 'dim_tiempo' AS tabla, fecha_key AS clave, COUNT(*) AS veces
FROM dim_tiempo GROUP BY fecha_key HAVING COUNT(*) > 1;

SELECT 'dim_geografia' AS tabla, municipio AS valor, COUNT(*) AS veces
FROM dim_geografia GROUP BY municipio HAVING COUNT(*) > 1;

SELECT 'dim_sistema' AS tabla, sistema AS valor, COUNT(*) AS veces
FROM dim_sistema GROUP BY sistema HAVING COUNT(*) > 1;

SELECT 'dim_riesgo' AS tabla, clasificacion AS valor, COUNT(*) AS veces
FROM dim_riesgo GROUP BY clasificacion HAVING COUNT(*) > 1;

SELECT 'dim_servicio' AS tabla, nivel_servicio AS valor, COUNT(*) AS veces
FROM dim_servicio GROUP BY nivel_servicio HAVING COUNT(*) > 1;

-- ---------------------------------------------------------------------
-- 2. CORRESPONDENCIA ENTRE CLAVES FORÁNEAS Y DIMENSIONES
-- Esperado: 0 en todas las columnas (ningún hecho apunta a una clave
-- que no exista en su dimensión)
-- ---------------------------------------------------------------------
SELECT
    SUM(t.fecha_key     IS NULL) AS sin_tiempo,
    SUM(g.municipio_key IS NULL) AS sin_geografia,
    SUM(s.sistema_key   IS NULL) AS sin_sistema,
    SUM(r.riesgo_key    IS NULL) AS sin_riesgo,
    SUM(v.servicio_key  IS NULL) AS sin_servicio
FROM fact_medicion f
LEFT JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
LEFT JOIN dim_geografia g ON g.municipio_key = f.municipio_key
LEFT JOIN dim_sistema   s ON s.sistema_key   = f.sistema_key
LEFT JOIN dim_riesgo    r ON r.riesgo_key    = f.riesgo_key
LEFT JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key;

-- Comprobación de SQLite sobre todas las claves foráneas. Esperado: 0 filas
PRAGMA foreign_key_check;

-- ---------------------------------------------------------------------
-- 3. AUSENCIA DE DUPLICADOS EN LA TABLA DE HECHOS (granularidad)
-- Esperado: 0 filas (un municipio tiene una sola medición por día)
-- ---------------------------------------------------------------------
SELECT fecha_key, municipio_key, COUNT(*) AS veces
FROM fact_medicion
GROUP BY fecha_key, municipio_key
HAVING COUNT(*) > 1;

-- ---------------------------------------------------------------------
-- 4. VALORES FALTANTES Y CATEGORÍAS DESCONOCIDAS
-- Esperado: sin_dato_irca = 262 (faltante real), irca_vacio = 262,
-- desconocidos = 0 (ninguna categoría sin reconocer),
-- precipitacion_vacia = 620 (faltante que ya venía en el CSV; se deja vacío)
-- ---------------------------------------------------------------------
SELECT
    SUM(riesgo_key = 6)    AS sin_dato_irca,
    SUM(irca IS NULL)      AS irca_vacio,
    SUM(irca_reportado = 0) AS irca_no_reportado,
    SUM(0 IN (fecha_key, municipio_key, sistema_key, riesgo_key, servicio_key)) AS desconocidos,
    SUM(precipitacion_mm IS NULL) AS precipitacion_vacia
FROM fact_medicion;

-- ---------------------------------------------------------------------
-- 5. COHERENCIA DE CONTEOS Y AGREGACIONES CON EL CSV DE ORIGEN
-- Valores del CSV dataset_calidad_agua_limpio.csv (calculados por
-- cargar_modelo.py): 12.680 registros, 12.418 con IRCA, IRCA promedio
-- 14,43, 7.606 Regional y 5.074 Nacional, 29 municipios.
-- ---------------------------------------------------------------------

-- 5.1 Registros totales. Esperado: 12680
SELECT COUNT(*) AS registros FROM fact_medicion;

-- 5.2 Mediciones con IRCA e IRCA promedio. Esperado: 12418 y 14.43
SELECT COUNT(irca) AS con_irca, ROUND(AVG(irca), 2) AS irca_promedio
FROM fact_medicion;

-- 5.3 Registros y municipios por región. Esperado: Nacional 5074 / 20,
-- Regional 7606 / 9
SELECT g.tipo_region,
       COUNT(*) AS registros,
       COUNT(DISTINCT f.municipio_key) AS municipios
FROM fact_medicion f
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
GROUP BY g.tipo_region;

-- 5.4 Registros por año (periodos equivalentes). Esperado: entre 1809 y 1814
SELECT t.anio, COUNT(*) AS registros
FROM fact_medicion f
JOIN dim_tiempo t ON t.fecha_key = f.fecha_key
GROUP BY t.anio
ORDER BY t.anio;

-- 5.5 Coherencia con la etapa 4: % de riesgo alto o inviable por región
-- (denominador: mediciones con IRCA). Esperado: Nacional 46.42, Regional 0
SELECT g.tipo_region,
       ROUND(100.0 * SUM(r.grupo_riesgo = 'Alto o inviable') / SUM(f.irca_reportado), 2)
           AS pct_alto_inviable
FROM fact_medicion f
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_riesgo    r ON r.riesgo_key    = f.riesgo_key
GROUP BY g.tipo_region;
