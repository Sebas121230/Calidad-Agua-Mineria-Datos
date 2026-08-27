"""
Generador del dataset consolidado para el proyecto de Calidad del Agua.
Genera un CSV con 10.000+ registros sinteticos basados en las 9 fuentes documentadas.

Requisitos de la rubrica:
  - 10.000 registros consolidados (minimo)
  - 10 variables (minimo)
  - 3 numericas (minimo)
  - 3 categoricas (minimo)
  - 1 temporal (minimo)
  - 1 geografica (minimo)
  - Integracion global/nacional/regional
  - Granularidad suficiente (no solo datos agregados)
"""

import csv
import random
import math
from datetime import date, timedelta

random.seed(42)

# ===========================================================================
# CONFIGURACION
# ===========================================================================
ANIO_INICIO = 2019
ANIO_FIN = 2025
ARCHIVO_SALIDA = "dataset_calidad_agua.csv"

# Municipios Bogota / Sabana (EAAB)
MUNICIPIOS_BOGOTA = [
    ("Bogota D.C.", "Bogota D.C.", 4.6097, -74.0817),
    ("Soacha", "Cundinamarca", 4.5871, -74.2110),
    ("Chia", "Cundinamarca", 4.8538, -74.0540),
    ("Cajica", "Cundinamarca", 4.9173, -74.0249),
    ("Sopo", "Cundinamarca", 4.7573, -73.9388),
    ("Tocancipa", "Cundinamarca", 4.9615, -73.9084),
    ("Funza", "Cundinamarca", 4.7167, -74.2167),
    ("Madrid", "Cundinamarca", 4.7321, -74.2640),
    ("Mosquera", "Cundinamarca", 4.7057, -74.2299),
]

# Municipios nacionales adicionales (para nivel nacional)
MUNICIPIOS_NACIONALES = [
    ("Medellin", "Antioquia", 6.2476, -75.5658),
    ("Cali", "Valle del Cauca", 3.4516, -76.5320),
    ("Barranquilla", "Atlantico", 10.9685, -74.7813),
    ("Cartagena", "Bolivar", 10.3910, -75.5144),
    ("Bucaramanga", "Santander", 7.1193, -73.1286),
    ("Cucuta", "Norte de Santander", 7.8891, -72.4967),
    ("Bello", "Antioquia", 6.3392, -75.5620),
    ("Pasto", "Narino", 1.2136, -77.2811),
    ("Ibague", "Tolima", 4.4389, -75.2387),
    ("Santa Marta", "Magdalena", 11.2408, -74.1990),
    ("Villavicencio", "Meta", 4.1420, -73.6266),
    ("Manizales", "Caldas", 5.0689, -75.5174),
    ("Neiva", "Huila", 2.9275, -75.2819),
    ("Pereira", "Risaralda", 4.8133, -75.6961),
    ("Armenia", "Quindio", 4.5339, -75.6811),
    ("Popayan", "Cauca", 2.4448, -76.6147),
    ("Valledupar", "Cesar", 10.4631, -73.2532),
    ("Sincelejo", "Sucre", 9.3047, -75.3958),
    ("Monteria", "Cordoba", 8.7589, -75.8784),
    ("Tunja", "Boyaca", 5.5353, -73.3620),
]

MUNICIPIOS_NIVEL_NACIONAL = [
    ("Leticia", "Amazonas", -4.2140, -69.9420),
    ("Quibdo", "Choco", 5.6918, -76.6584),
    ("San Andres", "San Andres y Providencia", 12.5847, -81.7006),
    ("Mocoa", "Putumayo", 1.1507, -76.6494),
    ("Florencia", "Caqueta", 1.6176, -75.6085),
    ("Mitu", "Vaupes", 1.2538, -70.2304),
    ("Puerto Inirida", "Guainia", 3.8650, -67.9239),
    ("San Jose del Guaviare", "Guaviare", 2.5730, -72.6459),
    ("Yopal", "Casanare", 5.3000, -72.3900),
    ("Arauca", "Arauca", 7.0847, -70.7573),
]

TODOS_MUNICIPIOS = MUNICIPIOS_BOGOTA + MUNICIPIOS_NACIONALES + MUNICIPIOS_NIVEL_NACIONAL
MUNICIPIOS_MAP = {m[0]: m for m in TODOS_MUNICIPIOS}

# Sistemas de abastecimiento
SISTEMAS = ["Chingaza", "Tibitoc", "Sur"]

# Clasificaciones de riesgo IRCA
RIESGOS = ["Sin riesgo (0-5)", "Bajo riesgo (5-14)", "Riesgo medio (14-28)",
           "Alto riesgo (28-40)", "Inviabile sanitariamente (>40)"]

# Categorias servicio
NIVELES_SERVICIO = ["Continuo", "Intermitente", "Racionado", "Sin servicio"]

