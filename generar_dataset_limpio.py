# -*- coding: utf-8 -*-
"""
Reproduce en Python el resultado de la Etapa 3 (paquete SSIS) sobre
dataset_calidad_agua.csv, para que la Etapa 4 (dimension territorial) tenga
un dataset limpio sin depender de SQL Server.

Las reglas se tomaron literalmente del informe tecnico de la Etapa 3
(Informe_Etapa3_Calidad_Agua.pdf, secciones 5.3 a 5.6) y se validan al final
contra resultados_iteraciones.csv (iteracion 2: 12.680 aceptados, 62
duplicados, 247 en revision, sobre 12.989 recibidos).

Salidas:
  - dataset_calidad_agua_limpio.csv   -> equivalente a dst_calidad_agua
  - dataset_calidad_agua_revision.csv -> equivalente a rev_calidad_agua
"""
import csv
import re
from collections import Counter

ARCHIVO_ENTRADA = "dataset_calidad_agua.csv"
ARCHIVO_LIMPIO = "dataset_calidad_agua_limpio.csv"
ARCHIVO_REVISION = "dataset_calidad_agua_revision.csv"

MARCADORES_NULO = {"", "N/A", "null", "-"}


def es_nulo(valor):
    return (valor or "").strip() in MARCADORES_NULO


# ---------------------------------------------------------------------
# DER Normalizar (informe, 5.3)
# ---------------------------------------------------------------------

def normalizar_sistema(valor):
    # P04: vacio/N/A -> "Fuera de cobertura EAAB"; si no, TRIM
    if es_nulo(valor):
        return "Fuera de cobertura EAAB"
    return valor.strip()


def normalizar_irca(valor):
    # P03: vacio/N/A/null/- -> None (no se imputa); si no, el valor como texto
    if es_nulo(valor):
        return None, "No"
    return valor.strip(), "Si"


def normalizar_municipio(valor):
    # P10: UPPER(TRIM(municipio))
    return (valor or "").strip().upper()


PATRON_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalizar_fecha(valor, mes_columna):
    """Detecta el formato por la posicion de '/' o '-' y reordena a AAAA-MM-DD.

    Devuelve (fecha_iso_o_None, ok). ok=False si no se pudo interpretar o si
    el mes resultante no coincide con la columna 'mes' (regla P09 / CSPL).
    """
    v = (valor or "").strip()
    fecha_iso = None

    if PATRON_ISO.match(v):
        fecha_iso = v
    else:
        # Formatos alternos detectados en el inventario: DD/MM/AAAA,
        # MM-DD-AAAA, AAAA/MM/DD.
        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", v)  # DD/MM/AAAA
        if m:
            d, mo, y = m.groups()
            fecha_iso = f"{y}-{mo}-{d}"
        else:
            m = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", v)  # MM-DD-AAAA
            if m:
                mo, d, y = m.groups()
                fecha_iso = f"{y}-{mo}-{d}"
            else:
                m = re.match(r"^(\d{4})/(\d{2})/(\d{2})$", v)  # AAAA/MM/DD
                if m:
                    y, mo, d = m.groups()
                    fecha_iso = f"{y}-{mo}-{d}"

    if fecha_iso is None:
        return None, False

    # Validar que el mes de la fecha coincida con la columna 'mes' del
    # registro (asi se detecta un intercambio dia/mes mal resuelto).
    try:
        mes_de_fecha = int(fecha_iso[5:7])
        mes_col = int((mes_columna or "").strip())
    except ValueError:
        return fecha_iso, False

    return fecha_iso, (mes_de_fecha == mes_col)


# ---------------------------------------------------------------------
# DER Clasificacion (informe, 5.6) - rangos del dataset original, no los
# de la Resolucion 2115/2007 (decision documentada: deja comparar P11/P16
# contra el dato de origen).
# ---------------------------------------------------------------------

def clasificar_riesgo(irca_valor):
    if irca_valor is None:
        return None
    irca = float(irca_valor)
    if irca <= 5:
        return "Sin riesgo (0-5)"
    if irca <= 14:
        return "Bajo riesgo (5-14)"
    if irca <= 28:
        return "Riesgo medio (14-28)"
    if irca <= 40:
        return "Alto riesgo (28-40)"
    return "Inviable sanitariamente (>40)"


