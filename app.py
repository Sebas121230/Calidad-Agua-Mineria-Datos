import csv
import os
from datetime import date

from flask import Flask, render_template

# Inicializar la aplicacion
app = Flask(__name__)

# Carpeta donde vive app.py (para leer los CSV sin importar desde donde se ejecute)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def leer_csv(nombre):
    """Lee un CSV del proyecto y lo devuelve como lista de diccionarios.
    Si el archivo no existe todavia, devuelve una lista vacia en vez de romper."""
    ruta = os.path.join(BASE_DIR, nombre)
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------- Pagina de inicio ----------
@app.route("/")
def inicio():
    return render_template("inicio.html")


# ---------- Etapa 1: los 8 submenus ----------
@app.route("/etapa1/problema")
def problema():
    return render_template("etapa1/problema.html")


@app.route("/etapa1/preguntas")
def preguntas():
    return render_template("etapa1/preguntas.html")


@app.route("/etapa1/necesidades")
def necesidades():
    return render_template("etapa1/necesidades.html")


@app.route("/etapa1/fuentes")
def fuentes():
    return render_template("etapa1/fuentes.html")


@app.route("/etapa1/limitaciones")
def limitaciones():
    return render_template("etapa1/limitaciones.html")


# ---------- Etapa 2 ----------
@app.route("/etapa2/proposito")
def proposito():
    """Puntos 1 y 2: proposito del conjunto de datos y requisitos de calidad.

    El proposito describe que pregunta responde el dataset y con que fuentes.
    Los requisitos RC01-RC06 fijan los criterios verificables que despues se
    eval uan en las dimensiones.
    """
    requisitos = [
        {"id": "RC01", "dimension": "Completitud", "umbral": ">= 92%",
         "requerimiento": "Al menos el 92% de las celdas deben contener un valor util. "
                          "Las variables criticas (irca, precipitacion_mm) no deben superar el 8% de faltantes.",
         "justificacion": "El IRCA es la variable objetivo del analisis; sin el, el registro no puede "
                          "clasificarse ni compararse. La precipitacion se requiere para correlacionarla "
                          "con el nivel de los embalses."},
        {"id": "RC02", "dimension": "Unicidad", "umbral": ">= 95% de registros unicos",
         "requerimiento": "Al menos el 95% de los registros deben ser unicos (maximo 5% de filas completas "
                          "duplicadas). La llave compuesta (fecha + municipio + sistema_abastecimiento) "
                          "debe ser en lo posible unica.",
         "justificacion": "Los duplicados inflan los conteos por municipio y fecha y sesgan todo promedio "
                          "sobre el conjunto. Se admite un 5% de tolerancia por re-muestreos esperables."},
        {"id": "RC03", "dimension": "Validez", "umbral": ">= 95% de valores dentro del dominio",
         "requerimiento": "Al menos el 95% de los valores numericos deben estar dentro de su dominio: "
                          "irca en [0, 100], precipitacion_mm >= 0, temperatura_c en [-10, 50], "
                          "cobertura_acueducto_pct en [0, 100], nivel_almacenamiento_pct en [0, 100].",
         "justificacion": "Con una tolerancia del 5% se capturan todas las violaciones dominantes reales "
                          "sin penalizar desviaciones puntuales de la escala normativa."},
        {"id": "RC04", "dimension": "Consistencia", "umbral": ">= 92% registros consistentes",
         "requerimiento": "Al menos el 92% de los registros deben cumplir todas las reglas de formato y "
                          "coherencia interna: fecha en formato ISO 8601 (YYYY-MM-DD), municipios en "
                          "Title Case sin espacios sobrantes ni simbolos, y clasificacion_riesgo "
                          "coherente con el IRCA.",
         "justificacion": "Se adopta una tolerancia del 8% por registros heredados de fuentes con "
                          "formatos dispares; el objetivo es que la llave temporal/geografica siga "
                          "funcionando en las agrupaciones."},
        {"id": "RC05", "dimension": "Exactitud", "umbral": ">= 92% registros sin atipicos ni errores de categoria",
         "requerimiento": "Al menos el 92% de los registros no deben presentar atipicos significativos "
                          "(criterio de Tukey) ni categorias mal escritas. 88.76% es valor real observado; "
                          "quedaria marcado como no conforme hasta corregir el error ortografico "
                          "'Inviabile' y verificar los atipicos del IRCA.",
         "justificacion": "Requiere el nivel mas alto de confianza del analisis: los atipicos de IRCA y "
                          "las categorias mal escritas distorsionan agregaciones y el cruce con las "
                          "fuentes oficiales."},
        {"id": "RC06", "dimension": "Actualidad", "umbral": "datos de los ultimos 5 años",
         "requerimiento": "El dataset debe contener datos dentro de una ventana de vigencia de 60 meses "
                          "(5 años) y su fecha maxima no debe ser anterior a 5 años respecto a la fecha "
                          "de analisis.",
         "justificacion": "El proyecto analiza el periodo 2019-2025 y la decision de racionamiento se "
                          "toma sobre la serie historica completa; un horizonte de 5 años conserva esa "
                          "perspectiva sin exigir frescura diaria."},
    ]
    proposito_texto = {
        "nombre_archivo": "dataset_calidad_agua.csv",
        "descripcion_corta": "Conjunto de datos que integra informacion sobre la disponibilidad, calidad y "
                             "continuidad del servicio de agua potable en Bogota D.C. y Colombia durante el "
                             "periodo 2019-2025, incluyendo el racionamiento extraordinario de 2024-2025.",
        "descripcion_detallada": "Integra 9 fuentes documentadas (IDEAM, EAAB IRCA, EAAB boletines, IDECA, "
                                 "SIVICAP, HDX, OMS/UNICEF JMP, UNESCO WWDR, WRI Aqueduct) en un solo CSV "
                                 "mediante llaves temporales (fecha, anio, mes, periodo) y geograficas "
                                 "(municipio, departamento, latitud, longitud), cubriendo tres niveles de "
                                 "analisis: global (20 paises), nacional (municipios colombianos) y regional "
                                 "(Bogota y Sabana). La unidad de analisis principal es dia-municipio.",
        "proposito_principal": "Analizar la disponibilidad y continuidad del servicio de agua potable en "
                               "Bogota D.C., identificar patrones de racionamiento y evaluar la calidad del "
                               "agua en los municipios de la Sabana, con el fin de construir modelos de "
                               "mineria de datos que permitan anticipar periodos de riesgo de desabastecimiento.",
        "preguntas_investigacion": [
            "Como ha variado el nivel de almacenamiento del sistema Chingaza durante 2019-2025?",
            "Cual es la relacion entre afluencias, precipitacion y nivel de almacenamiento del embalse?",
            "Como afecta el nivel de almacenamiento a la decision de racionamiento?",
            "Cuales municipios de la Sabana presentan los mayores riesgos en calidad del agua (IRCA)?",
            "Que diferencias existen en la cobertura del agua entre los municipios del area de influencia?",
        ],
        "fuentes_integradas": [
            "IDEAM DHIME (series hidrometeorologicas)",
            "EAAB IRCA (calidad del agua)",
            "EAAB boletines (niveles de embalse)",
            "IDECA / Datos Abiertos Bogota (coordenadas)",
            "SIVICAP (IRCA nacional)",
            "HDX (indicadores de desarrollo)",
            "OMS/UNICEF JMP (acceso a agua segura)",
            "UNESCO WWDR (informes mundiales del agua)",
            "WRI Aqueduct (riesgo hidrico)",
        ],
        "periodo_cubierto": "2019-01-01 a 2025-12-31",
        "script_generacion": "generar_dataset.py",
    }
    return render_template("etapa2/proposito.html", requisitos=requisitos, p=proposito_texto)