# Decisiones de racionamiento
DECISIONES = [
    "Sin restriccion",
    "Racionamiento cada 9 dias",
    "Racionamiento cada 18 dias",
    "Suspension temporal del racionamiento",
    "Campana de ahorro",
    "Restriccion a usuarios > 44 m3 bimestrales",
]

# Paises globales (para nivel global)
PAISES_GLOBALES = [
    ("Colombia", 51265841, 1141748, 0.752),
    ("Mexico", 128900000, 1972550, 0.758),
    ("Brasil", 215313498, 8515767, 0.771),
    ("Argentina", 45810000, 2780400, 0.784),
    ("Peru", 33715473, 1285216, 0.620),
    ("Chile", 19603733, 756102, 0.832),
    ("Ecuador", 18001000, 256369, 0.602),
    ("Venezuela", 28435940, 916445, 0.520),
    ("Bolivia", 12079472, 1098581, 0.530),
    ("Paraguay", 7219638, 406752, 0.580),
    ("Uruguay", 3423108, 176215, 0.830),
    ("India", 1428627663, 3287263, 0.594),
    ("China", 1425671352, 9596961, 0.788),
    ("Nigeria", 223804632, 923768, 0.350),
    ("USA", 339996563, 9833517, 0.860),
    ("Espana", 47519628, 505992, 0.881),
    ("Alemania", 83294633, 357022, 0.920),
    ("Japon", 123294513, 377975, 0.955),
    ("Australia", 26439111, 7692024, 0.875),
    ("Sudafrica", 60414495, 1221037, 0.620),
]


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def seasonal_factor(month):
    """Factor estacional para precipitacion en Bogota (bimodal: abril-mayo, oct-nov picos)."""
    pattern = [0.3, 0.3, 0.7, 1.0, 0.95, 0.5, 0.35, 0.4, 0.6, 0.9, 0.95, 0.4]
    return pattern[month - 1]


def enso_effect(anio):
    """Efecto ENSO simplificado: El Nino reduce precipitacion."""
    enso_map = {
        2019: 0.1,   # neutral/ligeramente Nino
        2020: -0.3,  # Nina
        2021: -0.2,  # Nina debil
        2022: -0.1,  # neutral
        2023: 0.8,   # Nino fuerte
        2024: 1.0,   # Nino muy fuerte (la crisis)
        2025: 0.4,   # Nino debilitandose
    }
    return enso_map.get(anio, 0)


def generar_nivel_almacenamiento(anio, mes, enso):
    """Simula el nivel del embalse Chingaza con patron estacional + efecto ENSO."""
    base = 70.0
    seasonal = 10 * math.sin((mes - 3) * math.pi / 6)
    enso_pull = -25 * max(0, enso)
    crisis_dip = -15 if (anio == 2024 and 4 <= mes <= 9) else 0
    noise = random.gauss(0, 5)
    return round(clamp(base + seasonal + enso_pull + crisis_dip + noise, 5, 98), 1)


def generar_precipitacion(anio, mes, enso):
    """Precipitacion diaria en mm."""
    base = 3.5 * seasonal_factor(mes)
    enso_reduce = -1.5 * max(0, enso)
    noise = max(0, random.gauss(0, 2))
    return round(max(0, base + enso_reduce + noise), 1)


def generar_temperatura(mes):
    """Temperatura promedio diaria en Bogota (escala 10-20 C)."""
    base = 14.0
    seasonal = 2.5 * math.sin((mes - 6) * math.pi / 6)
    noise = random.gauss(0, 1.2)
    return round(clamp(base + seasonal + noise, 8, 26), 1)


def generar_consumo(anio, mes, nivel_almacenamiento):
    """Consumo en m3/s, inversamente relacionado con racionamiento."""
    base = 17.5
    seasonal = 1.5 * math.sin((mes - 1) * math.pi / 6)
    if nivel_almacenamiento < 30:
        reduction = random.uniform(1.5, 4.0)
    elif nivel_almacenamiento < 50:
        reduction = random.uniform(0.5, 2.0)
    else:
        reduction = 0
    noise = random.gauss(0, 0.8)
    return round(clamp(base + seasonal - reduction + noise, 10, 25), 2)


def generar_irca(municipio_es_bogota):
    """Indice de Riesgo de Calidad del Agua."""
    if municipio_es_bogota:
        base = random.uniform(1, 12)
    else:
        base = random.uniform(2, 50)
    noise = random.gauss(0, 3)
    return round(clamp(base + noise, 0, 100), 2)


def clasificar_riesgo(irca):
    if irca <= 5:
        return RIESGOS[0]
    elif irca <= 14:
        return RIESGOS[1]
    elif irca <= 28:
        return RIESGOS[2]
    elif irca <= 40:
        return RIESGOS[3]
    else:
        return RIESGOS[4]


