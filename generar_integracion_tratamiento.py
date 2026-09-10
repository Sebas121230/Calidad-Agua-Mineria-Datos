# -*- coding: utf-8 -*-
"""
Genera los CSV de soporte para:
  - Punto 8: Integracion y homologacion de los datos
  - Punto 9: Plan de tratamiento (solo planeacion, no se ejecuta el ETL)

Se basa en las 9 fuentes documentadas en la Etapa 1 y en el inventario /
analisis de causas ya vigentes (post-commit "Ajustes al inventario y al
analisis de causas").
"""
import csv

# ===========================================================================
# PUNTO 8 - INTEGRACION Y HOMOLOGACION
# ===========================================================================

diferencias = [
    ("Formato de fecha",
     "IDEAM entrega fecha diaria ISO; JMP/UNESCO entregan solo el ano; los "
     "boletines de la EAAB usan la fecha de publicacion del PDF y no la de "
     "la medicion."),
    ("Granularidad temporal",
     "Diaria (IDEAM, EAAB embalses) frente a mensual (EAAB IRCA) frente a "
     "anual (JMP, UNESCO, World Bank)."),
    ("Granularidad espacial",
     "Estacion puntual (IDEAM) frente a municipio (SIVICAP) frente a pais "
     "(JMP / World Bank)."),
    ("Nomenclatura de campos",
     "\"% acceso a agua gestionada de forma segura\" (JMP) frente a "
     "\"cobertura de acueducto\" (Superservicios): mismo concepto general, "
     "nombre de campo distinto en cada fuente."),
    ("Codificacion de categorias",
     "Nombres de municipio sin normalizar entre IDECA y SIVICAP: mayusculas, "
     "tildes, espacios sobrantes y caracteres especiales."),
    ("Definicion del indicador",
     "El JMP mide acceso seguro (incluye tratamiento en el hogar); "
     "Superservicios mide cobertura de red (solo conexion fisica). Son "
     "conceptos distintos aunque terminaron homologados en una sola "
     "columna."),
    ("Marcador de ausencia",
     "Los registros nacionales y globales no tienen sistema de "
     "abastecimiento EAAB, y ese vacio se represento con el literal 'N/A' "
     "en vez de una celda vacia estandar (problema P04 del inventario)."),
]

homologacion = [
    ("fecha", "IDEAM, EAAB, SIVICAP, JMP/UNESCO/World Bank",
     "Todas las fechas se llevan a formato ISO 8601 (AAAA-MM-DD). Las "
     "fuentes anuales globales se anclan al 30 de junio de cada ano como "
     "fecha representativa.", ""),
    ("anio, mes, periodo", "Derivadas de fecha",
     "Se calculan una sola vez a partir de la fecha ya homologada, para no "
     "volver a tener formatos distintos por fuente.", ""),
    ("municipio, departamento", "IDECA, SIVICAP, DANE",
     "Se usa el nombre oficial DANE como catalogo maestro; los alias y "
     "variaciones de escritura de las demas fuentes se mapean contra ese "
     "catalogo.", "Ver problema P10 (variantes de escritura aun presentes)."),
    ("latitud, longitud", "IDECA, IDEAM",
     "Coordenadas en grados decimales (WGS84) para todas las fuentes.", ""),
    ("sistema_abastecimiento", "EAAB boletines",
     "Solo aplica a municipios de la Sabana cubiertos por la EAAB; para el "
     "resto se deberia declarar explicitamente 'Fuera de cobertura EAAB' en "
     "vez de dejarlo ambiguo.",
     "Homologado con el literal 'N/A' en vez de un nulo estandar (P04)."),
    ("nivel_almacenamiento_pct, afluencias_m3s", "EAAB boletines, IDEAM",
     "Ambas ya vienen en las mismas unidades de origen (% y m3/s); solo "
     "requieren alineacion temporal diaria.", ""),
    ("precipitacion_mm, temperatura_c", "IDEAM DHIME",
     "Unidad ya estandarizada por el IDEAM entre estaciones; se homologa "
     "solo el formato de fecha y el identificador estacion -> municipio.", ""),
    ("consumo_m3s", "EAAB / Superservicios",
     "Ambas fuentes reportan en m3/s; se homologa la periodicidad (diaria "
     "vs. bimestral) llevando todo a un agregado diario.", ""),
    ("irca, clasificacion_riesgo", "EAAB IRCA, SIVICAP",
     "Se usa la formula de la Res. 2115/2007 como referencia; cuando "
     "SIVICAP y EAAB reportan el mismo municipio-mes, se prioriza el dato "
     "de la EAAB por ser la autoridad del sistema de estudio.",
     "Persisten incoherencias irca/clasificacion (P11, P12)."),
    ("cobertura_acueducto_pct", "Superservicios, JMP",
     "Homologacion con perdida de matiz: se unifican dos indicadores que "
     "miden cosas distintas (cobertura de red vs. acceso seguro).",
     "Documentado como limitacion, no como una unificacion libre de costo "
     "(P14)."),
    ("nivel_servicio, decision_racionamiento", "EAAB boletines",
     "Se homologa el texto libre de los boletines de prensa a un catalogo "
     "cerrado de 4 y 6 categorias respectivamente.", ""),
    ("tipo_region", "Campo agregado en la integracion",
     "No viene de ninguna fuente; se crea para distinguir de donde vino "
     "cada fila (Global / Nacional / Regional).",
     "El nivel Global queda con muy poca representacion, 1.09% (P05, P06)."),
]

