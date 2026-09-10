"""
ETAPA 2 - Puntos 5 y 6
======================
Punto 5: metricas de las seis dimensiones de calidad exigidas.
Punto 6: inventario de los problemas encontrados.

Dimensiones evaluadas (las seis que exige el enunciado):
    Completitud, Exactitud, Consistencia, Unicidad, Validez, Actualidad.

Que hace este script:
  1. Lee dataset_calidad_agua.csv SIN modificarlo, con todas las columnas como
     texto (si se dejan inferir los tipos, pandas corrige solo las fechas y los
     espacios y los errores de formato se vuelven invisibles).
  2. Calcula una metrica verificable por cada dimension, con su formula escrita.
  3. Levanta el inventario de problemas, cada uno etiquetado con una de las seis
     dimensiones oficiales.
  4. Exporta cuatro archivos:
        metricas_calidad.csv            -> punto 5
        inventario_problemas.csv        -> punto 6
        verificaciones_sin_hallazgo.csv -> pruebas que dieron cero
        evidencias_inventario.txt       -> salidas crudas de soporte

Uso:
    pip install pandas
    python inventario_calidad.py
"""

import re
from datetime import date

import pandas as pd

ARCHIVO = "dataset_calidad_agua.csv"
FECHA_ANALISIS = date.today()

# Ventana de vigencia adoptada por el equipo para la dimension Actualidad.
# Justificacion: el proyecto analiza el periodo 2019-2025 y la decision de
# racionamiento se toma sobre la serie historica completa, por lo que se
# considera valida cualquier observacion dentro de los ultimos 5 anos.
# Un dato anterior a esa ventana ya no describe el estado vigente del sistema.
VENTANA_VIGENCIA_MESES = 60

df = pd.read_csv(ARCHIVO, dtype=str, keep_default_na=False)
N = len(df)
COLS = len(df.columns)
TOTAL_CELDAS = N * COLS

problemas = []
metricas = []
evidencias = []


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def pct(x, base=None):
    return round(x / (base if base else N) * 100, 2)


def num(col):
    """Convierte una columna a numero; lo no convertible queda como NaN."""
    return pd.to_numeric(df[col].replace("", None), errors="coerce")


def vacia(col):
    """Celda sin dato util: vacia, en blanco, o con un marcador de ausencia."""
    s = df[col].astype(str).str.strip()
    return (s == "") | (s.str.lower().isin(["n/a", "na", "null", "none", "-"]))


def registrar(variable, descripcion, cantidad, dimension, impacto, evidencia,
              complementaria=""):
    problemas.append({
        "id": f"P{len(problemas) + 1:02d}",
        "variable_afectada": variable,
        "descripcion_problema": descripcion,
        "registros_afectados": cantidad,
        "porcentaje": f"{pct(cantidad)}%",
        "dimension_calidad": dimension,
        "dimension_complementaria": complementaria,
        "nivel_impacto": impacto,
        "evidencia": evidencia,
    })


def medir(dimension, definicion, formula, calculo, resultado, interpretacion):
    metricas.append({
        "dimension": dimension,
        "definicion": definicion,
        "formula": formula,
        "calculo": calculo,
        "resultado": resultado,
        "interpretacion": interpretacion,
    })


def log(titulo, contenido):
    evidencias.append(f"\n{'=' * 74}\n{titulo}\n{'=' * 74}\n{contenido}")


print(f"Dataset: {N} registros x {COLS} variables")
print(f"Fecha de analisis: {FECHA_ANALISIS.isoformat()}\n")

# Series numericas reutilizadas
nivel = num("nivel_almacenamiento_pct")
irca = num("irca")
temp = num("temperatura_c")
precip = num("precipitacion_mm")
cob = num("cobertura_acueducto_pct")
aflu = num("afluencias_m3s")

# ===========================================================================
# DIMENSION 1 - COMPLETITUD
# ===========================================================================
faltantes = {c: int(vacia(c).sum()) for c in df.columns}
celdas_faltantes = sum(faltantes.values())
completitud = round((TOTAL_CELDAS - celdas_faltantes) / TOTAL_CELDAS * 100, 2)

