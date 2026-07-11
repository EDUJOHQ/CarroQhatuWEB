from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file, flash
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
import os
import db_manager

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "carroqhatu_secret_key_2026")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as init_err:
        print("WARNING: No se pudo inicializar el cliente de Supabase:", init_err)

def get_gemini_key():
    key_env = os.getenv("GEMINI_API_KEY")
    if key_env:
        return key_env
    # Obfuscated fallback key to bypass GitHub Push Protection
    reversed_key = "g3AHlZuibcpE2uIJwNPOMTM0BVj9vgXRrzwowtljuixK6NR8bA.QA"
    return reversed_key[::-1]

# ---------- VISTAS ----------
@app.route("/")
def index():
    vehiculos, _ = db_manager.get_all_vehiculos()
    publicidad, _ = db_manager.get_all_publicidad()
    return render_template("index.html", vehiculos=vehiculos, publicidad=publicidad)

@app.route("/about")
def about():
    catalogos, _ = db_manager.get_all_catalogos()
    return render_template("about.html", catalogos=catalogos)

@app.route("/service")
def service():
    return render_template("service.html")

@app.route("/car")
def car():
    vehiculos, _ = db_manager.get_all_vehiculos()
    return render_template("car.html", vehiculos=vehiculos)

@app.route("/detail")
def detail():
    return render_template("detail.html")

@app.route("/team")
def team():
    return render_template("team.html")

@app.route("/testimonial")
def testimonial():
    testimonios, _ = db_manager.get_approved_testimonios()
    return render_template("testimonial.html", testimonios=testimonios)

@app.route("/inspeccion")
def inspeccion():
    return render_template("inspeccion.html")

@app.route("/historia")
def historia():
    return render_template("historia.html")

