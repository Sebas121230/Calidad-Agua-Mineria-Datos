# -*- coding: utf-8 -*-
"""
Etapa 5 - Operación PIVOT sobre el modelo estrella (calidad del agua).
Responsable: Andrés Felipe Beltrán Barrera

PIVOT (rotación): cambia la disposición de las dimensiones en una matriz para ver
los mismos resultados desde otra perspectiva. La dimensión que estaba en las filas
pasa a las columnas y viceversa, o se reemplaza un eje por otra dimensión o por las
medidas.

- Matriz dimensión x dimensión: una medida en cada celda.
  Ejemplo del proyecto: % servicio continuo, filas = región, columnas = año
  -> pivot: filas = año, columnas = región.
- Matriz dimensión x medidas: varias medidas como columnas (o como filas).
  Ejemplo del proyecto: región Regional 2022-2025, filas = trimestre,
  columnas = almacenamiento, precipitación y % continuo -> pivot: medidas x trimestre.

Reglas que se cumplen en todas las consultas:
- Cada celda y cada total se recalcula desde la tabla de hechos (GROUP BY propio);
  los totales de fila y de columna NO son la suma ni el promedio de las celdas.
- Cada porcentaje indica su denominador (se reutilizan las medidas del módulo
  consultas_slice_dice, que son las del modelo).
- Los nombres de columnas solo se toman de listas permitidas y los valores van como
  parámetros (?), así que lo que llega desde la página no puede alterar el SQL.

Solo usa librerías que vienen con Python (sqlite3).
Prueba rápida desde la carpeta del proyecto:  python etapa5/consultas_pivot.py
"""
try:
    from etapa5 import consultas_slice_dice as base
except ImportError:  # al ejecutar el archivo directamente
    import consultas_slice_dice as base

BASE = base.BASE
FROM_ESTRELLA = base.FROM_ESTRELLA
FILTROS = base.FILTROS

# Ejes que se pueden poner en filas o columnas: nombre -> (columna, orden, etiqueta, dimensión)
EJES = {
    "region":       ("g.tipo_region",    "g.tipo_region",    "Región",            "Geografía"),
    "departamento": ("g.departamento",   "g.departamento",   "Departamento",      "Geografía"),
    "municipio":    ("g.municipio",      "g.municipio",      "Municipio",         "Geografía"),
    "anio":         ("t.anio",           "t.anio",           "Año",               "Tiempo"),
    "trimestre":    ("t.anio_trimestre", "t.anio_trimestre", "Trimestre",         "Tiempo"),
    "mes":          ("t.nombre_mes",     "MIN(t.mes)",       "Mes",               "Tiempo"),
    "sistema":      ("s.sistema",        "s.sistema",        "Sistema",           "Sistema de abastecimiento"),
    "servicio":     ("v.nivel_servicio", "MIN(v.orden)",     "Nivel de servicio", "Servicio"),
    "riesgo":       ("r.grupo_riesgo",   "MIN(r.orden)",     "Grupo de riesgo",   "Riesgo"),
}
EJE_MEDIDAS = "medidas"   # eje especial: las medidas ocupan las filas o las columnas

# Medidas: las del modelo + precipitación y cobertura, que también están en la tabla de hechos
MEDIDAS = dict(base.MEDIDAS)
MEDIDAS["precipitacion"] = ("ROUND(AVG(f.precipitacion_mm), 2)", "Precipitación promedio", "mm",
                            "Promedio de las mediciones con dato de precipitación")
MEDIDAS["cobertura"] = ("ROUND(AVG(f.cobertura_acueducto_pct), 1)", "Cobertura promedio", "%",
                        "Promedio de la cobertura de acueducto de las mediciones")


# Utilidades

def _validar_eje(nombre, que):
    if nombre != EJE_MEDIDAS and nombre not in EJES:
        raise ValueError(f"{que} no válido: {nombre}. Opciones: {', '.join(list(EJES) + [EJE_MEDIDAS])}")


def _validar_medida(nombre):
    if nombre not in MEDIDAS:
        raise ValueError(f"Medida no válida: {nombre}. Opciones: {', '.join(MEDIDAS)}")


def _agrupar(ejes, medidas, filtros):
    """
    Consulta la tabla de hechos agrupando por 0, 1 o 2 ejes.
    Devuelve (filas_resultado, sql_legible). Cada fila trae g0, g1 (si aplica),
    las medidas pedidas y 'n' (mediciones del grupo).
    """
    where, params = base.construir_where(filtros)
    cols = [f"{EJES[e][0]} AS g{i}" for i, e in enumerate(ejes)]
    sel = cols + [f"{MEDIDAS[m][0]} AS {m}" for m in medidas] + ["COUNT(*) AS n"]
    sql = "SELECT " + ",\n       ".join(sel) + f"\n{FROM_ESTRELLA}{where}"
    if ejes:
        sql += "\nGROUP BY " + ", ".join(EJES[e][0] for e in ejes)
        sql += "\nORDER BY " + ", ".join(EJES[e][1] for e in ejes)
    return base._consultar(sql, params), base.sql_legible(sql, params)