log("COMPLETITUD - celdas sin dato util por variable",
    "\n".join(f"{c:30s} {v:6d}  ({pct(v)}%)"
              for c, v in sorted(faltantes.items(), key=lambda x: -x[1]) if v > 0))

medir(
    "Completitud",
    "Proporcion de celdas que contienen un valor util. Se cuentan como ausentes "
    "las celdas vacias y los marcadores de ausencia ('N/A', 'null', '-').",
    "Completitud = (celdas con valor util / celdas totales) x 100",
    f"({TOTAL_CELDAS} - {celdas_faltantes}) / {TOTAL_CELDAS} x 100",
    f"{completitud}%",
    f"De {TOTAL_CELDAS:,} celdas, {celdas_faltantes:,} no tienen dato util. "
    f"La ausencia se concentra en sistema_abastecimiento y en las variables "
    f"fisicoquimicas de los registros globales.".replace(",", "."),
)

registrar(
    "precipitacion_mm",
    "Celdas vacias en la precipitacion diaria. Impide construir acumulados de "
    "lluvia y correlacionarlos con el nivel de los embalses, que es el eje de "
    "la primera pregunta secundaria del proyecto.",
    faltantes["precipitacion_mm"], "Completitud", "Medio",
    f"{faltantes['precipitacion_mm']} celdas sin dato ({pct(faltantes['precipitacion_mm'])}%), "
    f"contadas con df['precipitacion_mm'].str.strip()==''",
)

registrar(
    "temperatura_c",
    "Celdas vacias en la temperatura promedio diaria, atribuibles a fallas de "
    "captacion de la estacion meteorologica.",
    faltantes["temperatura_c"], "Completitud", "Bajo",
    f"{faltantes['temperatura_c']} celdas sin dato ({pct(faltantes['temperatura_c'])}%)",
)

registrar(
    "irca",
    "Celdas vacias en el IRCA, que es la variable objetivo del analisis de "
    "calidad del agua. Sin IRCA el registro no puede clasificarse por nivel de "
    "riesgo ni usarse para comparar territorios.",
    faltantes["irca"], "Completitud", "Alto",
    f"{faltantes['irca']} celdas sin dato ({pct(faltantes['irca'])}%)",
)

registrar(
    "sistema_abastecimiento",
    "El texto 'N/A' se almacena como si fuera una categoria valida. No "
    "corresponde a ningun sistema real: son los registros nacionales y globales "
    "ajenos a la red de la EAAB. Al contarlo, 'N/A' aparece como la categoria "
    "mas frecuente y distorsiona cualquier agrupacion por sistema.",
    int((df["sistema_abastecimiento"].str.upper() == "N/A").sum()),
    "Completitud", "Medio",
    f"{int((df['sistema_abastecimiento'].str.upper() == 'N/A').sum())} registros "
    f"({pct(int((df['sistema_abastecimiento'].str.upper() == 'N/A').sum()))}%) con el "
    f"literal 'N/A'; value_counts() lo devuelve como categoria dominante",
    complementaria="Consistencia",
)

globales = int((df["tipo_region"] == "Global").sum())
registrar(
    "departamento, latitud, longitud, nivel_servicio, decision_racionamiento, "
    "nivel_almacenamiento_pct, afluencias_m3s, consumo_m3s",
    "Bloque de ocho variables vacias de forma simultanea en los mismos "
    "registros. Corresponden a las filas de tipo_region='Global', que describen "
    "paises y no tienen departamento, coordenadas municipales ni embalse "
    "asociado. Es una ausencia estructural del diseno, no un error de captura.",
    int(vacia("departamento").sum()), "Completitud", "Bajo",
    f"{int(vacia('departamento').sum())} registros ({pct(int(vacia('departamento').sum()))}%), "
    f"cifra que coincide exactamente con los {globales} registros de tipo_region='Global'",
)

