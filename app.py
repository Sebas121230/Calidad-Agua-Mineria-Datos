from flask import Flask, render_template

# Inicializar la aplicacion
app = Flask(__name__)


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


# Ejecutar el servidor en modo desarrollo
if __name__ == "__main__":
    app.run(debug=True)
