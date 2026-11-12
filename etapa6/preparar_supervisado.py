# -*- coding: utf-8 -*-
"""
Etapa 6 - Conocimiento oculto. Preparación de los datos para los modelos supervisados.
Responsable: John Sebastián Rodríguez Domínguez.

Pregunta de predicción:
    ¿Las condiciones hidrológicas y climáticas de un día permiten anticipar si en
    Bogotá y la Sabana habrá una restricción del servicio de agua?

Entrada:  datos/dataset_calidad_agua_limpio.csv  (12.680 mediciones tratadas en la etapa 3)
Salida:   etapa6/datos/dataset_supervisado_dia.csv  (una fila por día de la región Regional)

Transformaciones:
1. Se conservan solo las mediciones de la región Regional (Bogotá y la Sabana), que es donde
   existen las decisiones de racionamiento de la EAAB.
2. Se agrupa por fecha: una fila por día. En el dataset, las mediciones de un mismo día
   comparten el almacenamiento, la precipitación, la temperatura, el consumo y la decisión;
   si se dejaran por separado, el mismo día quedaría a la vez en entrenamiento y en prueba
   durante la validación cruzada y las métricas saldrían infladas.
   - almacenamiento, precipitación, temperatura y consumo: promedio del día (los valores
     faltantes de una medición se ignoran; si faltan en todas, el día queda vacío).
   - afluencias: promedio de las mediciones del día.
   - decision_racionamiento: la del día (es la misma en todas sus mediciones).
3. Variable objetivo `restriccion`: "Si" cuando la decisión del día es distinta de
   "Sin restriccion" (racionamiento, suspensión temporal, campaña de ahorro o restricción a
   grandes consumidores); "No" en caso contrario.

Uso (desde la carpeta del proyecto):  python etapa6/preparar_supervisado.py
"""
import csv
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "datos" / "dataset_calidad_agua_limpio.csv"
SALIDA = Path(__file__).resolve().parent / "datos" / "dataset_supervisado_dia.csv"

NUMERICAS = {
    "nivel_almacenamiento_pct": "almacenamiento_pct",
    "afluencias_m3s": "afluencias_m3s",
    "precipitacion_mm": "precipitacion_mm",
    "temperatura_c": "temperatura_c",
    "consumo_m3s": "consumo_m3s",
}


def promedio(valores):
    numeros = [float(v) for v in valores if v not in ("", None)]
    return round(sum(numeros) / len(numeros), 2) if numeros else ""


def main():
    por_dia = defaultdict(list)
    with open(ENTRADA, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            if fila["tipo_region"].strip() == "Regional":
                por_dia[fila["fecha"]].append(fila)

    filas = []
    for fecha in sorted(por_dia):
        grupo = por_dia[fecha]
        decisiones = {g["decision_racionamiento"].strip() for g in grupo}
        if len(decisiones) != 1:
            raise ValueError(f"El día {fecha} tiene decisiones distintas: {decisiones}")
        decision = decisiones.pop()
        fila = {
            "fecha": fecha,
            "anio": int(grupo[0]["anio"]),
            "mes": int(grupo[0]["mes"]),
        }
        for origen, destino in NUMERICAS.items():
            fila[destino] = promedio(g[origen] for g in grupo)
        fila["decision_racionamiento"] = decision
        fila["restriccion"] = "No" if decision == "Sin restriccion" else "Si"
        filas.append(fila)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)

    con = sum(f["restriccion"] == "Si" for f in filas)
    print(f"Días: {len(filas)} | con restricción: {con} ({100 * con / len(filas):.1f} %)")
    for campo in NUMERICAS.values():
        vacios = sum(f[campo] == "" for f in filas)
        print(f"  {campo:20s} días sin dato: {vacios}")
    print(f"Archivo creado: {SALIDA}")


if __name__ == "__main__":
    main()