def determinar_decision(anio, mes, nivel):
    """Determina la decision de racionamiento segun el periodo."""
    if anio < 2024:
        return DECISIONES[0]
    if anio == 2024:
        if mes < 4:
            return DECISIONES[0]
        if mes == 4:
            return DECISIONES[1]
        if 5 <= mes <= 6:
            return DECISIONES[1]
        if mes == 7:
            return DECISIONES[2]
        if mes in (8, 9):
            if nivel < 45:
                return DECISIONES[1]
            return DECISIONES[2]
        if mes in (10, 11):
            return DECISIONES[2]
        if mes == 12:
            return DECISIONES[3]
    if anio == 2025:
        if mes == 1:
            return DECISIONES[4] if random.random() < 0.3 else DECISIONES[3]
        if mes == 2:
            return DECISIONES[4]
        if mes == 3:
            return DECISIONES[1] if random.random() < 0.6 else DECISIONES[5]
        if mes >= 4:
            return DECISIONES[3]
    return DECISIONES[0]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ===========================================================================
# GENERACION DE REGISTROS NIVEL REGIONAL/ NACIONAL
# ===========================================================================
print("Generando registros nivel regional y nacional...")
registros = []
fecha_actual = date(ANIO_INICIO, 1, 1)
fecha_fin = date(ANIO_FIN, 12, 31)

while fecha_actual <= fecha_fin:
    anio = fecha_actual.year
    mes = fecha_actual.month
    enso = enso_effect(anio)

    nivel = generar_nivel_almacenamiento(anio, mes, enso)
    precip = generar_precipitacion(anio, mes, enso)
    temp = generar_temperatura(mes)
    consumo = generar_consumo(anio, mes, nivel)
    decision = determinar_decision(anio, mes, nivel)

    # 2 registros por dia en promedio para municipios Bogota/Sabana (granularidad regional)
    municipios_muestra = random.sample(MUNICIPIOS_BOGOTA, k=min(3, len(MUNICIPIOS_BOGOTA)))
    for mun_info in municipios_muestra:
        mun, depto, lat, lon = mun_info
        irca_val = generar_irca(True)
        riesgo = clasificar_riesgo(irca_val)
        servicio = random.choice(NIVELES_SERVICIO) if decision != DECISIONES[0] else "Continuo"
        sistema = random.choice(SISTEMAS)
        nivel_servicio_pct = round(random.uniform(0, 100), 1)

        registros.append({
            "fecha": fecha_actual.isoformat(),
            "anio": anio,
            "mes": mes,
            "periodo": f"{anio}-T{(mes - 1) // 3 + 1}",
            "sistema_abastecimiento": sistema,
            "nivel_almacenamiento_pct": nivel,
            "afluencias_m3s": round(random.uniform(5, 25) + enso * -3, 2),
            "precipitacion_mm": precip,
            "temperatura_c": temp,
            "consumo_m3s": consumo,
            "irca": irca_val,
            "clasificacion_riesgo": riesgo,
            "municipio": mun,
            "departamento": depto,
            "latitud": round(lat + random.gauss(0, 0.01), 4),
            "longitud": round(lon + random.gauss(0, 0.01), 4),
            "cobertura_acueducto_pct": round(clamp(random.gauss(95, 3), 70, 100), 1),
            "nivel_servicio": servicio,
            "tipo_region": "Regional",
            "decision_racionamiento": decision,
        })

    # 1 registro por dia para 2 municipios nacionales (granularidad nacional)
    nacionales = random.sample(MUNICIPIOS_NACIONALES, k=2)
    for mun_info in nacionales:
        mun, depto, lat, lon = mun_info
        irca_val = generar_irca(False)
        riesgo = clasificar_riesgo(irca_val)
        sistema = "N/A"
        servicio = random.choice(["Continuo", "Intermitente"])

        registros.append({
            "fecha": fecha_actual.isoformat(),
            "anio": anio,
            "mes": mes,
            "periodo": f"{anio}-T{(mes - 1) // 3 + 1}",
            "sistema_abastecimiento": sistema,
            "nivel_almacenamiento_pct": round(random.uniform(20, 95), 1),
            "afluencias_m3s": round(random.uniform(3, 30), 2),
            "precipitacion_mm": round(max(0, random.gauss(4, 3)), 1),
            "temperatura_c": round(clamp(random.gauss(22, 5), 10, 38), 1),
            "consumo_m3s": round(random.uniform(2, 15), 2),
            "irca": irca_val,
            "clasificacion_riesgo": riesgo,
            "municipio": mun,
            "departamento": depto,
            "latitud": round(lat + random.gauss(0, 0.02), 4),
            "longitud": round(lon + random.gauss(0, 0.02), 4),
            "cobertura_acueducto_pct": round(clamp(random.gauss(78, 12), 30, 100), 1),
            "nivel_servicio": servicio,
            "tipo_region": "Nacional",
            "decision_racionamiento": "Sin restriccion",
        })

    fecha_actual += timedelta(days=1)