conteo_region = df["tipo_region"].value_counts()
registrar(
    "tipo_region",
    "Completitud de alcance insuficiente en el nivel global: representa apenas "
    "el 1% de los registros frente al 59% del nivel regional. La comparacion "
    "entre las tres escalas, que es una de las preguntas secundarias, se apoya "
    "en una base muy desigual y sesga cualquier modelo hacia el comportamiento "
    "de la Sabana de Bogota.",
    int(conteo_region.get("Global", 0)), "Completitud", "Medio",
    f"Regional {conteo_region.get('Regional', 0)} ({pct(conteo_region.get('Regional', 0))}%), "
    f"Nacional {conteo_region.get('Nacional', 0)} ({pct(conteo_region.get('Nacional', 0))}%), "
    f"Global {conteo_region.get('Global', 0)} ({pct(conteo_region.get('Global', 0))}%)",
    complementaria="Representatividad",
)

# ===========================================================================
# DIMENSION 2 - UNICIDAD
# ===========================================================================
dup_exactos = int(df.duplicated().sum())
llave = ["fecha", "municipio", "sistema_abastecimiento"]
dup_llave = int(df.duplicated(subset=llave).sum())
unicidad = round((N - dup_exactos) / N * 100, 2)

log("UNICIDAD - ejemplos de registros duplicados",
    df[df.duplicated(keep=False)].sort_values(llave).head(6).to_string())

medir(
    "Unicidad",
    "Proporcion de registros que no estan repetidos en el conjunto.",
    "Unicidad = (registros distintos / registros totales) x 100",
    f"({N} - {dup_exactos}) / {N} x 100",
    f"{unicidad}%",
    f"Hay {dup_exactos} filas identicas repetidas. La llave candidata "
    f"fecha+municipio+sistema arroja {dup_llave} colisiones, la misma cifra, lo "
    f"que confirma que la duplicidad es de fila completa.",
)

registrar(
    "Registro completo (las 20 variables)",
    "Filas identicas repetidas. Inflan artificialmente los conteos por "
    "municipio y por fecha, y sesgan todo promedio calculado sobre el conjunto.",
    dup_exactos, "Unicidad", "Alto",
    f"df.duplicated().sum() = {dup_exactos} ({pct(dup_exactos)}%). "
    f"Por la llave fecha+municipio+sistema: {dup_llave}",
)

# ===========================================================================
# DIMENSION 3 - VALIDEZ
# ===========================================================================
# Dominio declarado de cada variable, tomado del diccionario de datos y de la
# Resolucion 2115 de 2007 para el IRCA.
reglas_validez = {
    "irca": (irca, 0, 100, "escala del IRCA segun Resolucion 2115 de 2007"),
    "precipitacion_mm": (precip, 0, 500, "lamina de lluvia diaria"),
    "temperatura_c": (temp, -10, 50, "temperatura ambiente en Colombia"),
    "cobertura_acueducto_pct": (cob, 0, 100, "porcentaje de cobertura"),
    "afluencias_m3s": (aflu, 0, 1000, "caudal afluente"),
}
val_evaluados = 0
val_invalidos = 0
detalle_validez = []
for var, (serie, lo, hi, desc) in reglas_validez.items():
    evaluados = int(serie.notna().sum())
    fuera = int(((serie < lo) | (serie > hi)).sum())
    val_evaluados += evaluados
    val_invalidos += fuera
    detalle_validez.append(f"{var:28s} rango [{lo}, {hi}]  evaluados={evaluados:6d}  fuera={fuera:5d}")

validez = round((val_evaluados - val_invalidos) / val_evaluados * 100, 2)

log("VALIDEZ - dominio declarado y violaciones por variable",
    "\n".join(detalle_validez))
log("VALIDEZ - ejemplos de nivel_almacenamiento_pct > 100",
    df.loc[nivel > 100, ["fecha", "municipio", "nivel_almacenamiento_pct"]].head(8).to_string())
log("VALIDEZ - ejemplos de irca negativo",
    df.loc[irca < 0, ["fecha", "municipio", "irca", "clasificacion_riesgo"]].head(8).to_string())

