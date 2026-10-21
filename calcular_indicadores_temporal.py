"""Recalcula los indicadores temporales del dataset limpio.

Sirve para auditar las cifras de la dimension temporal de la Etapa 4 (pagina 3
del informe de Power BI) y para regenerar las tablas que se documentan en
docs/etapa4/temporal_datos.md.

Todo se calcula sobre dataset_calidad_agua_limpio.csv (12.680 registros
validos de 12.989 recibidos en la Etapa 3). Ningun numero esta fijado a mano:
si el dataset cambia, las tablas cambian.

Uso:
    python calcular_indicadores_temporal.py
"""

import csv
import os

ARCHIVO = "dataset_calidad_agua_limpio.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RIESGO_ALTO = {"Alto riesgo (28-40)", "Inviable sanitariamente (>40)"}
SIN_SERVICIO = {"Racionado", "Sin servicio"}


def leer():
    ruta = os.path.join(BASE_DIR, ARCHIVO)
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def a_numero(valor):
    if valor is None:
        return None
    texto = valor.strip()
    if texto == "":
        return None
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        return None


def promedio(registros, campo):
    valores = [a_numero(r.get(campo)) for r in registros]
    valores = [v for v in valores if v is not None]
    if not valores:
        return None
    return sum(valores) / len(valores)


def porcentaje(registros, condicion):
    if not registros:
        return None
    return sum(1 for r in registros if condicion(r)) / len(registros) * 100


def tabla(filas, titulo):
    print()
    print(titulo)
    print("-" * len(titulo))
    for fila in filas:
        print(fila)


