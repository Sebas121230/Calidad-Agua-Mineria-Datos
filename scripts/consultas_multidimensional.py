"""Consultas del modelo estrella para la seccion de analisis multidimensional.

Todas las cifras salen de etapa5/calidad_agua_dw.db. Las dimensiones se unen por
sus claves primarias, de modo que cada fila de fact_medicion se cuenta una sola
vez (no hay multiplicacion de registros por relaciones).
"""
from __future__ import annotations

import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "etapa5" / "calidad_agua_dw.db"

FROM = """
FROM fact_medicion f
JOIN dim_tiempo t ON t.fecha_key = f.fecha_key
JOIN dim_geografia g ON g.municipio_key = f.municipio_key
JOIN dim_sistema s ON s.sistema_key = f.sistema_key
JOIN dim_riesgo r ON r.riesgo_key = f.riesgo_key
JOIN dim_servicio sv ON sv.servicio_key = f.servicio_key
"""

FILTROS = {
    "anio": "t.anio",
    "tipo_region": "g.tipo_region",
    "sistema": "s.sistema",
    "nivel_servicio": "sv.nivel_servicio",
    "grupo_riesgo": "r.grupo_riesgo",
}

ALTO = "CASE WHEN r.grupo_riesgo = 'Alto o inviable' THEN 1 ELSE 0 END"
CONTINUO = "CASE WHEN sv.es_continuo = 1 THEN 1 ELSE 0 END"

GEO = {
    "region": ("g.tipo_region", "Región"),
    "departamento": ("g.departamento", "Departamento"),
    "municipio": ("g.municipio", "Municipio"),
}
TIEMPO = {
    "anio": ("t.anio", "Año"),
    "trimestre": ("t.anio_trimestre", "Trimestre"),
}

SERVICIOS = ["Continuo", "Intermitente", "Racionado", "Sin servicio"]
SISTEMAS = ["Chingaza", "Sur", "Tibitoc", "Fuera de cobertura EAAB"]
RIESGOS = ["Bajo o nulo", "Medio", "Alto o inviable"]
PERIODOS = {
    "2019-2023": "t.anio BETWEEN 2019 AND 2023",
    "2024": "t.anio = 2024",
    "2025": "t.anio = 2025",
    "2024-2025": "t.anio BETWEEN 2024 AND 2025",
}


def _conectar():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "No existe etapa5/calidad_agua_dw.db. Ejecute python etapa5/cargar_modelo.py"
        )
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


@contextmanager
def _db():
    con = _conectar()
    try:
        yield con
    finally:
        con.close()


def _where(filtros, extra=None):
    condiciones = []
    parametros = []
    for clave, columna in FILTROS.items():
        if clave not in filtros:
            continue
        valor = filtros.get(clave)
        if valor is None or str(valor).strip() in ("", "Todos"):
            continue
        if clave == "anio":
            try:
                valor = int(valor)
            except (TypeError, ValueError):
                continue
        condiciones.append(f"{columna} = ?")
        parametros.append(valor)
    periodo = filtros.get("periodo")
    if periodo in PERIODOS:
        condiciones.append(PERIODOS[periodo])
    if extra:
        condiciones.append(extra)
    where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    return where, parametros


def _pct(parte, total):
    if not total:
        return None
    return round(parte * 100.0 / total, 2)


def _pearson(xs, ys):
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    var_x = sum((x - mx) ** 2 for x in xs)
    var_y = sum((y - my) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(var_x * var_y), 3)


def _filtros_texto(filtros):
    partes = []
    if filtros.get("anio") not in (None, "", "Todos"):
        partes.append(f"año {filtros['anio']}")
    else:
        partes.append("todos los años")
    periodo = filtros.get("periodo")
    if periodo not in (None, "", "Todos"):
        partes.append(f"periodo {periodo}")
    for clave, etiqueta in (("tipo_region", "región"), ("sistema", "sistema"),
                            ("nivel_servicio", "servicio")):
        valor = filtros.get(clave)
        if valor not in (None, "", "Todos"):
            partes.append(f"{etiqueta} {valor}")
    return ", ".join(partes)


