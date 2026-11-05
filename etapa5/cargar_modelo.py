# -*- coding: utf-8 -*-
"""
Etapa 5 - Carga del modelo estrella (calidad del agua).

Lee el dataset tratado en la etapa 3 (datos/dataset_calidad_agua_limpio.csv), crea la base
SQLite con el script 01_crear_modelo.sql y llena las dimensiones y la tabla de hechos.
Al final imprime las comprobaciones contra el CSV.

Uso (desde la carpeta del proyecto):
    python etapa5/cargar_modelo.py

Solo usa librerías que vienen con Python (csv, sqlite3), así que no hay que instalar nada.
Se puede ejecutar las veces que sea: siempre crea la base desde cero.
"""
import csv
import sqlite3
from datetime import date
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
CSV_ORIGEN = CARPETA.parent / "datos" / "dataset_calidad_agua_limpio.csv"
SCRIPT_MODELO = CARPETA / "sql" / "01_crear_modelo.sql"
BASE = CARPETA / "calidad_agua_dw.db"

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
SIN_DATO_IRCA = "Sin dato de IRCA"


def numero(valor):
    """Convierte el texto del CSV en número; si está vacío devuelve None (NULL), no 0."""
    valor = (valor or "").strip()
    return float(valor) if valor else None


def limpiar_municipio(nombre):
    """Corrige el carácter @ que quedó en lugar de la A (29 filas del CSV)."""
    return nombre.replace("@", "A").strip()


def leer_csv():
    with open(CSV_ORIGEN, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def crear_modelo(con):
    con.executescript(SCRIPT_MODELO.read_text(encoding="utf-8"))


def cargar_dim_tiempo(con, filas):
    """Una fila por cada fecha distinta del CSV."""
    fechas = sorted({f["fecha"] for f in filas})
    for texto in fechas:
        d = date.fromisoformat(texto)
        trimestre = (d.month - 1) // 3 + 1
        con.execute(
            "INSERT INTO dim_tiempo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (int(d.strftime("%Y%m%d")), texto, d.year, trimestre, f"{d.year}-T{trimestre}",
             d.month, MESES[d.month - 1], f"{d.year}-{d.month:02d}", d.day),
        )


def cargar_dim_geografia(con, filas):
    """Una fila por municipio (con la @ corregida), con su departamento y región."""
    municipios = {}
    for f in filas:
        nombre = limpiar_municipio(f["municipio"])
        municipios.setdefault(nombre, (f["departamento"].strip(), f["tipo_region"].strip()))
    for clave, nombre in enumerate(sorted(municipios), start=1):
        departamento, region = municipios[nombre]
        con.execute("INSERT INTO dim_geografia VALUES (?, ?, ?, ?)",
                    (clave, nombre, departamento, region))


def cargar_dim_sistema(con, filas):
    """Una fila por sistema de abastecimiento."""
    sistemas = sorted({f["sistema_abastecimiento"].strip() for f in filas})
    for clave, nombre in enumerate(sistemas, start=1):
        cubierto = 0 if nombre == "Fuera de cobertura EAAB" else 1
        con.execute("INSERT INTO dim_sistema VALUES (?, ?, ?)", (clave, nombre, cubierto))


def diccionario(con, tabla, clave, texto):
    """Devuelve {texto: clave} de una dimensión para buscar las claves foráneas."""
    return {t: k for k, t in con.execute(f"SELECT {clave}, {texto} FROM {tabla}")}