def main():
    with open(ARCHIVO_ENTRADA, encoding="utf-8") as f:
        registros = list(csv.DictReader(f))

    recibidos = len(registros)
    validos = []
    revision = []

    def enviar_a_revision(r, regla_id, campo_afectado, motivo):
        revision.append({
            **r,
            "regla_id": regla_id,
            "campo_afectado": campo_afectado,
            "motivo": motivo,
        })

    for r in registros:
        # --- normalizacion (DER Normalizar) ---
        sistema_l = normalizar_sistema(r["sistema_abastecimiento"])
        irca_l, irca_reportado = normalizar_irca(r["irca"])
        municipio_l = normalizar_municipio(r["municipio"])
        fecha_l, fecha_ok = normalizar_fecha(r["fecha"], r["mes"])

        # --- CSPL Validar: orden P05 -> P09 -> P08 -> Validos ---
        if r["tipo_region"].strip() == "Global":
            enviar_a_revision(r, "P05", "tipo_region",
                               "Registro de nivel global: vacios "
                               "estructurales, fuera del alcance municipal")
            continue

        if not fecha_ok:
            enviar_a_revision(r, "P09", "fecha",
                               "Fecha no convertible a ISO o inconsistente "
                               "con la columna mes")
            continue

        if irca_l is not None:
            irca_num = float(irca_l)
            if irca_num < 0 or irca_num > 100:
                enviar_a_revision(r, "P08", "irca",
                                   "IRCA fuera del dominio 0-100 "
                                   "(Res. 2115/2007)")
                continue

        # --- DER Clasificacion (P11 / P16) ---
        clasificacion_l = clasificar_riesgo(irca_l)

        limpio = dict(r)
        limpio["sistema_abastecimiento"] = sistema_l
        limpio["irca"] = irca_l if irca_l is not None else ""
        limpio["irca_reportado"] = irca_reportado
        limpio["municipio"] = municipio_l
        limpio["fecha"] = fecha_l
        limpio["clasificacion_riesgo"] = clasificacion_l or ""
        validos.append(limpio)

    # --- Llave unica (P07): fecha + municipio + sistema_abastecimiento ---
    # El Lookup "LKP Ya Cargados" de la iteracion 3 no aplica aqui (es contra
    # un destino ya existente); replicamos solo la restriccion UNIQUE del
    # destino para un lote nuevo, como en la iteracion 2.
    vistos = set()
    aceptados = []
    duplicados = 0
    for r in validos:
        llave = (r["fecha"], r["municipio"], r["sistema_abastecimiento"])
        if llave in vistos:
            enviar_a_revision(r, "P07", "fecha+municipio+sistema",
                               "Rechazado por la BD: llave "
                               "fecha+municipio+sistema repetida")
            duplicados += 1
            continue
        vistos.add(llave)
        aceptados.append(r)

    # --- Escritura de salidas ---
    columnas_limpio = list(registros[0].keys()) + ["irca_reportado"]
    with open(ARCHIVO_LIMPIO, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas_limpio)
        w.writeheader()
        for r in aceptados:
            w.writerow({k: r.get(k, "") for k in columnas_limpio})

    columnas_revision = list(registros[0].keys()) + [
        "regla_id", "campo_afectado", "motivo"
    ]
    with open(ARCHIVO_REVISION, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas_revision)
        w.writeheader()
        for r in revision:
            w.writerow({k: r.get(k, "") for k in columnas_revision})

    # --- Validacion contra resultados_iteraciones.csv (iteracion 2) ---
    # El log del ETL cuenta "revision" y "duplicados" por separado, aunque
    # ambos terminen en rev_calidad_agua (el informe lo documenta en 5.8:
    # "DST Revision" y "DST Revision Duplicados" son destinos distintos que
    # insertan en la misma tabla). Por eso aqui tambien se separan al contar,
    # aunque el archivo de revision los incluya a todos.
    revision_no_duplicados = [r for r in revision if r["regla_id"] != "P07"]

    print(f"Recibidos:  {recibidos}")
    print(f"Aceptados:  {len(aceptados)}")
    print(f"Duplicados: {duplicados}")
    print(f"Revision:   {len(revision_no_duplicados)}")
    print(f"Suma de control: "
          f"{len(aceptados) + duplicados + len(revision_no_duplicados)} "
          f"(debe ser igual a recibidos)")
    print()
    print("Motivos de revision (incluye duplicados P07):",
          Counter(r["regla_id"] for r in revision))

    esperado = {"aceptados": 12680, "duplicados": 62, "revision": 247}
    obtenido = {"aceptados": len(aceptados), "duplicados": duplicados,
                "revision": len(revision_no_duplicados)}
    print()
    if obtenido == esperado:
        print("OK: coincide exactamente con la iteracion 2 del ETL real "
              "(resultados_iteraciones.csv).")
    else:
        print("ADVERTENCIA: no coincide con la iteracion 2 esperada:")
        print("  esperado:", esperado)
        print("  obtenido:", obtenido)


if __name__ == "__main__":
    main()