def opciones():
    with _db() as con:
        anios = [r["anio"] for r in con.execute(
            "SELECT DISTINCT anio FROM dim_tiempo WHERE anio > 0 ORDER BY anio"
        )]
        regiones = [r["tipo_region"] for r in con.execute(
            "SELECT DISTINCT tipo_region FROM dim_geografia "
            "WHERE tipo_region <> 'Desconocido' ORDER BY "
            "CASE tipo_region WHEN 'Regional' THEN 1 ELSE 2 END"
        )]
        sistemas = [r["sistema"] for r in con.execute(
            "SELECT DISTINCT sistema FROM dim_sistema WHERE sistema <> 'Desconocido' ORDER BY "
            "CASE sistema WHEN 'Chingaza' THEN 1 WHEN 'Sur' THEN 2 "
            "WHEN 'Tibitoc' THEN 3 ELSE 4 END"
        )]
        servicios = [r["nivel_servicio"] for r in con.execute(
            "SELECT DISTINCT nivel_servicio FROM dim_servicio "
            "WHERE es_continuo IN (0,1) AND nivel_servicio <> 'Desconocido' ORDER BY orden"
        )]
    return {"anios": anios, "regiones": regiones, "sistemas": sistemas,
            "servicios": servicios,
            "periodos": ["Todos", "2019-2023", "2024", "2025", "2024-2025"]}


def panorama():
    with _db() as con:
        fila = con.execute(
            f"SELECT COUNT(*) n, COUNT(f.irca) irca_n, "
            f"COUNT(DISTINCT f.municipio_key) municipios, "
            f"COUNT(DISTINCT g.departamento) departamentos, "
            f"COUNT(DISTINCT f.sistema_key) sistemas, "
            f"COUNT(DISTINCT t.anio_trimestre) periodos, "
            f"MIN(t.anio) anio_min, MAX(t.anio) anio_max, "
            f"ROUND(AVG(f.cobertura_acueducto_pct), 2) cobertura "
            f"FROM fact_medicion f JOIN dim_tiempo t ON t.fecha_key = f.fecha_key "
            f"JOIN dim_geografia g ON g.municipio_key = f.municipio_key"
        ).fetchone()
    return {
        "registros": fila["n"],
        "irca_validos": fila["irca_n"],
        "municipios": fila["municipios"],
        "departamentos": fila["departamentos"],
        "sistemas": fila["sistemas"],
        "periodos": fila["periodos"],
        "anio_min": fila["anio_min"],
        "anio_max": fila["anio_max"],
        "cobertura_media": fila["cobertura"],
        "fuente": "etapa5/calidad_agua_dw.db",
    }


