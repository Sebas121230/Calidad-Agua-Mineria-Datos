# -*- coding: utf-8 -*-
"""
Etapa 5 - Operaciones SLICE y DICE sobre el modelo estrella (calidad del agua).
Responsable: John Sebastian Rodriguez D.

Este módulo recibe los filtros que el usuario elige en Flask, arma la consulta SQL
sobre etapa5/calidad_agua_dw.db y devuelve los resultados listos para la vista.

- SLICE: se fija UN valor de UNA dimensión (por ejemplo, tipo_region = 'Nacional').
- DICE : se combinan filtros sobre DOS o más dimensiones
         (por ejemplo, Regional + 2024-2025 + sistemas de la EAAB).

Reglas que se cumplen en todas las consultas:
- Las medidas se recalculan desde la tabla de hechos con el filtro activo; nunca se
  suman ni se promedian porcentajes o promedios de otros grupos.
- Cada porcentaje indica su denominador.
- Los nombres de columnas solo se toman de listas permitidas y los valores van como
  parámetros (?), así que lo que llega desde la página no puede alterar el SQL.

Solo usa librerías que vienen con Python (sqlite3).
Prueba rápida desde la carpeta del proyecto:  python etapa5/consultas_slice_dice.py
"""
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent / "calidad_agua_dw.db"

# Uniones de la estrella: cada dimensión tiene una fila por clave, así que no se
# multiplican las mediciones.
FROM_ESTRELLA = """FROM fact_medicion f
JOIN dim_tiempo    t ON t.fecha_key     = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_sistema   s ON s.sistema_key   = f.sistema_key
JOIN dim_riesgo    r ON r.riesgo_key    = f.riesgo_key
JOIN dim_servicio  v ON v.servicio_key  = f.servicio_key
"""

# Dimensiones que se pueden filtrar: nombre que usa la página -> (columna, etiqueta, dimensión)
FILTROS = {
    "region":       ("g.tipo_region",    "Región",              "Geografía"),
    "departamento": ("g.departamento",   "Departamento",        "Geografía"),
    "anio":         ("t.anio",           "Año",                 "Tiempo"),
    "trimestre":    ("t.anio_trimestre", "Trimestre",           "Tiempo"),
    "sistema":      ("s.sistema",        "Sistema",             "Sistema de abastecimiento"),
    "servicio":     ("v.nivel_servicio", "Nivel de servicio",   "Servicio"),
    "riesgo":       ("r.grupo_riesgo",   "Grupo de riesgo",     "Riesgo"),
}

# Niveles por los que se puede agrupar el resultado: nombre -> (columna, orden, etiqueta)
NIVELES = {
    "region":       ("g.tipo_region",    "g.tipo_region",    "Región"),
    "departamento": ("g.departamento",   "g.departamento",   "Departamento"),
    "municipio":    ("g.municipio",      "g.municipio",      "Municipio"),
    "anio":         ("t.anio",           "t.anio",           "Año"),
    "trimestre":    ("t.anio_trimestre", "t.anio_trimestre", "Trimestre"),
    "sistema":      ("s.sistema",        "s.sistema",        "Sistema"),
    "servicio":     ("v.nivel_servicio", "MIN(v.orden)",     "Nivel de servicio"),
    "riesgo":       ("r.grupo_riesgo",   "MIN(r.orden)",     "Grupo de riesgo"),
}

# Columnas posibles de una matriz: nombre -> (columna, valores en orden)
COLUMNAS_MATRIZ = {
    "servicio": ("v.nivel_servicio", ["Continuo", "Intermitente", "Racionado", "Sin servicio"]),
    "riesgo":   ("r.grupo_riesgo",   ["Bajo o nulo", "Medio", "Alto o inviable", "Sin dato"]),
}

