import os
import sqlite3

from flask import Blueprint, render_template, request

pivot_bp = Blueprint("pivot", __name__)
DB = os.path.join(os.path.dirname(__file__), "calidad_agua_dw.db")

DIMS = {
    "anio":         ("t.anio",           "Año"),
    "trimestre":    ("t.anio_trimestre", "Trimestre"),
    "region":       ("g.tipo_region",    "Región"),
    "departamento": ("g.departamento",   "Departamento"),
    "sistema":      ("s.sistema",        "Sistema"),
    "riesgo":       ("r.grupo_riesgo",   "Grupo de riesgo"),
    "servicio":     ("v.nivel_servicio", "Nivel de servicio"),
}
MEDIDAS = {
    "mediciones": ("COUNT(*)", "Mediciones"),
    "irca": ("ROUND(AVG(f.irca),2)", "IRCA promedio"),
    "riesgo_alto": ("ROUND(100.0*SUM(CASE WHEN r.grupo_riesgo='Alto o inviable' "
                    "THEN 1 ELSE 0 END)/NULLIF(COUNT(f.irca),0),2)", "% riesgo alto o inviable"),
    "continuo": ("ROUND(100.0*AVG(v.es_continuo),2)", "% servicio continuo"),
    "cobertura": ("ROUND(AVG(f.cobertura_acueducto_pct),2)", "Cobertura promedio (%)"),
}
FROM_SQL = """
FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_sistema   s ON s.sistema_key   = f.sistema_key
JOIN dim_riesgo    r ON r.riesgo_key    = f.riesgo_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
"""


def matriz(filas, columnas, medida, region=None):
    f_sql, c_sql, m_sql = DIMS[filas][0], DIMS[columnas][0], MEDIDAS[medida][0]
    where, params = "", []
    if region:
        where, params = "WHERE g.tipo_region = ?", [region]
    con = sqlite3.connect(DB)
    try:
        celdas = con.execute(
            f"SELECT {f_sql}, {c_sql}, {m_sql} {FROM_SQL} {where} "
            "GROUP BY 1, 2 ORDER BY 1, 2",
            params,
        ).fetchall()
    finally:
        con.close()

    nombres_f = sorted({c[0] for c in celdas}, key=str)
    nombres_c = sorted({c[1] for c in celdas}, key=str)
    valor = {(a, b): v for a, b, v in celdas}
    return nombres_f, nombres_c, valor


@pivot_bp.route("/multidimensional/pivot")
def pivot():
    filas = request.args.get("filas", "region")
    columnas = request.args.get("columnas", "anio")
    medida = request.args.get("medida", "continuo")
    region = request.args.get("region") or None
    if filas not in DIMS or columnas not in DIMS or medida not in MEDIDAS:
        filas, columnas, medida = "region", "anio", "continuo"
    if filas == columnas:
        columnas = "anio" if filas != "anio" else "region"
    nf, nc, valor = matriz(filas, columnas, medida, region)
    return render_template(
        "multidimensional_pivot.html",
        filas=filas,
        columnas=columnas,
        medida=medida,
        region=region,
        nombres_f=nf,
        nombres_c=nc,
        valor=valor,
        dims=DIMS,
        medidas=MEDIDAS,
    )