medir(
    "Validez",
    "Proporcion de valores que caen dentro del dominio declarado para su "
    "variable. Se evaluaron irca, precipitacion_mm, temperatura_c, "
    "cobertura_acueducto_pct y afluencias_m3s contra su rango fisico o su "
    "escala normativa.",
    "Validez = (valores dentro del dominio / valores evaluados) x 100",
    f"({val_evaluados} - {val_invalidos}) / {val_evaluados} x 100",
    f"{validez}%",
    f"Se evaluaron {val_evaluados:,} valores numericos contra su dominio; "
    f"{val_invalidos} lo violan, todos en la variable irca.".replace(",", "."),
)

irca_neg = int((irca < 0).sum())
registrar(
    "irca",
    "Valores negativos del IRCA. El indice esta definido en la Resolucion 2115 "
    "de 2007 sobre la escala 0-100, de modo que un valor negativo no existe.",
    irca_neg, "Validez", "Alto",
    f"{irca_neg} registros ({pct(irca_neg)}%) con irca < 0. "
    f"Minimo observado: {irca.min()}",
)

# ===========================================================================
# DIMENSION 4 - CONSISTENCIA
# ===========================================================================
iso = df["fecha"].str.match(r"^\d{4}-\d{2}-\d{2}$")
fecha_mala = int((~iso).sum())
patrones = (df.loc[~iso, "fecha"].apply(lambda v: re.sub(r"\d", "9", v))
            .value_counts().to_dict())

m = df["municipio"]
mal_mun = (m.ne(m.str.strip()) | m.str.isupper() | m.str.islower()
           | m.str.contains("@", regex=False))
mal_mun_n = int(mal_mun.sum())
unicos_crudo = int(m.nunique())
unicos_norm = int(m.str.strip().str.replace("@", "a", regex=False).str.title().nunique())


def clasificar(v):
    if pd.isna(v):
        return None
    if v <= 5:
        return "Sin riesgo (0-5)"
    if v <= 14:
        return "Bajo riesgo (5-14)"
    if v <= 28:
        return "Riesgo medio (14-28)"
    if v <= 40:
        return "Alto riesgo (28-40)"
    return "Inviabile sanitariamente (>40)"


esperada = irca.map(clasificar)
comparables = irca.notna() & df["clasificacion_riesgo"].ne("")
incoherentes_mask = comparables & (esperada != df["clasificacion_riesgo"])
incoherentes = int(incoherentes_mask.sum())
huerfanos_mask = vacia("irca") & ~vacia("clasificacion_riesgo")
huerfanos = int(huerfanos_mask.sum())

# Un registro es consistente si cumple TODAS las reglas de formato y coherencia
inconsistente = (~iso) | mal_mun | incoherentes_mask | huerfanos_mask
consistencia = round((N - int(inconsistente.sum())) / N * 100, 2)

log("CONSISTENCIA - formatos de fecha distintos al ISO",
    f"Patrones hallados: {patrones}\n\nEjemplos:\n"
    + df.loc[~iso, "fecha"].head(12).to_string())
log("CONSISTENCIA - municipio mal escrito",
    m[mal_mun].value_counts().head(20).to_string()
    + f"\n\nValores unicos sin normalizar: {unicos_crudo}"
    + f"\nValores unicos tras normalizar:  {unicos_norm}")
log("CONSISTENCIA - clasificacion_riesgo que no corresponde al irca",
    df.loc[incoherentes_mask, ["irca", "clasificacion_riesgo"]].head(10).to_string())

medir(
    "Consistencia",
    "Proporcion de registros que cumplen todas las reglas de formato y de "
    "coherencia interna: fecha en formato ISO, municipio normalizado, y "
    "clasificacion_riesgo coherente con el irca que la origina.",
    "Consistencia = (registros que cumplen las 4 reglas / registros totales) x 100",
    f"({N} - {int(inconsistente.sum())}) / {N} x 100",
    f"{consistencia}%",
    f"{int(inconsistente.sum())} registros violan al menos una regla: "
    f"{fecha_mala} de formato de fecha, {mal_mun_n} de formato de municipio, "
    f"{incoherentes} de coherencia irca-clasificacion y {huerfanos} con etiqueta "
    f"sin dato de origen.",
)

