# Calidad y Accesibilidad del Agua - Mineria de Datos

Aplicacion Flask que documenta la **Etapa 1** del proyecto de Mineria de Datos sobre la
disponibilidad y continuidad del servicio de agua potable en Bogota D.C. (2019-2025).

**Universidad de Cundinamarca** - Ingenieria de Sistemas y Computacion

## Integrantes

- Diego Armando Guzman Garzon
- Andres Felipe Beltran Barrera
- Juan Sebastian Rodriguez Rivero
- John Sebastian Rodriguez Dominguez

## Estructura del proyecto

```
Calidad-Agua-Mineria-Datos/
├── app.py                  # Rutas de la aplicacion Flask
├── requirements.txt        # Dependencias
├── .gitignore
├── static/
│   ├── css/estilos.css     # Estilos propios (complementan Bootstrap)
│   └── img/logo_udec.png
└── templates/
    ├── base.html           # Plantilla base con el menu lateral
    ├── inicio.html         # Portada
    └── etapa1/             # Los 8 submenus de la Etapa 1
        ├── problema.html
        ├── preguntas.html
        ├── necesidades.html
        ├── fuentes.html
        ├── dataset.html
        ├── diccionario.html
        ├── calidad.html
        └── limitaciones.html
```

## Como ejecutar el proyecto

```bash
# 1. Crear el entorno virtual
python -m venv venv

# 2. Activarlo
#    Windows:
.\venv\Scripts\Activate
#    Linux / macOS:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python app.py
```

Luego abrir <http://127.0.0.1:5000> en el navegador.

## Contenido de la Etapa 1

| # | Submenu | Estado |
|---|---------|--------|
| 1 | Problema y contexto | Completo |
| 2 | Pregunta principal y preguntas secundarias | Completo |
| 3 | Necesidades de informacion | Completo |
| 4 | Fuentes de datos | Completo |
| 5 | Dataset | Estructura lista, pendiente consolidar datos |
| 6 | Diccionario de datos | Estructura lista, pendiente consolidar datos |
| 7 | Calidad inicial de los datos | Estructura lista, pendiente perfilado |
| 8 | Limitaciones y consideraciones | Completo |

## Flujo de trabajo con Git

El desarrollo de la Etapa 1 se realiza en la rama `feature/etapa-1`.
Una vez validada, se integra a `main` mediante merge.