def pregunta1(filtros):
    """Continuidad por sistema, geografia y tiempo (drill-down / roll-up)."""
    nivel_geo = filtros.get("nivel_geo", "region")
    nivel_tiempo = filtros.get("nivel_tiempo", "anio")
    if nivel_geo not in GEO:
        nivel_geo = "region"
    if nivel_tiempo not in TIEMPO:
        nivel_tiempo = "anio"
    geo_expr, geo_label = GEO[nivel_geo]
    tiempo_expr, tiempo_label = TIEMPO[nivel_tiempo]

    f1 = {"anio": filtros.get("anio"), "tipo_region": filtros.get("tipo_region")}
    where, params = _where(f1)

    with _db() as con:
        base = con.execute(
            f"SELECT COUNT(*) n, COALESCE(SUM({CONTINUO}),0) continuo, "
            f"COALESCE(SUM(CASE WHEN sv.nivel_servicio = 'Sin servicio' THEN 1 ELSE 0 END),0) sin "
            f"{FROM} {where}", params
        ).fetchone()
        n = base["n"]
        pct_cont = _pct(base["continuo"], n)
        pct_sin = _pct(base["sin"], n)

        # Comparacion 2023 -> 2025: se calcula sin el filtro de año para tener ambos extremos.
        f_base = {"tipo_region": filtros.get("tipo_region")}
        where_base, params_base = _where(f_base)
        por_anio = con.execute(
            f"SELECT t.anio, COUNT(*) n, COALESCE(SUM({CONTINUO}),0) continuo "
            f"{FROM} {where_base} GROUP BY t.anio ORDER BY t.anio", params_base
        ).fetchall()
        por_anio_sistema = con.execute(
            f"SELECT s.sistema, t.anio, COUNT(*) n, COALESCE(SUM({CONTINUO}),0) continuo "
            f"{FROM} {where_base} GROUP BY s.sistema, t.anio", params_base
        ).fetchall()

        def pct_anio(anio):
            fila = next((x for x in por_anio if x["anio"] == anio), None)
            return _pct(fila["continuo"], fila["n"]) if fila else None

        caida_global = None
        if pct_anio(2023) is not None and pct_anio(2025) is not None:
            caida_global = round(pct_anio(2025) - pct_anio(2023), 2)

        sistemas = {}
        for fila in por_anio_sistema:
            sistemas.setdefault(fila["sistema"], {})[fila["anio"]] = _pct(
                fila["continuo"], fila["n"]
            )
        caidas = sum(
            1 for valores in sistemas.values()
            if valores.get(2023) is not None and valores.get(2025) is not None
            and (valores[2023] - valores[2025]) >= 50
        )
        total_sistemas = sum(
            1 for valores in sistemas.values()
            if valores.get(2023) is not None and valores.get(2025) is not None
        )

        filas_tiempo = con.execute(
            f"SELECT {tiempo_expr} x, s.sistema, COUNT(*) n, "
            f"COALESCE(SUM({CONTINUO}),0) continuo {FROM} {where} "
            f"GROUP BY {tiempo_expr}, s.sistema "
            f"ORDER BY {tiempo_expr}, s.sistema", params
        ).fetchall()

        filas_geo = con.execute(
            f"SELECT {geo_expr} geo, sv.nivel_servicio, COUNT(*) n {FROM} {where} "
            f"GROUP BY {geo_expr}, sv.nivel_servicio", params
        ).fetchall()

        filas_matriz = con.execute(
            f"SELECT {geo_expr} geo, s.sistema, COUNT(*) n, "
            f"COALESCE(SUM({CONTINUO}),0) continuo {FROM} {where} "
            f"GROUP BY {geo_expr}, s.sistema", params
        ).fetchall()

    # Serie temporal por sistema
    series = {}
    for fila in filas_tiempo:
        series.setdefault(fila["sistema"], []).append({
            "x": str(fila["x"]),
            "pct": _pct(fila["continuo"], fila["n"]),
            "n": fila["n"],
        })

    # Composicion del servicio por unidad geografica
    geo_data = {}
    for fila in filas_geo:
        geo_data.setdefault(fila["geo"], {"total": 0, "servicios": {}})
        geo_data[fila["geo"]]["total"] += fila["n"]
        geo_data[fila["geo"]]["servicios"][fila["nivel_servicio"]] = fila["n"]
    chart_b = []
    for geo, info in geo_data.items():
        total = info["total"]
        chart_b.append({
            "geo": geo,
            "total": total,
            "pct": {servicio: _pct(info["servicios"].get(servicio, 0), total)
                    for servicio in SERVICIOS},
            "n": {servicio: info["servicios"].get(servicio, 0) for servicio in SERVICIOS},
        })
    chart_b.sort(key=lambda x: (-x["total"], x["geo"]))

    # Matriz geografia x sistema
    matriz = {}
    for fila in filas_matriz:
        matriz.setdefault(fila["geo"], {"total": 0, "continuo": 0, "celdas": {}})
        matriz[fila["geo"]]["total"] += fila["n"]
        matriz[fila["geo"]]["continuo"] += fila["continuo"]
        matriz[fila["geo"]]["celdas"][fila["sistema"]] = {
            "n": fila["n"], "pct": _pct(fila["continuo"], fila["n"])
        }
    filas_matriz = []
    for geo, info in matriz.items():
        filas_matriz.append({
            "geo": geo,
            "total": info["total"],
            "pct_total": _pct(info["continuo"], info["total"]),
            "celdas": info["celdas"],
        })
    filas_matriz.sort(key=lambda x: (-x["total"], x["geo"]))

    interpretacion = (
        f"Con los filtros activos ({_filtros_texto(filtros)}), el {pct_cont}% de "
        f"{n:,} registros tiene servicio continuo y el {pct_sin}% aparece como "
        f"'Sin servicio'. En el nivel {geo_label.lower()}, la matriz cruza cada unidad "
        f"con los cuatro sistemas; las celdas muestran el porcentaje de continuidad y "
        f"su denominador. La comparación 2023→2025, calculada sobre la región "
        f"seleccionada, cambia {caida_global:+.2f} puntos porcentuales."
        if caida_global is not None else
        f"Con los filtros activos ({_filtros_texto(filtros)}), el {pct_cont}% de "
        f"{n:,} registros tiene servicio continuo. No hay datos suficientes para "
        f"comparar 2023 y 2025 con estos filtros."
    )

    return {
        "vista": 1,
        "nivel_geo": nivel_geo,
        "nivel_tiempo": nivel_tiempo,
        "etiquetas": {"geo": geo_label, "tiempo": tiempo_label},
        "indicadores": [
            {"etiqueta": "Continuidad del servicio", "valor": pct_cont, "unidad": "%",
             "detalle": f"{base['continuo']:,} de {n:,} registros"},
            {"etiqueta": "Registros sin servicio", "valor": pct_sin, "unidad": "%",
             "detalle": f"{base['sin']:,} de {n:,} registros"},
            {"etiqueta": "Sistemas con caída ≥50 pp", "valor": caidas,
             "unidad": "", "detalle": f"de {total_sistemas} sistemas; cambio global "
                                     f"{caida_global:+.2f} pp (2023→2025)" if caida_global is not None
                                     else f"de {total_sistemas} sistemas"},
        ],
        "chart_a": {"series": series, "titulo_y": "% continuo"},
        "chart_b": {"filas": chart_b},
        "matriz": {"columnas": SISTEMAS, "filas": filas_matriz},
        "interpretacion": interpretacion,
        "denominador": f"Los porcentajes usan los {n:,} registros del filtro actual. "
                       f"La comparación temporal usa todos los años de la región seleccionada.",
    }


