-- Etapa 5 - Operación PIVOT sobre el modelo estrella
-- Responsable: Andrés Felipe Beltrán Barrera
-- Base: SQLite (etapa5/calidad_agua_dw.db)
--
-- PIVOT (rotación): cambia la disposición de las dimensiones en una matriz para
-- observar los mismos resultados desde otra perspectiva. Las medidas no cambian;
-- solo cambia qué dimensión va en las filas y cuál en las columnas.
--
-- Medidas usadas (definidas en el modelo de la etapa 5):
--   pct_continuo    = 100 * AVG(v.es_continuo)
--                     (denominador: todas las mediciones del grupo)  -> proporción, se recalcula
--   almacenamiento  = AVG(f.nivel_almacenamiento_pct)              -> promedio, se recalcula
--   precipitacion   = AVG(f.precipitacion_mm), ignora los NULL       -> promedio, se recalcula
--   mediciones      = COUNT(*)                                      -> conteo, aditiva
--
-- Los totales de fila y de columna se calculan con su propio GROUP BY desde la
-- tabla de hechos; nunca se suman ni se promedian los porcentajes de las celdas.


-- ---------------------------------------------------------------------
-- P1. Datos base del pivot 1: % servicio continuo por región y año
--     Una fila por combinación (región, año). La aplicación Flask acomoda
--     este resultado en la matriz en una orientación o en la otra.
-- ---------------------------------------------------------------------
SELECT g.tipo_region,
       t.anio,
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS pct_continuo,
       COUNT(*)                                                     AS mediciones
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
GROUP BY g.tipo_region, t.anio
ORDER BY g.tipo_region, t.anio;


-- ---------------------------------------------------------------------
-- P2. PIVOT 1, orientación A: filas = región, columnas = año
--     Se lee por fila: cómo evolucionó cada región en el tiempo.
-- ---------------------------------------------------------------------
SELECT g.tipo_region                                                AS region,
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2019 THEN v.es_continuo END), 1) AS "2019",
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2020 THEN v.es_continuo END), 1) AS "2020",
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2021 THEN v.es_continuo END), 1) AS "2021",
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2022 THEN v.es_continuo END), 1) AS "2022",
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2023 THEN v.es_continuo END), 1) AS "2023",
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2024 THEN v.es_continuo END), 1) AS "2024",
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2025 THEN v.es_continuo END), 1) AS "2025",
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS total_fila
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
GROUP BY g.tipo_region
ORDER BY g.tipo_region;


-- ---------------------------------------------------------------------
-- P3. PIVOT 1, orientación B (rotada): filas = año, columnas = región
--     Se lee por fila: en cada año, cuál región tuvo mejor continuidad.
--     Debe dar exactamente la transpuesta de P2.
-- ---------------------------------------------------------------------
SELECT t.anio,
       ROUND(100.0 * AVG(CASE WHEN g.tipo_region = 'Nacional' THEN v.es_continuo END), 1) AS nacional,
       ROUND(100.0 * AVG(CASE WHEN g.tipo_region = 'Regional' THEN v.es_continuo END), 1) AS regional,
       ROUND(100.0 * AVG(CASE WHEN g.tipo_region = 'Regional' THEN v.es_continuo END)
           - 100.0 * AVG(CASE WHEN g.tipo_region = 'Nacional' THEN v.es_continuo END), 1) AS diferencia_pp,
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS total_fila
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
GROUP BY t.anio
ORDER BY t.anio;


-- ---------------------------------------------------------------------
-- P4. PIVOT 2, orientación A: filas = trimestre, columnas = medidas
--     Filtros: región Regional y años 2022 a 2025.
--     Se lee por fila: el estado de la región en cada trimestre.
-- ---------------------------------------------------------------------
SELECT t.anio_trimestre,
       ROUND(AVG(f.nivel_almacenamiento_pct), 1)                    AS almacenamiento_pct,
       ROUND(AVG(f.precipitacion_mm), 2)                            AS precipitacion_mm,
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS pct_continuo,
       COUNT(*)                                                     AS mediciones
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
WHERE g.tipo_region = 'Regional'
  AND t.anio IN (2022, 2023, 2024, 2025)