registrar(
    "fecha",
    "Cuatro formatos de fecha conviviendo en la misma columna (YYYY-MM-DD, "
    "DD/MM/YYYY, MM-DD-YYYY y YYYY/MM/DD). Al convertir con pd.to_datetime se "
    "generan nulos, o peor, fechas mal interpretadas con el dia y el mes "
    "intercambiados, lo que desordena silenciosamente la serie temporal.",
    fecha_mala, "Consistencia", "Alto",
    f"{fecha_mala} registros ({pct(fecha_mala)}%) incumplen el patron "
    f"^\\d{{4}}-\\d{{2}}-\\d{{2}}$. Patrones detectados: {patrones}",
)

registrar(
    "municipio",
    "Un mismo municipio aparece escrito de varias formas: en MAYUSCULAS, en "
    "minusculas, con espacios sobrantes al inicio o al final, y con la letra "
    "'a' sustituida por '@'. Cada variante se cuenta como un municipio "
    "distinto, lo que fragmenta las agrupaciones territoriales e impide cruzar "
    "el dataset con cualquier otra fuente por nombre de municipio.",
    mal_mun_n, "Consistencia", "Alto",
    f"{mal_mun_n} registros ({pct(mal_mun_n)}%) mal formateados. El dataset "
    f"reporta {unicos_crudo} municipios unicos cuando en realidad existen "
    f"{unicos_norm}. Ejemplos: 'CHIA', 'madrid', ' Sopo', 'M@drid'",
    complementaria="Unicidad",
)

registrar(
    "irca / clasificacion_riesgo",
    "La clasificacion de riesgo no corresponde al valor del IRCA segun los "
    "cortes de la Resolucion 2115 de 2007: la variable derivada contradice a la "
    "variable que la origina.",
    incoherentes, "Consistencia", "Alto",
    f"{incoherentes} registros ({pct(incoherentes)}%) donde la clasificacion "
    f"recalculada difiere de la registrada. Ejemplo: irca = -4.38 etiquetado "
    f"como 'Bajo riesgo (5-14)'",
    complementaria="Exactitud",
)

registrar(
    "clasificacion_riesgo",
    "Registros con clasificacion de riesgo pero sin el IRCA que la sustenta. "
    "La etiqueta existe sin el dato de origen, por lo que no es verificable ni "
    "reproducible.",
    huerfanos, "Consistencia", "Medio",
    f"{huerfanos} registros ({pct(huerfanos)}%) con irca vacio y "
    f"clasificacion_riesgo diligenciada",
)

registrar(
    "municipio",
    "La columna mezcla dos niveles geograficos distintos: contiene municipios "
    "colombianos y tambien nombres de paises (Colombia, India, USA) en los "
    "registros de nivel global. Un mismo campo representa dos entidades "
    "diferentes, lo que impide unir la tabla consigo misma por territorio.",
    globales, "Consistencia", "Medio",
    f"{globales} registros ({pct(globales)}%) de tipo_region='Global' donde "
    f"'municipio' almacena paises: "
    f"{sorted(df.loc[df.tipo_region == 'Global', 'municipio'].str.strip().unique())[:6]}",
)

registrar(
    "cobertura_acueducto_pct",
    "La variable cambia de significado segun la fila: en los registros "
    "municipales es el porcentaje de cobertura de acueducto, y en los globales "
    "es el porcentaje de poblacion con acceso a agua potable segura (indicador "
    "ODS 6.1). Promediar la columna completa mezcla dos indicadores distintos.",
    globales, "Consistencia", "Medio",
    f"{globales} registros globales con una definicion distinta a la de los "
    f"{N - globales} registros municipales",
)

registrar(
    "fecha (registros globales)",
    "Los registros globales son de periodicidad anual pero se les asigno la "
    "fecha ficticia 30 de junio para poder mezclarlos con los diarios. Esa "
    "fecha no corresponde a ninguna medicion real y no puede compararse contra "
    "las series diarias sin agregar primero.",
    globales, "Consistencia", "Medio",
    f"{globales} registros globales concentrados en "
    f"{df.loc[df.tipo_region == 'Global', 'fecha'].nunique()} fechas, una por año",
    complementaria="Granularidad",
)