def pregunta2(filtros):
    """Prioridades por departamento: riesgo alto y continuidad del servicio."""
    region = filtros.get("tipo_region")
    if region in (None, "", "Todos"):
        region = "Nacional"
    f2 = {"sistema": filtros.get("sistema"),
          "periodo": filtros.get("periodo", "2024-2025"),
          "tipo_region": region}
    where_all, params_all = _where(f2)
    where_valid, params_valid = _where(f2, extra="r.grupo_riesgo <> 'Sin dato'")

    with _db() as con:
        dept = con.execute(
            f"SELECT g.departamento, g.tipo_region, COUNT(*) n, "
            f"SUM(CASE WHEN r.grupo_riesgo = 'Sin dato' THEN 1 ELSE 0 END) sin, "
            f"COALESCE(SUM({ALTO}),0) alto, COALESCE(SUM({CONTINUO}),0) continuo, "
            f"ROUND(AVG(f.cobertura_acueducto_pct),2) cobertura "
            f"{FROM} {where_all} GROUP BY g.departamento, g.tipo_region", params_all
        ).fetchall()
        dept_riesgo = con.execute(
            f"SELECT g.departamento, r.grupo_riesgo, COUNT(*) n, COALESCE(SUM({ALTO}),0) alto "
            f"{FROM} {where_valid} GROUP BY g.departamento, r.grupo_riesgo", params_valid
        ).fetchall()
        dept_servicio = con.execute(
            f"SELECT g.departamento, sv.nivel_servicio, COUNT(*) n, "
            f"SUM(CASE WHEN r.grupo_riesgo = 'Sin dato' THEN 0 ELSE 1 END) validos, "
            f"COALESCE(SUM({ALTO}),0) alto "
            f"{FROM} {where_all} GROUP BY g.departamento, sv.nivel_servicio", params_all
        ).fetchall()

    dept_rows = []
    for fila in dept:
        validos = fila["n"] - fila["sin"]
        dept_rows.append({
            "departamento": fila["departamento"],
            "region": fila["tipo_region"],
            "n": fila["n"],
            "validos": validos,
            "alto": fila["alto"],
            "continuo": fila["continuo"],
            "pct_alto": _pct(fila["alto"], validos),
            "pct_continuo": _pct(fila["continuo"], fila["n"]),
            "cobertura": fila["cobertura"],
        })
    dept_rows.sort(key=lambda x: (-(x["pct_alto"] or 0), x["departamento"]))

    def prioridad(fila):
        alto = fila["pct_alto"] or 0
        cont = fila["pct_continuo"] or 0
        if alto >= 40 and cont < 50:
            return "Prioridad conjunta"
        if alto >= 40:
            return "Prioridad de calidad"
        if cont < 50:
            return "Prioridad de servicio"
        return "Seguimiento"

    for fila in dept_rows:
        fila["prioridad"] = prioridad(fila)

    conjunta = [f for f in dept_rows if f["prioridad"] == "Prioridad conjunta"]
    calidad = [f for f in dept_rows if f["prioridad"] == "Prioridad de calidad"]
    servicio = [f for f in dept_rows if f["prioridad"] == "Prioridad de servicio"]
    seguimiento = [f for f in dept_rows if f["prioridad"] == "Seguimiento"]

    # Composicion del riesgo por departamento (columnas = grupos de riesgo).
    riesgo_data = {}
    for fila in dept_riesgo:
        riesgo_data.setdefault(fila["departamento"], {})[fila["grupo_riesgo"]] = fila["n"]
    chart_a = []
    for fila in dept_rows:
        valores = riesgo_data.get(fila["departamento"], {})
        chart_a.append({
            "departamento": fila["departamento"],
            "region": fila["region"],
            "n": fila["n"],
            "pct_alto": fila["pct_alto"],
            "celdas": {grupo: {"n": valores.get(grupo, 0),
                              "pct": _pct(valores.get(grupo, 0), fila["validos"])}
                      for grupo in RIESGOS},
        })

    # Matriz departamento x nivel de servicio (% alto sobre validos).
    servicio_data = {}
    for fila in dept_servicio:
        servicio_data.setdefault(fila["departamento"], {})[fila["nivel_servicio"]] = {
            "n": fila["n"],
            "validos": fila["validos"],
            "pct": _pct(fila["alto"], fila["validos"]),
        }
    servicios_presentes = [
        servicio for servicio in SERVICIOS
        if any(d.get(servicio, {}).get("n", 0) > 0 for d in servicio_data.values())
    ]
    matriz = []
    for fila in dept_rows:
        valores = servicio_data.get(fila["departamento"], {})
        matriz.append({
            "departamento": fila["departamento"],
            "region": fila["region"],
            "n": fila["n"],
            "pct_alto": fila["pct_alto"],
            "celdas": {servicio: valores.get(servicio) for servicio in servicios_presentes},
        })

    total_validos = sum(f["validos"] for f in dept_rows)
    total_alto = sum(f["alto"] for f in dept_rows)
    total_continuo = sum(f["continuo"] for f in dept_rows)
    total_n = sum(f["n"] for f in dept_rows)
    pct_alto = _pct(total_alto, total_validos)
    pct_continuo = _pct(total_continuo, total_n)

    def rango_cobertura(filas):
        valores = [f["cobertura"] for f in filas if f["cobertura"] is not None]
        if not valores:
            return "s/d"
        return f"{min(valores):.1f}%–{max(valores):.1f}%"

    nombres_conjunta = ", ".join(f["departamento"] for f in conjunta) or "ninguno"
    nombres_servicio = ", ".join(f["departamento"] for f in servicio) or "ninguno"
    interpretacion = (
        f"Con el periodo y los filtros activos, {len(conjunta)} departamentos combinan "
        f"alto riesgo (≥40%) y continuidad menor a 50%: {nombres_conjunta}. "
        f"{len(calidad)} tienen alto riesgo pero continuidad ≥50% (prioridad de calidad) "
        f"y {len(servicio)} tienen bajo riesgo pero baja continuidad (prioridad de servicio): "
        f"{nombres_servicio}. La cobertura media de los departamentos con prioridad conjunta "
        f"es {rango_cobertura(conjunta)} y la de prioridad de calidad es {rango_cobertura(calidad)}; "
        f"la cobertura no separa estos grupos, así que no sirve como criterio único de priorización."
    )

    return {
        "vista": 2,
        "periodo": filtros.get("periodo", "2024-2025"),
        "indicadores": [
            {"etiqueta": "Riesgo alto o inviable", "valor": pct_alto, "unidad": "%",
             "detalle": f"{total_alto:,} de {total_validos:,} registros con IRCA"},
            {"etiqueta": "Continuidad del servicio", "valor": pct_continuo, "unidad": "%",
             "detalle": f"{total_continuo:,} de {total_n:,} registros"},
            {"etiqueta": "Departamentos en prioridad conjunta", "valor": len(conjunta),
             "unidad": "", "detalle": f"de {len(dept_rows)}; {len(calidad)} de calidad, "
                                     f"{len(servicio)} de servicio, {len(seguimiento)} en seguimiento"},
        ],
        "chart_a": {"columnas": RIESGOS, "filas": chart_a},
        "chart_b": dept_rows,
        "matriz": {"columnas": servicios_presentes, "filas": matriz},
        "prioridades": {
            "conjunta": [f["departamento"] for f in conjunta],
            "calidad": [f["departamento"] for f in calidad],
            "servicio": [f["departamento"] for f in servicio],
            "seguimiento": [f["departamento"] for f in seguimiento],
        },
        "interpretacion": interpretacion,
        "denominador": f"Los porcentajes de riesgo usan {total_validos:,} registros con IRCA "
                       f"registrado; la continuidad y la cobertura usan los {total_n:,} "
                       f"registros del periodo y filtros.",
    }


