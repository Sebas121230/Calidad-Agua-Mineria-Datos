import csv
import os
from datetime import date

from flask import Flask, render_template

# Inicializar la aplicacion
app = Flask(__name__)

# Carpeta donde vive app.py (para leer los CSV sin importar desde donde se ejecute)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def leer_csv(nombre):
    """Lee un CSV del proyecto y lo devuelve como lista de diccionarios.
    Si el archivo no existe todavia, devuelve una lista vacia en vez de romper."""
    ruta = os.path.join(BASE_DIR, nombre)
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------- Pagina de inicio ----------
@app.route("/")
def inicio():
    return render_template("inicio.html")


# ---------- Etapa 1: los 8 submenus ----------
@app.route("/etapa1/problema")
def problema():
    return render_template("etapa1/problema.html")


@app.route("/etapa1/preguntas")
def preguntas():
    return render_template("etapa1/preguntas.html")


@app.route("/etapa1/necesidades")
def necesidades():
    return render_template("etapa1/necesidades.html")


@app.route("/etapa1/fuentes")
def fuentes():
    return render_template("etapa1/fuentes.html")


@app.route("/etapa1/dataset")
def dataset():
    return render_template("etapa1/dataset.html")


@app.route("/etapa1/diccionario")
def diccionario():
    return render_template("etapa1/diccionario.html")


@app.route("/etapa1/calidad")
def calidad():
    return render_template("etapa1/calidad.html")


@app.route("/etapa1/limitaciones")
def limitaciones():
    return render_template("etapa1/limitaciones.html")


# ---------- Etapa 2 ----------
@app.route("/etapa2/inventario")
def inventario():
    """Inventario de problemas de calidad.

    Lee los resultados que dejo el script inventario_calidad.py y los pinta en
    la tabla. Asi la pagina siempre muestra los numeros reales del dataset: si
    el dataset cambia, se vuelve a correr el script y la pagina se actualiza
    sola, sin tocar el HTML.
    """
    problemas = leer_csv("inventario_problemas.csv")
    metricas = leer_csv("metricas_calidad.csv")
    verificaciones = leer_csv("verificaciones_sin_hallazgo.csv")

    # Conteo de hallazgos por dimension, para la grafica de distribucion
    conteo = {}
    for p in problemas:
        conteo[p["dimension_calidad"]] = conteo.get(p["dimension_calidad"], 0) + 1
    por_dimension = sorted(conteo.items(), key=lambda x: -x[1])

    return render_template(
        "etapa2/inventario.html",
        problemas=problemas,
        metricas=metricas,
        verificaciones=verificaciones,
        por_dimension=por_dimension,
        max_dim=max(conteo.values()) if conteo else 1,
        total=len(problemas),
        altos=sum(1 for p in problemas if p["nivel_impacto"] == "Alto"),
        medios=sum(1 for p in problemas if p["nivel_impacto"] == "Medio"),
        bajos=sum(1 for p in problemas if p["nivel_impacto"] == "Bajo"),
        n_registros="12.989",
        n_variables=20,
        fecha_analisis=date.today().strftime("%d de %B de %Y"),
    )


@app.route("/etapa2/causas")
def causas():
    """Analisis de las causas de los problemas detectados.

    Lee analisis_causas.csv y resumen_causas.csv, generados por el script
    analisis_causas.py a partir del inventario del punto 6.
    """
    causas = leer_csv("analisis_causas.csv")
    resumen = leer_csv("resumen_causas.csv")
    raices = [int(c["problemas_como_causa_raiz"]) for c in resumen] or [1]

    return render_template(
        "etapa2/causas.html",
        causas=causas,
        resumen=resumen,
        total=len(causas),
        max_raiz=max(raices),
    )


# Ejecutar el servidor en modo desarrollo
if __name__ == "__main__":
    app.run(debug=True)
