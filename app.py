from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client

app = Flask(__name__)
CORS(app)

SUPABASE_URL = "https://tcctyjmmtqhozovcynwk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRjY3R5am1tdHFob3pvdmN5bndrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTY0NzIyMiwiZXhwIjoyMDg1MjIzMjIyfQ.Eza3HiSbsCtCESo1NHSWxy6cmiG9l5WQismbg-k2zEo"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

        # 👉 INSERTAR EN SUPABASE
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


# @app.route("/cotizar", methods=["POST"])
# def cotizar():
#     try:
#         data = request.json

#         year = int(data["year"])
#         km = int(data["km"])
#         estado = data["estado"]

#         precio_base = 50000
#         depreciacion_anual = (2025 - year) * 1500
#         depreciacion_km = (km // 10000) * 800

#         factor_estado = {
#             "excelente": 1.0,
#             "bueno": 0.9,
#             "regular": 0.8
#         }

#         precio = (precio_base - depreciacion_anual - depreciacion_km) * factor_estado.get(estado, 0.85)

#         precio_min = round(precio * 0.95)
#         precio_max = round(precio * 1.05)

#         # 🔹 GUARDAR EN SUPABASE (NO rompe la cotización)
#         print("DATA RECIBIDA:", data)
#         try:
#             supabase.table("tasaciones").insert({
#                 "marca": data["marca"],
#                 "modelo": data["modelo"],
#                 "year": year,
#                 "km": km,
#                 "estado": estado,
#                 "precio_min": precio_min,
#                 "precio_max": precio_max
#             }).execute()
#         except Exception as e:
#             print("Error Supabase:", e)

#         return jsonify({
#             "min": precio_min,
#             "max": precio_max
#         })

#     except Exception as e:
#         print("Error backend:", e)
#         return jsonify({"error": "Error interno"}), 500


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