def pregunta3(filtros):
    """Brecha entre cobertura de acueducto y continuidad del servicio."""
    f3 = {"anio": filtros.get("anio"), "tipo_region": filtros.get("tipo_region")}
    where, params = _where(f3)

    with _db() as con:
        base = con.execute(
            f"SELECT COUNT(*) n, ROUND(AVG(f.cobertura_acueducto_pct),2) cobertura, "
            f"COALESCE(SUM({CONTINUO}),0) continuo {FROM} {where}", params
        ).fetchone()
        municipios = con.execute(
            f"SELECT g.municipio, g.tipo_region, COUNT(*) n, "
            f"ROUND(AVG(f.cobertura_acueducto_pct),2) cobertura, "
            f"COALESCE(SUM({CONTINUO}),0) continuo {FROM} {where} "
            f"GROUP BY g.municipio, g.tipo_region", params
        ).fetchall()
        matriz = con.execute(
            f"SELECT g.municipio, g.tipo_region, sv.nivel_servicio, COUNT(*) n, "
            f"ROUND(AVG(f.cobertura_acueducto_pct),2) cobertura {FROM} {where} "
            f"GROUP BY g.municipio, g.tipo_region, sv.nivel_servicio", params
        ).fetchall()

    n = base["n"]
    pct_cont = _pct(base["continuo"], n)
    brecha = round(base["cobertura"] - pct_cont, 2) if base["cobertura"] is not None and pct_cont is not None else None
    muni_rows = []
    for fila in municipios:
        cont = _pct(fila["continuo"], fila["n"])
        muni_rows.append({
            "municipio": fila["municipio"],
            "region": fila["tipo_region"],
            "n": fila["n"],
            "cobertura": fila["cobertura"],
            "continuidad": cont,
            "brecha": round(fila["cobertura"] - cont, 2) if fila["cobertura"] is not None and cont is not None else None,
        })
    muni_rows.sort(key=lambda x: (-(x["brecha"] or -999), x["municipio"]))
    desalineados = sum(1 for fila in muni_rows if (fila["cobertura"] or 0) >= 90 and (fila["continuidad"] or 0) < 50)

    pares = [(fila["cobertura"], fila["continuidad"]) for fila in muni_rows
             if fila["cobertura"] is not None and fila["continuidad"] is not None]
    corr_global = _pearson([x for x, _ in pares], [y for _, y in pares])
    corr_region = {}
    for region in ("Regional", "Nacional"):
        subset = [(fila["cobertura"], fila["continuidad"]) for fila in muni_rows
                  if fila["region"] == region
                  and fila["cobertura"] is not None and fila["continuidad"] is not None]
        corr_region[region] = _pearson([x for x, _ in subset], [y for _, y in subset])

    servicios_data = {}
    for fila in matriz:
        servicios_data.setdefault(fila["municipio"], {})[fila["nivel_servicio"]] = {
            "n": fila["n"], "cobertura": fila["cobertura"]
        }
    filas_matriz = []
    for fila in muni_rows:
        valores = servicios_data.get(fila["municipio"], {})
        filas_matriz.append({
            "municipio": fila["municipio"],
            "region": fila["region"],
            "cobertura": fila["cobertura"],
            "continuidad": fila["continuidad"],
            "celdas": {servicio: valores.get(servicio) for servicio in SERVICIOS},
        })

    if corr_global is not None:
        corr_texto = (f"La correlación cobertura-continuidad entre municipios es r={corr_global}; "
                      f"dentro de Regional es r={corr_region.get('Regional')} y dentro de "
                      f"Nacional es r={corr_region.get('Nacional')}.")
    else:
        corr_texto = "No hay suficientes municipios para calcular la correlación."

    interpretacion = (
        f"Con los filtros activos ({_filtros_texto(filtros)}), la cobertura media es "
        f"{base['cobertura']}% y la continuidad es {pct_cont}%: la brecha es de "
        f"{brecha} puntos porcentuales. {desalineados} municipios tienen cobertura "
        f"≥90% y continuidad <50%. {corr_texto} Una correlación alta entre grupos puede "
        f"desaparecer al mirar dentro de cada región; no implica causalidad."
    )

    return {
        "vista": 3,
        "indicadores": [
            {"etiqueta": "Cobertura media", "valor": base["cobertura"], "unidad": "%",
             "detalle": f"{n:,} registros del filtro"},
            {"etiqueta": "Continuidad del servicio", "valor": pct_cont, "unidad": "%",
             "detalle": f"{base['continuo']:,} de {n:,} registros"},
            {"etiqueta": "Brecha cobertura–continuidad", "valor": brecha, "unidad": "pp",
             "detalle": f"cobertura menos continuidad; {desalineados} municipios en alerta"},
        ],
        "chart_a": {"filas": muni_rows},
        "chart_b": muni_rows[:15],
        "matriz": {"columnas": SERVICIOS, "filas": filas_matriz},
        "correlaciones": {"global": corr_global, **corr_region},
        "interpretacion": interpretacion,
        "denominador": f"La cobertura y la continuidad se calculan sobre {n:,} registros. "
                       f"Los promedios municipales usan el número de registros de cada municipio.",
    }


