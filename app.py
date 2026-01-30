import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/service")
def service():
    return render_template("service.html")

@app.route("/car")
def car():
    return render_template("car.html")

@app.route("/detail")
def detail():
    return render_template("detail.html")

@app.route("/team")
def team():
    return render_template("team.html")

@app.route("/testimonial")
def testimonial():
    return render_template("testimonial.html")

@app.route("/inspeccion")
def inspeccion():
    return render_template("inspeccion.html")

@app.route("/historia")
def historia():
    return render_template("historia.html")

@app.route("/booking")
def booking():
    return render_template("booking.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/comunidad")
def comunidad():
    return render_template("comunidad.html")


@app.route("/cotizar", methods=["POST"])
def cotizar():
    try:
        data = request.json

        year = int(data["year"])
        km = int(data["km"])
        estado = data["estado"]

        precio_base = 50000
        depreciacion_anual = (2025 - year) * 1500
        depreciacion_km = (km // 10000) * 800

        factor_estado = {
            "excelente": 1.0,
            "bueno": 0.9,
            "regular": 0.8
        }

        precio = (precio_base - depreciacion_anual - depreciacion_km) * factor_estado.get(estado, 0.85)

        precio_min = round(precio * 0.95)
        precio_max = round(precio * 1.05)

        # INSERTAR EN SUPABASE
        result = supabase.table("tasaciones").insert({
            "marca": data["marca"],
            "modelo": data["modelo"],
            "year": year,
            "km": km,
            "estado": estado,
            "precio_min": precio_min,
            "precio_max": precio_max
        }).execute()

        print("Insert Supabase OK:", result)

        return jsonify({
            "min": precio_min,
            "max": precio_max
        })

    except Exception as e:
        print("ERROR EN /cotizar:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
    
# @app.route("/cotizar", methods=["POST"])
# def cotizar():
#     data = request.json

#     try:
#         year = int(str(data["year"]).strip())
#         km = int(str(data["km"]).strip())
#         estado = data["estado"].strip()
#     except:
#         return jsonify({"error": "Datos inválidos"}), 400

#     precio_base = 50000
#     depreciacion_anual = (2025 - year) * 1500
#     depreciacion_km = (km // 10000) * 800

#     factor_estado = {
#         "excelente": 1.0,
#         "bueno": 0.9,
#         "regular": 0.8
#     }

#     precio = (precio_base - depreciacion_anual - depreciacion_km) * factor_estado.get(estado, 0.85)

#     precio_min = round(precio * 0.95)
#     precio_max = round(precio * 1.05)

#     # Guardar en Supabase
#     supabase.table("cotizaciones").insert({
#         "marca": data["marca"],
#         "modelo": data["modelo"],
#         "year": year,
#         "km": km,
#         "estado": estado,
#         "precio_min": precio_min,
#         "precio_max": precio_max
#     }).execute()

#     return jsonify({
#         "min": precio_min,
#         "max": precio_max
#     })


