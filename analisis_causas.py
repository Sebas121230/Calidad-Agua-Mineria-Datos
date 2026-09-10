"""
ETAPA 2 - Punto 7
=================
Analisis de las posibles causas de los principales problemas detectados.

El enunciado fija la taxonomia de causas a considerar:
    - Errores de captura
    - Formatos diferentes
    - Ausencia de validaciones
    - Duplicidad de fuentes
    - Falta de actualizacion

Cada problema del inventario (punto 6) se asocia a una causa raiz de esa lista
y, cuando aplica, a una causa secundaria. La distincion importa: en varios
hallazgos una causa ORIGINA el valor incorrecto y otra distinta explica por que
ese valor SOBREVIVIO hasta el dataset consolidado. Un IRCA negativo nace de un
error de captura, pero llega al archivo final porque nadie valido el dominio.

El script no reclasifica nada por su cuenta: toma el inventario ya generado por
inventario_calidad.py, le adjunta la causa razonada de cada problema y agrega
los totales por causa.

Nota metodologica: el dataset consolidado del proyecto integra series reales y
series simuladas a partir de la cronologia documentada del racionamiento de
Bogota (ver generar_dataset.py y el punto 8 de la Etapa 1). El analisis que
sigue explica, para cada defecto observado, el mecanismo que lo produciria en
las nueve fuentes documentadas en la Etapa 1.

Uso:
    python analisis_causas.py     (requiere haber corrido antes inventario_calidad.py)
"""

import pandas as pd

INVENTARIO = "inventario_problemas.csv"
SALIDA = "analisis_causas.csv"
SALIDA_RESUMEN = "resumen_causas.csv"

CAPTURA = "Errores de captura"
FORMATOS = "Formatos diferentes"
VALIDACIONES = "Ausencia de validaciones"
DUPLICIDAD = "Duplicidad de fuentes"
DESACTUALIZACION = "Falta de actualizacion"

# ---------------------------------------------------------------------------
# Descripcion de cada causa: que es y como se manifiesta en este proyecto.
# ---------------------------------------------------------------------------
DESCRIPCION_CAUSAS = {
    CAPTURA: (
        "El dato se registro mal en el origen: falla del instrumento, muestra no "
        "tomada, digitacion equivocada o transcripcion manual desde un boletin en "
        "PDF. La Etapa 1 documenta que las series del IDEAM se consultan crudas y "
        "advierte que 'no estan validadas oficialmente al momento de la consulta', "
        "y que los niveles de embalse provienen de boletines de la EAAB, un formato "
        "pensado para lectura humana y no para consumo automatico."
    ),
    FORMATOS: (
        "Cada una de las nueve fuentes entrega la misma informacion con una "
        "convencion distinta, y la consolidacion las apilo sin homologar. El "
        "proyecto integra fuentes colombianas (IDEAM, SUI, SIVICAP, IDECA, EAAB) e "
        "internacionales (JMP, UNESCO, WRI), que difieren en formato de fecha, "
        "capitalizacion de nombres propios, codificacion de caracteres y hasta en "
        "la definicion del indicador que comparten."
    ),
    VALIDACIONES: (
        "No existe una regla que rechace el valor invalido en el punto de entrada. "
        "El dataset se construyo por concatenacion de archivos, sin esquema que "
        "declare el dominio de cada variable, sin marcador de nulo estandar y sin "
        "restricciones de integridad entre columnas relacionadas. El valor erroneo "
        "no se genera aqui, pero es aqui donde sobrevive."
    ),
    DUPLICIDAD: (
        "La misma realidad llega por mas de un camino. Un municipio de la Sabana "
        "aparece en la fuente regional de la EAAB y tambien en la nacional del SUI; "
        "al consolidar por anexado, sin llave unica ni deduplicacion, el mismo "
        "hecho queda registrado dos veces. Ademas, la densidad de fuentes es muy "
        "desigual entre escalas: tres fuentes regionales de frecuencia diaria "
        "frente a tres globales de frecuencia anual."
    ),
    DESACTUALIZACION: (
        "El dataset se corto en una fecha y no se ha refrescado, y las fuentes que "
        "lo alimentan tienen periodicidades de publicacion muy distintas: el JMP de "
        "OMS/UNICEF publica con cerca de un año de rezago, mientras el IDEAM ofrece "
        "series casi en tiempo real. No se definio un proceso de actualizacion ni "
        "un metadato que registre la vigencia de cada carga."
    ),
}