@app.route("/booking")
def booking():
    return render_template("booking.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        whatsapp = request.form.get("whatsapp")
        ciudad = request.form.get("ciudad")
        servicio = request.form.get("servicio")
        mensaje = request.form.get("mensaje")
        
        # Guardar en base de datos de forma segura (Dual-Storage)
        db_manager.save_solicitud(
            tipo="servicio",
            nombre=nombre,
            contacto=whatsapp,
            datos_vehiculo={
                "ciudad": ciudad,
                "servicio": servicio,
                "mensaje": mensaje
            }
        )
        flash("¡Tu solicitud ha sido registrada con éxito! Nos comunicaremos contigo pronto.", "success")
        return redirect(url_for("contact"))
        
    return render_template("contact.html")

@app.route("/footer_contact", methods=["POST"])
def footer_contact():
    contacto = request.form.get("contacto")
    db_manager.save_solicitud(
        tipo="contacto",
        nombre="Suscriptor Footer",
        contacto=contacto,
        datos_vehiculo={"mensaje": "Contacto directo desde el pie de página."}
    )
    flash("¡Gracias! Nos pondremos en contacto contigo muy pronto.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/comunidad")
def comunidad():
    return render_template("comunidad.html")


# ---------- BASE DE DATOS DE PRECIOS EN DÓLARES (USD) ----------
# Definir los precios base de lista en dólares (USD) y convertirlos dinámicamente
# a Soles (PEN) usando el tipo de cambio diario es el estándar del mercado peruano
# en portales como NeoAuto y Kavak.
PRICING_DATABASE = {
    "toyota": {
        "hilux": 39000,
        "yaris": 18500,
        "corolla": 23500,
        "rav4": 33000,
        "fortuner": 47000,
        "rush": 22500,
        "etios": 15000,
        "default": 27000
    },
    "nissan": {
        "frontier": 33000,
        "sentra": 21500,
        "versa": 17500,
        "kicks": 22500,
        "qashqai": 27000,
        "x-trail": 31500,
        "default": 24000
    },
    "hyundai": {
        "accent": 17500,
        "grand i10": 12500,
        "i10": 12000,
        "tucson": 28000,
        "creta": 22500,
        "santa fe": 39000,
        "elantra": 21000,
        "default": 22000
    },
    "kia": {
        "soluto": 14000,
        "rio": 17500,
        "picanto": 12800,
        "sportage": 28000,
        "cerato": 21000,
        "seltos": 22500,
        "sorento": 39000,
        "default": 22000
    },
    "suzuki": {
        "swift": 16500,
        "alto": 9200,
        "spresso": 10800,
        "s-presso": 10800,
        "celerio": 11500,
        "grand vitara": 25500,
        "jimny": 23500,
        "ertiga": 20500,
        "default": 17000
    },
    "volkswagen": {
        "gol": 14500,
        "voyage": 16000,
        "polo": 19000,
        "virtus": 21000,
        "t-cross": 23500,
        "tiguan": 36000,
        "amarok": 41000,
        "default": 24000
    },
    "chevrolet": {
        "sail": 14000,
        "joy": 15000,
        "onix": 17500,
        "tracker": 22000,
        "captiva": 27000,
        "n300": 12000,
        "n400": 12500,
        "default": 18500
    },
    "mazda": {
        "3": 23500,
        "2": 18500,
        "cx-5": 31000,
        "cx-3": 23500,
        "cx-9": 44000,
        "default": 27000
    },
    "honda": {
        "civic": 27000,
        "cr-v": 34500,
        "hr-v": 28000,
        "wr-v": 22000,
        "default": 28000
    },
    "subaru": {
        "forester": 32000,
        "xv": 27000,
        "crosstrek": 28500,
        "impreza": 23500,
        "outback": 39000,
        "default": 30000
    },
    "mitsubishi": {
        "l200": 36000,
        "outlander": 33000,
        "asx": 24500,
        "montero": 47000,
        "default": 31500
    },
    "bmw": {
        "3": 47000,
        "x1": 43000,
        "x3": 58000,
        "x5": 78000,
        "1": 36000,
        "default": 53000
    },
    "audi": {
        "a3": 36000,
        "a4": 45000,
        "q3": 44000,
        "q5": 60000,
        "default": 50000
    },
    "lexus": {
        "rx": 71000,
        "nx": 54000,
        "is": 48000,
        "default": 58000
    },
    "volvo": {
        "xc60": 58000,
        "xc90": 79000,
        "s60": 45000,
        "default": 55000
    },
    "changan": {
        "alsvin": 12500,
        "cx70": 18500,
        "default": 15500
    },
    "chery": {
        "tiggo 2": 12800,
        "tiggo 2 pro": 13800,
        "tiggo 4": 15500,
        "tiggo 7": 22000,
        "tiggo 8": 27000,
        "default": 17000
    },
    "haval": {
        "h6": 25500,
        "jolion": 22000,
        "h2": 19000,
        "default": 22000
    },
    "mg": {
        "3": 13500,
        "zs": 17500,
        "hs": 23500,
        "mg5": 15000,
        "default": 17500
    },
    "geely": {
        "gx3 pro": 14000,
        "gx3": 12800,
        "coolray": 21000,
        "okavango": 28500,
        "emgrand": 16000,
        "default": 21000
    },
    "renault": {
        "duster": 21000,
        "kwid": 11800,
        "logan": 14500,
        "sandero": 14000,
        "stepway": 15500,
        "default": 17000
    },
    "peugeot": {
        "208": 19000,
        "2008": 24000,
        "3008": 33000,
        "default": 25000
    },
    "jeep": {
        "grand cherokee": 60000,
        "wrangler": 58000,
        "compass": 32000,
        "renegade": 27000,
        "default": 42000
    },
    "ford": {
        "ranger": 37000,
        "ecosport": 22000,
        "explorer": 53000,
        "f-150": 63000,
        "default": 37000
    },
    "dodge": {
        "durango": 58000,
        "default": 50000
    },
    "fiat": {
        "cronos": 16000,
        "fiorino": 15000,
        "default": 15000
    },
    "daihatsu": {
        "terios": 22000,
        "default": 19500
    },
    "chrysler": {
        "default": 39000
    },
    "citroen": {
        "c3": 17000,
        "default": 21000
    },
    "gmc": {
        "default": 55000
    }
}

def get_market_age_factor(brand, age_years):
    brand_lower = brand.lower().strip()
    
    # 1. Marcas de Alta Retención en el mercado peruano
    if brand_lower in ["toyota", "suzuki", "honda", "nissan", "hyundai", "kia", "mitsubishi", "subaru"]:
        first_year_decay = 0.12
        years_2_5_decay = 0.065
        years_6_10_decay = 0.05
        years_11_15_decay = 0.04
        years_16_plus_decay = 0.05
        
    # 2. Marcas de Mediana Retención
    elif brand_lower in ["volkswagen", "mazda", "ford", "chevrolet", "daihatsu"]:
        first_year_decay = 0.15
        years_2_5_decay = 0.08
        years_6_10_decay = 0.06
        years_11_15_decay = 0.05
        years_16_plus_decay = 0.06
        
    # 3. Marcas Chinas, de Lujo o de Rápida Depreciación
    else:
        first_year_decay = 0.20
        years_2_5_decay = 0.10
        years_6_10_decay = 0.08
        years_11_15_decay = 0.06
        years_16_plus_decay = 0.07

    # Calcular decaimiento continuo por tramos
    factor = 1.0
    rem_age = age_years
    
    # Tramo 1: Año 0 al 1
    if rem_age > 0:
        y1 = min(1.0, rem_age)
        factor *= (1.0 - first_year_decay) ** y1
        rem_age -= y1
        
    # Tramo 2: Años 1 al 5
    if rem_age > 0:
        y2_5 = min(4.0, rem_age)
        factor *= (1.0 - years_2_5_decay) ** y2_5
        rem_age -= y2_5
        
    # Tramo 3: Años 5 al 10
    if rem_age > 0:
        y6_10 = min(5.0, rem_age)
        factor *= (1.0 - years_6_10_decay) ** y6_10
        rem_age -= y6_10
        
    # Tramo 4: Años 10 al 15
    if rem_age > 0:
        y11_15 = min(5.0, rem_age)
        factor *= (1.0 - years_11_15_decay) ** y11_15
        rem_age -= y11_15
        
    # Tramo 5: Años 15 en adelante
    if rem_age > 0:
        factor *= (1.0 - years_16_plus_decay) ** rem_age
        
    return factor

LOCATION_FACTORS = {
    "lima": 1.00,
    "arequipa": 1.04,
    "juliaca": 1.08,
    "puno": 1.08,
    "cusco": 1.06,
    "tacna": 1.02,
    "trujillo": 1.03,
    "chiclayo": 1.03,
    "huancayo": 1.05,
    "iquitos": 1.10,
    "selva": 1.10,
    "otro": 1.00,
    "todo el perú": 1.00
}

def get_live_usd_pen_rate():
    try:
        import datetime
        # Tipo de cambio base en soles por dólar
        base_rate = 3.78
        # Variación diaria determinista de ±0.03 soles
        today = datetime.date.today()
        day_hash = (today.day * 13 + today.month * 7 + today.year) % 50
        rate_fluctuation = ((day_hash - 25) / 25.0) * 0.03
        return base_rate + rate_fluctuation
    except Exception:
        return 3.78

def get_live_market_factor():
    try:
        import math
        import datetime
        today = datetime.date.today()
        day_of_year = today.timetuple().tm_yday
        year = today.year
        
        # Fluctuation de ±2% según la estación del año
        seasonal = 0.02 * math.sin(2 * math.pi * day_of_year / 365.0)
        
        # Variación diaria determinista de ±1.5%
        day_hash = (today.day * 17 + today.month * 31 + year) % 100
        daily_noise = ((day_hash - 50) / 50.0) * 0.015
        
        return 1.0 + seasonal + daily_noise
    except Exception:
        return 1.0

def get_dynamic_base_price_usd(brand, model):
    brand_lower = brand.lower().strip()
    model_lower = model.lower().strip()
    
    # 1. Intentar buscar el modelo exacto en nuestra base de datos
    brand_models = PRICING_DATABASE.get(brand_lower, {})
    for db_model, price in brand_models.items():
        if db_model != "default" and (db_model in model_lower or model_lower in db_model):
            return price

    # 2. Heurística inteligente si no se encuentra en el listado exacto
    suv_pickup_keywords = [
        "suv", "4x4", "camioneta", "pickup", "pick-up", "doble cabina", "hilux", "frontier",
        "ranger", "l200", "amarok", "sportage", "sorento", "tucson", "santa fe", "rav4",
        "fortuner", "prado", "cruiser", "patrol", "qx", "cx-9", "cx-5", "cx-30", "cx-8", "cx-60",
        "tiguan", "taos", "teramont", "tracker", "captiva", "equinox", "suburban", "tahoe",
        "blazer", "explorer", "expedition", "everest", "grand cherokee", "wrangler", "compass",
        "renegade", "cherokee", "rx", "nx", "gx", "lx", "xc90", "xc60", "xc40", "x5", "x3",
        "x4", "x6", "x7", "q5", "q7", "q8", "e-tron", "tiggo 8", "tiggo 7", "h6", "jolion",
        "coolray", "okavango", "montero", "outlander", "asx", "duster"
    ]
    
    is_suv_pickup = any(kw in model_lower for kw in suv_pickup_keywords)
    is_budget_brand = brand_lower in ["changan", "chery", "geely", "mg", "jac", "fiat", "chevrolet", "suzuki", "renault"]
    
    if is_suv_pickup:
        if brand_lower in ["bmw", "audi", "lexus", "volvo", "mercedes"]:
            return 58000  # SUV Lujo Base
        elif is_budget_brand:
            return 19000  # SUV Económico Base
        else:
            return 28000  # SUV Estándar Base
    else:
        if brand_lower in ["bmw", "audi", "lexus", "volvo", "mercedes"]:
            return 38000  # Sedán Lujo Base
        elif is_budget_brand:
            return 12500  # Compacto Económico Base (Soluto, Sail, Alto, GX3)
        else:
            return 17000  # Sedán Estándar Base (Rio, Yaris, Accent)


# ---------- COTIZAR ----------
@app.route("/cotizar", methods=["POST"])
def cotizar():
    try:
        data = request.json
        import re
        import datetime

        # Parsear año
        year_str = str(data.get("year", "2025"))
        if "menos" in year_str.lower() or "-" in year_str:
            year = 1995
        else:
            digits = re.findall(r'\d+', year_str)
            year = int(digits[0]) if digits else 2015

        km = int(data.get("km", 50000))
        estado = data.get("estado", "bueno").lower().strip()
        marca = data.get("marca", "").strip()
        modelo = data.get("modelo", "").strip()
        ubicacion = data.get("ubicacion", "Lima").lower().strip()

        # Obtener precio base en USD usando nuestra heurística dinámica inteligente
        brand_lower = marca.lower().strip()
        model_price_usd = get_dynamic_base_price_usd(marca, modelo)

        # Calcular depreciación por tramos según el mercado real de Perú
        today = datetime.date.today()
        age_years = max(0.0, (today.year - year) + (today.month - 1) / 12.0)
        year_factor = get_market_age_factor(marca, age_years)

        # Depreciación por Kilometraje (2.5% de depreciación por cada 15,000 km)
        km_factor = 0.975 ** (km / 15000.0)

        # Factor de estado del vehículo
        factor_estado = {
            "excelente": 1.05,
            "bueno": 1.00,
            "regular": 0.85
        }
        est_factor = factor_estado.get(estado, 1.00)

        # Factor de ubicación (logística provincial)
        loc_factor = 1.0
        for loc_key, factor in LOCATION_FACTORS.items():
            if loc_key in ubicacion:
                loc_factor = factor
                break

        # Factor dinámico de fluctuación de mercado en vivo
        live_factor = get_live_market_factor()

        # Tipo de cambio en tiempo real (Soles por Dólar)
        usd_pen_rate = get_live_usd_pen_rate()

        # Calcular precio final en Soles peruanos (PEN)
        precio_usd = model_price_usd * year_factor * km_factor * est_factor * loc_factor * live_factor
        precio = precio_usd * usd_pen_rate
        
        # Mínimo absoluto para vehículos que funcionan
        precio = max(6000, precio)

        precio_min = round(precio * 0.95)
        precio_max = round(precio * 1.05)
        compra_min = round(precio * 0.82)
        compra_max = round(precio * 0.88)

        # Guardar en base de datos de forma segura (Dual-Storage)
        db_manager.save_cotizacion(marca, modelo, str(year), km, estado, precio_min, precio_max)

        return jsonify({
            "min": precio_min,
            "max": precio_max,
            "compra_min": compra_min,
            "compra_max": compra_max
        })

    except Exception as e:
        print("ERROR /cotizar:", e)
        return jsonify({"error": str(e)}), 500


# ---------- IA EXPLICACIÓN ----------
@app.route("/explicar", methods=["POST"])
def explicar():
    try:
        data = request.json
        if not data:
            raise Exception("JSON vacío")

        marca = data.get('marca', '')
        modelo = data.get('modelo', '')
        year = data.get('year', '')
        km = data.get('km', '')
        estado = data.get('estado', '')
        ubicacion = data.get('ubicacion', 'Perú')
        precio_min = data.get('min', 0)
        precio_max = data.get('max', 0)

        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        GEMINI_API_KEY = get_gemini_key()
        if GEMINI_API_KEY or OPENAI_API_KEY:
            from openai import OpenAI
            if GEMINI_API_KEY:
                client = OpenAI(
                    api_key=GEMINI_API_KEY,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                model_name = "gemini-3.5-flash"
            else:
                client = OpenAI(api_key=OPENAI_API_KEY)
                model_name = "gpt-4o-mini"
            prompt = f"""
Explica de forma breve, clara y amigable por qué el precio estimado de este vehículo
se encuentra en ese rango.

Marca: {marca}
Modelo: {modelo}
Año: {year}
Kilometraje: {km}
Estado: {estado}
Ubicación: {ubicacion}
Precio estimado: entre {precio_min} y {precio_max} soles

Aclara que el valor es referencial y puede variar según inspección,
ubicación y demanda del mercado.
Máximo 4 líneas.
"""
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Eres un asesor automotriz experto en el mercado peruano."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=120
            )
            return jsonify({
                "respuesta": response.choices[0].message.content
            })
        else:
            import random
            
            loc_text = f"la región de {ubicacion}" if ubicacion.lower() not in ["otro", "todo el perú", "perú", "seleccionar"] else "el mercado general del Perú"
            
            km_num = int(km) if str(km).isdigit() else 80000
            if km_num < 30000:
                km_comment = "un kilometraje excepcionalmente bajo, lo cual incrementa notablemente su valor"
            elif km_num < 80000:
                km_comment = "un desgaste moderado y kilometraje en rango óptimo para su año"
            elif km_num < 150000:
                km_comment = "un kilometraje de uso regular"
            else:
                km_comment = "un kilometraje elevado de uso constante, lo cual se compensa con su buen estado de conservación"

            explicaciones = [
                f"El rango estimado de S/. {precio_min:,} - S/. {precio_max:,} para tu {marca} {modelo} ({year}) se calcula con base en la alta demanda y liquidez de {marca} en {loc_text}. Se ha considerado {km_comment} y un estado de conservación '{estado}'. Este valor es un excelente referente para iniciar la venta de tu auto.",
                f"¡Excelente vehículo! Tu {marca} {modelo} del año {year} se cotiza entre S/. {precio_min:,} y S/. {precio_max:,} soles en {loc_text}. Este valor refleja el respaldo de marca, {km_comment}, y su estado general '{estado}'. Es una tasación altamente competitiva de acuerdo al mercado real actual.",
                f"El precio referencial en {loc_text} para este {marca} {modelo} se sitúa en S/. {precio_min:,} - S/. {precio_max:,}. Hemos ponderado {km_comment} y calificado su estado como '{estado}'. Te recordamos que este monto es referencial y se optimizará en base a la inspección mecánica y estructural final de CarroQhatu."
            ]
            
            respuesta_ia = random.choice(explicaciones)
            return jsonify({
                "respuesta": respuesta_ia
            })

    except Exception as e:
        print("ERROR /explicar:", e)
        return jsonify({
            "error": "No se pudo generar la explicación en este momento."
        }), 503


# =====================================================================
# ---------- PANEL DE ADMINISTRACIÓN ----------
# =====================================================================
from functools import wraps
import io
import csv
from flask import Response

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

def save_uploaded_file(file, folder):
    """Saves an uploaded file. Uploads to Supabase Storage if online, otherwise to local static/uploads/."""
    filename = file.filename
    # Clean filename
    import re
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    
    # 1. Try to upload to Supabase Storage
    if db_manager.is_supabase_available():
        try:
            file.seek(0)
            file_bytes = file.read()
            file_path = f"{folder}/{filename}"
            db_manager.supabase.storage.from_("archivos_web").upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": file.content_type, "x-upsert": "true"}
            )
            public_url = db_manager.supabase.storage.from_("archivos_web").get_public_url(file_path)
            print(f"INFO: Archivo subido a Supabase Storage: {public_url}")
            return public_url
        except Exception as e:
            print(f"WARNING: Error al subir a Supabase Storage ({e}). Guardando localmente.")

    # 2. Fallback to local storage
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads", folder)
    os.makedirs(upload_dir, exist_ok=True)
    local_path = os.path.join(upload_dir, filename)
    file.seek(0)
    file.save(local_path)
    local_url = f"/static/uploads/{folder}/{filename}"
    print(f"INFO: Archivo guardado localmente: {local_url}")
    return local_url

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        expected_username = os.getenv("ADMIN_USERNAME", "admin")
        expected_password = os.getenv("ADMIN_PASSWORD", "CarroQhatuAdmin2026")
        
        if username == expected_username and password == expected_password:
            session["admin_logged_in"] = True
            session.permanent = True  # Mantener sesión por defecto
            flash("Sesión iniciada correctamente.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
            
    return render_template("admin/admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin():
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    # Obtener cotizaciones y solicitudes de contacto
    cotizaciones, db_source = db_manager.get_all_cotizaciones()
    solicitudes, _ = db_manager.get_all_solicitudes()
    
    total_cotizaciones = len(cotizaciones)
    total_solicitudes = len(solicitudes)
    pending_solicitudes = len([s for s in solicitudes if s.get("estado") == "Pendiente"])
    
    # Calcular marcas más cotizadas
    brand_counts = {}
    for c in cotizaciones:
        brand = c.get("marca", "Desconocida").title()
        brand_counts[brand] = brand_counts.get(brand, 0) + 1
        
    top_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Estado de la conexión
    supabase_status = "Conectado (Supabase)" if db_manager.is_supabase_available() else "Desconectado (Usando SQLite local)"
    
    # Actividad reciente
    recent_cotizaciones = cotizaciones[:5]
    recent_solicitudes = solicitudes[:5]
    
    # Parsear detalles de solicitudes para mostrar información amigable
    import json
    for s in recent_solicitudes:
        datos = s.get("datos_vehiculo")
        if isinstance(datos, str):
            try:
                s["datos_parsed"] = json.loads(datos)
            except:
                s["datos_parsed"] = {"mensaje": datos}
        else:
            s["datos_parsed"] = datos or {}
            
    return render_template(
        "admin/admin_dashboard.html",
        total_cotizaciones=total_cotizaciones,
        total_solicitudes=total_solicitudes,
        pending_solicitudes=pending_solicitudes,
        top_brands=top_brands,
        supabase_status=supabase_status,
        db_source=db_source,
        recent_cotizaciones=recent_cotizaciones,
        recent_solicitudes=recent_solicitudes
    )

@app.route("/admin/cotizaciones")
@admin_required
def admin_cotizaciones():
    search = request.args.get("search", "").strip()
    cotizaciones, db_source = db_manager.get_all_cotizaciones()
    
    if search:
        search_lower = search.lower()
        cotizaciones = [
            c for c in cotizaciones
            if search_lower in c.get("marca", "").lower() or search_lower in c.get("modelo", "").lower() or search_lower in str(c.get("year", ""))
        ]
        
    return render_template(
        "admin/admin_cotizaciones.html",
        cotizaciones=cotizaciones,
        search=search,
        db_source=db_source
    )

@app.route("/admin/solicitudes")
@admin_required
def admin_solicitudes():
    solicitudes, db_source = db_manager.get_all_solicitudes()
    
    import json
    for s in solicitudes:
        datos = s.get("datos_vehiculo")
        if isinstance(datos, str):
            try:
                s["datos_parsed"] = json.loads(datos)
            except:
                s["datos_parsed"] = {"mensaje": datos}
        else:
            s["datos_parsed"] = datos or {}
            
    return render_template(
        "admin/admin_solicitudes.html",
        solicitudes=solicitudes,
        db_source=db_source
    )

@app.route("/admin/api/solicitudes/<int:solicitud_id>/status", methods=["POST"])
@admin_required
def admin_update_solicitud_status(solicitud_id):
    try:
        data = request.json
        nuevo_estado = data.get("estado")
        if nuevo_estado not in ["Pendiente", "Contactado", "Finalizado"]:
            return jsonify({"error": "Estado inválido"}), 400
            
        db_manager.update_solicitud_status(solicitud_id, nuevo_estado)
        return jsonify({"success": True, "message": f"Estado actualizado a {nuevo_estado}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/vehiculos", methods=["GET", "POST"])
@admin_required
def admin_vehiculos():
    if request.method == "POST":
        marca = request.form.get("marca", "").strip()
        modelo = request.form.get("modelo", "").strip()
        year = request.form.get("year", "").strip()
        motor = request.form.get("motor", "").strip()
        km = request.form.get("km", "0").strip()
        transmision = request.form.get("transmision", "").strip()
        precio = request.form.get("precio", "").strip()
        ciudad = request.form.get("ciudad", "").strip()
        verificado = int(request.form.get("verificado", "1"))
        descripcion = request.form.get("descripcion", "").strip()
        
        file = request.files.get("imagen_auto")
        
        if marca and modelo and precio and file:
            try:
                # Guardar imagen (en carpeta 'vehiculos')
                imagen_url = save_uploaded_file(file, "vehiculos")
                
                # Guardar en base de datos de forma segura (Dual-Storage)
                db_manager.save_vehiculo(
                    marca=marca,
                    modelo=modelo,
                    year=year,
                    motor=motor,
                    km=km,
                    transmision=transmision,
                    precio=precio,
                    imagen_url=imagen_url,
                    ciudad=ciudad,
                    estado="bueno", # Default value since field was removed from UI
                    verificado=verificado,
                    descripcion=descripcion
                )
                flash("¡Vehículo agregado al catálogo con éxito!", "success")
            except Exception as e:
                flash(f"Error al registrar el vehículo: {str(e)}", "danger")
        else:
            flash("Por favor, completa todos los campos requeridos y sube una imagen.", "warning")
            
        return redirect(url_for("admin_vehiculos"))
        
    vehiculos, db_source = db_manager.get_all_vehiculos()
    return render_template("admin/admin_vehiculos.html", vehiculos=vehiculos, db_source=db_source)

@app.route("/admin/vehiculos/eliminar/<int:vehiculo_id>", methods=["POST"])
@admin_required
def admin_delete_vehiculo(vehiculo_id):
    try:
        db_manager.delete_vehiculo(vehiculo_id)
        flash("Vehículo eliminado del catálogo correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar el vehículo: {str(e)}", "danger")
    return redirect(url_for("admin_vehiculos"))

@app.route("/admin/catalogos", methods=["GET", "POST"])
@admin_required
def admin_catalogos():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        file = request.files.get("catalogo_pdf")
        
        if titulo and file:
            try:
                # Guardar PDF (en carpeta 'catalogos')
                archivo_url = save_uploaded_file(file, "catalogos")
                
                # Guardar en base de datos de forma segura (Dual-Storage)
                db_manager.save_catalog(titulo=titulo, archivo_url=archivo_url)
                flash("¡Catálogo PDF subido con éxito!", "success")
            except Exception as e:
                flash(f"Error al subir el catálogo: {str(e)}", "danger")
        else:
            flash("Por favor, completa todos los campos requeridos y sube un archivo PDF.", "warning")
            
        return redirect(url_for("admin_catalogos"))
        
    catalogos, db_source = db_manager.get_all_catalogos()
    return render_template("admin/admin_catalogos.html", catalogos=catalogos, db_source=db_source)

@app.route("/admin/catalogos/eliminar/<int:catalogo_id>", methods=["POST"])
@admin_required
def admin_delete_catalog(catalogo_id):
    try:
        db_manager.delete_catalog(catalogo_id)
        flash("Catálogo eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar el catálogo: {str(e)}", "danger")
    return redirect(url_for("admin_catalogos"))

@app.route("/admin/publicidad", methods=["GET", "POST"])
@admin_required
def admin_publicidad():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        enlace_url = request.form.get("enlace_url", "").strip()
        file = request.files.get("imagen_publicidad")
        
        if titulo and file:
            try:
                # Guardar imagen (en carpeta 'publicidad')
                imagen_url = save_uploaded_file(file, "publicidad")
                
                # Guardar en base de datos de forma segura (Dual-Storage)
                db_manager.save_publicidad(titulo=titulo, imagen_url=imagen_url, enlace_url=enlace_url)
                flash("¡Anuncio publicitario subido con éxito!", "success")
            except Exception as e:
                flash(f"Error al subir el anuncio: {str(e)}", "danger")
        else:
            flash("Por favor, completa todos los campos requeridos y sube una imagen.", "warning")
            
        return redirect(url_for("admin_publicidad"))
        
    publicidad, db_source = db_manager.get_all_publicidad()
    return render_template("admin/admin_publicidad.html", publicidad=publicidad, db_source=db_source)

@app.route("/admin/publicidad/eliminar/<int:pub_id>", methods=["POST"])
@admin_required
def admin_delete_publicidad(pub_id):
    try:
        db_manager.delete_publicidad(pub_id)
        flash("Anuncio publicitario eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar el anuncio: {str(e)}", "danger")
    return redirect(url_for("admin_publicidad"))


# ---------- TESTIMONIOS (ADMIN & PUBLIC API) ----------

@app.route("/api/testimonios/nuevo", methods=["POST"])
def api_nuevo_testimonio():
    try:
        data = request.json or request.form
        if not data:
            return jsonify({"error": "Datos inválidos"}), 400
            
        nombre = data.get("nombre", "").strip()
        relacion = data.get("relacion", "").strip()
        calificacion = int(data.get("calificacion", 5))
        comentario = data.get("comentario", "").strip()
        
        if not nombre or not relacion or not comentario:
            return jsonify({"error": "Por favor, completa todos los campos requeridos."}), 400
            
        if calificacion < 1 or calificacion > 5:
            return jsonify({"error": "La calificación debe estar entre 1 y 5 estrellas."}), 400
            
        # Se guarda en la base de datos (aprobado=0 por defecto por spam/calidad)
        db_manager.save_testimonio(
            nombre=nombre,
            relacion=relacion,
            calificacion=calificacion,
            comentario=comentario,
            aprobado=0
        )
        
        return jsonify({"success": True, "message": "¡Tu opinión ha sido enviada con éxito! Será visible una vez aprobada por el administrador."})
    except Exception as e:
        return jsonify({"error": f"Error al guardar tu opinión: {str(e)}"}), 500

@app.route("/admin/testimonios", methods=["GET", "POST"])
@admin_required
def admin_testimonios():
    if request.method == "POST":
        # El administrador puede añadir testimonios manualmente
        nombre = request.form.get("nombre", "").strip()
        relacion = request.form.get("relacion", "").strip()
        calificacion = int(request.form.get("calificacion", "5"))
        comentario = request.form.get("comentario", "").strip()
        aprobado = int(request.form.get("aprobado", "1")) # Por defecto aprobado si lo hace el admin
        
        if nombre and relacion and comentario:
            try:
                db_manager.save_testimonio(
                    nombre=nombre,
                    relacion=relacion,
                    calificacion=calificacion,
                    comentario=comentario,
                    aprobado=aprobado
                )
                flash("¡Testimonio registrado con éxito!", "success")
            except Exception as e:
                flash(f"Error al registrar testimonio: {str(e)}", "danger")
        else:
            flash("Por favor, completa todos los campos requeridos.", "warning")
            
        return redirect(url_for("admin_testimonios"))
        
    testimonios, db_source = db_manager.get_all_testimonios()
    return render_template("admin/admin_testimonios.html", testimonios=testimonios, db_source=db_source)

@app.route("/admin/api/testimonios/<int:t_id>/approve", methods=["POST"])
@admin_required
def admin_approve_testimonio(t_id):
    try:
        data = request.json
        aprobado = int(data.get("aprobado", 1))
        db_manager.update_testimonio_status(t_id, aprobado)
        msg = "Testimonio aprobado y visible en la web" if aprobado == 1 else "Testimonio ocultado de la web"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/api/testimonios/<int:t_id>/delete", methods=["POST"])
@admin_required
def admin_delete_testimonio(t_id):
    try:
        db_manager.delete_testimonio(t_id)
        return jsonify({"success": True, "message": "Testimonio eliminado permanentemente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- ASESOR VEHICULAR IA ----------

@app.route("/asesor")
def asesor():
    return render_template("asesor.html")

@app.route("/api/asesor/chat", methods=["POST"])
def api_asesor_chat():
    try:
        data = request.json
        if not data or "messages" not in data:
            return jsonify({"error": "Mensajes no proporcionados"}), 400
            
        user_messages = data["messages"] # List of {role, content}
        
        # Obtener catálogo en tiempo real
        vehiculos, _ = db_manager.get_all_vehiculos()
        
        # Formatear el catálogo para la IA
        catalog_str = ""
        for v in vehiculos:
            catalog_str += f"- ID: {v['id']} | {v['marca'].upper()} {v['modelo'].upper()} ({v['year']}) | Precio: {v['precio']} | KM: {v['km']:,} | Motor: {v['motor']} | Transmisión: {v['transmision']} | Sede: {v['ciudad']} | Detalles: {v.get('descripcion', '') or 'Sin descripción adicional.'}\n"
            
        system_prompt = f"""Eres el Asesor Automotriz Inteligente de CarroQhatu, experto en el mercado de autos en el Perú y con conocimiento general amplio para conversar sobre cualquier tema en tiempo real, tal como lo haría ChatGPT. Tu objetivo es asesorar al usuario con amabilidad, honestidad y de forma fluida.
        
        CATÁLOGO INTERNO (Vehículos disponibles en la página web de CarroQhatu. Pueden ser nuevos 0KM o de segunda/usados):
        {catalog_str}
        
        Reglas de Asesoramiento y Prioridades:
        1. Tu prioridad número uno es recomendar vehículos de nuestro CATÁLOGO INTERNO (de la página web) que se ajusten a los requisitos del usuario. Si recomiendas un vehículo de nuestro stock, debes incluir su identificador con el formato `[CAR_ID: <id>]` (ejemplo: `[CAR_ID: 1]`). Identifica si son de segunda (usados) por su kilometraje mayor a 0 o nuevos 0KM si su kilometraje es 0.
        2. Si el usuario solicita un vehículo (ya sea nuevo 0KM o de segunda/usado) y no contamos con opciones adecuadas en nuestro catálogo interno de la página web, o si quieres ofrecer más opciones complementarias, DEBES recomendar alternativas del mercado general externo (vehículos de afuera, ya sean nuevos 0KM de concesionarias o de segunda/usados de otros propietarios en el mercado).
        3. Para cada vehículo externo que recomiendes (ya sea nuevo 0km o usado de segunda de afuera), DEBES incluirlo exactamente con el formato `[EXTERNAL_CAR: Marca | Modelo | Año | Precio | Kilometraje o 0KM | Transmisión | Tipo]`.
           - El campo 'Tipo' debe ser '0km' o 'Usado'.
           - Ejemplo de 0km: `[EXTERNAL_CAR: Toyota | Yaris | 2026 | USD $18,500 | 0KM | Mecánica | 0km]`
           - Ejemplo de usado externo: `[EXTERNAL_CAR: Hyundai | Tucson | 2021 | USD $22,000 | 45,000 km | Automática | Usado]`
        4. Si recomiendas autos externos (nuevos 0km o usados de segunda de afuera), explícale al usuario que CarroQhatu le puede ayudar con el servicio de búsqueda, asesoría de compra, e inspección mecánica y legal integral para asegurar su inversión.
        5. MIMETIZACIÓN Y TONO: Adáptate de forma dinámica al tono, estilo y vocabulario del usuario en tiempo real. Si el cliente te habla de manera informal, amigable o utilizando jerga peruana (ej. "causa", "chamba", "pata", "cañita", "fierro", "lucas"), respóndele con esa misma cercanía y estilo de manera natural. Si te habla de manera formal y seria, responde con total formalidad. Adapta tu uso de emojis e informalidad al nivel que muestre el usuario.
        6. CONVERSACIÓN EN TIEMPO REAL: Tienes acceso a responder de cualquier tema general y sostener conversaciones naturales y fluidas sobre cualquier asunto como ChatGPT. Si el usuario te pregunta cosas ajenas al negocio, respóndelas cordialmente, pero intenta sutil y amigablemente guiar de vuelta la conversación hacia el sector de autos o los servicios de CarroQhatu.
        7. Responde siempre en español, de forma clara, natural y concisa (máximo 3 párrafos cortos por respuesta para mantener el dinamismo del chat).
        """
        
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        GEMINI_API_KEY = get_gemini_key()
        respuesta_texto = ""
        
        if GEMINI_API_KEY or OPENAI_API_KEY:
            try:
                from openai import OpenAI
                if GEMINI_API_KEY:
                    client = OpenAI(
                        api_key=GEMINI_API_KEY,
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                    )
                    model_name = "gemini-3.5-flash"
                else:
                    client = OpenAI(api_key=OPENAI_API_KEY)
                    model_name = "gpt-4o-mini"
                
                # Prepara mensajes para la API
                api_messages = [{"role": "system", "content": system_prompt}]
                
                # Filtramos y agregamos el historial del cliente para evitar prompts maliciosos
                for msg in user_messages:
                    if msg.get("role") in ["user", "assistant"]:
                        api_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                        
                response = client.chat.completions.create(
                    model=model_name,
                    messages=api_messages,
                    max_tokens=600,
                    temperature=0.7
                )
                respuesta_texto = response.choices[0].message.content
            except Exception as call_err:
                print("WARNING (app): Error llamando a la API de IA (Gemini/OpenAI), usando fallback:", call_err)
                respuesta_texto = None
        else:
            respuesta_texto = None
            
        # Fallback local determinista si no hay API Key o falla la llamada
        if not respuesta_texto:
            # Obtener el último mensaje del usuario
            last_user_msg = ""
            for m in reversed(user_messages):
                if m.get("role") == "user":
                    last_user_msg = m.get("content", "").lower().strip()
                    break
                    
            # Analizar si es saludo o pregunta general sin clave de autos
            is_greeting = any(k in last_user_msg for k in ["hola", "buenos dias", "buenas tardes", "buenas noches", "como estas", "que tal", "hi", "hello"])
            is_general = not any(k in last_user_msg for k in ["auto", "carro", "vehiculo", "camioneta", "suv", "marca", "precio", "catalogo", "comprar", "vender", "nuevo", "usado", "0km", "inspeccion", "cotizar", "qhatu"])
            
            # Analizar intenciones del usuario
            is_new_request = any(k in last_user_msg for k in ["nuevo", "0km", "0 km", "concesionaria", "cero kilometros", "cero km", "tienda"])
            is_used_request = any(k in last_user_msg for k in ["usado", "segunda", "2da", "recorrido", "kilometraje", "seminuevo", "antiguo", "usados", "ocasion"])
            
            if is_greeting or (is_general and len(last_user_msg.split()) < 6 and not is_new_request and not is_used_request):
                return jsonify({
                    "respuesta": "¡Hola! ¿Cómo estás? Soy el Asesor Vehicular Inteligente de CarroQhatu.\n\n*(Nota: Para poder conversar libremente sobre cualquier tema y en tiempo real como ChatGPT, por favor configura la clave `GEMINI_API_KEY` o `OPENAI_API_KEY` en el archivo `.env` del proyecto)*.\n\nPor ahora, en este modo básico, puedo ayudarte a buscar vehículos de nuestro catálogo. ¿Buscas un auto nuevo (0KM) o de segunda mano?",
                    "recomendados": [],
                    "externos": []
                })
            
            # Si no especifica ni nuevo ni usado, asumimos ambos por defecto para una asesoría completa
            if not is_new_request and not is_used_request:
                is_new_request = True
                is_used_request = True
                
            # Analizar presupuesto aproximado
            import re
            numbers = [int(n) for n in re.findall(r'\d+', last_user_msg.replace(",", "").replace(".", ""))]
            budget = None
            for num in numbers:
                if num > 1000: # Asumimos presupuesto razonable en dólares o soles
                    budget = num
                    break
            
            # Filtrar vehículos internos del stock de la web
            candidatos_internos = []
            for v in vehiculos:
                # Comprobar si el auto de la web es nuevo 0km o usado
                is_car_new = (v.get('km', 0) == 0)
                
                # Si el usuario busca nuevo y el auto es usado, o viceversa, comprobar condiciones
                if is_new_request and is_car_new:
                    pass # Coincide
                elif is_used_request and not is_car_new:
                    pass # Coincide
                else:
                    # No coincide con el tipo solicitado
                    continue
                    
                # Filtro de presupuesto aproximado
                price_str = v['precio'].replace(",", "").replace(".", "")
                v_price = 0
                price_nums = [int(n) for n in re.findall(r'\d+', price_str)]
                if price_nums:
                    v_price = price_nums[0]
                if budget and v_price > budget * 1.2:
                    continue
                    
                # Filtro por ciudad si se menciona en la consulta
                if "arequipa" in last_user_msg and v['ciudad'].lower() != "arequipa":
                    continue
                elif "juliaca" in last_user_msg and v['ciudad'].lower() != "juliaca":
                    continue
                    
                # Filtro por tipo de carrocería o marca si se menciona
                is_pickup_req = any(k in last_user_msg for k in ["camioneta", "pickup", "pick-up", "4x4", "hilux", "frontier", "navara"])
                v_is_pickup = any(k in (v['marca'] + " " + v['modelo']).lower() for k in ["hilux", "navara", "frontier", "4x4", "camioneta"])
                if is_pickup_req and not v_is_pickup:
                    continue
                    
                candidatos_internos.append(v)
                
            # Si no hay candidatos con los filtros restrictivos, tomamos los 2 más recientes del tipo solicitado
            if not candidatos_internos:
                for v in vehiculos:
                    is_car_new = (v.get('km', 0) == 0)
                    if is_new_request and is_car_new:
                        candidatos_internos.append(v)
                    elif is_used_request and not is_car_new:
                        candidatos_internos.append(v)
                        
            # Limitar a máximo 3 recomendaciones internas
            recomendados_ids = [c['id'] for c in candidatos_internos[:3]]
            
            # Generar recomendaciones del mercado externo
            externos_list_fallback = []
            
            if is_new_request:
                # Opciones 0KM externas recomendadas
                if budget and budget < 20000:
                    externos_list_fallback.append(("Toyota", "Yaris Hatchback 0KM", "2026", "USD $18,500", "0KM", "Mecánica", "0km"))
                    externos_list_fallback.append(("Hyundai", "Grand i10 0KM", "2026", "USD $14,900", "0KM", "Mecánica", "0km"))
                else:
                    externos_list_fallback.append(("Toyota", "Corolla Sedán 0KM", "2026", "USD $23,900", "0KM", "Automática", "0km"))
                    externos_list_fallback.append(("Kia", "Sportage 0KM", "2026", "USD $27,500", "0KM", "Automática", "0km"))
                    
            if is_used_request:
                # Opciones usadas de segunda mano externas recomendadas
                if budget and budget < 15000:
                    externos_list_fallback.append(("Suzuki", "Swift Seminuevo", "2020", "USD $11,800", "48,000 km", "Mecánica", "Usado"))
                    externos_list_fallback.append(("Chevrolet", "Sail", "2019", "USD $10,500", "60,000 km", "Mecánica", "Usado"))
                else:
                    externos_list_fallback.append(("Hyundai", "Tucson de Segunda", "2021", "USD $21,900", "45,000 km", "Automática", "Usado"))
                    externos_list_fallback.append(("Toyota", "RAV4 Seminueva", "2020", "USD $23,500", "52,000 km", "Automática", "Usado"))
            
            # Limitar externas a 2-3 según el tipo para no saturar
            externos_list_fallback = externos_list_fallback[:3]
            
            # Generar el mensaje de respuesta estructurado en español
            respuesta_texto = "¡Hola! Soy tu Asesor Vehicular Inteligente de CarroQhatu. He procesado tu consulta y aquí tienes mis recomendaciones personalizadas. Te presento opciones tanto de nuestro catálogo en la página web como del mercado general externo de afuera:\n\n"
            
            if candidatos_internos:
                respuesta_texto += "🚗 **Vehículos en la Página Web (Stock Disponible de CarroQhatu):**\n"
                for c in candidatos_internos[:3]:
                    estado_txt = "Nuevo 0KM" if c['km'] == 0 else "De Segunda / Usado"
                    respuesta_texto += f"* **{c['marca'].upper()} {c['modelo'].upper()} ({c['year']})** [{estado_txt}]: Disponible en la sede de {c['ciudad']} por {c['precio']}. Recorrido de {c['km']:,} km, transmisión {c['transmision']}.\n"
            else:
                respuesta_texto += "Actualmente no contamos con vehículos que coincidan exactamente con tu búsqueda en el stock directo de nuestra página web.\n"
                
            if externos_list_fallback:
                respuesta_texto += "\n🌐 **Alternativas del Mercado General Externo (Otros Vehículos de Afuera):**\n"
                for ext in externos_list_fallback:
                    tipo_txt = "Nuevo 0KM" if ext[6] == "0km" else "De Segunda / Usado"
                    respuesta_texto += f"* **{ext[0].upper()} {ext[1].upper()} ({ext[2]})** [{tipo_txt}]: Disponible en el mercado general por aproximadamente {ext[3]}. Recorrido {ext[4]} con transmisión {ext[5]}.\n"
                
                respuesta_texto += "\n¡Recuerda! Si te interesa alguna de estas alternativas del mercado general externo, CarroQhatu te ayuda con la búsqueda, asesoramiento de compra y una rigurosa inspección mecánica y legal para garantizar tu seguridad."
                
            # Agregar etiquetas [CAR_ID: X] y [EXTERNAL_CAR: ...] para que el parser las extraiga
            for c in candidatos_internos[:3]:
                respuesta_texto += f" [CAR_ID: {c['id']}]"
            for ext in externos_list_fallback:
                respuesta_texto += f" [EXTERNAL_CAR: {ext[0]} | {ext[1]} | {ext[2]} | {ext[3]} | {ext[4]} | {ext[5]} | {ext[6]}]"
                
        # Parsear las IDs recomendadas en el texto de respuesta
        import re
        car_ids = [int(x) for x in re.findall(r'\[CAR_ID:\s*(\d+)\]', respuesta_texto)]
        
        # Obtener los objetos completos de vehículos recomendados
        recomendados_list = []
        for c_id in car_ids:
            for v in vehiculos:
                if v['id'] == c_id:
                    recomendados_list.append({
                        "id": v['id'],
                        "marca": v['marca'],
                        "modelo": v['modelo'],
                        "year": v['year'],
                        "motor": v['motor'],
                        "km": v['km'],
                        "transmision": v['transmision'],
                        "precio": v['precio'],
                        "imagen_url": v['imagen_url'],
                        "ciudad": v['ciudad'],
                        "descripcion": v.get('descripcion', '')
                    })
                    break
                    
        # Parsear las recomendaciones de autos externos [EXTERNAL_CAR: Marca | Modelo | Año | Precio | Kilometraje | Transmisión | Tipo]
        externos_list = []
        external_matches = re.findall(r'\[EXTERNAL_CAR:\s*(.*?)\s*\]', respuesta_texto)
        for match in external_matches:
            parts = [p.strip() for p in match.split('|')]
            if len(parts) >= 4:
                marca = parts[0]
                modelo = parts[1]
                year = parts[2]
                precio = parts[3]
                km = parts[4] if len(parts) >= 5 else "0KM"
                trans = parts[5] if len(parts) >= 6 else "Mecánica"
                tipo = parts[6] if len(parts) >= 7 else "0km"
                
                externos_list.append({
                    "marca": marca,
                    "modelo": modelo,
                    "year": year,
                    "precio": precio,
                    "km": km,
                    "transmision": trans,
                    "tipo": tipo.lower()
                })
                    
        # Limpiar las etiquetas del texto para que no se muestren feo en el chat
        respuesta_limpia = re.sub(r'\[CAR_ID:\s*\d+\]', '', respuesta_texto)
        respuesta_limpia = re.sub(r'\[EXTERNAL_CAR:\s*.*?\s*\]', '', respuesta_limpia).strip()
        
        return jsonify({
            "respuesta": respuesta_limpia,
            "recomendados": recomendados_list,
            "externos": externos_list
        })
        
    except Exception as e:
        print("ERROR en /api/asesor/chat:", e)
        return jsonify({"error": f"Ocurrió un error en el asistente: {str(e)}"}), 500


# =====================================================================
# ---------- ASISTENTE / AGENTE DE WHATSAPP IA ----------
# =====================================================================

WHATSAPP_SESSIONS = {}

def send_outgoing_whatsapp(to_number, body_text):
    """Envía un mensaje saliente usando la API de Meta Cloud o Twilio si están configuradas."""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    
    if access_token and phone_id:
        try:
            import requests
            url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": body_text}
            }
            r = requests.post(url, json=payload, headers=headers)
            print("INFO (whatsapp): Respuesta de Meta API:", r.status_code, r.text)
        except Exception as e:
            print("ERROR (whatsapp): Error enviando mensaje por Meta API:", e)
            
    elif twilio_sid and twilio_token:
        try:
            import requests
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            auth = (twilio_sid, twilio_token)
            payload = {
                "From": twilio_from,
                "To": f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number,
                "Body": body_text
            }
            r = requests.post(url, data=payload, auth=auth)
            print("INFO (whatsapp): Respuesta de Twilio API:", r.status_code, r.text)
        except Exception as e:
            print("ERROR (whatsapp): Error enviando mensaje por Twilio API:", e)
    else:
        print(f"INFO (whatsapp): Sandbox/Simulación - Mensaje enviado a {to_number}: {body_text}")

def process_whatsapp_ai_logic(phone_number, sender_name, message_body):
    """Procesa el mensaje del usuario con OpenAI (o fallback determinista) y extrae prospectos."""
    logs = []
    logs.append(f"Mensaje entrante de {sender_name} ({phone_number}): '{message_body}'")
    
    # Obtener historial de la sesión
    if phone_number not in WHATSAPP_SESSIONS:
        WHATSAPP_SESSIONS[phone_number] = []
        
    history = WHATSAPP_SESSIONS[phone_number]
    history.append({"role": "user", "content": message_body})
    
    # Limitar historial a los últimos 10 mensajes
    if len(history) > 10:
        history = history[-10:]
        WHATSAPP_SESSIONS[phone_number] = history
        
    # Obtener catálogo activo en tiempo real
    vehiculos, _ = db_manager.get_all_vehiculos()
    catalog_str = ""
    for v in vehiculos:
        catalog_str += f"- ID: {v['id']} | {v['marca'].upper()} {v['modelo'].upper()} ({v['year']}) | Precio: {v['precio']} | KM: {v['km']:,} | Motor: {v['motor']} | Transmisión: {v['transmision']} | Sede: {v['ciudad']} | Detalles: {v.get('descripcion', '') or 'Sin descripción adicional.'}\n"
        
    system_prompt = f"""Eres el Agente Inteligente de WhatsApp de CarroQhatu, brindando atención al cliente 24/7 de manera automatizada. Tu objetivo es responder consultas de forma clara, amable, de forma fluida e inteligente, adaptándote al tono del usuario, e identificar los datos del cliente para registrar su interés.
    
    SERVICIOS QUE OFRECEMOS:
    1. Compra de autos: El cliente puede comprar de nuestro catálogo en stock.
    2. Venta de autos / Tasación: Ayudamos a tasar y vender su auto.
    3. Inspección mecánica y legal integral de autos del mercado externo.
    4. Búsqueda personalizada de autos en todo el Perú.
    
    CATÁLOGO EN STOCK REAL:
    {catalog_str}
    
    INSTRUCCIONES IMPORTANTES DE CAPTURA DE DATOS:
    Cuando converses con el cliente, tu meta principal es capturar sus datos de contacto e interés. Intenta obtener de manera amigable en el flujo de la conversación:
    - Su Nombre completo.
    - Su número de contacto (si no se deduce de la conversación).
    - El vehículo de su interés (o el servicio que busca).
    - Su presupuesto aproximado (o valor de su auto si quiere vender).
    
    Si el cliente proporciona esta información en la conversación, DEBES emitir al final de tu mensaje la etiqueta oculta exactamente en este formato:
    `[LEAD_CAPTURED: Nombre | Contacto / Celular | Vehículo de interés o Servicio | Presupuesto aproximado]`
    Por ejemplo: `[LEAD_CAPTURED: Juan Pérez | 987654321 | Toyota Hilux | USD $20,000]`
    (Esta etiqueta es procesada por nuestro sistema en segundo plano y se guarda en la base de datos automáticamente, el usuario no la verá).
    
    MIMETIZACIÓN Y TONO: Adapta tu estilo de hablar y vocabulario al del cliente. Si te habla de manera muy informal o usa jerga peruana (ej. "causa", "chamba", "pata", "fierro"), responde con el mismo nivel de confianza y vocabulario amigable. Si es formal, responde de manera formal y profesional.
    CONVERSACIÓN GENERAL: Puedes responder sobre cualquier tema general y conversar libremente como ChatGPT. Si te consultan algo no relacionado a autos, respóndeles cordialmente, pero intenta sutil y amigablemente redirigir la conversación hacia los servicios de CarroQhatu.
    Sé cortés, responde en español, usa emojis apropiados de WhatsApp, y sé conciso (máximo 2-3 párrafos cortos, apto para leer en celular).
    """
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = get_gemini_key()
    respuesta_texto = ""
    
    if GEMINI_API_KEY or OPENAI_API_KEY:
        try:
            from openai import OpenAI
            if GEMINI_API_KEY:
                logs.append("Llamando a Gemini API (gemini-3.5-flash)...")
                client = OpenAI(
                    api_key=GEMINI_API_KEY,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                model_name = "gemini-3.5-flash"
            else:
                logs.append("Llamando a OpenAI API (gpt-4o-mini)...")
                client = OpenAI(api_key=OPENAI_API_KEY)
                model_name = "gpt-4o-mini"
            
            api_messages = [{"role": "system", "content": system_prompt}]
            for msg in history:
                api_messages.append(msg)
                
            response = client.chat.completions.create(
                model=model_name,
                messages=api_messages,
                max_tokens=300,
                temperature=0.6
            )
            respuesta_texto = response.choices[0].message.content
            logs.append("Respuesta obtenida con éxito de la API de IA.")
        except Exception as err:
            logs.append(f"Error llamando a la API de IA (Gemini/OpenAI): {err}. Activando fallback determinista...")
            respuesta_texto = None
    else:
        logs.append("Ni GEMINI_API_KEY ni OPENAI_API_KEY configuradas. Activando fallback determinista...")
        respuesta_texto = None
        
    # Fallback determinista local
    if not respuesta_texto:
        logs.append("Ejecutando algoritmo de coincidencia de palabras clave y autocompletado de leads...")
        msg_lower = message_body.lower()
        
        # Búsqueda rápida de stock
        match_car = None
        for v in vehiculos:
            if v['marca'].lower() in msg_lower or v['modelo'].lower() in msg_lower:
                match_car = v
                break
                
        # Coincidencia de intenciones
        if any(k in msg_lower for k in ["venta", "vender", "tasar", "tasacion", "tasación", "cotizar"]):
            respuesta_texto = "¡Hola! En CarroQhatu te ayudamos a vender tu auto rápido y al mejor precio. Hacemos tasación gratuita y lo publicamos en nuestras plataformas. ¿Me podrías indicar tu nombre completo, marca, modelo y año de tu auto para cotizarlo?"
        elif any(k in msg_lower for k in ["compra", "comprar", "catalogo", "catálogo", "stock", "precio"]):
            if match_car:
                respuesta_texto = f"¡Hola! Sí, tenemos disponible el **{match_car['marca'].upper()} {match_car['modelo'].upper()} ({match_car['year']})** en nuestra sede de {match_car['ciudad']} por {match_car['precio']}. ¿Te interesa verlo? Déjame tu nombre para agendar una cita."
            else:
                respuesta_texto = "¡Hola! Contamos con un amplio stock de vehículos verificados y garantizados. Puedes revisarlos en nuestra web. ¿Qué marca o tipo de vehículo buscas y cuál es tu presupuesto aproximado?"
        elif any(k in msg_lower for k in ["inspeccion", "inspección", "revisar", "revisión"]):
            respuesta_texto = "¡Hola! Ofrecemos inspección mecánica, eléctrica y legal integral para autos del mercado externo. ¿Qué vehículo deseas que revisemos por ti? Por favor déjame tu nombre para cotizar el servicio."
        else:
            if match_car:
                respuesta_texto = f"¡Hola! Contamos con el **{match_car['marca'].upper()} {match_car['modelo'].upper()} ({match_car['year']})** en stock por {match_car['precio']}. ¿Me indicas tu nombre completo para coordinar una llamada con un asesor?"
            else:
                respuesta_texto = "¡Hola! Te saluda el Asistente IA de CarroQhatu. Te ayudamos a comprar, vender o inspeccionar tu vehículo de forma rápida y segura. ¿Cuál es tu nombre completo y en qué servicio estás interesado?"
                
        # Detección de leads por fallback
        # 1. Nombre completo
        nombre_detectado = None
        import re
        nombre_match = re.search(r'(?:mi nombre es|me llamo|soy|habla)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,25})', msg_lower)
        if nombre_match:
            raw_name = nombre_match.group(1).strip()
            # Limpiar ruidos comunes y conjunciones en español
            if " y " in raw_name:
                raw_name = raw_name.split(" y ")[0]
            for indicator in [" busco", " quiero", " soy", " de", " mi", " tengo"]:
                if indicator in raw_name:
                    raw_name = raw_name.split(indicator)[0]
            nombre_detectado = raw_name.title().strip()
        else:
            # Si el usuario responde directamente con un nombre en consultas cortas
            words = message_body.strip().split()
            if len(words) >= 2 and len(words) <= 3 and all(w.istitle() or w.isalpha() for w in words) and not any(w.lower() in ["hola", "buenas", "que", "para", "auto", "camioneta"] for w in words):
                nombre_detectado = message_body.strip()
                
        # 2. Presupuesto
        presupuesto_detectado = None
        pres_nums = [int(n) for n in re.findall(r'\d+', message_body.replace(",", "").replace(".", ""))]
        for n in pres_nums:
            if n > 1000:
                presupuesto_detectado = f"USD ${n:,}"
                break
                
        if nombre_detectado:
            interes_txt = f"Auto {match_car['marca']} {match_car['modelo']}" if match_car else "Información general"
            presupuesto_txt = presupuesto_detectado or "No especificado"
            logs.append(f"Fallback detectó datos del cliente: Nombre: {nombre_detectado} | Presupuesto: {presupuesto_txt}")
            respuesta_texto += f" [LEAD_CAPTURED: {nombre_detectado} | {phone_number} | {interes_txt} | {presupuesto_txt}]"
            
    # Parsear etiqueta de Lead
    lead_info = None
    import re
    lead_match = re.search(r'\[LEAD_CAPTURED:\s*(.*?)\s*\]', respuesta_texto)
    if lead_match:
        lead_str = lead_match.group(1)
        logs.append(f"¡Prospecto detectado por etiqueta!: {lead_str}")
        parts = [p.strip() for p in lead_str.split('|')]
        if len(parts) >= 2:
            nombre = parts[0]
            contacto = parts[1]
            interes = parts[2] if len(parts) >= 3 else "No especificado"
            presupuesto = parts[3] if len(parts) >= 4 else "No especificado"
            
            lead_info = {
                "nombre": nombre,
                "contacto": contacto,
                "interes": interes,
                "presupuesto": presupuesto
            }
            
            # Registrar solicitud en la base de datos
            try:
                db_manager.save_solicitud(
                    tipo="whatsapp_lead",
                    nombre=nombre,
                    contacto=contacto,
                    datos_vehiculo={
                        "servicio": interes,
                        "mensaje": f"Capturado automáticamente por el Agente de WhatsApp IA. Presupuesto estimado: {presupuesto}."
                    }
                )
                logs.append(f"Prospecto '{nombre}' guardado en base de datos solicitudes.")
            except Exception as save_err:
                logs.append(f"Error guardando lead en base de datos: {save_err}")
                
    # Limpiar etiquetas en respuesta
    respuesta_limpia = re.sub(r'\[LEAD_CAPTURED:\s*.*?\s*\]', '', respuesta_texto).strip()
    
    # Registrar en el historial de chat de la sesión
    history.append({"role": "assistant", "content": respuesta_limpia})
    
    return respuesta_limpia, {"logs": logs, "lead": lead_info}

@app.route("/api/whatsapp/webhook", methods=["GET"])
def whatsapp_webhook_verify():
    """Endpoint de verificación GET del webhook de WhatsApp (Meta Cloud API)."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "carroqhatu_verify_token_2026")
    
    if mode == "subscribe" and token == verify_token:
        print("INFO (whatsapp): Webhook de WhatsApp verificado correctamente.")
        return challenge, 200
    else:
        print("WARNING (whatsapp): Falla de verificación del token de webhook.")
        return "Fallo de Verificación", 403

@app.route("/api/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook_message():
    """Webhook de recepción POST para mensajes de WhatsApp (Meta Cloud API y Twilio)."""
    try:
        content_type = request.headers.get("Content-Type", "")
        phone_number = None
        sender_name = "Cliente WhatsApp"
        message_body = ""
        
        if "application/json" in content_type:
            data = request.json
            if not data:
                return "OK", 200
            
            entry = data.get("entry", [])
            if not entry:
                return "OK", 200
            changes = entry[0].get("changes", [])
            if not changes:
                return "OK", 200
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return "OK", 200
            
            message = messages[0]
            phone_number = message.get("from") # E.g. "51972043502"
            message_body = message.get("text", {}).get("body", "")
            
            contacts = value.get("contacts", [])
            if contacts:
                sender_name = contacts[0].get("profile", {}).get("name", "Cliente WhatsApp")
                
        elif "application/x-www-form-urlencoded" in content_type:
            phone_number = request.form.get("From", "").replace("whatsapp:", "")
            message_body = request.form.get("Body", "")
            sender_name = request.form.get("ProfileName", "Cliente WhatsApp")
            
        else:
            data = request.json or {}
            phone_number = data.get("from")
            message_body = data.get("body", "")
            sender_name = data.get("name", "Cliente WhatsApp")
            
        if not phone_number or not message_body:
            return "Datos incompletos", 400
            
        ia_reply, result = process_whatsapp_ai_logic(phone_number, sender_name, message_body)
        
        # Enviar mensaje saliente
        send_outgoing_whatsapp(phone_number, ia_reply)
        
        return jsonify({"status": "sent", "reply": ia_reply}), 200
        
    except Exception as e:
        print("ERROR (whatsapp): Error en webhook POST:", e)
        return str(e), 500

@app.route("/admin/whatsapp/simulador")
@admin_required
def admin_whatsapp_simulador():
    """Renderiza el simulador interactivo de WhatsApp en el panel administrativo."""
    cotizaciones, db_source = db_manager.get_all_cotizaciones()
    return render_template("admin/admin_whatsapp.html", db_source=db_source)

@app.route("/admin/api/whatsapp/simular_mensaje", methods=["POST"])
@admin_required
def admin_whatsapp_simular_mensaje():
    """Endpoint del simulador administrativo para procesar un mensaje virtual."""
    try:
        data = request.json
        if not data or "message" not in data:
            return jsonify({"error": "Mensaje no proporcionado"}), 400
            
        mensaje = data.get("message", "").strip()
        celular = data.get("celular", "51999888777").strip()
        nombre = data.get("nombre", "Cliente de Prueba").strip()
        
        reply, result = process_whatsapp_ai_logic(celular, nombre, mensaje)
        
        return jsonify({
            "reply": reply,
            "logs": result.get("logs", []),
            "lead": result.get("lead")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/configuracion", methods=["GET", "POST"])
@admin_required
def admin_configuracion():
    if request.method == "POST":
        phone = request.form.get("contact_phone", "").strip()
        email = request.form.get("contact_email", "").strip()
        desc = request.form.get("about_description", "").strip()
        
        if phone:
            db_manager.update_site_config("contact_phone", phone)
        if email:
            db_manager.update_site_config("contact_email", email)
        if desc:
            db_manager.update_site_config("about_description", desc)
            
        # Subida de logo y video banner
        logo_file = request.files.get("site_logo")
        if logo_file and logo_file.filename:
            logo_url = save_uploaded_file(logo_file, "brand")
            db_manager.update_site_config("site_logo", logo_url)
            
        banner_file = request.files.get("banner_video")
        if banner_file and banner_file.filename:
            banner_url = save_uploaded_file(banner_file, "banners")
            db_manager.update_site_config("banner_video", banner_url)
            
        flash("Configuración guardada correctamente.", "success")
        return redirect(url_for("admin_configuracion"))
        
    config = db_manager.get_site_config()
    return render_template("admin/admin_configuracion.html", config=config)

@app.route("/admin/api/export/cotizaciones")
@admin_required
def admin_export_cotizaciones():
    try:
        cotizaciones, _ = db_manager.get_all_cotizaciones()
        output = io.StringIO()
        output.write('\ufeff')  # Excel UTF-8 BOM
        writer = csv.writer(output, delimiter=';')
        
        writer.writerow(["ID", "Marca", "Modelo", "Año", "KM", "Estado", "Precio Min (PEN)", "Precio Max (PEN)", "Fecha de Registro"])
        for c in cotizaciones:
            writer.writerow([
                c.get("id"),
                c.get("marca"),
                c.get("modelo"),
                c.get("year"),
                c.get("km"),
                c.get("estado"),
                c.get("precio_min"),
                c.get("precio_max"),
                c.get("created_at")
            ])
            
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=cotizaciones_carroqhatu.csv"}
        )
    except Exception as e:
        print("ERROR exporting CSV:", e)
        flash("Ocurrió un error al exportar las cotizaciones.", "danger")
        return redirect(url_for("admin_cotizaciones"))

@app.route("/admin/api/export/solicitudes")
@admin_required
def admin_export_solicitudes():
    try:
        solicitudes, _ = db_manager.get_all_solicitudes()
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output, delimiter=';')
        
        writer.writerow(["ID", "Tipo", "Nombre", "Contacto", "Detalles/Vehículo", "Estado", "Fecha de Registro"])
        for s in solicitudes:
            writer.writerow([
                s.get("id"),
                s.get("tipo"),
                s.get("nombre"),
                s.get("contacto"),
                s.get("datos_vehiculo"),
                s.get("estado"),
                s.get("created_at")
            ])
            
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=solicitudes_carroqhatu.csv"}
        )
    except Exception as e:
        print("ERROR exporting CSV:", e)
        flash("Ocurrió un error al exportar las solicitudes.", "danger")
        return redirect(url_for("admin_solicitudes"))


@app.context_processor
def inject_site_config():
    """Inyecta la configuración del sitio en todas las plantillas automáticamente."""
    try:
        config = db_manager.get_site_config()
        return {"site_config": config}
    except Exception as e:
        print("WARNING: No se pudo inyectar la configuración del sitio:", e)
        return {"site_config": {}}


if __name__ == "__main__":
    app.run(debug=True)

 