with open("integracion_diferencias.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["tipo_diferencia", "ejemplo"])
    w.writerows(diferencias)

with open("integracion_homologacion.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["variable_final", "fuentes_origen", "regla_homologacion", "limitacion"])
    w.writerows(homologacion)

print(f"integracion_diferencias.csv: {len(diferencias)} filas")
print(f"integracion_homologacion.csv: {len(homologacion)} filas")

# ===========================================================================
# PUNTO 9 - PLAN DE TRATAMIENTO (solo planeacion, no se ejecuta)
# ===========================================================================

tratamiento = [
    ("P01", "precipitacion_mm", "Nulos: 765 registros (5.89%)",
     "Imputacion por mediana estacional (mismo mes, misma region) en vez de "
     "un valor global fijo.",
     "Tratamiento de valores nulos", "Completitud"),
    ("P02", "temperatura_c", "Nulos: 534 registros (4.11%)",
     "Imputacion por mediana mensual de la estacion mas cercana.",
     "Tratamiento de valores nulos", "Completitud"),
    ("P03", "irca", "Nulos: 405 registros (3.12%)",
     "No imputar: al ser la variable objetivo, los registros sin IRCA se "
     "excluyen de los analisis que dependen de ella y se marcan con una "
     "bandera irca_reportado = No, en vez de inventar un valor de riesgo.",
     "Tratamiento de valores nulos (por exclusion)", "Completitud, Exactitud"),
    ("P04", "sistema_abastecimiento", "Literal 'N/A': 5279 registros (40.64%)",
     "Reemplazar el texto 'N/A' por un valor nulo estandar, y agregar una "
     "categoria explicita 'Fuera de cobertura EAAB' para no perder el "
     "significado original.",
     "Estandarizacion de textos / tratamiento de nulos", "Completitud, Consistencia"),
    ("P07", "Registro completo (20 variables)", "Duplicados: 63 registros (0.49%)",
     "Eliminacion de duplicados exactos, usando la llave candidata fecha + "
     "municipio + sistema_abastecimiento para confirmarlos antes de "
     "borrar.",
     "Eliminacion de duplicados", "Unicidad"),
    ("P08", "irca", "Valores negativos: 107 registros (0.82%)",
     "Validacion de rango contra el dominio normativo (Res. 2115/2007, "
     "escala 0-100); los valores fuera de rango se marcan como invalidos "
     "y se excluyen del analisis en vez de recortarlos artificialmente.",
     "Validacion de rangos", "Validez"),
    ("P09", "fecha", "Formato inconsistente: 136 registros (1.05%)",
     "Parseo de los formatos alternos detectados (DD/MM/AAAA, MM-DD-AAAA, "
     "AAAA/MM/DD) y conversion a ISO 8601.",
     "Estandarizacion de fechas", "Consistencia"),
    ("P10", "municipio", "Formato inconsistente: 212 registros (1.63%)",
     "Normalizacion de texto (mayusculas/minusculas consistentes, remocion "
     "de espacios y caracteres no validos) y homologacion contra el "
     "catalogo oficial DANE.",
     "Estandarizacion de textos / homologacion de categorias", "Consistencia, Unicidad"),
    ("P11", "irca / clasificacion_riesgo", "Incoherencia: 77 registros (0.59%)",
     "Recalcular siempre clasificacion_riesgo a partir del irca numerico "
     "segun la Res. 2115/2007, en vez de mantenerlo como un campo "
     "independiente que se puede desincronizar.",
     "Correccion de tipos de datos / regla derivada", "Consistencia"),
    ("P12", "clasificacion_riesgo", "Sin irca de respaldo: 265 registros (2.04%)",
     "Igual que P11: la clasificacion deja de guardarse como texto libre y "
     "se deriva siempre del IRCA; si no hay IRCA, tampoco hay "
     "clasificacion.",
     "Correccion de tipos de datos / regla derivada", "Consistencia"),
    ("P16", "clasificacion_riesgo", "Error ortografico: 1073 registros (8.26%)",
     "Correccion de la categoria mal escrita ('Inviabile' -> 'Inviable') "
     "en el catalogo cerrado de valores validos.",
     "Homologacion de categorias", "Exactitud"),
    ("P17, P18, P19", "irca, cobertura_acueducto_pct, temperatura_c",
     "Atipicos por rango intercuartilico (Tukey)",
     "Marcar (no eliminar) los atipicos, y decidir caso por caso si "
     "corresponden a eventos reales (crisis de 2024, municipios apartados, "
     "diversidad climatica del pais) o a errores, antes de cualquier "
     "tratamiento. Estratificar por tipo_region y piso termico antes de "
     "calcular estadisticos.",
     "Tratamiento justificado de valores atipicos", "Exactitud"),
    ("P20, P21", "fecha",
     "Actualidad: 252 dias de rezago general, 436 en el nivel global",
     "Definir un proceso de actualizacion periodica alineado con la fuente "
     "mas lenta relevante para cada uso (mensual para EAAB/SIVICAP, anual "
     "para JMP).",
     "Proceso de actualizacion (planeado, no una correccion puntual)", "Actualidad"),
    ("P22", "Metadato ausente", "Sin fecha_carga ni fuente_version en 20 columnas",
     "Incorporar columnas fecha_carga y fuente_version en el esquema, para "
     "poder auditar la vigencia de cada fuente de forma independiente.",
     "Correccion de tipos de datos / diseno de esquema", "Actualidad"),
    ("P05, P06, P13, P14, P15", "Registros de tipo_region='Global'",
     "Vacios estructurales, alcance desigual, mezcla de pais/municipio, "
     "definicion distinta de cobertura_acueducto_pct y fecha ficticia",
     "No se homologan por correccion de dato: son consecuencia del diseno "
     "de integracion (punto 8). El tratamiento planeado es documental: "
     "separar tipo_region='Global' en su propio esquema en vez de forzarlo "
     "dentro del esquema diario municipal.",
     "Rediseno de esquema (fuera de una correccion puntual)", "Completitud, Consistencia"),
]

with open("plan_tratamiento.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "variable_o_campo", "problema_resumen", "accion_planeada",
                "tipo_accion", "dimension_que_mejora"])
    w.writerows(tratamiento)

print(f"plan_tratamiento.csv: {len(tratamiento)} filas")
