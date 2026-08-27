"""Analisis de calidad de datos del dataset consolidado."""
import pandas as pd
import json

df = pd.read_csv("dataset_calidad_agua.csv")

print("=" * 60)
print("RESUMEN GENERAL")
print("=" * 60)
print(f"Registros totales: {len(df)}")
print(f"Variables: {len(df.columns)}")
print(f"Periodo: {df['anio'].min()} - {df['anio'].max()}")
print(f"Municipios unicos: {df['municipio'].nunique()}")
print(f"Departamentos unicos: {df['departamento'].nunique()}")
print()

# Tipos
print("TIPOS DE DATOS:")
print(df.dtypes.to_string())
print()

# === COMPLETITUD ===
print("=" * 60)
print("COMPLETITUD (valores faltantes)")
print("=" * 60)
total_celdas = df.shape[0] * df.shape[1]
faltantes_total = df.isnull().sum().sum()
pct_global = round(faltantes_total / total_celdas * 100, 2)
print(f"Total celdas: {total_celdas}")
print(f"Celdas faltantes: {faltantes_total} ({pct_global}%)")
print()
print("Por variable:")
for col in df.columns:
    n_null = df[col].isnull().sum()
    if n_null > 0:
        print(f"  {col}: {n_null} ({round(n_null/len(df)*100, 2)}%)")
    else:
        print(f"  {col}: 0 (0.0%)")
print()

# === DUPLICADOS ===
print("=" * 60)
print("DUPLICADOS")
print("=" * 60)
duplicados_exactos = df.duplicated().sum()
print(f"Registros duplicados exactos: {duplicados_exactos} ({round(duplicados_exactos/len(df)*100, 2)}%)")
# Llave candidata: fecha + municipio + sistema
llave = ["fecha", "municipio", "sistema_abastecimiento"]
duplicados_llave = df.duplicated(subset=llave).sum()
print(f"Duplicados por llave (fecha+municipio+sistema): {duplicados_llave}")
print()

# === VALIDEZ ===
print("=" * 60)
print("VALIDEZ (valores fuera de rango)")
print("=" * 60)
nivel_col = pd.to_numeric(df["nivel_almacenamiento_pct"], errors="coerce")
irca_col = pd.to_numeric(df["irca"], errors="coerce")
precip_col = pd.to_numeric(df["precipitacion_mm"], errors="coerce")
temp_col = pd.to_numeric(df["temperatura_c"], errors="coerce")

fuera_nivel = ((nivel_col > 100) | (nivel_col < 0)).sum()
fuera_irca_neg = (irca_col < 0).sum()
fuera_irca_alto = (irca_col > 100).sum()
fuera_precip_neg = (precip_col < 0).sum()
fuera_temp = ((temp_col < -10) | (temp_col > 50)).sum()

print(f"nivel_almacenamiento_pct > 100%: {fuera_nivel}")
print(f"irca negativo: {fuera_irca_neg}")
print(f"irca > 100: {fuera_irca_alto}")
print(f"precipitacion negativa: {fuera_precip_neg}")
print(f"temperatura fuera de rango (-10 a 50): {fuera_temp}")
print()

# === CONSISTENCIA ===
print("=" * 60)
print("CONSISTENCIA (formatos)")
print("=" * 60)
# Revisar formatos de fecha
fechas = df["fecha"].dropna()
formato_iso = fechas.str.match(r"^\d{4}-\d{2}-\d{2}$").sum()
formato_otro = len(fechas) - formato_iso
print(f"Formato fecha ISO (YYYY-MM-DD): {formato_iso}")
print(f"Formato fecha inconsistente: {formato_otro}")

# Revisar capitalizacion de municipios
municipios = df["municipio"].dropna()
capitalizado = municipios.str.istitle().sum()
no_capitalizado = len(municipios) - capitalizado
print(f"Municipios formato correcto (Title): {capitalizado}")
print(f"Municipios formato inconsistente: {no_capitalizado}")
print()

# === CONTINUIDAD TEMPORAL ===
print("=" * 60)
print("CONTINUIDAD TEMPORAL")
print("=" * 60)
fechas_unicas = pd.to_datetime(df["fecha"], errors="coerce").dropna()
rango = (fechas_unicas.max() - fechas_unicas.min()).days + 1
dias_unicos = fechas_unicas.nunique()
print(f"Dias en el rango teorico: {rango}")
print(f"Dias con datos: {dias_unicos}")
print(f"Cobertura temporal: {round(dias_unicos/rango*100, 1)}%")
print()

# === DISTRIBUCION POR REGION ===
print("=" * 60)
print("DISTRIBUCION POR TIPO DE REGION")
print("=" * 60)
print(df["tipo_region"].value_counts().to_string())
print()

# === DISTRIBUCION NUMERICA ===
print("=" * 60)
print("ESTADISTICAS DESCRIPTIVAS (variables numericas)")
print("=" * 60)
cols_num = ["nivel_almacenamiento_pct", "afluencias_m3s", "precipitacion_mm",
            "temperatura_c", "consumo_m3s", "irca", "cobertura_acueducto_pct"]
for col in cols_num:
    serie = pd.to_numeric(df[col], errors="coerce")
    print(f"\n{col}:")
    print(f"  count: {serie.count()}, mean: {round(serie.mean(), 2)}, "
          f"std: {round(serie.std(), 2)}, min: {round(serie.min(), 2)}, "
          f"max: {round(serie.max(), 2)}")
print()

# === SESGOS ===
print("=" * 60)
print("POSIBLES SESGOS")
print("=" * 60)
print("1. Sobrerrepresentacion regional vs nacional/global:")
print(df["tipo_region"].value_counts().to_string())
print()
print("2. Datos globales solo anuales (no diarios)")
print("3. SIVICAP y HDX no se integraron directamente (solo documentadas como fuentes)")
print("4. IDECA (estaciones geograficas) se uso solo para coordenadas simuladas")
print("5. Datos de EAAB boletines (niveles embalses) son simulados basados en cronologia")