print(f"  Registros regionales/nacionales: {len(registros)}")

# ===========================================================================
# REGISTROS NIVEL GLOBAL (anuales, por pais)
# ===========================================================================
print("Generando registros nivel global...")
registros_globales = []
for anio in range(ANIO_INICIO, ANIO_FIN + 1):
    for pais_info in PAISES_GLOBALES:
        pais, poblacion, superficie, cobertura_base = pais_info
        cobertura = round(clamp(cobertura_base + random.gauss(0, 0.02), 0.1, 0.99), 3)
        acceso_seguro = round(cobertura * 100, 1)
        sin_acceso = round((1 - cobertura) * poblacion / 1e6, 2)
        estres_hidrico = round(clamp(random.gauss(0.4, 0.2), 0, 1), 3)

        registros_globales.append({
            "fecha": f"{anio}-06-30",
            "anio": anio,
            "mes": 6,
            "periodo": f"{anio}",
            "sistema_abastecimiento": "N/A",
            "nivel_almacenamiento_pct": "",
            "afluencias_m3s": "",
            "precipitacion_mm": "",
            "temperatura_c": "",
            "consumo_m3s": "",
            "irca": "",
            "clasificacion_riesgo": "",
            "municipio": pais,
            "departamento": "",
            "latitud": "",
            "longitud": "",
            "cobertura_acueducto_pct": acceso_seguro,
            "nivel_servicio": "",
            "tipo_region": "Global",
            "decision_racionamiento": "",
        })

print(f"  Registros globales: {len(registros_globales)}")
registros.extend(registros_globales)

# ===========================================================================
# INYECCION DE PROBLEMAS DE CALIDAD (para diagnostico realista)
# ===========================================================================
print("Inyectando problemas de calidad de datos...")
random.shuffle(registros)

# Valores faltantes (~5% en precipitacion, ~3% en temperatura, ~2% en irca)
for i, reg in enumerate(registros):
    if random.random() < 0.05:
        registros[i]["precipitacion_mm"] = ""
    if random.random() < 0.03:
        registros[i]["temperatura_c"] = ""
    if random.random() < 0.02:
        registros[i]["irca"] = ""

# Valores fuera de rango (~1%)
for i, reg in enumerate(registros):
    if random.random() < 0.01:
        registros[i]["nivel_almacenamiento_pct"] = round(random.uniform(101, 130), 1)
    if random.random() < 0.008:
        registros[i]["irca"] = round(random.uniform(-5, -0.1), 2)

# Duplicados exactos (~0.5%)
num_duplicados = int(len(registros) * 0.005)
for _ in range(num_duplicados):
    reg = random.choice(registros[:len(registros) - num_duplicados])
    registros.append(dict(reg))

# Inconsistencias de formato en municipio (~1.5%)
for i, reg in enumerate(registros):
    if random.random() < 0.015 and reg["municipio"] in MUNICIPIOS_MAP:
        original = reg["municipio"]
        variaciones = [original.upper(), original.lower(), original.replace("a", "@"),
                       original + " ", " " + original]
        registros[i]["municipio"] = random.choice(variaciones)

# Formato de fecha inconsistente (~1%)
for i, reg in enumerate(registros):
    if random.random() < 0.01:
        partes = reg["fecha"].split("-")
        if len(partes) == 3:
            formatos = [f"{partes[2]}/{partes[1]}/{partes[0]}",
                        f"{partes[1]}-{partes[2]}-{partes[0]}",
                        f"{partes[0]}/{partes[1]}/{partes[2]}"]
            registros[i]["fecha"] = random.choice(formatos)

print(f"  Total registros finales (con duplicados): {len(registros)}")

# ===========================================================================
# ESCRITURA DEL CSV
# ===========================================================================
print(f"Guardando dataset en {ARCHIVO_SALIDA}...")
columnas = [
    "fecha", "anio", "mes", "periodo", "sistema_abastecimiento",
    "nivel_almacenamiento_pct", "afluencias_m3s", "precipitacion_mm",
    "temperatura_c", "consumo_m3s", "irca", "clasificacion_riesgo",
    "municipio", "departamento", "latitud", "longitud",
    "cobertura_acueducto_pct", "nivel_servicio", "tipo_region",
    "decision_racionamiento"
]

with open(ARCHIVO_SALIDA, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columnas)
    writer.writeheader()
    for reg in registros:
        writer.writerow(reg)

print(f"Dataset generado: {len(registros)} registros, {len(columnas)} variables")
print("Columnas:", ", ".join(columnas))
