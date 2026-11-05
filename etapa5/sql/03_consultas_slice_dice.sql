-- Etapa 5 - Operaciones SLICE y DICE sobre el modelo estrella
-- Base: SQLite (etapa5/calidad_agua_dw.db)
--
-- Medidas usadas (definidas en el modelo de la etapa 5):
--   mediciones        = COUNT(*)                                    -> conteo, aditiva
--   municipios        = COUNT(DISTINCT f.municipio_key)             -> conteo distinto, no aditiva
--   irca_promedio     = AVG(f.irca)  (ignora los NULL)              -> promedio, se recalcula
--   pct_riesgo_alto   = 100 * mediciones 'Alto o inviable'
--                       / mediciones con IRCA reportado              -> proporción, se recalcula
--   pct_continuo      = 100 * AVG(v.es_continuo)
--                       (denominador: todas las mediciones del grupo) -> proporción, se recalcula
--   pct_interrumpido  = 100 * mediciones 'Racionado' o 'Sin servicio'
--                       / todas las mediciones del grupo              -> proporción, se recalcula
--   almacenamiento    = AVG(f.nivel_almacenamiento_pct)             -> promedio, se recalcula
--
-- Ningún porcentaje ni promedio se suma o se promedia entre grupos:
-- siempre se recalcula desde la tabla de hechos con el filtro activo.
-- Cada dimensión tiene una fila por clave, así que los JOIN no multiplican
-- las mediciones.


-- ---------------------------------------------------------------------
-- S0. Contexto del SLICE: las dos regiones antes de cortar
--     Sirve para ubicar el subconjunto frente al total.
-- ---------------------------------------------------------------------
SELECT g.tipo_region,
       COUNT(*)                                                     AS mediciones,
       COUNT(DISTINCT f.municipio_key)                              AS municipios,
       ROUND(AVG(f.irca), 2)                                        AS irca_promedio,
       ROUND(100.0 * SUM(r.grupo_riesgo = 'Alto o inviable')
                   / SUM(f.irca_reportado), 1)                      AS pct_riesgo_alto,
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS pct_continuo
FROM fact_medicion f
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_riesgo    r ON r.riesgo_key    = f.riesgo_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
GROUP BY g.tipo_region
ORDER BY g.tipo_region;


-- ---------------------------------------------------------------------
-- S1. SLICE: tipo_region = 'Nacional'
--     Se fija UN valor de la dimensión geografía y se estudia el
--     subconjunto bajando al nivel departamento.
-- ---------------------------------------------------------------------
SELECT g.departamento,
       COUNT(*)                                                     AS mediciones,
       COUNT(DISTINCT f.municipio_key)                              AS municipios,
       ROUND(AVG(f.irca), 2)                                        AS irca_promedio,
       ROUND(100.0 * SUM(r.grupo_riesgo = 'Alto o inviable')
                   / SUM(f.irca_reportado), 1)                      AS pct_riesgo_alto,
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS pct_continuo
FROM fact_medicion f
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_riesgo    r ON r.riesgo_key    = f.riesgo_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
WHERE g.tipo_region = 'Nacional'                 -- <== SLICE
GROUP BY g.departamento
ORDER BY pct_riesgo_alto DESC;


-- ---------------------------------------------------------------------
-- S2. SLICE 'Nacional': matriz nivel de servicio x grupo de riesgo
--     Pregunta: ¿la calidad del agua cambia según la continuidad del
--     servicio dentro de la región Nacional?
--     Porcentaje por fila: denominador = mediciones con IRCA reportado
--     de ese nivel de servicio.
-- ---------------------------------------------------------------------
SELECT v.nivel_servicio,
       SUM(r.grupo_riesgo = 'Bajo o nulo')                          AS bajo_o_nulo,
       SUM(r.grupo_riesgo = 'Medio')                                AS medio,
       SUM(r.grupo_riesgo = 'Alto o inviable')                      AS alto_o_inviable,
       SUM(r.grupo_riesgo = 'Sin dato')                             AS sin_dato_irca,
       COUNT(*)                                                     AS mediciones,
       ROUND(AVG(f.irca), 2)                                        AS irca_promedio,
       ROUND(100.0 * SUM(r.grupo_riesgo = 'Alto o inviable')
                   / SUM(f.irca_reportado), 1)                      AS pct_riesgo_alto
FROM fact_medicion f
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_riesgo    r ON r.riesgo_key    = f.riesgo_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
WHERE g.tipo_region = 'Nacional'                 -- <== SLICE
GROUP BY v.nivel_servicio, v.orden
ORDER BY v.orden;


