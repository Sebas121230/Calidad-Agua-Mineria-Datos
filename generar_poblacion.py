"""Genera poblacion_municipios.csv a partir de las proyecciones del DANE.

El dataset de calidad del agua no trae ninguna variable de poblacion, por eso
se usa una fuente externa: DANE, Serie municipal de poblacion por area,
periodo 2018-2042 (CNPV 2018, publicada el 8 de agosto de 2025).
Archivo original sin modificar: fuentes/PPED-AreaMun-2018-2042_VP.xlsx
"""
import pandas as pd

ARCHIVO = "fuentes/PPED-AreaMun-2018-2042_VP.xlsx"
SALIDA = "poblacion_municipios.csv"

# Nombre como aparece en nuestro dataset -> codigo DIVIPOLA del DANE.
# Se cruza por codigo y no por nombre porque el DANE escribe con tildes
# ("Cajicá", "Bogotá, D.C.") y nuestro dataset no (y a veces trae "CHI@").
CODIGOS = {
    # Sabana (Regional)
    "BOGOTA D.C.": "11001",
    "CAJICA": "25126",
    "CHIA": "25175",
    "FUNZA": "25286",
    "MADRID": "25430",
    "MOSQUERA": "25473",
    "SOACHA": "25754",
    "SOPO": "25758",
    "TOCANCIPA": "25817",
    # Resto del pais (Nacional)
    "MEDELLIN": "05001",
    "BELLO": "05088",
    "BARRANQUILLA": "08001",
    "CARTAGENA": "13001",
    "TUNJA": "15001",
    "MANIZALES": "17001",
    "POPAYAN": "19001",
    "VALLEDUPAR": "20001",
    "MONTERIA": "23001",
    "NEIVA": "41001",
    "SANTA MARTA": "47001",
    "VILLAVICENCIO": "50001",
    "PASTO": "52001",
    "CUCUTA": "54001",
    "ARMENIA": "63001",
    "PEREIRA": "66001",
    "BUCARAMANGA": "68001",
    "SINCELEJO": "70001",
    "IBAGUE": "73001",
    "CALI": "76001",
}

# Los encabezados estan en la fila 8 de Excel -> header=7 (pandas cuenta desde 0).
# MPIO se lee como texto para no perder el cero inicial (05001, no 5001).
df = pd.read_excel(ARCHIVO, sheet_name="PobMunicipalxÁrea", header=7, dtype={"MPIO": str})

# Solo el total del municipio (no cabecera ni rural) y los anios del dataset.
df = df[df["ÁREA GEOGRÁFICA"] == "Total"]
df = df[(df["AÑO"] >= 2019) & (df["AÑO"] <= 2025)]
df = df[df["MPIO"].isin(CODIGOS.values())]

# Renombrar al formato del proyecto y agregar el nombre como esta en el dataset.
nombre_por_codigo = {codigo: nombre for nombre, codigo in CODIGOS.items()}
salida = pd.DataFrame({
    "codigo_divipola": df["MPIO"],
    "municipio": df["MPIO"].map(nombre_por_codigo),
    "departamento": df["DPNOM"],
    "anio": df["AÑO"].astype(int),
    "poblacion": df["TOTAL"].astype(int),
}).sort_values(["municipio", "anio"])

# Verificacion: 29 municipios x 7 anios = 203 filas.
esperado = len(CODIGOS) * 7
print(f"Filas generadas: {len(salida)} (esperado {esperado})")
assert len(salida) == esperado, "Falta o sobra algun municipio/anio"

salida.to_csv(SALIDA, index=False, encoding="utf-8")
print(f"Archivo guardado: {SALIDA}")