def _sql_eje(nombre):
    return EJES[nombre][0]


# Operación

def operacion_pivot(filas, columnas, medida="pct_continuo", filtros=None, medidas=None):
    """
    PIVOT: arma la matriz con 'filas' en las filas y 'columnas' en las columnas.
    Para rotarla basta con llamar otra vez intercambiando filas y columnas.

    filas, columnas : nombre de un eje de EJES o "medidas" (solo uno de los dos).
    medida          : medida de las celdas cuando los dos ejes son dimensiones.
    filtros         : filtros opcionales, por ejemplo {'region': ['Regional']}.
    medidas         : lista de medidas cuando un eje es "medidas".
    """
    _validar_eje(filas, "Filas")
    _validar_eje(columnas, "Columnas")
    if filas == columnas:
        raise ValueError("Filas y columnas deben ser ejes diferentes para poder pivotar.")
    if EJE_MEDIDAS in (filas, columnas):
        return _pivot_con_medidas(filas, columnas, filtros, medidas)
    _validar_medida(medida)
    filtros = base._normalizar(filtros)

    # 1) Celdas: GROUP BY filas, columnas
    celdas, sql = _agrupar([filas, columnas], [medida], filtros)
    # 2) Totales de fila y de columna: cada uno con su propio GROUP BY (no se suman celdas)
    tot_filas, _ = _agrupar([filas], [medida], filtros)
    tot_cols, _ = _agrupar([columnas], [medida], filtros)
    # 3) Total general
    general, _ = _agrupar([], [medida], filtros)

    etq_filas = [str(f["g0"]) for f in tot_filas]
    etq_cols = [str(f["g0"]) for f in tot_cols]
    pos_f = {e: i for i, e in enumerate(etq_filas)}
    pos_c = {e: j for j, e in enumerate(etq_cols)}
    valores = [[None] * len(etq_cols) for _ in etq_filas]
    conteos = [[0] * len(etq_cols) for _ in etq_filas]
    for c in celdas:
        i, j = pos_f[str(c["g0"])], pos_c[str(c["g1"])]
        valores[i][j] = c[medida]
        conteos[i][j] = c["n"]

    return {
        "operacion": "Pivot",
        "tipo": "dimensiones",
        "filas_eje": filas, "columnas_eje": columnas,
        "etiqueta_filas": EJES[filas][2], "etiqueta_columnas": EJES[columnas][2],
        "dimensiones": [EJES[filas][3], EJES[columnas][3]],
        "medida": medida, "medida_etiqueta": MEDIDAS[medida][1],
        "unidad": MEDIDAS[medida][2], "denominador": MEDIDAS[medida][3],
        "filas": etq_filas, "columnas": etq_cols,
        "valores": valores, "conteos": conteos,
        "total_fila": [f[medida] for f in tot_filas],
        "total_columna": [f[medida] for f in tot_cols],
        "n_fila": [f["n"] for f in tot_filas],
        "n_columna": [f["n"] for f in tot_cols],
        "total_general": general[0][medida],
        "n_total": general[0]["n"],
        "seleccion": base.describir_seleccion(filtros),
        "sql": sql,
    }


def _pivot_con_medidas(filas, columnas, filtros, medidas):
    """Matriz dimensión x medidas (o medidas x dimensión)."""
    medidas = [m for m in (medidas or []) if m in MEDIDAS] or ["almacenamiento", "precipitacion", "pct_continuo"]
    eje = columnas if filas == EJE_MEDIDAS else filas
    filtros = base._normalizar(filtros)
    grupos, sql = _agrupar([eje], medidas, filtros)
    general, _ = _agrupar([], medidas, filtros)

    etq_eje = [str(g["g0"]) for g in grupos]
    # matriz con el eje en las filas y las medidas en las columnas
    valores = [[g[m] for m in medidas] for g in grupos]
    conteos = [[g["n"]] * len(medidas) for g in grupos]
    totales_medida = [general[0][m] for m in medidas]
    etq_medidas = [f"{MEDIDAS[m][1]} ({MEDIDAS[m][2]})" for m in medidas]

    datos = {
        "operacion": "Pivot",
        "tipo": "medidas",
        "filas_eje": filas, "columnas_eje": columnas,
        "dimensiones": [EJES[eje][3]],
        "medidas": medidas,
        "unidades": [MEDIDAS[m][2] for m in medidas],
        "medida_etiqueta": "Varias medidas",
        "denominador": "; ".join(f"{MEDIDAS[m][1]}: {MEDIDAS[m][3]}" for m in medidas),
        "total_general": None,
        "n_total": general[0]["n"],
        "seleccion": base.describir_seleccion(filtros),
        "sql": sql,
    }
    if filas == EJE_MEDIDAS:  # rotada: medidas en las filas, el eje en las columnas
        datos.update({
            "etiqueta_filas": "Medida", "etiqueta_columnas": EJES[eje][2],
            "filas": etq_medidas, "columnas": etq_eje,
            "valores": [list(col) for col in zip(*valores)] if valores else [],
            "conteos": [list(col) for col in zip(*conteos)] if conteos else [],
            "total_fila": totales_medida, "total_columna": [None] * len(etq_eje),
            "n_fila": [general[0]["n"]] * len(medidas), "n_columna": [g["n"] for g in grupos],
            "unidades_filas": [MEDIDAS[m][2] for m in medidas],
        })
    else:
        datos.update({
            "etiqueta_filas": EJES[eje][2], "etiqueta_columnas": "Medida",
            "filas": etq_eje, "columnas": etq_medidas,
            "valores": valores, "conteos": conteos,
            "total_fila": [None] * len(etq_eje), "total_columna": totales_medida,
            "n_fila": [g["n"] for g in grupos], "n_columna": [general[0]["n"]] * len(medidas),
            "unidades_columnas": [MEDIDAS[m][2] for m in medidas],
        })
    return datos