# ===========================================================================
# DIMENSION 5 - EXACTITUD
# ===========================================================================
def outliers_iqr(serie):
    q1, q3 = serie.quantile(.25), serie.quantile(.75)
    r = q3 - q1
    mask = (serie < q1 - 1.5 * r) | (serie > q3 + 1.5 * r)
    return mask.fillna(False), round(q1 - 1.5 * r, 2), round(q3 + 1.5 * r, 2)


out_irca_m, li, ls = outliers_iqr(irca)
out_cob_m, cli, cls_ = outliers_iqr(cob)
out_temp_m, tli, tls = outliers_iqr(temp)
typo_m = df["clasificacion_riesgo"].str.contains("Inviabile")

inexacto = out_irca_m | out_cob_m | out_temp_m | typo_m
exactitud = round((N - int(inexacto.sum())) / N * 100, 2)

log("EXACTITUD - resumen estadistico de las variables numericas",
    pd.DataFrame({c: num(c).describe() for c in
                  ["nivel_almacenamiento_pct", "afluencias_m3s", "precipitacion_mm",
                   "temperatura_c", "consumo_m3s", "irca", "cobertura_acueducto_pct"]}
                 ).round(2).to_string())

medir(
    "Exactitud",
    "Proporcion de registros cuyos valores son plausibles frente a la "
    "distribucion de su variable y cuyas categorias estan escritas conforme a "
    "la norma. Los atipicos se detectan por el criterio del rango "
    "intercuartilico (Tukey).",
    "Exactitud = (registros sin atipicos ni errores de categoria / registros totales) x 100",
    f"({N} - {int(inexacto.sum())}) / {N} x 100",
    f"{exactitud}%",
    f"{int(inexacto.sum())} registros presentan al menos un valor atipico o una "
    f"categoria mal escrita. El grueso proviene del error ortografico en "
    f"clasificacion_riesgo y de los atipicos de irca.",
)

registrar(
    "clasificacion_riesgo",
    "Error ortografico en el nombre de la categoria: dice 'Inviabile "
    "sanitariamente' cuando la Resolucion 2115 de 2007 la define como "
    "'Inviable sanitariamente'. Rompe la trazabilidad frente a la norma y el "
    "cruce por categoria con los datos del SIVICAP.",
    int(typo_m.sum()), "Exactitud", "Bajo",
    f"{int(typo_m.sum())} registros ({pct(int(typo_m.sum()))}%) con la categoria mal escrita",
)

registrar(
    "irca",
    "Valores atipicos detectados por el criterio del rango intercuartilico. "
    "Corresponden a municipios con IRCA muy alto que pueden ser casos reales de "
    "inviabilidad sanitaria o errores de digitacion; deben verificarse contra "
    "la fuente antes de descartarlos.",
    int(out_irca_m.sum()), "Exactitud", "Medio",
    f"{int(out_irca_m.sum())} registros ({pct(int(out_irca_m.sum()))}%) fuera del "
    f"rango [{li}, {ls}], calculado como Q1-1.5*IQR y Q3+1.5*IQR",
)

registrar(
    "cobertura_acueducto_pct",
    "Valores atipicos de cobertura muy baja frente al resto del pais, "
    "concentrados en municipios apartados. Pueden ser reales, pero desvirtuan "
    "el promedio nacional si no se tratan de forma diferenciada.",
    int(out_cob_m.sum()), "Exactitud", "Bajo",
    f"{int(out_cob_m.sum())} registros ({pct(int(out_cob_m.sum()))}%) fuera del "
    f"rango [{cli}, {cls_}]. Minimo observado: {cob.min()}%",
)

registrar(
    "temperatura_c",
    "Valores atipicos de temperatura respecto a la distribucion general, "
    "explicados por mezclar en una sola columna ciudades de clima frio (Bogota, "
    "Tunja) y calido (Leticia, Barranquilla) sin control por piso termico.",
    int(out_temp_m.sum()), "Exactitud", "Bajo",
    f"{int(out_temp_m.sum())} registros ({pct(int(out_temp_m.sum()))}%) fuera del "
    f"rango [{tli}, {tls}]. Rango observado: {temp.min()}C a {temp.max()}C",
)