GROUP BY t.anio_trimestre
ORDER BY t.anio_trimestre;


-- ---------------------------------------------------------------------
-- P5. PIVOT 2, orientación B (rotada): filas = medidas, columnas = año
--     Las medidas pasan a las filas y el tiempo a las columnas, para leer
--     cada medida como una serie y ver cuál se movió primero.
--     (Se muestra por año para que quepa; la vista lo hace por trimestre.)
-- ---------------------------------------------------------------------
SELECT 'Almacenamiento promedio (%)'                                AS medida,
       ROUND(AVG(CASE WHEN t.anio = 2022 THEN f.nivel_almacenamiento_pct END), 1) AS "2022",
       ROUND(AVG(CASE WHEN t.anio = 2023 THEN f.nivel_almacenamiento_pct END), 1) AS "2023",
       ROUND(AVG(CASE WHEN t.anio = 2024 THEN f.nivel_almacenamiento_pct END), 1) AS "2024",
       ROUND(AVG(CASE WHEN t.anio = 2025 THEN f.nivel_almacenamiento_pct END), 1) AS "2025"
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
WHERE g.tipo_region = 'Regional' AND t.anio BETWEEN 2022 AND 2025
UNION ALL
SELECT 'Precipitación promedio (mm)',
       ROUND(AVG(CASE WHEN t.anio = 2022 THEN f.precipitacion_mm END), 2),
       ROUND(AVG(CASE WHEN t.anio = 2023 THEN f.precipitacion_mm END), 2),
       ROUND(AVG(CASE WHEN t.anio = 2024 THEN f.precipitacion_mm END), 2),
       ROUND(AVG(CASE WHEN t.anio = 2025 THEN f.precipitacion_mm END), 2)
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
WHERE g.tipo_region = 'Regional' AND t.anio BETWEEN 2022 AND 2025
UNION ALL
SELECT '% servicio continuo',
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2022 THEN v.es_continuo END), 1),
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2023 THEN v.es_continuo END), 1),
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2024 THEN v.es_continuo END), 1),
       ROUND(100.0 * AVG(CASE WHEN t.anio = 2025 THEN v.es_continuo END), 1)
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
WHERE g.tipo_region = 'Regional' AND t.anio BETWEEN 2022 AND 2025;


-- =====================================================================
-- VALIDACIONES DEL PIVOT
-- =====================================================================

-- V1. Las mediciones de las 14 celdas (región x año) suman el total
--     Esperado: 12680 = 12680
SELECT (SELECT SUM(n) FROM (SELECT COUNT(*) AS n
                            FROM fact_medicion f
                            JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
                            JOIN dim_geografia g ON g.municipio_key = f.municipio_key
                            GROUP BY g.tipo_region, t.anio))   AS suma_celdas,
       (SELECT COUNT(*) FROM fact_medicion)                    AS total_hechos;


-- V2. El total general se recalcula desde los hechos y NO es el promedio
--     de los totales de las regiones.
--     Esperado: total_general = 68.8 ; promedio_simple_regiones = 65.7
SELECT ROUND(100.0 * AVG(v.es_continuo), 1)                    AS total_general,
       (SELECT ROUND(AVG(p), 1) FROM (
            SELECT 100.0 * AVG(v2.es_continuo) AS p
            FROM fact_medicion f2
            JOIN dim_geografia g2 ON g2.municipio_key = f2.municipio_key
            JOIN dim_servicio  v2 ON v2.servicio_key  = f2.servicio_key
            GROUP BY g2.tipo_region))                          AS promedio_simple_regiones
FROM fact_medicion f
JOIN dim_servicio v ON v.servicio_key = f.servicio_key;


-- V3. Las mediciones del pivot 2 (Regional, 2022-2025) suman lo mismo en
--     las dos orientaciones. Esperado: 4348
SELECT COUNT(*) AS mediciones_pivot2
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
WHERE g.tipo_region = 'Regional' AND t.anio BETWEEN 2022 AND 2025;