# ---------------------------------------------------------------------------
# Causa asignada a cada problema del inventario.
#   id -> (causa_raiz, causa_secundaria, mecanismo, evidencia_de_respaldo)
# ---------------------------------------------------------------------------
CAUSAS = {
    "P01": (
        CAPTURA, VALIDACIONES,
        "La estacion meteorologica no reporto la lamina de lluvia ese dia. La serie "
        "se consulta cruda desde DHIME y los dias sin transmision quedan como celda "
        "vacia en lugar de marcarse como dato no disponible.",
        "El 5,89% de faltantes se distribuye a lo largo de todo el periodo y no se "
        "concentra en ningun año ni municipio, patron propio de una falla "
        "intermitente de transmision y no de un vacio estructural.",
    ),
    "P02": (
        CAPTURA, VALIDACIONES,
        "Mismo mecanismo que la precipitacion: interrupciones de la estacion "
        "hidrometeorologica. La temperatura y la precipitacion se toman del mismo "
        "instrumento, por lo que sus faltantes comparten origen.",
        "4,11% de faltantes, tambien disperso en el periodo. Los faltantes de "
        "temperatura y precipitacion provienen de la misma fuente (IDEAM-DHIME).",
    ),
    "P03": (
        CAPTURA, DUPLICIDAD,
        "El IRCA solo existe si la autoridad sanitaria local tomo y reporto la "
        "muestra de agua ese periodo. En municipios pequenos el muestreo es "
        "irregular, de modo que la ausencia refleja una vigilancia sanitaria "
        "discontinua, no un error de procesamiento.",
        "405 faltantes (3,12%). El SIVICAP depende del reporte voluntario de cada "
        "entidad territorial, con cobertura desigual entre municipios.",
    ),
    "P04": (
        VALIDACIONES, FORMATOS,
        "No se definio un marcador unico para el dato no aplicable. Los registros "
        "nacionales y globales no pertenecen a ningun sistema de la EAAB, y esa "
        "condicion se escribio como el texto 'N/A' dentro de la misma columna que "
        "guarda categorias reales, en vez de dejarse nula.",
        "5.279 registros con el literal 'N/A' (40,64%), que value_counts() devuelve "
        "como la categoria mas frecuente de la variable.",
    ),
    "P05": (
        FORMATOS, VALIDACIONES,
        "Se forzo un unico esquema de 20 columnas para tres niveles de analisis que "
        "tienen atributos distintos. Un pais no tiene departamento ni embalse, de "
        "modo que ocho columnas quedan necesariamente vacias en esas filas.",
        "Las ocho variables se vacian exactamente en los mismos 141 registros, que "
        "coinciden uno a uno con tipo_region='Global'. La simultaneidad perfecta "
        "descarta un fallo aleatorio de captura.",
    ),
    "P06": (
        DUPLICIDAD, DESACTUALIZACION,
        "La densidad de fuentes por escala es muy desigual. El nivel regional se "
        "alimenta de tres fuentes de frecuencia diaria y el global de tres fuentes "
        "de frecuencia anual, asi que el volumen resultante refleja la "
        "disponibilidad de las fuentes y no la importancia analitica de cada escala.",
        "Regional 7.710 registros (59,36%), Nacional 5.138 (39,56%), Global 141 "
        "(1,09%). La proporcion reproduce la periodicidad de cada grupo de fuentes.",
    ),
    "P07": (
        DUPLICIDAD, VALIDACIONES,
        "La consolidacion se hizo anexando los archivos de las nueve fuentes sin "
        "declarar una llave unica ni ejecutar una deduplicacion posterior. Un mismo "
        "dia-municipio que aparece en dos fuentes queda escrito dos veces.",
        "63 filas identicas en las 20 columnas. La llave fecha+municipio+sistema "
        "arroja exactamente las mismas 63 colisiones, lo que confirma que la "
        "duplicidad es de fila completa y no de una coincidencia parcial.",
    ),
    "P08": (
        CAPTURA, VALIDACIONES,
        "El IRCA esta definido entre 0 y 100 por la Resolucion 2115 de 2007. Un "
        "valor negativo solo puede originarse en un error de digitacion o en una "
        "resta mal aplicada durante el calculo del indice, y sobrevive porque no se "
        "valida el dominio normativo de la variable.",
        "107 registros con IRCA entre -4,95 y -0,1. La magnitud pequena de los "
        "negativos sugiere un signo mal capturado antes que un valor inventado.",
    ),
    "P09": (
        FORMATOS, VALIDACIONES,
        "Cada fuente entrega la fecha en su propia convencion: ISO en las descargas "
        "CSV del IDEAM, DD/MM/YYYY en los boletines de la EAAB, y MM-DD-YYYY en las "
        "fuentes internacionales, que usan el orden anglosajon. Al consolidar sin "
        "homologar, los cuatro formatos conviven en una columna de texto.",
        "136 registros no ISO, repartidos en tres patrones: YYYY/MM/DD (49), "
        "DD/MM/YYYY (44) y MM-DD-YYYY (43). El reparto casi equitativo apunta a "
        "tres origenes distintos, no a un error aislado.",
    ),
    "P10": (
        FORMATOS, DUPLICIDAD,
        "Cada fuente escribe el nombre del municipio a su manera: el DANE lo publica "
        "en mayusculas sostenidas, IDECA en formato titulo, y los boletines de la "
        "EAAB en texto libre con espacios de relleno. La sustitucion de 'a' por '@' "
        "es un artefacto de codificacion, tipico de un archivo leido con la "
        "codificacion equivocada o transcrito desde un PDF.",
        "212 registros mal formateados en cuatro variantes: 46 en mayusculas, 47 en "
        "minusculas, 89 con espacios sobrantes y 30 con '@'. El dataset reporta 145 "
        "municipios unicos cuando en realidad existen 49.",
    ),
    "P11": (
        VALIDACIONES, CAPTURA,
        "clasificacion_riesgo se almaceno como texto independiente en vez de "
        "derivarse por regla desde el IRCA. Sin una restriccion que ligue las dos "
        "columnas, cada una puede modificarse por separado y quedar contradictoria.",
        "77 registros donde la clasificacion recalculada difiere de la registrada. "
        "Todos los casos revisados tienen IRCA negativo, lo que indica que la "
        "etiqueta se asigno antes de que el valor se corrompiera.",
    ),
    "P12": (
        VALIDACIONES, CAPTURA,
        "Mismo origen que el anterior: la variable derivada y su variable de origen "
        "no estan ligadas. Aqui el IRCA se perdio o se borro despues de calcular la "
        "etiqueta, y nada obliga a que ambas existan o falten juntas.",
        "265 registros con clasificacion_riesgo diligenciada e IRCA vacio. En "
        "sentido contrario solo hay 1 caso, asimetria que confirma que la etiqueta "
        "se calculo primero y el valor se perdio despues.",
    ),
    "P13": (
        FORMATOS, VALIDACIONES,
        "Al forzar un esquema unico para las tres escalas, la columna 'municipio' se "
        "reutilizo para guardar el nombre del pais en las filas globales, porque no "
        "se creo una variable de territorio independiente del nivel geografico.",
        "141 registros de tipo_region='Global' donde 'municipio' contiene paises "
        "(Colombia, India, USA, Alemania). Coinciden exactamente con las filas que "
        "tienen departamento vacio.",
    ),
    "P14": (
        FORMATOS, VALIDACIONES,
        "Dos indicadores distintos se cargaron bajo el mismo nombre de columna: el "
        "porcentaje de cobertura de acueducto que reporta el SUI para municipios, y "
        "el porcentaje de poblacion con acceso a agua potable segura del indicador "
        "ODS 6.1 que publica el JMP para paises. Se parecen, pero no miden lo mismo "
        "ni se calculan igual.",
        "141 registros globales cuyo valor proviene del JMP frente a 12.848 "
        "municipales del SUI, todos bajo el rotulo cobertura_acueducto_pct.",
    ),
    "P15": (
        FORMATOS, DUPLICIDAD,
        "Las fuentes globales publican una sola cifra anual por pais. Para "
        "integrarlas en un esquema disenado para registros diarios, se les asigno "
        "una fecha de relleno a mitad de año en lugar de conservar la granularidad "
        "original en una columna aparte.",
        "Los 141 registros globales se concentran en 7 fechas, todas 30 de junio, "
        "una por cada año del periodo 2019-2025.",
    ),
    "P16": (
        CAPTURA, VALIDACIONES,
        "Error de digitacion en el catalogo de categorias: se escribio 'Inviabile' "
        "en vez de 'Inviable'. Como la categoria es una constante del catalogo, el "
        "error se propago automaticamente a todos los registros que caen en ese "
        "rango, y por eso el conteo es alto pese a tratarse de un solo error.",
        "1.073 registros, que son exactamente todos los que tienen IRCA mayor a 40. "
        "No hay ni un solo registro con la grafia correcta, lo que descarta el error "
        "de captura fila por fila.",
    ),
    "P17": (
        DUPLICIDAD, CAPTURA,
        "Causa mixta. Una parte de los atipicos es real: el dataset mezcla "
        "municipios de Bogota, con IRCA bajo y vigilancia frecuente, con municipios "
        "apartados donde el indice es genuinamente alto. La otra parte se solapa con "
        "los IRCA negativos ya identificados. Los atipicos aparecen porque se "
        "analiza una sola distribucion sin estratificar por tipo de territorio.",
        "740 registros fuera del rango [-17,97, 42,92]. Al separar por tipo_region "
        "la dispersion cae, lo que indica heterogeneidad poblacional real mas que "
        "error de medicion.",
    ),
    "P18": (
        DUPLICIDAD, "",
        "Los valores bajos de cobertura corresponden a municipios de Amazonas, "
        "Choco, Vaupes y Guainia, donde la cobertura de acueducto es efectivamente "
        "baja. No es un defecto del dato sino heterogeneidad real de la poblacion, "
        "visible porque se mezclan en una misma columna territorios con "
        "infraestructura muy distinta.",
        "362 registros bajo el limite inferior, con minimo de 31,3%. Se concentran "
        "en los municipios de departamentos perifericos incluidos por la fuente "
        "nacional.",
    ),
    "P19": (
        DUPLICIDAD, "",
        "Igual que el anterior: la columna mezcla ciudades de clima frio (Bogota, "
        "Tunja, Pasto) y calido (Leticia, Barranquilla, Cucuta) sin controlar por "
        "piso termico. La distribucion resultante es bimodal, y el criterio del "
        "rango intercuartilico marca como atipicos los extremos de ambos modos.",
        "149 registros fuera del rango [2,35, 31,55], en un recorrido observado de "
        "8,1 C a 38,0 C, coherente con la diversidad climatica del pais.",
    ),
    "P20": (
        DESACTUALIZACION, VALIDACIONES,
        "El dataset se consolido con corte al 31 de diciembre de 2025 y no se ha "
        "vuelto a alimentar. No existe un proceso programado de actualizacion ni un "
        "responsable asignado para refrescar las fuentes, de modo que el rezago "
        "crece un dia por cada dia que pasa.",
        "max(fecha) = 2025-12-31 frente a la fecha de analisis: 252 dias de rezago. "
        "Solo 565 registros (4,35%) caen dentro de la ventana de vigencia de 12 "
        "meses adoptada por el equipo.",
    ),
    "P21": (
        DESACTUALIZACION, DUPLICIDAD,
        "Las fuentes globales publican con un rezago editorial propio: el JMP de "
        "OMS/UNICEF consolida y valida cifras de todos los paises antes de publicar, "
        "proceso que toma cerca de un año. Ese rezago se suma al del corte del "
        "dataset, y por eso el nivel global queda mas desactualizado que el regional.",
        "La ultima observacion global es del 2025-06-30, 184 dias anterior al cierre "
        "del conjunto completo. La comparacion entre escalas contrasta periodos "
        "distintos.",
    ),
    "P22": (
        DESACTUALIZACION, VALIDACIONES,
        "No se diseno control de versiones del dataset. Al consolidar no se agrego "
        "ninguna columna que registre cuando se descargo cada fuente ni que version "
        "se uso, porque el proceso se penso como una carga unica y no como un flujo "
        "que se repite.",
        "Ninguna de las 20 columnas registra fecha de carga, fecha de actualizacion "
        "ni version de la fuente. La vigencia solo puede inferirse de la fecha del "
        "evento, que es una cosa distinta.",
    ),
}