# Medidas: nombre -> (SQL, etiqueta, unidad, denominador o forma de agregar)
MEDIDAS = {
    "mediciones": ("COUNT(*)", "Mediciones", "mediciones",
                   "Conteo de filas de la tabla de hechos (aditiva)"),
    "municipios": ("COUNT(DISTINCT f.municipio_key)", "Municipios", "municipios",
                   "Conteo distinto (no se suma entre grupos)"),
    "irca_promedio": ("ROUND(AVG(f.irca), 2)", "IRCA promedio", "puntos (0-100)",
                      "Promedio de las mediciones con IRCA reportado"),
    "pct_riesgo_alto": (
        "ROUND(100.0 * SUM(r.grupo_riesgo = 'Alto o inviable') / NULLIF(SUM(f.irca_reportado), 0), 1)",
        "% riesgo alto o inviable", "%",
        "Denominador: mediciones con IRCA reportado"),
    "pct_continuo": ("ROUND(100.0 * AVG(v.es_continuo), 1)", "% servicio continuo", "%",
                     "Denominador: todas las mediciones del grupo"),
    "pct_interrumpido": (
        "ROUND(100.0 * AVG(v.nivel_servicio IN ('Racionado', 'Sin servicio')), 1)",
        "% racionado o sin servicio", "%",
        "Denominador: todas las mediciones del grupo"),
    "almacenamiento": ("ROUND(AVG(f.nivel_almacenamiento_pct), 1)", "Almacenamiento promedio", "%",
                       "Promedio de las mediciones con dato de almacenamiento"),
}

SELECT_MEDIDAS = ",\n       ".join(f"{sql} AS {nombre}" for nombre, (sql, *_r) in MEDIDAS.items())


# Utilidades

def conectar():
    con = sqlite3.connect(BASE)
    con.row_factory = sqlite3.Row
    return con