-- ---------------------------------------------------------------------
-- D1. DICE: tipo_region = 'Regional'
--           AND anio IN (2024, 2025)
--           AND sistema IN ('Chingaza', 'Sur', 'Tibitoc')
--     Filtros combinados sobre tres dimensiones (geografía, tiempo y
--     sistema). Resultado por trimestre: continuidad, interrupciones y
--     nivel de almacenamiento.
-- ---------------------------------------------------------------------
SELECT t.anio_trimestre,
       COUNT(*)                                                     AS mediciones,
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS pct_continuo,
       ROUND(100.0 * AVG(v.nivel_servicio IN ('Racionado', 'Sin servicio')), 1)
                                                                    AS pct_interrumpido,
       ROUND(AVG(f.nivel_almacenamiento_pct), 1)                    AS almacenamiento_pct
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_sistema   s ON s.sistema_key   = f.sistema_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
WHERE g.tipo_region = 'Regional'                             -- <== DICE (geografía)
  AND t.anio IN (2024, 2025)                                 -- <== DICE (tiempo)
  AND s.sistema IN ('Chingaza', 'Sur', 'Tibitoc')            -- <== DICE (sistema)
GROUP BY t.anio_trimestre
ORDER BY t.anio_trimestre;


-- ---------------------------------------------------------------------
-- D2. DICE (mismos filtros): matriz sistema x nivel de servicio
--     Porcentaje por fila: denominador = mediciones del sistema en el
--     subconjunto filtrado.
-- ---------------------------------------------------------------------
SELECT s.sistema,
       SUM(v.nivel_servicio = 'Continuo')                           AS continuo,
       SUM(v.nivel_servicio = 'Intermitente')                       AS intermitente,
       SUM(v.nivel_servicio = 'Racionado')                          AS racionado,
       SUM(v.nivel_servicio = 'Sin servicio')                       AS sin_servicio,
       COUNT(*)                                                     AS mediciones,
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS pct_continuo,
       ROUND(100.0 * AVG(v.nivel_servicio IN ('Racionado', 'Sin servicio')), 1)
                                                                    AS pct_interrumpido
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_sistema   s ON s.sistema_key   = f.sistema_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
WHERE g.tipo_region = 'Regional'
  AND t.anio IN (2024, 2025)
  AND s.sistema IN ('Chingaza', 'Sur', 'Tibitoc')
GROUP BY s.sistema
ORDER BY s.sistema;


-- ---------------------------------------------------------------------
-- D3. DICE de comparación con un periodo equivalente (2 años contra 2 años)
--     Mismos filtros de geografía y sistema, cambiando solo el periodo:
--     2022-2023 frente a 2024-2025.
-- ---------------------------------------------------------------------
SELECT CASE WHEN t.anio IN (2022, 2023) THEN '2022-2023'
            ELSE '2024-2025' END                                    AS periodo,
       COUNT(*)                                                     AS mediciones,
       ROUND(100.0 * AVG(v.es_continuo), 1)                         AS pct_continuo,
       ROUND(100.0 * AVG(v.nivel_servicio IN ('Racionado', 'Sin servicio')), 1)
                                                                    AS pct_interrumpido,
       ROUND(AVG(f.nivel_almacenamiento_pct), 1)                    AS almacenamiento_pct
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_sistema   s ON s.sistema_key   = f.sistema_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
WHERE g.tipo_region = 'Regional'
  AND t.anio IN (2022, 2023, 2024, 2025)
  AND s.sistema IN ('Chingaza', 'Sur', 'Tibitoc')
GROUP BY periodo
ORDER BY periodo;


-- =====================================================================
-- VALIDACIONES de las operaciones (deben coincidir)
-- =====================================================================

-- V1. Las mediciones del SLICE por departamento suman lo mismo que el
--     conteo directo de la región Nacional (el conteo sí es aditivo).
SELECT (SELECT COUNT(*) FROM fact_medicion f
        JOIN dim_geografia g ON g.municipio_key = f.municipio_key
        WHERE g.tipo_region = 'Nacional')                           AS conteo_directo,
       (SELECT SUM(n) FROM (SELECT COUNT(*) AS n FROM fact_medicion f
        JOIN dim_geografia g ON g.municipio_key = f.municipio_key
        WHERE g.tipo_region = 'Nacional' GROUP BY g.departamento))  AS suma_departamentos;

-- V2. Las celdas de la matriz del DICE (sistema x servicio) suman el
--     total del subconjunto filtrado.
SELECT COUNT(*) AS total_dice
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_sistema   s ON s.sistema_key   = f.sistema_key
WHERE g.tipo_region = 'Regional'
  AND t.anio IN (2024, 2025)
  AND s.sistema IN ('Chingaza', 'Sur', 'Tibitoc');

-- V3. El porcentaje se recalcula y no se promedia: el % continuo del
--     DICE completo se compara con el promedio simple de los % de cada
--     sistema (pueden diferir porque cada sistema tiene distinto número
--     de mediciones).
SELECT ROUND(100.0 * AVG(v.es_continuo), 2)                         AS pct_recalculado
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_sistema   s ON s.sistema_key   = f.sistema_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
WHERE g.tipo_region = 'Regional'
  AND t.anio IN (2024, 2025)
  AND s.sistema IN ('Chingaza', 'Sur', 'Tibitoc');
