from flask import Flask, render_template

# Inicializar la aplicación
app = Flask(__name__)


# Definir la ruta principal
@app.route("/")
def inicio():
  return render_template("index.html")


# Ejecutar el servidor en modo desarrollo
if __name__ == "__main__":
  app.run(debug=True)