def pregunta4(filtros):
    """Consumo, almacenamiento y continuidad: recuperacion hidrica vs servicio."""
    f4 = {"tipo_region": filtros.get("tipo_region"),
          "periodo": filtros.get("periodo", "2024-2025")}
    where, params = _where(f4)

    with _db() as con:
        serie = con.execute(
            f"SELECT t.anio, t.anio_trimestre, t.trimestre, COUNT(*) n, "
            f"ROUND(AVG(f.nivel_almacenamiento_pct),2) almacenamiento, "
            f"ROUND(AVG(f.consumo_m3s),2) consumo, "
            f"ROUND(AVG(f.precipitacion_mm),2) precipitacion, "
            f"COALESCE(SUM({CONTINUO}),0) continuo "
            f"{FROM} {where} GROUP BY t.anio, t.anio_trimestre, t.trimestre "
            f"ORDER BY t.anio, t.trimestre", params
        ).fetchall()
        anual = con.execute(
            f"SELECT t.anio, COUNT(*) n, "
            f"ROUND(AVG(f.nivel_almacenamiento_pct),2) almacenamiento, "
            f"ROUND(AVG(f.consumo_m3s),2) consumo, "
            f"ROUND(AVG(f.precipitacion_mm),2) precipitacion, "
            f"COALESCE(SUM({CONTINUO}),0) continuo "
            f"{FROM} {where} GROUP BY t.anio ORDER BY t.anio", params
        ).fetchall()
        matriz = con.execute(
            f"SELECT t.anio, g.tipo_region, COUNT(*) n, "
            f"ROUND(AVG(f.nivel_almacenamiento_pct),2) almacenamiento, "
            f"ROUND(AVG(f.consumo_m3s),2) consumo, "
            f"COALESCE(SUM({CONTINUO}),0) continuo "
            f"{FROM} {where} GROUP BY t.anio, g.tipo_region "
            f"ORDER BY t.anio, g.tipo_region", params
        ).fetchall()

    serie_rows = []
    for fila in serie:
        serie_rows.append({
            "anio": fila["anio"],
            "trimestre": fila["anio_trimestre"],
            "n": fila["n"],
            "almacenamiento": fila["almacenamiento"],
            "consumo": fila["consumo"],
            "precipitacion": fila["precipitacion"],
            "continuidad": _pct(fila["continuo"], fila["n"]),
        })

    anual_rows = []
    for fila in anual:
        anual_rows.append({
            "anio": fila["anio"],
            "n": fila["n"],
            "almacenamiento": fila["almacenamiento"],
            "consumo": fila["consumo"],
            "precipitacion": fila["precipitacion"],
            "continuidad": _pct(fila["continuo"], fila["n"]),
        })

    matriz_data = {}
    for fila in matriz:
        matriz_data.setdefault(fila["anio"], {})[fila["tipo_region"]] = {
            "n": fila["n"],
            "almacenamiento": fila["almacenamiento"],
            "consumo": fila["consumo"],
            "continuidad": _pct(fila["continuo"], fila["n"]),
        }
    regiones = [r for r in ("Regional", "Nacional")
                if any(r in fila for fila in matriz_data.values())]
    filas_matriz = []
    for anio in sorted(matriz_data):
        filas_matriz.append({
            "anio": anio,
            "celdas": {region: matriz_data[anio].get(region) for region in regiones},
        })

    n_total = sum(f["n"] for f in serie_rows)
    consumo = (round(sum(f["consumo"] * f["n"] for f in serie_rows) / n_total, 2)
               if n_total else None)
    almacenamiento = (round(sum(f["almacenamiento"] * f["n"] for f in serie_rows) / n_total, 2)
                       if n_total else None)
    continuidad = (round(sum(f["continuidad"] * f["n"] for f in serie_rows) / n_total, 2)
                   if n_total else None)

    if len(anual_rows) >= 2:
        primero, ultimo = anual_rows[0], anual_rows[-1]
        interpretacion = (
            f"Entre {primero['anio']} y {ultimo['anio']}, el consumo promedio pasó de "
            f"{primero['consumo']} a {ultimo['consumo']} m³/s; el almacenamiento pasó de "
            f"{primero['almacenamiento']}% a {ultimo['almacenamiento']}% y la continuidad "
            f"de {primero['continuidad']}% a {ultimo['continuidad']}%. "
            + ("El consumo y el almacenamiento se recuperaron, pero la continuidad no: "
               "la restricción del servicio no siguió la recuperación hídrica."
               if (ultimo["consumo"] > primero["consumo"] * 1.03
                   and ultimo["almacenamiento"] >= primero["almacenamiento"] + 3
                   and ultimo["continuidad"] <= primero["continuidad"])
               else "Los cambios de consumo y almacenamiento fueron pequeños; no hay "
                    "evidencia suficiente para afirmar una recuperación hídrica en este corte.")
        )
    elif anual_rows:
        anio = anual_rows[0]
        interpretacion = (
            f"En {anio['anio']}, el consumo promedio es {anio['consumo']} m³/s, el "
            f"almacenamiento {anio['almacenamiento']}% y la continuidad {anio['continuidad']}%. "
            f"Se necesitan al menos dos años para comparar la recuperación."
        )
    else:
        interpretacion = "No hay registros para los filtros seleccionados."

    return {
        "vista": 4,
        "periodo": filtros.get("periodo", "2024-2025"),
        "indicadores": [
            {"etiqueta": "Consumo promedio", "valor": consumo, "unidad": "m³/s",
             "detalle": f"{n_total:,} registros del periodo"},
            {"etiqueta": "Almacenamiento promedio", "valor": almacenamiento, "unidad": "%",
             "detalle": "nivel del embalse en los registros filtrados"},
            {"etiqueta": "Continuidad del servicio", "valor": continuidad, "unidad": "%",
             "detalle": f"porcentaje de registros con servicio continuo"},
        ],
        "chart_a": {"filas": serie_rows},
        "chart_b": serie_rows,
        "matriz": {"columnas": regiones, "filas": filas_matriz},
        "anual": anual_rows,
        "interpretacion": interpretacion,
        "denominador": f"Los promedios usan {n_total:,} registros del periodo y la región "
                       f"seleccionados. La continuidad es un conteo de registros, no un promedio "
                       f"de porcentajes.",
    }