def indicadores(filtros):
    """Medidas del subconjunto filtrado (una fila) y del total sin filtro, para comparar."""
    nombres = list(MEDIDAS)
    sel, _ = _agrupar([], nombres, base._normalizar(filtros))
    tot, _ = _agrupar([], nombres, {})
    return sel[0], tot[0]


def validar_pivot(filas, columnas, medida="pct_continuo", filtros=None, medidas=None):
    """
    Comprueba que el pivot solo cambia la disposición y no los resultados:
    P1. Las mediciones de las celdas suman el total del subconjunto.
    P2. La matriz rotada es exactamente la transpuesta de la original.
    P3. Los totales se recalculan desde la tabla de hechos (no son el promedio de las celdas).
    """
    a = operacion_pivot(filas, columnas, medida, filtros, medidas)
    b = operacion_pivot(columnas, filas, medida, filtros, medidas)
    if a["tipo"] == "dimensiones":
        suma = sum(sum(f) for f in a["conteos"])
    else:
        suma = sum(a["n_fila"] if a["etiqueta_columnas"] == "Medida" else a["n_columna"])
    transpuesta = [list(col) for col in zip(*a["valores"])] if a["valores"] else []
    resultado = {
        "p1_suma_celdas": suma, "p1_total": a["n_total"], "p1_ok": suma == a["n_total"],
        "p2_ok": transpuesta == b["valores"] and a["filas"] == b["columnas"] and a["columnas"] == b["filas"],
        "p2_celdas": sum(len(f) for f in a["valores"]),
    }
    if a["tipo"] == "dimensiones" and a["unidad"] == "%":
        # se compara con el promedio simple de los totales del eje con menos grupos
        eje = a["total_fila"] if len(a["total_fila"]) <= len(a["total_columna"]) else a["total_columna"]
        validos = [v for v in eje if v is not None]
        promedio_simple = round(sum(validos) / len(validos), 1) if validos else None
        resultado.update({"p3_total": a["total_general"], "p3_promedio_simple": promedio_simple,
                          "p3_eje": a["etiqueta_filas"] if eje is a["total_fila"] else a["etiqueta_columnas"]})
    return resultado


# Prueba rápida: imprime los ejemplos del proyecto

if __name__ == "__main__":
    p = operacion_pivot("region", "anio", "pct_continuo")
    print("PIVOT 1 (región x año):", p["medida_etiqueta"])
    print("  ", p["columnas"])
    for etq, fila, tot in zip(p["filas"], p["valores"], p["total_fila"]):
        print("  ", etq, fila, "total:", tot)
    print("   total columna:", p["total_columna"], "general:", p["total_general"])
    r = operacion_pivot("anio", "region", "pct_continuo")
    print("  rotado (año x región):", r["columnas"])
    for etq, fila in zip(r["filas"], r["valores"]):
        print("  ", etq, fila)
    print("  Validación:", validar_pivot("region", "anio", "pct_continuo"))

    f2 = {"region": ["Regional"], "anio": ["2022", "2023", "2024", "2025"]}
    m = ["almacenamiento", "precipitacion", "pct_continuo"]
    q = operacion_pivot("trimestre", "medidas", filtros=f2, medidas=m)
    print("\nPIVOT 2 (trimestre x medidas):", q["seleccion"])
    for etq, fila in zip(q["filas"], q["valores"]):
        print("  ", etq, fila)
    print("  Validación:", validar_pivot("trimestre", "medidas", filtros=f2, medidas=m))