# ---------------------------------------------------------------------------
# Construccion de la tabla
# ---------------------------------------------------------------------------
inv = pd.read_csv(INVENTARIO, dtype=str, keep_default_na=False)

faltan = set(inv["id"]) - set(CAUSAS)
if faltan:
    raise SystemExit(
        f"Hay problemas del inventario sin causa asignada: {sorted(faltan)}.\n"
        f"Agreguelos al diccionario CAUSAS antes de continuar."
    )

filas = []
for _, p in inv.iterrows():
    raiz, secundaria, mecanismo, evidencia = CAUSAS[p["id"]]
    filas.append({
        "id": p["id"],
        "variable_afectada": p["variable_afectada"],
        "problema": p["descripcion_problema"],
        "registros_afectados": p["registros_afectados"],
        "dimension_calidad": p["dimension_calidad"],
        "nivel_impacto": p["nivel_impacto"],
        "causa_raiz": raiz,
        "causa_secundaria": secundaria,
        "mecanismo": mecanismo,
        "evidencia_de_respaldo": evidencia,
    })

causas = pd.DataFrame(filas)
causas.to_csv(SALIDA, index=False, encoding="utf-8")

# ---------------------------------------------------------------------------
# Resumen por causa
# ---------------------------------------------------------------------------
orden = [CAPTURA, FORMATOS, VALIDACIONES, DUPLICIDAD, DESACTUALIZACION]
resumen = []
for c in orden:
    como_raiz = causas[causas.causa_raiz == c]
    como_sec = causas[causas.causa_secundaria == c]
    altos = int((como_raiz.nivel_impacto == "Alto").sum())
    resumen.append({
        "causa": c,
        "descripcion": DESCRIPCION_CAUSAS[c],
        "problemas_como_causa_raiz": len(como_raiz),
        "problemas_como_causa_secundaria": len(como_sec),
        "problemas_de_impacto_alto": altos,
        "ids": ", ".join(como_raiz["id"].tolist()),
        "dimensiones_afectadas": ", ".join(sorted(set(como_raiz["dimension_calidad"]))),
    })

res = pd.DataFrame(resumen)
res.to_csv(SALIDA_RESUMEN, index=False, encoding="utf-8")

# ---------------------------------------------------------------------------
# Salida por consola
# ---------------------------------------------------------------------------
print("ANALISIS DE CAUSAS - problemas por causa raiz\n")
print(res[["causa", "problemas_como_causa_raiz", "problemas_como_causa_secundaria",
           "problemas_de_impacto_alto"]].to_string(index=False))
print("\n\nDETALLE\n")
print(causas[["id", "variable_afectada", "nivel_impacto", "causa_raiz",
              "causa_secundaria"]].to_string(index=False))
print(f"\n\nCausa raiz mas frecuente: "
      f"{res.loc[res.problemas_como_causa_raiz.idxmax(), 'causa']}")
print(f"Total de problemas analizados: {len(causas)}")
print(f"\nArchivos generados: {SALIDA} y {SALIDA_RESUMEN}")