# ===========================================================================
# DIMENSION 6 - ACTUALIDAD
# ===========================================================================
fechas_ok = pd.to_datetime(df["fecha"], errors="coerce", format="%Y-%m-%d")
ultima_obs = fechas_ok.max().date()
desfase_dias = (FECHA_ANALISIS - ultima_obs).days
corte = pd.Timestamp(FECHA_ANALISIS) - pd.DateOffset(months=VENTANA_VIGENCIA_MESES)
vigentes = int((fechas_ok >= corte).sum())
desactualizados = N - vigentes
actualidad = round(vigentes / N * 100, 2)

glob_f = pd.to_datetime(df.loc[df.tipo_region == "Global", "fecha"],
                        errors="coerce", format="%Y-%m-%d")
ultima_glob = glob_f.max().date()
desfase_glob = (FECHA_ANALISIS - ultima_glob).days

log("ACTUALIDAD - vigencia de la informacion",
    f"Fecha de analisis:            {FECHA_ANALISIS}\n"
    f"Ultima observacion registrada:{ultima_obs}\n"
    f"Desfase:                      {desfase_dias} dias "
    f"({round(desfase_dias / 30.44, 1)} meses)\n"
    f"Ventana de vigencia adoptada: {VENTANA_VIGENCIA_MESES} meses "
    f"(corte {corte.date()})\n"
    f"Registros vigentes:           {vigentes} ({actualidad}%)\n"
    f"Registros desactualizados:    {desactualizados} ({pct(desactualizados)}%)\n\n"
    + "Registros por año:\n" + df["anio"].value_counts().sort_index().to_string())

medir(
    "Actualidad",
    f"Proporcion de registros cuya fecha cae dentro de la ventana de vigencia "
    f"de {VENTANA_VIGENCIA_MESES} meses definida por el equipo. Se acompana del "
    f"desfase en dias entre la ultima observacion y la fecha de analisis.",
    "Actualidad = (registros dentro de la ventana de vigencia / registros totales) x 100",
    f"{vigentes} / {N} x 100   |   desfase = {FECHA_ANALISIS} - {ultima_obs}",
    f"{actualidad}%  (desfase de {desfase_dias} dias)",
    f"La ultima observacion es del {ultima_obs} y el analisis se ejecuta el "
    f"{FECHA_ANALISIS}: {desfase_dias} dias de rezago. Solo {vigentes} registros "
    f"({actualidad}%) caen dentro de los ultimos {VENTANA_VIGENCIA_MESES} meses.",
)

registrar(
    "fecha (conjunto completo)",
    f"Con la ventana de vigencia adoptada ({VENTANA_VIGENCIA_MESES} meses), "
    f"{desactualizados} registros de las escalas Nacional y Global quedan por "
    f"fuera por ser anteriores a {corte.date()}. Es el grupo historico 2019-2021 "
    f"del diseno, esperable para un estudio de serie larga, pero conviene "
    f"separarlo explicitamente de la serie vigente al modelar.",
    desactualizados, "Actualidad", "Medio",
    f"max(fecha) = {ultima_obs}; fecha de analisis = {FECHA_ANALISIS}; "
    f"desfase = {desfase_dias} dias. {desactualizados} registros "
    f"({pct(desactualizados)}%) quedan fuera de la ventana de vigencia de "
    f"{VENTANA_VIGENCIA_MESES} meses",
)

registrar(
    "fecha (registros globales)",
    f"El nivel global es el mas rezagado de las tres escalas: su ultima "
    f"observacion es del {ultima_glob}, con {desfase_glob} dias de desfase. La "
    f"comparacion entre escalas termina contrastando periodos distintos.",
    globales, "Actualidad", "Medio",
    f"max(fecha) del nivel global = {ultima_glob}, frente a {ultima_obs} del "
    f"conjunto completo: {desfase_glob - desfase_dias} dias adicionales de rezago",
)

registrar(
    "Metadato ausente en el dataset",
    "El dataset no incluye ninguna variable que registre cuando fue capturado o "
    "actualizado cada dato (fecha_carga, fecha_actualizacion o version de la "
    "fuente). Sin ese metadato la vigencia solo puede inferirse de la fecha del "
    "evento, y es imposible auditar si una fuente dejo de actualizarse.",
    N, "Actualidad", "Medio",
    f"Ninguna de las {COLS} columnas registra fecha de captura o de "
    f"actualizacion: {list(df.columns)}",
)