def _consultar(sql, params=()):
    con = conectar()
    try:
        return [dict(fila) for fila in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def _normalizar(filtros):
    """Deja solo dimensiones permitidas y valores no vacíos. {'anio': ['2024']} -> {'anio': ['2024']}"""
    limpios = {}
    for nombre, valores in (filtros or {}).items():
        if nombre not in FILTROS:
            continue
        if not isinstance(valores, (list, tuple)):
            valores = [valores]
        valores = [str(v).strip() for v in valores if str(v).strip() not in ("", "Todos")]
        if valores:
            limpios[nombre] = valores
    return limpios


def construir_where(filtros):
    """Arma el WHERE con parámetros. Devuelve (texto_sql, lista_de_parámetros)."""
    condiciones, params = [], []
    for nombre, valores in filtros.items():
        columna = FILTROS[nombre][0]
        if nombre == "anio":
            valores = [int(v) for v in valores]
        marcas = ", ".join("?" for _ in valores)
        condiciones.append(f"{columna} IN ({marcas})")
        params.extend(valores)
    where = "WHERE " + "\n  AND ".join(condiciones) if condiciones else ""
    return where, params


def _validar(nombre, permitido, que):
    """Evita niveles o columnas que no existen en el modelo."""
    if nombre not in permitido:
        raise ValueError(f"{que} no válido: {nombre}. Opciones: {', '.join(permitido)}")


def describir_seleccion(filtros):
    """Texto legible de la selección activa, para mostrarlo en la vista."""
    if not filtros:
        return "Sin filtros (todas las mediciones)"
    return " | ".join(f"{FILTROS[n][1]} = {', '.join(v)}" for n, v in filtros.items())


def sql_legible(sql, params):
    """Reemplaza los ? por los valores para mostrar la consulta en la página (solo lectura)."""
    for p in params:
        valor = str(p) if isinstance(p, int) else "'" + str(p).replace("'", "''") + "'"
        sql = sql.replace("?", valor, 1)
    return sql.strip()



# Consultas

def opciones():
    """Valores disponibles para llenar los filtros de la página."""
    def lista(sql):
        return [fila["v"] for fila in _consultar(sql)]
    return {
        "region": lista("SELECT DISTINCT tipo_region AS v FROM dim_geografia WHERE municipio_key > 0 ORDER BY v"),
        "departamento": lista("SELECT DISTINCT departamento AS v FROM dim_geografia WHERE municipio_key > 0 ORDER BY v"),
        "anio": lista("SELECT DISTINCT anio AS v FROM dim_tiempo WHERE fecha_key > 0 ORDER BY v"),
        "sistema": lista("SELECT sistema AS v FROM dim_sistema WHERE sistema_key > 0 ORDER BY v"),
        "servicio": lista("SELECT nivel_servicio AS v FROM dim_servicio WHERE servicio_key > 0 ORDER BY orden"),
        "riesgo": lista("SELECT DISTINCT grupo_riesgo AS v FROM dim_riesgo WHERE riesgo_key > 0 ORDER BY orden"),
    }


def indicadores(filtros):
    """Todas las medidas recalculadas para el subconjunto filtrado (una sola fila)."""
    where, params = construir_where(filtros)
    sql = f"SELECT {SELECT_MEDIDAS}\n{FROM_ESTRELLA}{where}"
    return _consultar(sql, params)[0]


def tabla_por_nivel(filtros, nivel):
    """Medidas del subconjunto agrupadas por un nivel de una jerarquía."""
    _validar(nivel, NIVELES, "Nivel")
    columna, orden, _ = NIVELES[nivel]
    where, params = construir_where(filtros)
    sql = (f"SELECT {columna} AS grupo,\n       {SELECT_MEDIDAS}\n{FROM_ESTRELLA}{where}\n"
           f"GROUP BY {columna}\nORDER BY {orden}")
    return _consultar(sql, params), sql_legible(sql, params)


def matriz(filtros, filas, columnas):
    """
    Matriz que cruza dos dimensiones (conteo de mediciones) con el % por fila.
    Denominador del % por fila: total de mediciones de esa fila en el subconjunto
    (incluye las mediciones "Sin dato" de IRCA, que se muestran en su propia columna).
    """
    _validar(filas, NIVELES, "Filas de la matriz")
    _validar(columnas, COLUMNAS_MATRIZ, "Columnas de la matriz")
    col_filas, orden, etiqueta = NIVELES[filas]
    col_cols, valores = COLUMNAS_MATRIZ[columnas]
    where, params = construir_where(filtros)
    celdas = ",\n       ".join(
        f"SUM({col_cols} = ?) AS c{i}" for i in range(len(valores)))
    sql = (f"SELECT {col_filas} AS grupo,\n       {celdas},\n       COUNT(*) AS total\n"
           f"{FROM_ESTRELLA}{where}\nGROUP BY {col_filas}\nORDER BY {orden}")
    todos = list(valores) + params
    resultado = []
    for fila in _consultar(sql, todos):
        conteos = [fila[f"c{i}"] for i in range(len(valores))]
        total = fila["total"]
        resultado.append({
            "grupo": fila["grupo"],
            "conteos": conteos,
            "porcentajes": [round(100.0 * c / total, 1) if total else 0 for c in conteos],
            "total": total,
        })
    totales = [sum(f["conteos"][i] for f in resultado) for i in range(len(valores))]
    return {
        "etiqueta_filas": etiqueta,
        "columnas": valores,
        "filas": resultado,
        "totales": totales,
        "total_general": sum(totales),
        "sql": sql_legible(sql, todos),
    }



# Operaciones

def operacion_slice(dimension, valor, nivel, filas_matriz, columnas_matriz):
    """
    SLICE: fija UN valor de UNA dimensión.
    Ejemplo del proyecto: dimension='region', valor='Nacional', nivel='departamento',
    filas_matriz='servicio', columnas_matriz='riesgo'.
    """
    _validar(dimension, FILTROS, "Dimensión")
    filtros = _normalizar({dimension: [valor]})
    if len(filtros) != 1 or len(filtros[dimension]) != 1:
        raise ValueError("El slice necesita exactamente una dimensión con un solo valor.")
    tabla, sql = tabla_por_nivel(filtros, nivel)
    return {
        "operacion": "Slice",
        "seleccion": describir_seleccion(filtros),
        "dimensiones_filtradas": [FILTROS[dimension][2]],
        "indicadores": indicadores(filtros),
        "contexto": indicadores({}),          # total sin filtro, para comparar
        "nivel": NIVELES[nivel][2],
        "tabla": tabla,
        "sql": sql,
        "matriz": matriz(filtros, filas_matriz, columnas_matriz),
    }


def operacion_dice(filtros, nivel, filas_matriz, columnas_matriz):
    """
    DICE: combina filtros sobre DOS o más dimensiones.
    Ejemplo del proyecto: {'region': ['Regional'], 'anio': ['2024', '2025'],
    'sistema': ['Chingaza', 'Sur', 'Tibitoc']}, nivel='trimestre',
    filas_matriz='sistema', columnas_matriz='servicio'.
    """
    filtros = _normalizar(filtros)
    dimensiones = {FILTROS[n][2] for n in filtros}
    if len(dimensiones) < 2:
        raise ValueError("El dice necesita filtros sobre al menos dos dimensiones diferentes.")
    tabla, sql = tabla_por_nivel(filtros, nivel)
    return {
        "operacion": "Dice",
        "seleccion": describir_seleccion(filtros),
        "dimensiones_filtradas": sorted(dimensiones),
        "indicadores": indicadores(filtros),
        "contexto": indicadores({}),
        "nivel": NIVELES[nivel][2],
        "tabla": tabla,
        "sql": sql,
        "matriz": matriz(filtros, filas_matriz, columnas_matriz),
    }


def comparar_periodos(filtros, periodo_a, periodo_b):
    """
    Compara dos periodos de la misma duración con los demás filtros iguales.
    Ejemplo: Regional + EAAB, 2022-2023 frente a 2024-2025.
    """
    if len(periodo_a) != len(periodo_b):
        raise ValueError("Los periodos deben tener la misma cantidad de años.")
    base = {n: v for n, v in _normalizar(filtros).items() if n != "anio"}
    return [
        {"periodo": f"{min(p)}-{max(p)}" if len(p) > 1 else str(p[0]),
         **indicadores({**base, "anio": [str(a) for a in p]})}
        for p in (periodo_a, periodo_b)
    ]



# Prueba rápida: imprime los ejemplos del proyecto

if __name__ == "__main__":
    s = operacion_slice("region", "Nacional", "departamento", "servicio", "riesgo")
    print("SLICE:", s["seleccion"])
    print("  Indicadores:", {k: s["indicadores"][k] for k in
                             ("mediciones", "municipios", "irca_promedio", "pct_riesgo_alto")})
    print("  Mayor riesgo:", max(s["tabla"], key=lambda f: f["pct_riesgo_alto"])["grupo"])
    print("  Suma de departamentos:", sum(f["mediciones"] for f in s["tabla"]))
    for f in s["matriz"]["filas"]:
        print("  Matriz", f["grupo"], f["conteos"], f["porcentajes"])

    d = operacion_dice({"region": "Regional", "anio": ["2024", "2025"],
                        "sistema": ["Chingaza", "Sur", "Tibitoc"]},
                       "trimestre", "sistema", "servicio")
    print("\nDICE:", d["seleccion"])
    print("  Dimensiones filtradas:", d["dimensiones_filtradas"])
    print("  Indicadores:", {k: d["indicadores"][k] for k in
                             ("mediciones", "pct_continuo", "pct_interrumpido", "almacenamiento")})
    for f in d["tabla"]:
        print("  ", f["grupo"], f["pct_continuo"], f["pct_interrumpido"], f["almacenamiento"])
    print("  Total matriz:", d["matriz"]["total_general"])

    print("\nPERIODOS EQUIVALENTES:")
    for p in comparar_periodos({"region": "Regional", "sistema": ["Chingaza", "Sur", "Tibitoc"]},
                               [2022, 2023], [2024, 2025]):
        print("  ", p["periodo"], p["mediciones"], p["pct_continuo"], p["pct_interrumpido"],
              p["almacenamiento"])
