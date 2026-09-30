"""Recalcula los indicadores de calidad sobre el dataset ya tratado.

Aplica sobre dataset_calidad_agua.csv las mismas reglas que ejecuta el paquete
SSIS (reglas P01-P22 documentadas en plan_tratamiento.csv) y devuelve los
indicadores despues del tratamiento, para compararlos con la linea base de
metricas_calidad.csv.

No reemplaza al ETL: sirve para auditar que los numeros publicados en el informe
de la Etapa 3 sean consistentes con las reglas declaradas.

AVISO: los indicadores que imprime este script son una ESTIMACION obtenida al
aplicar las reglas en Python. No son los valores del servidor. Las cifras
autoritativas son los conteos de ejecucion de resultados_iteraciones.csv y
etl_log: 12.680 aceptados, 62 duplicados (P07) y 247 en revision (141 casos P05
+ 106 casos P08). Este script puede marcar algun caso adicional porque evalua
cada regla de forma independiente, mientras que el paquete las aplica en el orden
de sus transformaciones.

Uso:
    python calcular_indicadores_etapa3.py
"""

import csv
import re
import statistics

ARCHIVO = "dataset_calidad_agua.csv"
MARCADORES = {"", "N/A", "N/A ", "null", "-", "NA", "N/D"}

# Cortes normativos del IRCA (Res. 2115/2007), replicados del Derived Column.
# El catalogo tiene 5 categorias: la quinta es la de ">40" (fuera del rango de
# riesgo bajo y medio), que es justamente la que arrastra el error ortografico
# "Inviabile" corregido por la regla P16.
CORTES_IRCA = [(5, "Sin riesgo (0-5)"), (14, "Bajo riesgo (5-14)"),
                (28, "Riesgo medio (14-28)"), (40, "Alto riesgo (28-40)")]


def clasificar_riesgo(irca):
    """Deriva la categoria a partir del IRCA (regla P11/P16)."""
    if irca is None:
        return ""
    for limite, etiqueta in CORTES_IRCA:
        if irca <= limite:
            return etiqueta
    return "Inviable sanitariamente (>40)"


def a_numero(txt):
    """Convierte a float tolerando coma decimal. Devuelve None si no es numero."""
    if txt is None:
        return None
    t = txt.strip().replace(",", ".")
    if t in MARCADORES or t == "":
        return None
    try:
        return float(t)
    except ValueError:
        return None


# ---------------- Transformaciones del Data Flow (P09 / P10) ----------------
# El Derived Column normaliza la fecha a ISO 8601 y el Data Conversion aplica
# trim + mayusculas al municipio. Estas funciones reproducen esa transformacion
# para que el indicador de consistencia se mida sobre el dato ya tratado.

PATRONES_FECHA = [
    (re.compile(r"^(\d{4})/(\d{2})/(\d{2})$"), (1, 2, 3)),   # AAAA/MM/DD
    (re.compile(r"^(\d{2})/(\d{2})/(\d{4})$"), (3, 2, 1)),   # DD/MM/AAAA
    (re.compile(r"^(\d{2})-(\d{2})-(\d{4})$"), (3, 2, 1)),   # MM-DD-AAAA
]
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalizar_fecha(txt):
    """P09: convierte los tres formatos alternos a ISO 8601 (YYYY-MM-DD)."""
    v = (txt or "").strip()
    if ISO.match(v):
        return v
    for patron, (ia, im, idd) in PATRONES_FECHA:
        m = patron.match(v)
        if m:
            return f"{m.group(ia)}-{m.group(im)}-{m.group(idd)}"
    return v  # formato no recuperable: se conserva el texto original


def homologar_municipio(txt):
    """P10: trim + mayusculas, el mismo criterio que el Data Conversion."""
    return (txt or "").strip().upper()