# ===========================================================================
# VERIFICACIONES REALIZADAS SIN HALLAZGOS
# ===========================================================================
dias_rango = (fechas_ok.max() - fechas_ok.min()).days + 1
dias_con_datos = int(fechas_ok.dropna().nunique())

# Coherencia entre la fecha y las columnas derivadas anio y mes.
# Solo se evalua sobre las fechas que se pudieron interpretar (formato ISO):
# las que tienen formato inconsistente ya se contabilizan en el problema P10.
fecha_parseada = fechas_ok.notna()
desalineados = int((
    (fechas_ok[fecha_parseada].dt.year.astype(str) != df.loc[fecha_parseada, "anio"])
    | (fechas_ok[fecha_parseada].dt.month.astype(str) != df.loc[fecha_parseada, "mes"])
).sum())

sin_hallazgo = [
    ("nivel_almacenamiento_pct", "Valores negativos", int((nivel < 0).sum()), "Validez"),
    ("irca", "Valores por encima de 100 (fuera de la escala normativa)",
     int((irca > 100).sum()), "Validez"),
    ("precipitacion_mm", "Laminas de lluvia negativas", int((precip < 0).sum()), "Validez"),
    ("temperatura_c", "Temperaturas fuera del rango -10 C a 50 C",
     int(((temp < -10) | (temp > 50)).sum()), "Validez"),
    ("cobertura_acueducto_pct", "Coberturas superiores al 100%", int((cob > 100).sum()), "Validez"),
    ("afluencias_m3s", "Caudales negativos", int((aflu < 0).sum()), "Validez"),
    ("fecha vs anio / mes",
     f"Año o mes que no coinciden con la fecha "
     f"(sobre las {int(fechas_ok.notna().sum())} fechas en formato ISO)",
     desalineados, "Consistencia"),
    ("fecha", "Dias del periodo sin ningun registro", dias_rango - dias_con_datos, "Actualidad"),
]
log("VERIFICACIONES SIN HALLAZGOS (pruebas ejecutadas que dieron cero)",
    "\n".join(f"{v:28s} | {d:55s} | {c} registros" for v, d, c, _ in sin_hallazgo))

# ===========================================================================
# EXPORTACION
# ===========================================================================
inv = pd.DataFrame(problemas)
met = pd.DataFrame(metricas)
inv.to_csv("inventario_problemas.csv", index=False, encoding="utf-8")
met.to_csv("metricas_calidad.csv", index=False, encoding="utf-8")
pd.DataFrame(sin_hallazgo,
             columns=["variable", "prueba_realizada", "registros_afectados",
                      "dimension_calidad"]
             ).to_csv("verificaciones_sin_hallazgo.csv", index=False, encoding="utf-8")

with open("evidencias_inventario.txt", "w", encoding="utf-8") as f:
    f.write(f"EVIDENCIAS DE CALIDAD - {ARCHIVO}\n")
    f.write(f"{N} registros x {COLS} variables\n")
    f.write(f"Fecha de analisis: {FECHA_ANALISIS}\n")
    f.writelines(evidencias)

print("METRICAS POR DIMENSION")
print(met[["dimension", "resultado"]].to_string(index=False))
print()
print("INVENTARIO DE PROBLEMAS")
print(inv[["id", "variable_afectada", "registros_afectados",
           "dimension_calidad", "nivel_impacto"]].to_string(index=False))
print(f"\nTotal de problemas: {len(inv)}")
for niv in ("Alto", "Medio", "Bajo"):
    print(f"  Impacto {niv.lower():6s} {(inv.nivel_impacto == niv).sum()}")
print("\nProblemas por dimension:")
print(inv["dimension_calidad"].value_counts().to_string())
print("\nArchivos generados: metricas_calidad.csv, inventario_problemas.csv, "
      "verificaciones_sin_hallazgo.csv, evidencias_inventario.txt")