@app.route("/etapa2/perfilamiento")
def perfilamiento():
    """Punto 3: perfilamiento del conjunto de datos.

    Calcula la estructura, la distribucion por nivel, los nulos por variable,
    los duplicados y las estadisticas descriptivas directamente sobre
    dataset_calidad_agua.csv con la libreria estandar de Python, para que los
    numeros siempre coincidan con el archivo.
    """
    registros = leer_csv("dataset_calidad_agua.csv")
    if not registros:
        return render_template("etapa2/perfilamiento.html", datos={})

    variables = list(registros[0].keys())
    total_celdas = len(registros) * len(variables)

    # Nulos por variable: vacios + marcadores de ausencia ('N/A', 'null', '-')
    marcadores = {"", "N/A", "null", "-"}
    nulos_por_variable = {}
    for var in variables:
        nulos_por_variable[var] = sum(
            1 for r in registros if (r.get(var) or "").strip() in marcadores
        )
    total_nulos = sum(nulos_por_variable.values())

    # Duplicados exactos (filas identicas)
    vistos = {}
    duplicados_extra = 0
    for r in registros:
        llave = tuple(r[var] for var in variables)
        vistos[llave] = vistos.get(llave, 0) + 1
    duplicados_extra = sum(c - 1 for c in vistos.values() if c > 1)
    grupos_dup = sum(1 for c in vistos.values() if c > 1)
    pct_dup = round(grupos_dup / len(registros) * 100, 2)

    # Distribucion por nivel de analisis
    from collections import Counter
    dist = Counter(r["tipo_region"] for r in registros)
    distribucion = [
        {"nivel": n, "registros": c, "porcentaje": round(c / len(registros) * 100, 2)}
        for n, c in dist.most_common()
    ]

    # Estadisticas de las variables numericas
    import statistics
    numericas = ["nivel_almacenamiento_pct", "afluencias_m3s", "precipitacion_mm",
                 "temperatura_c", "consumo_m3s", "irca", "cobertura_acueducto_pct"]

    def rango_tukey(vals):
        # vals: lista de numeros; cuartiles inclusivos de la libreria estandar.
        q1, _, q3 = statistics.quantiles(vals, n=4, method="inclusive")
        iqr = q3 - q1
        return round(q1 - 1.5 * iqr, 2), round(q3 + 1.5 * iqr, 2)

    estadisticas = []
    atipicos = []
    for var in numericas:
        vals = []
        for r in registros:
            v = (r.get(var) or "").strip()
            try:
                vals.append(float(v))
            except ValueError:
                continue
        if not vals:
            continue
        estadisticas.append({
            "variable": var,
            "count": len(vals),
            "media": round(sum(vals) / len(vals), 2),
            "desv": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0,
            "min": min(vals),
            "max": max(vals),
        })
        if len(vals) >= 5:
            li, ls = rango_tukey(vals)
            fuera = [v for v in vals if v < li or v > ls]
            atipicos.append({
                "variable": var,
                "li": li,
                "ls": ls,
                "conteo": len(fuera),
                "porcentaje": round(len(fuera) / len(vals) * 100, 2),
                "min": round(min(vals), 2),
                "max": round(max(vals), 2),
            })

    # Tipo de dato inferido del contenido real y valores unicos por variable.
    # El CSV se lee como texto, por lo que el tipo se deduce de los valores
    # (fecha ISO, entero, decimal o texto) sin conversiones previas.
    import re
    patron_fecha = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    marcadores = {"", "N/A", "null", "-"}

    def es_entero(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def es_decimal(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def inferir_tipo(var):
        valores = [r[var].strip() for r in registros
                   if r[var].strip() not in marcadores]
        if not valores:
            return "solo nulos"
        iso = patron_fecha.match
        if all(iso(v) for v in valores):
            return "fecha (ISO YYYY-MM-DD)"
        # La mayoria puede ser ISO con una minoria en otro formato (ej. P09).
        if sum(1 for v in valores if iso(v)) >= len(valores) * 0.95:
            return "fecha (ISO mayoritario; hay formatos mixtos)"
        if all(es_entero(v) for v in valores):
            return "entero"
        if all(es_decimal(v) for v in valores):
            return "decimal"
        return "texto (categorico)"

    tipos = []
    unicos_por_variable = {}
    for var in variables:
        tipos.append({"variable": var, "tipo": inferir_tipo(var)})
        unicos_por_variable[var] = len(
            {r[var].strip() for r in registros if r[var].strip() not in marcadores}
        )

    datos = {
        "registros": len(registros),
        "variables": variables,
        "n_variables": len(variables),
        "total_celdas": total_celdas,
        "nulos_por_variable": nulos_por_variable,
        "total_nulos": total_nulos,
        "pct_nulos": round(total_nulos / total_celdas * 100, 2),
        "completitud": round((total_celdas - total_nulos) / total_celdas * 100, 2),
        "duplicados_extra": duplicados_extra,
        "grupos_dup": grupos_dup,
        "pct_duplicados": pct_dup,
        "distribucion": distribucion,
        "estadisticas": estadisticas,
        "tipos": tipos,
        "unicos_por_variable": unicos_por_variable,
        "atipicos": atipicos,
    }
    return render_template("etapa2/perfilamiento.html", datos=datos)


@app.route("/etapa2/dimensiones")
def dimensiones():
    """Puntos 4 y 5: las seis dimensiones de calidad con su metrica aplicada.

    Lee metricas_calidad.csv (definicion, formula y calculo de cada metrica) y
    verifica cada resultado contra el requisito RC01-RC06 correspondiente.
    """
    metricas = leer_csv("metricas_calidad.csv")
    import re
    # Regla de cumplimiento de cada dimension frente a su requisito.
    # Todas las dimensiones porcentuales se comparan contra el umbral RC:
    # Completitud, Consistencia, Exactitud en 92%; Unicidad y Validez en 95%.
    # Actualidad se evalua contra la ventana de vigencia de 5 años (60 meses):
    # el desfase de la ultima observacion no puede superar 1825 dias.
    cumplimiento = {}
    for m in metricas:
        dim = m["dimension"]
        num = re.search(r"[-+]?\d+(?:\.\d+)?", m["resultado"])
        valor = float(num.group()) if num else 0.0
        if dim == "Completitud":
            ok = valor >= 92.0
        elif dim == "Unicidad":
            ok = valor >= 95.0
        elif dim == "Validez":
            ok = valor >= 95.0
        elif dim == "Consistencia":
            ok = valor >= 92.0
        elif dim == "Exactitud":
            ok = valor >= 92.0
        elif dim == "Actualidad":
            desfase = re.search(r"desfase de (\d+) dias", m["resultado"])
            ok = desfase and int(desfase.group(1)) <= 1825
        else:
            ok = False
        cumplimiento[dim] = ok
    return render_template(
        "etapa2/dimensiones.html",
        metricas=metricas,
        cumplimiento=cumplimiento,
    )


@app.route("/etapa2/inventario")
def inventario():
    """Inventario de problemas de calidad.

    Lee los resultados que dejo el script inventario_calidad.py y los pinta en
    la tabla. Asi la pagina siempre muestra los numeros reales del dataset: si
    el dataset cambia, se vuelve a correr el script y la pagina se actualiza
    sola, sin tocar el HTML.
    """
    problemas = leer_csv("inventario_problemas.csv")
    metricas = leer_csv("metricas_calidad.csv")
    verificaciones = leer_csv("verificaciones_sin_hallazgo.csv")

    # Conteo de hallazgos por dimension, para la grafica de distribucion
    conteo = {}
    for p in problemas:
        conteo[p["dimension_calidad"]] = conteo.get(p["dimension_calidad"], 0) + 1
    por_dimension = sorted(conteo.items(), key=lambda x: -x[1])

    # Diccionario dimension -> resultado, para citar las cifras en la sintesis
    # sin escribirlas a mano (asi nunca se desfasan del script).
    met = {m["dimension"]: m["resultado"].split("  ")[0] for m in metricas}
    desfase = ""
    for m in metricas:
        if m["dimension"] == "Actualidad" and "desfase de" in m["resultado"]:
            desfase = m["resultado"].split("desfase de ")[1].split(" dias")[0]

    return render_template(
        "etapa2/inventario.html",
        problemas=problemas,
        metricas=metricas,
        met=met,
        desfase_dias=desfase,
        verificaciones=verificaciones,
        por_dimension=por_dimension,
        max_dim=max(conteo.values()) if conteo else 1,
        total=len(problemas),
        altos=sum(1 for p in problemas if p["nivel_impacto"] == "Alto"),
        medios=sum(1 for p in problemas if p["nivel_impacto"] == "Medio"),
        bajos=sum(1 for p in problemas if p["nivel_impacto"] == "Bajo"),
        n_registros="12.989",
        n_variables=20,
        fecha_analisis=date.today().strftime("%d de %B de %Y"),
    )


@app.route("/etapa2/causas")
def causas():
    """Analisis de las causas de los problemas detectados.

    Lee analisis_causas.csv y resumen_causas.csv, generados por el script
    analisis_causas.py a partir del inventario del punto 6.
    """
    causas = leer_csv("analisis_causas.csv")
    resumen = leer_csv("resumen_causas.csv")
    raices = [int(c["problemas_como_causa_raiz"]) for c in resumen] or [1]

    return render_template(
        "etapa2/causas.html",
        causas=causas,
        resumen=resumen,
        total=len(causas),
        max_raiz=max(raices),
    )


@app.route("/etapa2/integracion")
def integracion():
    """Punto 6: integracion y homologacion de los datos.

    Documenta como se unificaron las 9 fuentes de la Etapa 1: las diferencias
    de formato/granularidad/nomenclatura encontradas y la regla de
    homologacion aplicada por variable. Lee integracion_diferencias.csv e
    integracion_homologacion.csv, generados por
    generar_integracion_tratamiento.py.
    """
    diferencias = leer_csv("integracion_diferencias.csv")
    homologacion = leer_csv("integracion_homologacion.csv")
    problemas = leer_csv("inventario_problemas.csv")

    return render_template(
        "etapa2/integracion.html",
        diferencias=diferencias,
        homologacion=homologacion,
        n_registros="12.989",
    )


@app.route("/etapa2/tratamiento")
def tratamiento():
    """Punto 7: plan de tratamiento (solo planeacion, no se ejecuta el ETL).

    Para cada problema del inventario (punto 4) se declara la accion que se
    aplicaria en una etapa posterior. No se corre ningun script de limpieza
    ni se muestra el dataset resultante. Lee plan_tratamiento.csv, generado
    por generar_integracion_tratamiento.py.
    """
    tratamiento = leer_csv("plan_tratamiento.csv")
    problemas = leer_csv("inventario_problemas.csv")

    return render_template(
        "etapa2/tratamiento.html",
        tratamiento=tratamiento,
        total_problemas=len(problemas),
    )


# Ejecutar el servidor en modo desarrollo
if __name__ == "__main__":
    app.run(debug=True)