def main():
    with open(ARCHIVO, encoding="utf-8") as f:
        registros = list(csv.DictReader(f))

    variables = list(registros[0].keys())
    n = len(registros)

    # ---------------- TRANSFORMACIONES PREVIAS ----------------
    # P01/P02 se imputan con la mediana, asi que deben calcularse a partir de los
    # datos antes de medir los indicadores. P02 dice "mediana de la estacion mas
    # cercana", pero el dataset no tiene columna de estacion, por lo que se usa
    # la mediana estacional por (mes, tipo_region) como aproximacion documentada.
    def mediana_por(grupos, columna):
        acum = {}
        for r in registros:
            v = a_numero(r[columna])
            if v is None:
                continue
            acum.setdefault(grupos(r), []).append(v)
        return {g: statistics.median(vs) for g, vs in acum.items()}

    med_precip = mediana_por(lambda r: (r["mes"].strip(), r["tipo_region"].strip()),
                             "precipitacion_mm")
    med_temp = mediana_por(lambda r: (r["mes"].strip(), r["tipo_region"].strip()),
                           "temperatura_c")

    # ---------------- CONTEOS DE TRATAMIENTO ----------------
    p01 = p02 = p03 = p04 = 0
    for r in registros:
        g = (r["mes"].strip(), r["tipo_region"].strip())
        if r["precipitacion_mm"].strip() in MARCADORES:
            p01 += 1
            r["precipitacion_mm"] = f"{med_precip.get(g, 0.0):.1f}"
        if r["temperatura_c"].strip() in MARCADORES:
            p02 += 1
            r["temperatura_c"] = f"{med_temp.get(g, 0.0):.1f}"
        if r["irca"].strip() in MARCADORES:
            # P03: no se imputa, se marca. Sigue siendo celda vacia a proposito.
            p03 += 1
        if r["sistema_abastecimiento"].strip().upper() == "N/A":
            # P04: el marcador se reemplaza por una categoria explicita, que si
            # es un dato valido, no una celda nula.
            p04 += 1
            r["sistema_abastecimiento"] = "Fuera de cobertura EAAB"

    # P07: duplicados por llave compuesta.
    llaves = {}
    for r in registros:
        k = (r["fecha"].strip(), r["municipio"].strip().upper(),
             r["sistema_abastecimiento"].strip().upper())
        llaves[k] = llaves.get(k, 0) + 1
    p07 = sum(c - 1 for c in llaves.values() if c > 1)

    # P08: IRCA fuera del dominio [0, 100].
    p08 = 0
    for r in registros:
        v = a_numero(r["irca"])
        if v is not None and (v < 0 or v > 100):
            p08 += 1

    # P16: grafia erronea del catalogo.
    p16 = sum(1 for r in registros if r["clasificacion_riesgo"].startswith("Inviabile"))

    # P05: registros Global (se separan del flujo regional).
    p05 = sum(1 for r in registros if r["tipo_region"].strip() == "Global")

    # Revision = lo que no puede entrar al destino (coincide con etl_log).
    en_revision = p05 + p08

    # Destino: todo menos duplicados y revision.
    n_destino = n - p07 - en_revision

    # ---------------- INDICADORES DESPUES ----------------
    # Se construye el conjunto realmente cargado: se excluyen duplicados (P07),
    # Global (P05) e IRCA fuera de dominio (P08), y sobre las filas restantes se
    # aplican las normalizaciones que hace el Data Flow (P09, P10, P11, P16).
    filas_destino = []
    for r in registros:
        k = (r["fecha"].strip(), r["municipio"].strip().upper(),
             r["sistema_abastecimiento"].strip().upper())
        if llaves[k] > 1:
            continue
        if r["tipo_region"].strip() == "Global":
            continue
        irca = a_numero(r["irca"])
        if irca is not None and (irca < 0 or irca > 100):
            continue
        # P09 fecha a ISO, P10 municipio homologado, P11/P16 clase derivada del
        # IRCA con la grafia corregida del catalogo.
        r["fecha"] = normalizar_fecha(r["fecha"])
        r["municipio"] = homologar_municipio(r["municipio"])
        if irca is not None:
            r["clasificacion_riesgo"] = clasificar_riesgo(irca)
        filas_destino.append(r)

    n_destino = len(filas_destino)
    celdas = n_destino * len(variables)

    # ---- Comparabilidad de la Completitud -------------------------------
    # La linea base de la etapa 2 se midio sobre las 20 columnas del CSV y las
    # 12.989 filas originales (259.780 celdas). Medir el "despues" solo sobre
    # las variables del destino compararia universos distintos y inflaria la
    # mejora. Por eso se calcula una segunda completitud sobre el MISMO
    # universo de la linea base, aplicando a las 12.989 filas las
    # transformaciones que el Data Flow hace sobre cada fila (P01, P02, P04,
    # P09, P10, P16). El IRCA no se imputa (P03) y por eso sigue contando como
    # celda ausente: eso es correcto, no un defecto del calculo.
    columnas_base = list(registros[0].keys())

    celdas_base = 0
    ausentes_base = 0
    for r in registros:
        grupo = (r["mes"].strip(), r["tipo_region"].strip())
        for c in columnas_base:
            celdas_base += 1
            val = r[c].strip()
            if val in MARCADORES:
                # P01/P02: imputacion por mediana estacional de mes y region.
                if c == "precipitacion_mm" and grupo in med_precip:
                    val = "imputado"
                elif c == "temperatura_c" and grupo in med_temp:
                    val = "imputado"
                # P04: el marcador N/A se convierte en categoria explicita.
                elif c == "sistema_abastecimiento":
                    val = "Fuera de cobertura EAAB"
            # P03: el IRCA ausente NO se imputa, sigue ausente.
            if val in MARCADORES:
                ausentes_base += 1
    completitud_base = (celdas_base - ausentes_base) / celdas_base * 100

    # Completitud sobre el destino: solo queda el IRCA no imputable por decision
    # metodologica (P03, marcado con irca_reportado = 'No').
    nulos_destino = 0
    for r in filas_destino:
        for v in variables:
            if r[v].strip() in MARCADORES:
                nulos_destino += 1
    completitud = (celdas - nulos_destino) / celdas * 100 if celdas else 0.0

    # Unicidad: el destino tiene llave UNIQUE (iteracion, fecha, municipio,
    # sistema_abastecimiento), asi que es 100% por construccion. Los duplicados
    # P07 se excluyen antes de la carga.
    unicidad = 100.0

    # Validez: las reglas de dominio ya enviaron a revision los valores fuera de
    # rango, por lo que la validez se mide sobre lo que efectivamente quedo
    # cargado.
    numericas_dom = {
        "nivel_almacenamiento_pct": (0, 100), "afluencias_m3s": (0, 1000),
        "precipitacion_mm": (0, 500), "temperatura_c": (-10, 50),
        "irca": (0, 100), "cobertura_acueducto_pct": (0, 100),
    }
    evaluados = fuera = 0
    for r in filas_destino:
        for col, (lo, hi) in numericas_dom.items():
            v = a_numero(r[col])
            if v is None:
                continue
            evaluados += 1
            if v < lo or v > hi:
                fuera += 1
    validez = ((evaluados - fuera) / evaluados * 100) if evaluados else 0.0

    # Consistencia: se mide DESPUES de la transformacion, igual que en el
    # destino, donde las fechas ya estan en ISO (P09) y los municipios
    # homologados (P10).
    iso = ISO
    inconsistentes = 0
    for r in filas_destino:
        fecha_ok = bool(iso.match(normalizar_fecha(r["fecha"])))
        mun_ok = bool(homologar_municipio(r["municipio"]))
        # La clasificacion se deriva del IRCA, por lo que solo es coherente si
        # el IRCA es valido; los ausentes (P03) se marcan y no se evaluan.
        irca = a_numero(r["irca"])
        clas_ok = True if irca is None else (
            r["clasificacion_riesgo"].strip() == clasificar_riesgo(irca))
        if not (fecha_ok and mun_ok and clas_ok):
            inconsistentes += 1
    consistencia = ((n_destino - inconsistentes) / n_destino * 100) if n_destino else 0.0

    # Exactitud: se corrige P16; los atipicos de Tukey se MARCAN, no se eliminan,
    # por lo que siguen contamiendo el indicador (decision deliberada).
    atipicos = set()
    for col in ("irca", "cobertura_acueducto_pct", "temperatura_c"):
        vals = [a_numero(r[col]) for r in filas_destino]
        vals = [v for v in vals if v is not None]
        if len(vals) >= 5:
            q1, _, q3 = statistics.quantiles(vals, n=4, method="inclusive")
            iqr = q3 - q1
            for r in filas_destino:
                v = a_numero(r[col])
                if v is not None and (v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr):
                    atipicos.add(id(r))
    exactos = n_destino - len(atipicos)
    exactitud = (exactos / n_destino * 100) if n_destino else 0.0

    print("=" * 78)
    print("INDICADORES DE CALIDAD - ANTES Y DESPUES DEL TRATAMIENTO SSIS")
    print("=" * 78)
    print(f"Registros originales           : {n:>7,}".replace(",", "."))
    print(f"Duplicados excluidos (P07)     : {p07:>7,}".replace(",", "."))
    print(f"En revision (P05 {p05} + P08 {p08})  : {en_revision:>7,}".replace(",", "."))
    print(f"Registros en el destino        : {n_destino:>7,}".replace(",", "."))
    print("-" * 78)
    print(f"{'Dimension':<16}{'Antes':>12}{'Despues':>12}{'Delta':>12}")
    print("-" * 78)
    lineas = [
        ("Completitud", 96.82, completitud_base, "pp"),
        ("Unicidad", 99.51, unicidad, "pp"),
        ("Validez", 99.83, validez, "pp"),
        ("Consistencia", 94.80, consistencia, "pp"),
        ("Exactitud", 88.76, exactitud, "pp"),
    ]
    for nombre, antes, despues, _ in lineas:
        delta = despues - antes
        print(f"{nombre:<16}{antes:>11.2f}%{despues:>11.2f}%{delta:>+11.2f} pp")
    print(f"{'Actualidad':<16}{60.87:>11.2f}%{60.87:>11.2f}%{0.0:>+11.2f} pp  (fuera del ETL)")
    print("-" * 78)
    print("Completitud, dos lecturas:")
    print(f"  sobre las 12.989 filas y las 20 columnas (base comparable): "
          f"{completitud_base:.2f}%")
    print(f"  sobre las {n_destino:,} filas del destino y {len(variables)} variables: "
          f"{completitud:.2f}%".replace(",", "."))
    print("  La comparacion antes/despues usa la primera, que comparte")
    print("  universo con la linea base de la etapa 2.")
    print("-" * 78)
    print("Tratamiento aplicado por regla:")
    for etiqueta, valor in [
        ("P01 precipitacion imputada", p01), ("P02 temperatura imputada", p02),
        ("P03 IRCA no imputado (marca)", p03), ("P04 N/A homologado", p04),
        ("P05 Global separado", p05), ("P07 duplicados excluidos", p07),
        ("P08 IRCA fuera de dominio", p08), ("P16 'Inviabile' corregido", p16),
    ]:
        print(f"  {etiqueta:<34}: {valor:>6,}".replace(",", "."))
    print("=" * 78)
    print("Nota: Actualidad no mejora porque depende de la frecuencia de")
    print("publicacion de las fuentes externas, no de la carga.")


if __name__ == "__main__":
    main()