def main():
    registros = leer()
    anios = sorted({r["anio"] for r in registros})

    # 1) Serie anual completa
    filas = []
    for anio in anios:
        rs = [r for r in registros if r["anio"] == anio]
        con_irca = [r for r in rs if r.get("irca_reportado") != "No"]
        filas.append(
            f"{anio} | n={len(rs):5d} | con IRCA={len(con_irca):5d} "
            f"| IRCA prom={promedio(con_irca, 'irca'):6.2f} "
            f"| % continuo={porcentaje(rs, lambda r: r['nivel_servicio'] == 'Continuo'):6.2f} "
            f"| % racion/sin serv={porcentaje(rs, lambda r: r['nivel_servicio'] in SIN_SERVICIO):6.2f} "
            f"| % alto riesgo={porcentaje(con_irca, lambda r: r['clasificacion_riesgo'] in RIESGO_ALTO):6.2f} "
            f"| % sin IRCA={porcentaje(rs, lambda r: r.get('irca_reportado') == 'No'):5.2f} "
            f"| almac={promedio(rs, 'nivel_almacenamiento_pct'):6.2f} "
            f"| precip={promedio(rs, 'precipitacion_mm'):6.2f}"
        )
    tabla(filas, "1) Serie anual (todos los municipios)")

    # 2) Continuidad por anio y tipo de region
    filas = []
    for anio in anios:
        por_region = []
        for region in ("Regional", "Nacional"):
            rs = [r for r in registros if r["anio"] == anio and r["tipo_region"] == region]
            pct = porcentaje(rs, lambda r: r["nivel_servicio"] == "Continuo")
            por_region.append(f"{region} n={len(rs):5d} continuo={pct:6.2f}%")
        filas.append(f"{anio} | " + " | ".join(por_region))
    tabla(filas, "2) % de servicio continuo por anio y tipo de region")

    # 3) Trimestre contra trimestre (periodos equivalentes)
    filas = []
    for anio in anios:
        por_trimestre = []
        for t in ("T1", "T2", "T3", "T4"):
            rs = [r for r in registros if r["anio"] == anio and r["periodo"].endswith(t)]
            por_trimestre.append(f"{t}={porcentaje(rs, lambda r: r['nivel_servicio'] == 'Continuo'):6.2f}%")
        filas.append(f"{anio} | " + " | ".join(por_trimestre))
    tabla(filas, "3) % de servicio continuo por trimestre (periodos equivalentes)")

    # 4) Primer registro no continuo del dataset y su contexto
    no_continuos = sorted(
        (r for r in registros if r["nivel_servicio"] != "Continuo"),
        key=lambda r: r["fecha"],
    )

    def primero_de(rs):
        return sorted(rs, key=lambda r: r["fecha"])[0]

    regional_no_continuo = primero_de(
        [r for r in no_continuos if r["tipo_region"] == "Regional"]
    )
    racionado = primero_de([r for r in registros if r["nivel_servicio"] == "Racionado"])
    sin_servicio = primero_de([r for r in registros if r["nivel_servicio"] == "Sin servicio"])
    tabla(
        [
            f"Primer registro no continuo del dataset: {primero_de(no_continuos)['fecha']} | "
            f"{primero_de(no_continuos)['municipio']} "
            f"({primero_de(no_continuos)['tipo_region']}) | {primero_de(no_continuos)['nivel_servicio']}",
            f"Primer registro Regional no continuo: {regional_no_continuo['fecha']} | "
            f"{regional_no_continuo['municipio']} | {regional_no_continuo['nivel_servicio']} | "
            f"{regional_no_continuo['periodo']}",
            f"Primer 'Racionado': {racionado['fecha']} | {racionado['municipio']} | "
            f"{racionado['tipo_region']} | {racionado['periodo']}",
            f"Primer 'Sin servicio': {sin_servicio['fecha']} | {sin_servicio['municipio']} | "
            f"{sin_servicio['tipo_region']} | {sin_servicio['periodo']}",
            f"Registros no continuos antes de 2024-04-01: "
            f"{sum(1 for r in no_continuos if r['fecha'] < '2024-04-01')} "
            f"(todos de tipo Nacional y nivel Intermitente: "
            f"{sum(1 for r in no_continuos if r['fecha'] < '2024-04-01' and r['tipo_region'] == 'Nacional' and r['nivel_servicio'] == 'Intermitente')})",
            f"Total de registros no continuos: {len(no_continuos)} "
            f"(de {sum(1 for r in registros if r['tipo_region'] == 'Regional')} Regional y "
            f"{sum(1 for r in registros if r['tipo_region'] == 'Nacional')} Nacional)",
        ],
        "4) Punto de quiebre del servicio",
    )

    # 5) Variacion del IRCA promedio frente al anio anterior (medida Temp_Variacion IRCA)
    filas = []
    for anio in anios:
        actual = [r for r in registros if r["anio"] == anio]
        anterior = [r for r in registros if r["anio"] == str(int(anio) - 1)]
        if not actual or not anterior:
            continue
        filas.append(
            f"{anio} | IRCA={promedio(actual, 'irca'):6.2f} | "
            f"{int(anio) - 1} IRCA={promedio(anterior, 'irca'):6.2f} | "
            f"variacion={promedio(actual, 'irca') - promedio(anterior, 'irca'):+6.2f} pp"
        )
    tabla(filas, "5) Variacion del IRCA promedio frente al anio anterior")

    # 6) Cobertura por trimestre (los periodos son comparables entre anios)
    filas = []
    for anio in anios:
        rs = [r for r in registros if r["anio"] == anio]
        meses = sorted({r["mes"] for r in rs})
        periodos = len({r["periodo"] for r in rs})
        filas.append(
            f"{anio} | registros={len(rs):5d} | periodos={periodos} | meses={len(meses)} "
            f"| municipios={len({r['municipio'] for r in rs})}"
        )
    tabla(filas, "6) Cobertura de la serie temporal (comparabilidad entre anios)")

    # 7) Almacenamiento y precipitacion por anio y tipo de region
    filas = []
    for anio in anios:
        por_region = []
        for region in ("Regional", "Nacional"):
            rs = [r for r in registros if r["anio"] == anio and r["tipo_region"] == region]
            por_region.append(
                f"{region} almac={promedio(rs, 'nivel_almacenamiento_pct'):6.2f} "
                f"precip={promedio(rs, 'precipitacion_mm'):5.2f}"
            )
        filas.append(f"{anio} | " + " | ".join(por_region))
    tabla(filas, "7) Almacenamiento y precipitacion por anio y tipo de region")

    # 8) Municipios: nombres crudos frente a nombres homologados
    crudos = sorted({r["municipio"] for r in registros})
    homologados = sorted({r["municipio"].replace("@", "A") for r in registros})
    tabla(
        [
            f"Municipios con nombre crudo: {len(crudos)}",
            f"Municipios tras homologar '@' -> 'A': {len(homologados)}",
            "Nombres con '@' que se homologan: "
            + ", ".join(m for m in crudos if "@" in m),
        ],
        "8) Municipios",
    )


if __name__ == "__main__":
    main()