def cargar_hechos(con, filas):
    """Una fila de hechos por cada medición diaria de un municipio."""
    k_municipio = diccionario(con, "dim_geografia", "municipio_key", "municipio")
    k_sistema = diccionario(con, "dim_sistema", "sistema_key", "sistema")
    k_riesgo = diccionario(con, "dim_riesgo", "riesgo_key", "clasificacion")
    k_servicio = diccionario(con, "dim_servicio", "servicio_key", "nivel_servicio")

    for i, f in enumerate(filas, start=1):
        reportado = 1 if f["irca_reportado"].strip() == "Si" else 0
        # Faltante (no se reportó el IRCA) se diferencia de categoría desconocida (clave 0)
        clasificacion = f["clasificacion_riesgo"].strip() or (SIN_DATO_IRCA if not reportado else "")
        con.execute(
            "INSERT INTO fact_medicion VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                i,
                int(f["fecha"].replace("-", "")),
                k_municipio.get(limpiar_municipio(f["municipio"]), 0),
                k_sistema.get(f["sistema_abastecimiento"].strip(), 0),
                k_riesgo.get(clasificacion, 0),
                k_servicio.get(f["nivel_servicio"].strip(), 0),
                numero(f["irca"]),
                reportado,
                numero(f["cobertura_acueducto_pct"]),
                numero(f["nivel_almacenamiento_pct"]),
                numero(f["precipitacion_mm"]),
                numero(f["consumo_m3s"]),
            ),
        )


def comprobar(con, filas):
    """Compara el modelo con el CSV de origen e imprime el resultado."""
    uno = lambda sql: con.execute(sql).fetchone()[0]
    con_irca = [numero(f["irca"]) for f in filas if numero(f["irca"]) is not None]
    regional_csv = sum(1 for f in filas if f["tipo_region"].strip() == "Regional")

    comprobaciones = [
        ("Registros", len(filas), uno("SELECT COUNT(*) FROM fact_medicion")),
        ("Mediciones con IRCA", len(con_irca),
         uno("SELECT COUNT(irca) FROM fact_medicion")),
        ("IRCA promedio", round(sum(con_irca) / len(con_irca), 2),
         round(uno("SELECT AVG(irca) FROM fact_medicion"), 2)),
        ("Mediciones Regional", regional_csv,
         uno("SELECT COUNT(*) FROM fact_medicion f JOIN dim_geografia g "
             "ON g.municipio_key = f.municipio_key WHERE g.tipo_region = 'Regional'")),
        ("Municipios distintos (CSV con @ corregida)",
         len({limpiar_municipio(f["municipio"]) for f in filas}),
         uno("SELECT COUNT(DISTINCT municipio_key) FROM fact_medicion")),
    ]
    print("\nComprobaciones contra el CSV")
    print(f"{'Comprobación':45} {'CSV':>10} {'Modelo':>10}  Resultado")
    for nombre, origen, modelo in comprobaciones:
        estado = "OK" if origen == modelo else "DIFERENTE"
        print(f"{nombre:45} {origen:>10} {modelo:>10}  {estado}")

    print("\nCalidad del modelo")
    print("Claves foráneas sin dimensión :", len(con.execute("PRAGMA foreign_key_check").fetchall()))
    print("Hechos con alguna clave 0     :", uno(
        "SELECT COUNT(*) FROM fact_medicion WHERE 0 IN "
        "(fecha_key, municipio_key, sistema_key, riesgo_key, servicio_key)"))
    print("Fecha + municipio repetidos   :", uno(
        "SELECT COUNT(*) FROM (SELECT 1 FROM fact_medicion "
        "GROUP BY fecha_key, municipio_key HAVING COUNT(*) > 1)"))
    print("Mediciones 'Sin dato de IRCA' :", uno(
        "SELECT COUNT(*) FROM fact_medicion WHERE riesgo_key = 6"))


def main():
    filas = leer_csv()
    print(f"Filas leídas del CSV: {len(filas)}")
    if BASE.exists():
        BASE.unlink()
    con = sqlite3.connect(BASE)
    try:
        crear_modelo(con)
        cargar_dim_tiempo(con, filas)
        cargar_dim_geografia(con, filas)
        cargar_dim_sistema(con, filas)
        cargar_hechos(con, filas)
        con.commit()
        for tabla in ("dim_tiempo", "dim_geografia", "dim_sistema", "dim_riesgo",
                      "dim_servicio", "fact_medicion"):
            print(f"{tabla:15} {con.execute(f'SELECT COUNT(*) FROM {tabla}').fetchone()[0]:>6} filas")
        comprobar(con, filas)
    finally:
        con.close()
    print(f"\nBase creada en: {BASE}")


if __name__ == "__main__":
    main()
