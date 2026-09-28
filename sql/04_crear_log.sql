CREATE TABLE etl_log (
    log_id          INT IDENTITY(1,1) PRIMARY KEY,
    lote_id         INT,
    iteracion       INT,
    fecha_inicio    DATETIME,
    fecha_fin       DATETIME,
    recibidos       INT,
    aceptados       INT,
    duplicados      INT,
    revision        INT,
    ya_cargados     INT,
    estado          VARCHAR(20),
    observacion     VARCHAR(500)
);