-- =============================================================
-- 06 - Sentencias SQL que ejecuta el paquete SSIS
--      (solo documentacion: SSIS las ejecuta automaticamente,
--       no es necesario correrlas a mano)
-- =============================================================

-- Tarea "SQL Limpiar Staging" (antes de cargar el CSV)
TRUNCATE TABLE stg_calidad_agua;

-- Tarea "SQL Limpiar Revision Lote" (antes de la limpieza)
-- Parametros: 0 = User::vLote, 1 = User::vIteracion
DELETE FROM rev_calidad_agua WHERE lote_id = ? AND iteracion = ?;

-- Tarea "SQL Registrar Log" (al final)
-- Parametros 0..8: vLote, vIteracion, System::StartTime, vRecibidos,
-- vAceptadosNetos, vDuplicados, vRevision, vYaCargados, vObservacion
INSERT INTO etl_log (lote_id, iteracion, fecha_inicio, fecha_fin, recibidos, aceptados,
                     duplicados, revision, ya_cargados, estado, observacion)
VALUES (?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, 'OK', ?);

-- Consulta de referencia del Lookup "LKP Ya Cargados"
SELECT iteracion, fecha, municipio, sistema_abastecimiento
FROM dst_calidad_agua;
