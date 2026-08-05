from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file, flash
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
import os
import json
import db_manager
from datetime import timedelta
import hmac
import time
from werkzeug.security import check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "carroqhatu_secret_key_2026")

# Configuración de seguridad para cookies de sesión de Flask
app.config.update(
    SESSION_COOKIE_SECURE=not app.debug,         # Solo enviar sobre HTTPS en producción (Render)
    SESSION_COOKIE_HTTPONLY=True,                # Evitar acceso desde scripts JS (XSS)
    SESSION_COOKIE_SAMESITE='Lax',               # Mitigación contra ataques CSRF
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2) # Expiración de sesión tras 2 horas de inactividad
)

# Registro global en memoria para limitar intentos de acceso: { ip: {"attempts": int, "blocked_until": float} }
FAILED_LOGIN_ATTEMPTS = {}

@app.after_request
def add_security_headers(response):
    """Agrega cabeceras HTTP de seguridad robustas a todas las respuestas del servidor."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy compatible pero restrictiva
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' https:; "
        "script-src 'self' 'unsafe-inline' https://code.jquery.com https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://stackpath.bootstrapcdn.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:;"
    )
    
    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
    return response

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as init_err:
        print("WARNING: No se pudo inicializar el cliente de Supabase:", init_err)

def get_gemini_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Falta configurar GEMINI_API_KEY")
    return key

def get_ai_completion(api_messages, max_tokens=2000, temperature=0.7):
    """Llama a la API de IA (Gemini u OpenAI) con reintentos multimodelo automáticos."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    try:
        GEMINI_API_KEY = get_gemini_key()
    except RuntimeError:
        GEMINI_API_KEY = None

    if not (GEMINI_API_KEY or OPENAI_API_KEY):
        return None

    from openai import OpenAI
    
    if GEMINI_API_KEY:
        client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        models_to_try = ["gemini-flash-latest", "gemini-2.0-flash", "gemini-pro-latest", "gemini-2.0-flash-lite"]
        last_error = None
        for m_name in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=m_name,
                    messages=api_messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                content = response.choices[0].message.content
                if content:
                    return content
            except Exception as e:
                last_error = e
                print(f"WARNING (app): Intento con modelo {m_name} falló: {e}")
                continue
        if last_error:
            raise last_error
    else:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content

    return None

# ---------- VISTAS ----------
@app.route("/")
def index():
    vehiculos, _ = db_manager.get_all_vehiculos()
    publicidad, _ = db_manager.get_all_publicidad()
    videos, _ = db_manager.get_active_videos()
    return render_template("index.html", vehiculos=vehiculos, publicidad=publicidad, videos=videos)

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
    vehiculo_id = request.args.get("id")
    car = None
    vehiculos, _ = db_manager.get_all_vehiculos()
    if vehiculo_id:
        try:
            # Buscar primero por ID numérico en la BD
            try:
                numeric_id = int(vehiculo_id)
                car = db_manager.get_vehiculo_by_id(numeric_id)
            except (ValueError, TypeError):
                car = None
                
            if not car and vehiculos:
                for v in vehiculos:
                    if str(v.get('id')) == str(vehiculo_id):
                        car = v
                        break
                        
            if car:
                raw_extra = car.get("imagenes_extra")
                if isinstance(raw_extra, str) and raw_extra.strip():
                    try:
                        car["imagenes_extra_list"] = json.loads(raw_extra)
                    except:
                        car["imagenes_extra_list"] = [x.strip() for x in raw_extra.split(",") if x.strip()]
                elif isinstance(raw_extra, list):
                    car["imagenes_extra_list"] = raw_extra
                else:
                    car["imagenes_extra_list"] = []
        except Exception as e:
            print("Error en ruta /detail cargando vehiculo:", e)
            car = None
    return render_template("detail.html", car=car, vehiculos=vehiculos)

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

@app.route("/manifest.json")
def serve_manifest():
    return send_file(os.path.join(app.root_path, "static", "manifest.json"), mimetype="application/json")

@app.route("/sw.js")
def serve_sw():
    response = send_file(os.path.join(app.root_path, "static", "sw.js"), mimetype="application/javascript")
    response.headers["Service-Worker-Allowed"] = "/"
    return response

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
        data = request.json or {}

        marca = str(data.get('marca', '')).strip()
        modelo = str(data.get('modelo', '')).strip()
        year = str(data.get('year', '')).strip()
        km = data.get('km', '')
        estado = str(data.get('estado', '')).strip()
        ubicacion = str(data.get('ubicacion', 'Perú')).strip()
        precio_min = data.get('min', 0)
        precio_max = data.get('max', 0)

        # Intento con IA asistida
        respuesta_ia = None
        api_messages = [
            {
                "role": "system", 
                "content": (
                    "Eres un asesor automotriz experto de CarroQhatu en Perú. "
                    "Responde DIRECTAMENTE con la explicación técnica y comercial en 2 a 3 oraciones completas. "
                    "REGLA OBLIGATORIA: NO uses saludos como '¡Hola!', NO te presentes, NO uses frases de cortesía como 'Con gusto te explico'. "
                    "Comienza DIRECTAMENTE explicando los factores del precio."
                )
            },
            {
                "role": "user", 
                "content": f"""
Explica directamente los factores del precio para este auto:
- Vehículo: {marca} {modelo} ({year})
- Kilometraje: {km} km | Estado: {estado} | Ubicación: {ubicacion}
- Rango de precio: S/. {precio_min:,.0f} a S/. {precio_max:,.0f} soles

Explica la depreciación, demanda en {ubicacion} y estado del vehículo de forma clara y directa en máximo 3 oraciones.
"""
            }
        ]

        try:
            raw_response = get_ai_completion(api_messages, max_tokens=600, temperature=0.7)
            if raw_response:
                import re
                clean = re.sub(r'^(¡?Hola!?\s*|Con gusto\s*|Claro,?\s*|Saludos,?\s*)+', '', raw_response.strip(), flags=re.IGNORECASE).strip()
                invalid_keywords = ["check", "constraint", "persona", "expert", "direct response", "yes.", "no."]
                if not any(k in clean.lower() for k in invalid_keywords) and len(clean) > 60:
                    if clean.endswith('S/.') or clean.endswith('S/'):
                        clean = ""
                    elif not clean[-1] in '.!?':
                        # Evitar cortar en el punto de S/. 
                        clean_check = clean.replace('S/.', 'S_').replace('s/.', 's_')
                        last_period = max(clean_check.rfind('.'), clean_check.rfind('!'), clean_check.rfind('?'))
                        if last_period > 50:
                            clean = clean[:last_period+1]
                        else:
                            clean = ""
                    if len(clean) > 60:
                        respuesta_ia = clean
        except Exception as ai_err:
            print("WARNING (/explicar AI call exception):", ai_err)
            respuesta_ia = None

        if respuesta_ia and len(respuesta_ia) > 60:
            return jsonify({"respuesta": respuesta_ia})

        # --- FALLBACK INTELIGENTE (Garantiza respuesta completa 100% de las veces) ---
        import random
        loc_text = f"la región de {ubicacion}" if ubicacion.lower() not in ["otro", "todo el perú", "perú", "seleccionar", "otro / todo el perú"] else "el mercado peruano"

        km_num = int(km) if str(km).isdigit() else 80000
        if km_num < 30000:
            km_comment = "un kilometraje bajo que preserva muy bien su valor comercial"
        elif km_num < 80000:
            km_comment = "un desgaste moderado y kilometraje idóneo para su uso"
        elif km_num < 150000:
            km_comment = "un kilometraje de uso regular y continuo"
        else:
            km_comment = "un kilometraje avanzado que ajusta el valor referencial"

        estado_clean = estado if estado.lower() not in ["selecccionar", "seleccionar", ""] else "bueno"

        explicaciones = [
            f"El precio estimado de S/. {precio_min:,.0f} a S/. {precio_max:,.0f} para tu {marca} {modelo} ({year}) se determina según la oferta y demanda de {marca} en {loc_text}. Se evalúa {km_comment}, la depreciación por año y su estado de conservación '{estado_clean}'. Este monto es una referencia en tiempo real antes de la inspección presencial.",
            f"Tu {marca} {modelo} ({year}) se cotiza entre S/. {precio_min:,.0f} y S/. {precio_max:,.0f} soles en {loc_text}. Esta tasación pondera la liquidez del modelo, {km_comment} y la condición '{estado_clean}' del vehículo. Te sugerimos realizar la inspección técnica final con nuestros asesores para confirmar el precio definitivo.",
            f"La estimación de S/. {precio_min:,.0f} - S/. {precio_max:,.0f} refleja el rango de transacción frecuente para un {marca} {modelo} del año {year} en {loc_text}. Se ha considerado {km_comment} y un estado '{estado_clean}'. Es una referencia confiable basada en algoritmos de mercado peruano en vivo."
        ]

        respuesta_fallback = random.choice(explicaciones)
        return jsonify({"respuesta": respuesta_fallback})

    except Exception as e:
        print("ERROR /explicar:", e)
        return jsonify({
            "respuesta": "El precio estimado se calcula analizando la marca, modelo, año de fabricación, kilometraje recorrido, estado de conservación y la demanda actual del mercado automotriz peruano. Este valor es una referencia previa a la revisión presencial."
        })


# =====================================================================
# ---------- PANEL DE ADMINISTRACIÓN ----------
# =====================================================================
from functools import wraps
import io
import csv
from flask import Response

def get_client_ip():
    """Obtiene la IP real del cliente detrás de proxies de Render."""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.remote_addr

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            # En vez de redirigir a admin_login y exponer la URL oculta,
            # redirigimos silenciosamente a la página principal pública.
            flash("Acceso no autorizado.", "warning")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

def save_uploaded_file(file, folder):
    """Saves an uploaded file instantly. Saves locally first and attempts Supabase Storage if online."""
    import re, time
    raw_filename = file.filename or "file.jpg"
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', raw_filename)
    unique_filename = f"{int(time.time()*1000)}_{clean_name}"
    
    # 1. Save to local storage first (instant response < 1ms)
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads", folder)
    os.makedirs(upload_dir, exist_ok=True)
    local_path = os.path.join(upload_dir, unique_filename)
    file.seek(0)
    file.save(local_path)
    local_url = f"/static/uploads/{folder}/{unique_filename}"

    # 2. Upload to Supabase Storage if available
    if db_manager.is_supabase_available():
        try:
            file_path = f"{folder}/{unique_filename}"
            with open(local_path, "rb") as f:
                file_bytes = f.read()
            db_manager.supabase.storage.from_("archivos_web").upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": getattr(file, "content_type", "image/jpeg") or "image/jpeg", "x-upsert": "true"}
            )
            public_url = db_manager.supabase.storage.from_("archivos_web").get_public_url(file_path)
            print(f"INFO: Archivo subido a Supabase Storage: {public_url}")
            return public_url
        except Exception as e:
            print(f"WARNING: Error al subir a Supabase Storage ({e}). Usando URL local instantánea.")
            db_manager.mark_supabase_offline()

    print(f"INFO: Archivo guardado localmente: {local_url}")
    return local_url

# Ruta dinámica para el inicio de sesión del administrador
ADMIN_SECRET_SLUG = os.getenv("ADMIN_SECRET_SLUG", "").strip()
login_path = "/admin/login"
if ADMIN_SECRET_SLUG:
    login_path = f"/admin/login-{ADMIN_SECRET_SLUG}"

@app.route(login_path, methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
        
    expected_2fa_pin = os.getenv("ADMIN_2FA_PIN")
    show_2fa = bool(expected_2fa_pin)
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        pin_2fa = request.form.get("pin_2fa")
        
        client_ip = get_client_ip()
        now = time.time()
        
        # 1. Verificar bloqueo temporal por IP
        if client_ip in FAILED_LOGIN_ATTEMPTS:
            block_data = FAILED_LOGIN_ATTEMPTS[client_ip]
            if block_data["blocked_until"] > now:
                remaining_time = int(block_data["blocked_until"] - now)
                flash(f"Demasiados intentos fallidos. IP bloqueada temporalmente por {remaining_time} segundos.", "danger")
                return render_template("admin/admin_login.html", show_2fa=show_2fa)
        
        expected_username = os.getenv("ADMIN_USERNAME", "admin")
        expected_password = os.getenv("ADMIN_PASSWORD", "CarroQhatuAdmin2026")
        expected_password_hash = os.getenv("ADMIN_PASSWORD_HASH")
        
        # 2. Validaciones con hmac y hash de contraseñas
        username_valid = hmac.compare_digest(username.encode('utf-8'), expected_username.encode('utf-8'))
        
        password_valid = False
        if expected_password_hash:
            try:
                password_valid = check_password_hash(expected_password_hash, password)
            except Exception as hash_err:
                print("WARNING (auth): Error al validar con hash, cayendo a contraseña plana:", hash_err)
                password_valid = False
        
        if not expected_password_hash:
            password_valid = hmac.compare_digest(password.encode('utf-8'), expected_password.encode('utf-8'))
            
        pin_valid = True
        if expected_2fa_pin:
            if not pin_2fa:
                pin_valid = False
            else:
                pin_valid = hmac.compare_digest(pin_2fa.encode('utf-8'), expected_2fa_pin.encode('utf-8'))
                
        if username_valid and password_valid and pin_valid:
            # Login correcto: resetear intentos fallidos
            if client_ip in FAILED_LOGIN_ATTEMPTS:
                del FAILED_LOGIN_ATTEMPTS[client_ip]
                
            session["admin_logged_in"] = True
            session.permanent = True  # Mantener sesión por defecto (respetará la expiración de 2 horas)
            flash("Sesión iniciada correctamente.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            # Login incorrecto: retardo artificial de 2 segundos para ralentizar brute force
            time.sleep(2)
            
            # Registrar intento fallido
            if client_ip not in FAILED_LOGIN_ATTEMPTS:
                FAILED_LOGIN_ATTEMPTS[client_ip] = {"attempts": 1, "blocked_until": 0}
            else:
                FAILED_LOGIN_ATTEMPTS[client_ip]["attempts"] += 1
                
            if FAILED_LOGIN_ATTEMPTS[client_ip]["attempts"] >= 5:
                FAILED_LOGIN_ATTEMPTS[client_ip]["blocked_until"] = now + 900  # Bloqueo por 15 minutos (900 seg)
                flash("Demasiados intentos fallidos. Tu dirección IP ha sido bloqueada por 15 minutos.", "danger")
            else:
                flash("Usuario, contraseña o PIN incorrectos.", "danger")
                
    return render_template("admin/admin_login.html", show_2fa=show_2fa)

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
        year = request.form.get("year", "2024").strip()
        motor = request.form.get("motor", "2.0 cc").strip()
        km = request.form.get("km", "0").strip()
        transmision = request.form.get("transmision", "Mecánica").strip()
        precio = request.form.get("precio", "").strip()
        ciudad = request.form.get("ciudad", "Arequipa").strip()
        verificado = int(request.form.get("verificado", "1"))
        descripcion = request.form.get("descripcion", "").strip()
        
        file = request.files.get("imagen_auto")
        imagen_url = ""
        if file and file.filename != "":
            try:
                imagen_url = save_uploaded_file(file, "vehiculos")
            except Exception as e:
                print("Error guardando foto principal:", e)
                
        if not imagen_url:
            imagen_url_alt = request.form.get("imagen_url_alt", "").strip()
            if imagen_url_alt:
                imagen_url = imagen_url_alt
            else:
                imagen_url = "/static/img/HONDA-HR-V.jpg"
        
        if marca and modelo and precio:
            try:
                # Guardar imágenes adicionales (múltiples fotos)
                extra_files = request.files.getlist("imagenes_extra_auto")
                extra_urls = []
                for ef in extra_files:
                    if ef and hasattr(ef, 'filename') and ef.filename != "":
                        try:
                            u = save_uploaded_file(ef, "vehiculos")
                            if u:
                                extra_urls.append(u)
                        except Exception as e_extra:
                            print("Error subiendo foto extra:", e_extra)
                            
                # Si no se adjuntó foto principal pero sí fotos de galería, usar la 1ra como portada
                if extra_urls and (not imagen_url or imagen_url == "/static/img/HONDA-HR-V.jpg"):
                    imagen_url = extra_urls[0]

                imagenes_extra_str = json.dumps(extra_urls) if extra_urls else ""
                
                # Guardar en base de datos
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
                    estado="bueno",
                    verificado=verificado,
                    descripcion=descripcion,
                    imagenes_extra=imagenes_extra_str
                )
                flash("¡Vehículo publicado con éxito en el catálogo web y panel de control!", "success")
            except Exception as e:
                flash(f"Error al registrar el vehículo: {str(e)}", "danger")
        else:
            flash("Por favor, completa los campos requeridos: Marca, Modelo y Precio.", "warning")
            
        return redirect(url_for("admin_vehiculos"))
        
    vehiculos, db_source = db_manager.get_all_vehiculos()
    for car in vehiculos:
        raw_extra = car.get("imagenes_extra")
        if isinstance(raw_extra, str) and raw_extra.strip():
            try:
                car["imagenes_extra_list"] = json.loads(raw_extra)
            except:
                car["imagenes_extra_list"] = [x.strip() for x in raw_extra.split(",") if x.strip()]
        elif isinstance(raw_extra, list):
            car["imagenes_extra_list"] = raw_extra
        else:
            car["imagenes_extra_list"] = []

    return render_template("admin/admin_vehiculos.html", vehiculos=vehiculos, db_source=db_source)

@app.route("/admin/vehiculos/editar/<int:vehiculo_id>", methods=["POST"])
@admin_required
def admin_edit_vehiculo(vehiculo_id):
    existing_car = db_manager.get_vehiculo_by_id(vehiculo_id)
    if not existing_car:
        flash("El vehículo especificado no existe.", "danger")
        return redirect(url_for("admin_vehiculos"))
        
    marca = request.form.get("marca", existing_car.get("marca", "")).strip()
    modelo = request.form.get("modelo", existing_car.get("modelo", "")).strip()
    year = request.form.get("year", existing_car.get("year", "")).strip()
    motor = request.form.get("motor", existing_car.get("motor", "")).strip()
    km = request.form.get("km", str(existing_car.get("km", "0"))).strip()
    transmision = request.form.get("transmision", existing_car.get("transmision", "")).strip()
    precio = request.form.get("precio", existing_car.get("precio", "")).strip()
    ciudad = request.form.get("ciudad", existing_car.get("ciudad", "")).strip()
    verificado = int(request.form.get("verificado", existing_car.get("verificado", 1)))
    descripcion = request.form.get("descripcion", existing_car.get("descripcion", "")).strip()
    
    # Imagen principal
    imagen_url = existing_car.get("imagen_url", "")
    file = request.files.get("imagen_auto")
    if file and file.filename != "":
        try:
            imagen_url = save_uploaded_file(file, "vehiculos")
        except Exception as e:
            flash(f"Error al subir la nueva foto principal del vehículo: {str(e)}", "danger")
            return redirect(url_for("admin_vehiculos"))
            
    # Imágenes extra de la galería
    existing_extra = existing_car.get("imagenes_extra", "")
    try:
        current_extra_list = json.loads(existing_extra) if existing_extra else []
    except:
        current_extra_list = [x.strip() for x in existing_extra.split(",") if x.strip()] if isinstance(existing_extra, str) else []
        
    extra_action = request.form.get("imagenes_extra_action", "append")
    new_extra_files = request.files.getlist("imagenes_extra_auto")
    new_extra_urls = []
    for ef in new_extra_files:
        if ef and ef.filename != "":
            u = save_uploaded_file(ef, "vehiculos")
            new_extra_urls.append(u)

    if extra_action == "replace":
        final_extra_list = new_extra_urls if new_extra_urls else current_extra_list
    elif extra_action == "clear":
        final_extra_list = []
    else: # append / keep
        final_extra_list = current_extra_list + new_extra_urls

    imagenes_extra_str = json.dumps(final_extra_list) if final_extra_list else ""

    if marca and modelo and precio:
        try:
            db_manager.update_vehiculo(
                vehiculo_id=vehiculo_id,
                marca=marca,
                modelo=modelo,
                year=year,
                motor=motor,
                km=km,
                transmision=transmision,
                precio=precio,
                imagen_url=imagen_url,
                ciudad=ciudad,
                verificado=verificado,
                descripcion=descripcion,
                imagenes_extra=imagenes_extra_str
            )
            flash("¡Datos del vehículo e imágenes actualizadas correctamente!", "success")
        except Exception as e:
            flash(f"Error al actualizar el vehículo: {str(e)}", "danger")
    else:
        flash("Por favor, completa los campos requeridos.", "warning")

    return redirect(url_for("admin_vehiculos"))


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


# ---------- VIDEOS Y TIPS (ADMIN) ----------

@app.route("/admin/videos", methods=["GET", "POST"])
@admin_required
def admin_videos():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        categoria = request.form.get("categoria", "Tip Vehicular").strip()
        video_tipo = request.form.get("video_tipo", "url")
        miniatura_tipo = request.form.get("miniatura_tipo", "url")
        
        video_url = ""
        if video_tipo == "file":
            file_v = request.files.get("video_file")
            if file_v and file_v.filename != "":
                try:
                    video_url = save_uploaded_file(file_v, "videos")
                except Exception as e:
                    flash(f"Error al subir el archivo de video: {str(e)}", "danger")
                    return redirect(url_for("admin_videos"))
        else:
            video_url = request.form.get("video_url", "").strip()
            
        miniatura_url = ""
        if miniatura_tipo == "file":
            file_m = request.files.get("miniatura_file")
            if file_m and file_m.filename != "":
                try:
                    miniatura_url = save_uploaded_file(file_m, "miniaturas")
                except Exception as e:
                    print("Error miniatura:", e)
        else:
            miniatura_url = request.form.get("miniatura_url", "").strip()
            
        if not miniatura_url:
            miniatura_url = "/static/img/miniaturasomos.svg"
            
        if titulo and video_url:
            try:
                db_manager.save_video(titulo=titulo, categoria=categoria, video_url=video_url, miniatura_url=miniatura_url)
                flash("¡Video / Tip agregado con éxito al catálogo web!", "success")
            except Exception as e:
                flash(f"Error al guardar el video: {str(e)}", "danger")
        else:
            flash("Por favor, proporciona el título y el video (URL o archivo).", "warning")
            
        return redirect(url_for("admin_videos"))
        
    videos, db_source = db_manager.get_all_videos()
    return render_template("admin/admin_videos.html", videos=videos, db_source=db_source)

@app.route("/admin/videos/toggle/<int:video_id>", methods=["POST"])
@admin_required
def admin_toggle_video(video_id):
    try:
        data = request.json or {}
        activo = int(data.get("activo", 1))
        db_manager.toggle_video_status(video_id, activo)
        msg = "Video activado y visible en la web" if activo == 1 else "Video ocultado de la web pública"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/videos/editar/<int:video_id>", methods=["POST"])
@admin_required
def admin_edit_video(video_id):
    existing_video = db_manager.get_video_by_id(video_id)
    if not existing_video:
        flash("El video que intentas editar no existe.", "danger")
        return redirect(url_for("admin_videos"))
        
    titulo = request.form.get("titulo", existing_video.get("titulo", "")).strip()
    categoria = request.form.get("categoria", existing_video.get("categoria", "Tip Vehicular")).strip()
    activo = int(request.form.get("activo", existing_video.get("activo", 1)))
    
    # Video source handling
    video_tipo = request.form.get("video_tipo", "keep")
    video_url = existing_video.get("video_url", "")
    if video_tipo == "file":
        file_v = request.files.get("video_file")
        if file_v and file_v.filename != "":
            try:
                video_url = save_uploaded_file(file_v, "videos")
            except Exception as e:
                flash(f"Error al subir el nuevo archivo de video: {str(e)}", "danger")
                return redirect(url_for("admin_videos"))
    elif video_tipo == "url":
        new_url = request.form.get("video_url", "").strip()
        if new_url:
            video_url = new_url

    # Thumbnail handling
    miniatura_tipo = request.form.get("miniatura_tipo", "keep")
    miniatura_url = existing_video.get("miniatura_url", "")
    if miniatura_tipo == "file":
        file_m = request.files.get("miniatura_file")
        if file_m and file_m.filename != "":
            try:
                miniatura_url = save_uploaded_file(file_m, "miniaturas")
            except Exception as e:
                print("Error miniatura:", e)
    elif miniatura_tipo == "url":
        new_min_url = request.form.get("miniatura_url", "").strip()
        if new_min_url:
            miniatura_url = new_min_url

    if titulo and video_url:
        try:
            db_manager.update_video(
                video_id=video_id,
                titulo=titulo,
                categoria=categoria,
                video_url=video_url,
                miniatura_url=miniatura_url,
                activo=activo
            )
            flash("¡Video / Tip actualizado con éxito!", "success")
        except Exception as e:
            flash(f"Error al actualizar el video: {str(e)}", "danger")
    else:
        flash("Por favor, proporciona el título y la ubicación del video.", "warning")

    return redirect(url_for("admin_videos"))

@app.route("/admin/videos/eliminar/<int:video_id>", methods=["POST"])
@admin_required
def admin_delete_video(video_id):
    try:
        db_manager.delete_video(video_id)
        flash("Video / Tip eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar el video: {str(e)}", "danger")
    return redirect(url_for("admin_videos"))




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
            
        user_messages = data["messages"]
        
        # Obtener el último mensaje del usuario
        last_user_msg = ""
        for m in reversed(user_messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "").strip()
                break
                
        last_user_lower = last_user_msg.lower()
        
        # Obtener catálogo en tiempo real
        vehiculos, _ = db_manager.get_all_vehiculos()
        
        # -------------------------------------------------------------
        # FAST-PATH: Respuestas instantáneas (< 5ms) para consultas web
        # -------------------------------------------------------------
        # 1. Solicitud de Contacto / WhatsApp / Teléfono
        if any(k in last_user_lower for k in ["contacto", "telefono", "teléfono", "whatsapp", "wspp", "llamar", "celular", "numero", "número"]):
            resp = "¡Hola! Soy **Qhatuchay IA** 🚗🤖. Aquí tienes los datos de contacto oficial de **CarroQhatu**:\n\n" \
                   "📱 **WhatsApp Directo**: [+51 972043502](https://wa.me/51972043502)\n" \
                   "📍 **Sedes de Atención**: Juliaca, Arequipa y Lima (Perú)\n" \
                   "🌐 **Servicios Web**: Catálogo de autos, Inspección 360°, Tasaciones y Asesoría Inteligente.\n\n" \
                   "¡Escríbenos al WhatsApp para ayudarte al instante con la compra o venta de tu vehículo!"
            return jsonify({"respuesta": resp, "recomendados": [], "externos": []})
            
        # 2. Solicitud de Información Completa de la Web / "Dame todo" / "Qué ofrecen"
        if any(k in last_user_lower for k in ["dame todo", "toda la información", "toda la informacion", "todo de la pagina", "todo de la página", "qué es carroqhatu", "servicios de la web", "qué ofrecen", "que ofrecen"]):
            resp = "¡Hola! Soy **Qhatuchay IA** 🚗🤖 y te doy **TODA la información oficial de la plataforma CarroQhatu**:\n\n" \
                   "🚗 **1. Catálogo de Autos**: Publicamos vehículos seminuevos verificados y 0KM con fotos reales, precios, motor, kilometraje y ficha técnica completa.\n" \
                   "🔍 **2. Inspección 360°**: Servicio de evaluación técnica, mecánica y verificación legal de documentos para comprar o vender con total seguridad.\n" \
                   "💰 **3. Vende tu Auto / Tasaciones**: Herramienta de cotización gratuita para valuar tu vehículo al precio real de mercado.\n" \
                   "📊 **4. Comparador de Vehículos**: Permite comparar dos o más autos en tiempo real para tomar la mejor decisión.\n" \
                   "📱 **5. Contacto Directo**: WhatsApp +51 972043502 | Atendemos en Juliaca, Arequipa y Lima.\n\n" \
                   "¿Qué parte de nuestra página web te gustaría explorar ahora?"
            return jsonify({"respuesta": resp, "recomendados": [], "externos": []})

        # Formatear el catálogo para la IA
        catalog_str = ""
        for v in vehiculos:
            catalog_str += f"- ID: {v['id']} | {v['marca'].upper()} {v['modelo'].upper()} ({v['year']}) | Precio: {v['precio']} | KM: {v['km']:,} | Motor: {v['motor']} | Transmisión: {v['transmision']} | Sede: {v['ciudad']} | Detalles: {v.get('descripcion', '') or 'Sin descripción adicional.'}\n"
            
        system_prompt = f"""Tu nombre es Qhatuchay IA, el Asesor Automotriz Experto y Representante Oficial de CarroQhatu en Perú.

COMPORTAMIENTO Y SERVICIO DE BÚSQUEDA Y COTIZACIÓN EXTERNA:
1. SI EL CLIENTE BUSCA UN VEHÍCULO (0KM O DE SEGUNDA) QUE NO ESTÁ EN NUESTRO STOCK DIRECTO:
   - Sé 100% transparente y dile: "Actualmente no contamos con este modelo específico en nuestro stock directo de la web, PERO en **CarroQhatu** te ofrecemos el **Servicio de Búsqueda Personalizada, Cotización e Inspección Técnica 360°** en todo el mercado peruano (concesionarias oficiales 0KM, portales verificados o vendedores particulares)".
   - Ofrécete a buscarle, cotizarle y mostrarle opciones reales del mercado general con sus precios aproximados en soles o dólares y fotos reales del modelo.
   - Para cada alternativa recomendada del mercado general, DEBES incluir la etiqueta:
     `[EXTERNAL_CAR: Marca | Modelo | Año | Precio Aprox | Kilometraje o 0KM | Transmisión | 0km o usado]`
   - Invita al usuario a solicitar la cotización e inspección directa a través de nuestro WhatsApp Oficial: +51 972043502.

2. SI EL CLIENTE BUSCA VEHÍCULOS QUE SÍ ESTÁN EN NUESTRO CATÁLOGO DE LA WEB:
   - Recomienda los modelos del stock e incluye la etiqueta `[CAR_ID: <id>]`.

3. REGLA DE INVENTARIO INTERNO:
   - ÚNICAMENTE los vehículos listados en "CATÁLOGO ACTUAL EN BASE DE DATOS" pertenecen al stock propio directo de la web. NO inventes otros autos dentro del stock propio.

CATÁLOGO ACTUAL EN BASE DE DATOS DE CARROQHATU:
{catalog_str}

REGLAS DE ATENCIÓN Y FORMATO:
- Actúa como un asesor automotriz real, amable, experto, técnico y servicial.
- Usa negritas (*texto*) y listas organizadas para una lectura clara.
"""
        
        respuesta_texto = None
        try:
            api_messages = [{"role": "system", "content": system_prompt}]
            for msg in user_messages:
                if msg.get("role") in ["user", "assistant"]:
                    api_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            respuesta_texto = get_ai_completion(api_messages, max_tokens=1600, temperature=0.3)
        except Exception as call_err:
            print("WARNING (app): Error llamando a la API de IA (Gemini/OpenAI), usando fallback:", call_err)
            respuesta_texto = None
            
        # Fallback local determinista rápido
        if not respuesta_texto:
            is_greeting = any(k in last_user_lower for k in ["hola", "buenos dias", "buenas tardes", "buenas noches", "como estas", "que tal", "hi", "hello"])
            if is_greeting or len(last_user_lower.split()) < 3:
                note_msg = "¡Hola! Soy **Qhatuchay IA** 🚗🤖, el asesor oficial de **CarroQhatu**.\n\nPuedo darte toda la información de nuestra página web: catálogo de vehículos, precios, ficha técnica, contacto WhatsApp (+51 972043502), Inspección 360° o cómo vender tu auto. ¿Qué deseas consultar?"
                return jsonify({
                    "respuesta": note_msg,
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
                    tipo_txt = "Nuevo 0KM" if ext[6] == "0km" else "De Segunda"
                    respuesta_texto += f"* **{ext[0].upper()} {ext[1].upper()} ({ext[2]})** [{tipo_txt}]: Precio aprox {ext[3]}, transmisión {ext[5]}.\n"
                respuesta_texto += "\n*Recuerda que en CarroQhatu te ayudamos a buscar, verificar físicamente e inspeccionar legalmente cualquier vehículo nuevo 0KM o de segunda del mercado.*"
                
            for c in candidatos_internos:
                respuesta_texto += f" [CAR_ID: {c['id']}]"
            for ext in externos_list_fallback:
                respuesta_texto += f" [EXTERNAL_CAR: {ext[0]} | {ext[1]} | {ext[2]} | {ext[3]} | {ext[4]} | {ext[5]} | {ext[6]} | {ext[7]}]"

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
                    
        # Parsear las recomendaciones de autos externos [EXTERNAL_CAR: Marca | Modelo | Año | Precio | Kilometraje | Transmisión | Tipo | ImagenURL (opcional)]
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
                imagen_url = parts[7] if len(parts) >= 8 else None
                
                # Asignar foto real autenticada del repositorio
                if not imagen_url or not (imagen_url.startswith('/') or imagen_url.startswith('http')):
                    m_lower = (marca + " " + modelo).lower()
                    if "hilux" in m_lower:
                        imagen_url = "/static/img/HILUX2017-1.jpg"
                    elif "rav4" in m_lower:
                        imagen_url = "/static/img/RAV4-1.jpg"
                    elif "yaris" in m_lower or "corolla" in m_lower:
                        imagen_url = "/static/img/toyotayaris.jpg"
                    elif "sportage" in m_lower:
                        imagen_url = "/static/img/KIASPORTAGE2.jpg"
                    elif "seltos" in m_lower:
                        imagen_url = "/static/img/KIA SELTOS.jpg"
                    elif "sonet" in m_lower:
                        imagen_url = "/static/img/KIANEWSONET.jpg"
                    elif "soluto" in m_lower:
                        imagen_url = "/static/img/kiasoluto.jpg"
                    elif "tucson" in m_lower:
                        imagen_url = "/static/img/TUCSON2019.jpg"
                    elif "verna" in m_lower:
                        imagen_url = "/static/img/hyundaiverna.jpg"
                    elif "tracker" in m_lower:
                        imagen_url = "/static/img/HYUNDAITRACKER-1.png"
                    elif "hr-v" in m_lower or "honda" in m_lower:
                        imagen_url = "/static/img/HONDA-HR-V.jpg"
                    elif "cx-5" in m_lower or "mazda" in m_lower:
                        imagen_url = "/static/img/MAZDACX5.jpg"
                    elif "navara" in m_lower or "frontier" in m_lower or "nissan" in m_lower:
                        imagen_url = "/static/img/NAVARA1.jpg"
                    elif "glory" in m_lower or "dfsk" in m_lower:
                        imagen_url = "/static/img/DFSKGLORYNEW580.jpg"
                    elif "ecosport" in m_lower or "ford" in m_lower:
                        imagen_url = "/static/img/Ford_Ecosport.jpg"
                    elif "audi" in m_lower or "q5" in m_lower:
                        imagen_url = "/static/img/AUDIQ5-2.png"
                    elif "tiguan" in m_lower or "volkswagen" in m_lower:
                        imagen_url = "/static/img/W-TIGUAN1.png"
                    elif "stepway" in m_lower or "renault" in m_lower:
                        imagen_url = "/static/img/RenaultStepway.jpg"
                    elif "aveo" in m_lower or "spin" in m_lower or "chevrolet" in m_lower:
                        imagen_url = "/static/img/TRACKERLTZ.jpg"
                    elif "l200" in m_lower or "mitsubishi" in m_lower:
                        imagen_url = "/static/img/mitsubishil200.jpg"
                    elif "vigus" in m_lower or "jmc" in m_lower:
                        imagen_url = "/static/img/JMCVIGUS.png"
                    elif "king" in m_lower or "long" in m_lower:
                        imagen_url = "/static/img/kinglong.jpg"
                    elif "toyota" in m_lower:
                        imagen_url = "/static/img/HILUX2017-1.jpg"
                    elif "kia" in m_lower:
                        imagen_url = "/static/img/KIASPORTAGE2.jpg"
                    elif "hyundai" in m_lower:
                        imagen_url = "/static/img/TUCSON2019.jpg"
                    else:
                        imagen_url = "/static/img/cardetail3.svg"

                externos_list.append({
                    "marca": marca,
                    "modelo": modelo,
                    "year": year,
                    "precio": precio,
                    "km": km,
                    "transmision": trans,
                    "tipo": tipo.lower(),
                    "imagen_url": imagen_url
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
WHATSAPP_PROCESSED_MESSAGE_IDS = []

def get_evolution_status():
    """Consulta el estado de conexión de la instancia en Evolution API y la crea/actualiza si es necesario."""
    evolution_url = os.getenv("EVOLUTION_API_URL")
    evolution_key = os.getenv("EVOLUTION_API_KEY")
    evolution_instance = os.getenv("EVOLUTION_INSTANCE_NAME", "carroqhatu")
    
    if not evolution_url or not evolution_key:
        return {"configured": False, "connected": False, "qr": None, "error": "No configurado en el archivo .env"}
        
    try:
        import requests
        headers = {"apikey": evolution_key}
        
        # 1. Verificar estado de conexión de la instancia
        state_url = f"{evolution_url.rstrip('/')}/instance/connectionState/{evolution_instance}"
        r_state = requests.get(state_url, headers=headers, timeout=20)
        
        if r_state.status_code == 200:
            state_data = r_state.json()
            state = state_data.get("instance", {}).get("state", "close")
            if state == "open":
                return {"configured": True, "connected": True, "qr": None, "state": "open"}
        elif r_state.status_code == 404:
            # Si la instancia no existe en la API, intentar crearla automáticamente
            create_url = f"{evolution_url.rstrip('/')}/instance/create"
            payload = {
                "instanceName": evolution_instance,
                "token": evolution_key,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS"
            }
            r_create = requests.post(create_url, json=payload, headers=headers, timeout=20)
            if r_create.status_code != 201:
                return {"configured": True, "connected": False, "qr": None, "error": f"Error al crear instancia: {r_create.text}"}
        else:
            return {"configured": True, "connected": False, "qr": None, "error": f"API respondió HTTP {r_state.status_code}"}
            
        # 2. Si no está abierta (open), obtener el código QR
        connect_url = f"{evolution_url.rstrip('/')}/instance/connect/{evolution_instance}"
        r_connect = requests.get(connect_url, headers=headers, timeout=20)
        
        if r_connect.status_code == 200:
            connect_data = r_connect.json()
            # Si ya se conectó justo en esta llamada
            if connect_data.get("instance", {}).get("state") == "open":
                return {"configured": True, "connected": True, "qr": None, "state": "open"}
                
            # Primero intentar obtener la base64 directamente (API nueva)
            qr_base64 = connect_data.get("base64")
            # Si no, intentar del diccionario qrcode (API antigua)
            if not qr_base64 and "qrcode" in connect_data:
                qr_base64 = connect_data.get("qrcode", {}).get("base64")
                
            if qr_base64:
                return {"configured": True, "connected": False, "qr": qr_base64, "state": "connecting"}
                
        return {"configured": True, "connected": False, "qr": None, "error": "No se pudo obtener el código QR."}
        
    except Exception as e:
        return {"configured": True, "connected": False, "qr": None, "error": str(e)}

def reset_evolution_instance():
    """Elimina y vuelve a crear la instancia en Evolution API para limpiar sesiones corruptas o atascadas."""
    evolution_url = os.getenv("EVOLUTION_API_URL")
    evolution_key = os.getenv("EVOLUTION_API_KEY")
    evolution_instance = os.getenv("EVOLUTION_INSTANCE_NAME", "carroqhatu")
    
    if not evolution_url or not evolution_key:
        return False, "Evolution API no está configurada."
        
    try:
        import requests
        headers = {"apikey": evolution_key}
        
        # 1. Eliminar la instancia existente para borrar la sesión desincronizada
        delete_url = f"{evolution_url.rstrip('/')}/instance/delete/{evolution_instance}"
        try:
            requests.delete(delete_url, headers=headers, timeout=15)
        except Exception as e:
            print("WARNING (whatsapp): Error eliminando instancia previa:", e)
            
        # 2. Recrear la instancia desde cero
        create_url = f"{evolution_url.rstrip('/')}/instance/create"
        payload = {
            "instanceName": evolution_instance,
            "token": evolution_key,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        r_create = requests.post(create_url, json=payload, headers=headers, timeout=20)
        
        # 3. Actualizar webhook
        webhook_url = get_best_webhook_url()
        configure_evolution_webhook(webhook_url)
        
        return True, "Sesión de WhatsApp reiniciada exitosamente. Se ha generado un código QR 100% nuevo."
    except Exception as e:
        return False, f"Error al reiniciar la sesión: {str(e)}"


def get_best_webhook_url(request_url_root=None):
    """Obtiene la mejor URL pública disponible para el webhook (Env var > public request.url_root > ngrok activo > local fallback)."""
    # 1. Variable de entorno explícita (EVOLUTION_WEBHOOK_URL o PUBLIC_WEBHOOK_URL)
    env_url = os.getenv("EVOLUTION_WEBHOOK_URL") or os.getenv("PUBLIC_WEBHOOK_URL")
    if env_url:
        return env_url if env_url.endswith("/api/whatsapp/webhook") else env_url.rstrip('/') + "/api/whatsapp/webhook"

    # 2. Si la petición viene de un dominio público (ej. ngrok o dominio real)
    if request_url_root:
        clean_root = request_url_root.rstrip('/')
        if not ("127.0.0.1" in clean_root or "localhost" in clean_root):
            return clean_root + "/api/whatsapp/webhook"

    # 3. Intentar auto-detectar túnel local de ngrok si está corriendo en segundo plano
    try:
        import requests
        r = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        if r.status_code == 200:
            tunnels = r.json().get("tunnels", [])
            for t in tunnels:
                pub_url = t.get("public_url", "")
                if pub_url.startswith("https"):
                    return pub_url.rstrip('/') + "/api/whatsapp/webhook"
    except Exception:
        pass

    # 4. Fallback a request.url_root o localhost si no hay túnel ni dominio público
    if request_url_root:
        return request_url_root.rstrip('/') + "/api/whatsapp/webhook"

    return "http://localhost:5000/api/whatsapp/webhook"


def configure_evolution_webhook(webhook_url=None):
    """Configura el Webhook en la instancia de Evolution API para recibir mensajes."""
    evolution_url = os.getenv("EVOLUTION_API_URL")
    evolution_key = os.getenv("EVOLUTION_API_KEY")
    evolution_instance = os.getenv("EVOLUTION_INSTANCE_NAME", "carroqhatu")
    
    if not evolution_url or not evolution_key:
        return

    if not webhook_url:
        webhook_url = get_best_webhook_url()
    else:
        # Si webhook_url trae 127.0.0.1 o localhost pero tenemos una URL pública mejor (ngrok/env), usar la mejor
        if "127.0.0.1" in webhook_url or "localhost" in webhook_url:
            best = get_best_webhook_url()
            if not ("127.0.0.1" in best or "localhost" in best):
                webhook_url = best
        
    try:
        import requests
        url = f"{evolution_url.rstrip('/')}/webhook/set/{evolution_instance}"
        headers = {
            "apikey": evolution_key,
            "Content-Type": "application/json"
        }
        payload = {
            "webhook": {
                "enabled": True,
                "url": webhook_url,
                "events": ["MESSAGES_UPSERT"]
            }
        }
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        print(f"INFO (whatsapp): Configuración Webhook Evolution API ({webhook_url}):", r.status_code, r.text)
    except Exception as e:
        print("ERROR (whatsapp): Error configurando webhook en Evolution API:", e)


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            clean_args = [str(a).encode('ascii', 'xmlcharrefreplace').decode('ascii') for a in args]
            print(*clean_args, **kwargs)
        except Exception:
            pass

def send_outgoing_whatsapp(to_number, body_text):
    """Envía un mensaje saliente usando la API de Meta Cloud, Twilio, o Evolution API si están configuradas."""
    # 1. Evolution API (Alta Prioridad para QR)
    evolution_url = os.getenv("EVOLUTION_API_URL")
    evolution_key = os.getenv("EVOLUTION_API_KEY")
    evolution_instance = os.getenv("EVOLUTION_INSTANCE_NAME", "carroqhatu")
    
    if evolution_url and evolution_key:
        try:
            import requests
            # Limpiar el número a E.164 simple (solo dígitos)
            clean_number = "".join(filter(str.isdigit, to_number))
            url = f"{evolution_url.rstrip('/')}/message/sendText/{evolution_instance}"
            headers = {
                "apikey": evolution_key,
                "Content-Type": "application/json"
            }
            payload = {
                "number": clean_number,
                "text": body_text,
                "options": {
                    "delay": 1200,
                    "presence": "composing"
                }
            }
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            if r.status_code in [200, 201]:
                safe_print("INFO (whatsapp): Mensaje enviado exitosamente vía Evolution API (HTTP", r.status_code, ")")
            else:
                safe_print(f"WARNING (whatsapp): Evolution API devolvió HTTP {r.status_code}: {r.text}. Verifica que el celular esté vinculado escaneando el QR en /admin/whatsapp.")
            return
        except Exception as e:
            safe_print("ERROR (whatsapp): Error enviando mensaje por Evolution API:", str(e))
            
    # 2. Meta Cloud API (Oficial)
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    # 3. Twilio API (Alternativa)
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
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            safe_print("INFO (whatsapp): Respuesta de Meta API:", r.status_code)
        except Exception as e:
            safe_print("ERROR (whatsapp): Error enviando mensaje por Meta API:", str(e))
            
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
            r = requests.post(url, data=payload, auth=auth, timeout=10)
            safe_print("INFO (whatsapp): Respuesta de Twilio API:", r.status_code)
        except Exception as e:
            safe_print("ERROR (whatsapp): Error enviando mensaje por Twilio API:", str(e))
    else:
        safe_print(f"INFO (whatsapp): Sandbox/Simulación - Mensaje enviado a {to_number}")

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
    try:
        GEMINI_API_KEY = get_gemini_key()
    except RuntimeError:
        GEMINI_API_KEY = None
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        api_messages.append(msg)

    respuesta_texto = None
    try:
        respuesta_texto = get_ai_completion(api_messages, max_tokens=1500, temperature=0.7)
        if respuesta_texto:
            logs.append("Respuesta obtenida con éxito de la API de IA (get_ai_completion).")
    except Exception as err:
        logs.append(f"Error en get_ai_completion: {err}. Activando fallback inteligente local...")
        respuesta_texto = None

    # Fallback inteligente local conversacional si la IA externa no está disponible
    if not respuesta_texto:
        logs.append("Ejecutando algoritmo conversacional de respaldo...")
        msg_lower = message_body.lower().strip()

        # 1. Búsqueda de vehículos en stock
        match_car = None
        for v in vehiculos:
            if v['marca'].lower() in msg_lower or v['modelo'].lower() in msg_lower:
                match_car = v
                break

        # 2. Respuestas inteligentes según intención
        if any(k in msg_lower for k in ["ninguno", "ninguna", "nada", "no me interesa", "no gracias", "no quiero"]):
            respuesta_texto = "¡Entendido! Si en algún momento necesitas vender, comprar o inspeccionar un vehículo con total seguridad en Perú, con gusto te ayudaremos en CarroQhatu. ¡Que tengas un excelente día! 🚗✨"
        elif any(k in msg_lower for k in ["empresa", "carroqhatu", "quienes son", "quiénes son", "que hacen", "qué hacen", "servicios", "informacion", "información", "que es esto"]):
            respuesta_texto = (
                "En **CarroQhatu** somos la plataforma líder en Perú para la compra, venta e inspección técnica de vehículos.\n\n"
                "📌 **Nuestros Servicios Principales:**\n"
                "1️⃣ **Venta de tu auto**: Obtenemos la mejor tasación de mercado y gestionamos la venta por ti.\n"
                "2️⃣ **Compra de autos**: Contamos con catálogo de seminuevos 100% inspeccionados y verificados.\n"
                "3️⃣ **Inspección Técnica Integral**: Revisión mecánica, electrónica y legal de cualquier auto que desees comprar.\n\n"
                "¿Te gustaría cotizar un vehículo o ver nuestro catálogo disponible?"
            )
        elif any(k in msg_lower for k in ["venta", "vender", "tasar", "tasacion", "tasación", "cotizar"]):
            respuesta_texto = "¡Excelente! En CarroQhatu te ayudamos a vender tu auto al mejor precio del mercado peruano. ¿Me podrías indicar tu nombre completo, la marca, modelo y año de tu vehículo para realizar la cotización?"
        elif any(k in msg_lower for k in ["compra", "comprar", "catalogo", "catálogo", "stock", "precio"]):
            if match_car:
                respuesta_texto = f"¡Sí! Tenemos disponible el **{match_car['marca'].upper()} {match_car['modelo'].upper()} ({match_car['year']})** en nuestra sede de {match_car['ciudad']} por {match_car['precio']}. ¿Te gustaría agendar una cita o llamada para verlo?"
            else:
                respuesta_texto = "Contamos con un amplio stock de vehículos 100% verificados y garantizados. ¿Qué marca o tipo de vehículo estás buscando y cuál es tu presupuesto aproximado?"
        elif any(k in msg_lower for k in ["inspeccion", "inspección", "revisar", "revisión"]):
            respuesta_texto = "Ofrecemos inspección mecánica, electrónica, estructural y legal completa para autos. ¿Qué vehículo deseas que revisemos por ti y en qué ciudad te encuentras?"
        else:
            if match_car:
                respuesta_texto = f"Contamos con el **{match_car['marca'].upper()} {match_car['modelo'].upper()} ({match_car['year']})** en stock por {match_car['precio']}. ¿Me indicas tu nombre completo para coordinar una llamada con un asesor?"
            else:
                respuesta_texto = (
                    "¡Hola! Te saluda CarroQhatu, especialistas en compra, venta e inspección vehicular en Perú.\n\n"
                    "¿En qué te podemos ayudar hoy? Cuéntanos si deseas **vender tu auto**, **comprar un semi-nuevo** o **solicitar una revisión técnica**."
                )
                
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


# ---------- COMPARADOR DE VEHÍCULOS ----------

@app.route("/comparador")
def comparador():
    vehiculos, _ = db_manager.get_all_vehiculos()
    return render_template("comparador.html", vehiculos=vehiculos)

@app.route("/api/comparar", methods=["POST"])
def api_comparar():
    try:
        data = request.json
        if not data or "ids" not in data:
            return jsonify({"error": "IDs de vehículos no proporcionados"}), 400
            
        vehiculo_ids = data["ids"]
        if not isinstance(vehiculo_ids, list) or len(vehiculo_ids) < 2:
            return jsonify({"error": "Se requieren al menos 2 vehículos para comparar"}), 400
            
        vehiculos = []
        for v_id in vehiculo_ids:
            v = db_manager.get_vehiculo_by_id(v_id)
            if v:
                vehiculos.append(v)
                
        if len(vehiculos) < 2:
            return jsonify({"error": "No se encontraron suficientes vehículos válidos para comparar"}), 400
            
        # Intentar analizar con Gemini
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        try:
            GEMINI_API_KEY = get_gemini_key()
        except RuntimeError:
            GEMINI_API_KEY = None
            
        respuesta_texto = None
        
        # Formatear la lista de vehículos para el prompt
        vehiculos_info = ""
        for idx, v in enumerate(vehiculos):
            vehiculos_info += f"VEHÍCULO {idx + 1}:\n"
            vehiculos_info += f"- ID: {v['id']}\n"
            vehiculos_info += f"- Marca: {v['marca']}\n"
            vehiculos_info += f"- Modelo: {v['modelo']}\n"
            vehiculos_info += f"- Año: {v['year']}\n"
            vehiculos_info += f"- Precio: {v['precio']}\n"
            vehiculos_info += f"- Kilometraje: {v['km']:,} km\n"
            vehiculos_info += f"- Motor: {v['motor']}\n"
            vehiculos_info += f"- Transmisión: {v['transmision']}\n"
            vehiculos_info += f"- Sede (Ciudad): {v['ciudad']}\n"
            vehiculos_info += f"- Estado de conservación: {v['estado']}\n"
            vehiculos_info += f"- Verificado por CarroQhatu: {'Sí' if v['verificado'] == 1 else 'No'}\n"
            vehiculos_info += f"- Descripción adicional: {v.get('descripcion') or 'Sin descripción adicional.'}\n\n"

        system_prompt = (
            "Eres un asesor automotriz experto de CarroQhatu. Tu tarea es realizar una comparación detallada "
            "y técnica entre los siguientes vehículos seleccionados por un cliente. Al final, debes elegir el "
            "mejor de todos justificando técnicamente tu decisión (relación calidad-precio, desgaste, equipamiento, "
            "año de fabricación, etc.).\n\n"
            "Por favor, estructura tu respuesta con los siguientes puntos, redactados de forma atractiva, en español, "
            "usando negritas y viñetas de manera profesional:\n"
            "1. **Resumen de la Comparación**: Breve introducción de los vehículos a comparar.\n"
            "2. **Tabla / Análisis Técnico Detallado**: Un desglose de ventajas y desventajas de cada uno (Marca, Modelo, Desgaste/KM, Año, etc.).\n"
            "3. **El Veredicto (El Mejor de Todos)**: Declarar claramente cuál es el mejor vehículo en general para la mayoría de clientes y por qué. "
            "Opcionalmente, indica si alguno de los otros es mejor para un perfil específico (ej. para trabajo pesado, para ciudad, o por presupuesto ajustado).\n"
            "4. **Recomendación de CarroQhatu**: Explica que todos nuestros vehículos en catálogo pasan por un proceso de revisión y que el cliente puede "
            "darle clic al botón de WhatsApp del auto ganador para agendar una prueba de manejo o solicitar asesoría personalizada.\n\n"
            "Mantén un tono profesional, amigable, transparente y objetivo."
        )

        try:
            respuesta_texto = get_ai_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Por favor, compara estos vehículos:\n\n{vehiculos_info}"}
            ], max_tokens=2000, temperature=0.7)
        except Exception as call_err:
            print("WARNING (app): Error llamando a la API de IA en el comparador, usando fallback:", call_err)
            respuesta_texto = None
                
        # Fallback local programático si falla la IA
        if not respuesta_texto:
            # Algoritmo de puntuación determinista
            # Puntuamos cada auto
            scores = []
            for v in vehiculos:
                score = 0
                
                # 1. Puntuación por Año (más nuevo es mejor)
                try:
                    yr = int(v['year'])
                    score += (yr - 2000) * 2
                except:
                    score += 20
                    
                # 2. Puntuación por Kilometraje (menos es mejor)
                try:
                    km = int(v['km'])
                    if km == 0:
                        score += 35
                    elif km < 50000:
                        score += 25
                    elif km < 100000:
                        score += 18
                    elif km < 150000:
                        score += 10
                    elif km < 200000:
                        score += 5
                except:
                    pass
                    
                # 3. Puntuación por Precio (más barato es mejor)
                precio_str = v['precio'].upper()
                try:
                    num_val = float(''.join(c for c in precio_str if c.isdigit() or c == '.'))
                    if 'PEN' in precio_str or 'S/.' in precio_str or 'S/' in precio_str:
                        usd_equiv = num_val / 3.75
                    else:
                        usd_equiv = num_val
                        
                    if usd_equiv < 12000:
                        score += 30
                    elif usd_equiv < 18000:
                        score += 22
                    elif usd_equiv < 25000:
                        score += 15
                    elif usd_equiv < 35000:
                        score += 8
                    else:
                        score += 3
                except:
                    score += 10
                    
                # 4. Verificado
                if v['verificado'] == 1:
                    score += 8
                    
                # 5. Estado
                est = v['estado'].lower()
                if 'excelente' in est:
                    score += 10
                elif 'bueno' in est:
                    score += 6
                else:
                    score += 2
                    
                scores.append((score, v))
                
            scores.sort(key=lambda x: x[0], reverse=True)
            ganador = scores[0][1]
            
            # Construir reporte fallback en HTML / Markdown
            respuesta_texto = f"### Resumen de la Comparación Técnica\n" \
                              f"Hemos analizado detalladamente los **{len(vehiculos)} vehículos** seleccionados en base a su precio, kilometraje, año y estado de conservación.\n\n"
            
            respuesta_texto += "#### Puntos Clave de cada vehículo:\n"
            for score_val, v in scores:
                verif_text = " verificado por nuestro equipo" if v['verificado'] == 1 else ""
                respuesta_texto += f"- **{v['marca'].upper()} {v['modelo'].upper()} ({v['year']})**: " \
                                  f"Se encuentra en estado **{v['estado']}**{verif_text}. " \
                                  f"Tiene un kilometraje de **{v['km']:,} km** y un precio de **{v['precio']}**. " \
                                  f"(Puntuación de relación calidad-precio: **{score_val} pts**)\n"
            
            respuesta_texto += f"\n### 🏆 El Veredicto: El Mejor de Todos\n" \
                              f"El ganador indiscutible de esta comparación técnica es el **{ganador['marca'].upper()} {ganador['modelo'].upper()} ({ganador['year']})**.\n\n" \
                              f"**¿Por qué es la mejor opción?**\n"
            
            razones = []
            if ganador['km'] == 0:
                razones.append("Es un vehículo **0KM completamente nuevo**, lo que garantiza cero desgaste mecánico y la mayor vida útil posible.")
            elif ganador['km'] < 80000:
                razones.append(f"Cuenta con un **bajo kilometraje ({ganador['km']:,} km)** para su año de fabricación, lo que minimiza costos de mantenimiento a corto plazo.")
            
            try:
                precios_usd = []
                for v in vehiculos:
                    p_str = v['precio'].upper()
                    num = float(''.join(c for c in p_str if c.isdigit() or c == '.'))
                    if 'PEN' in p_str or 'S/.' in p_str or 'S/' in p_str:
                        num = num / 3.75
                    precios_usd.append(num)
                ganador_p_str = ganador['precio'].upper()
                ganador_p = float(''.join(c for c in ganador_p_str if c.isdigit() or c == '.'))
                if 'PEN' in ganador_p_str or 'S/.' in ganador_p_str or 'S/' in ganador_p_str:
                    ganador_p = ganador_p / 3.75
                    
                if ganador_p <= min(precios_usd):
                    razones.append("Ofrece el **precio más competitivo** de toda la selección, maximizando el valor de tu presupuesto.")
            except:
                pass
                
            if ganador['verificado'] == 1:
                razones.append("Cuenta con la insignia de **Vehículo Verificado**, lo que certifica que ha superado nuestra inspección mecánica y legal rigurosa.")
                
            if len(razones) == 0:
                razones.append("Presenta el equilibrio más sólido entre año de fabricación, kilometraje recorrido y precio de venta.")
                
            for razon in razones:
                respuesta_texto += f"- {razon}\n"
                
            respuesta_texto += f"\n**Consejo de CarroQhatu**: Si deseas continuar con el proceso para el **{ganador['marca'].upper()} {ganador['modelo'].upper()}**, puedes presionar el botón de WhatsApp ubicado en su columna correspondiente para chatear directamente con nuestro equipo y separar tu cita."
            
        return jsonify({
            "comparacion": respuesta_texto,
            "vehiculos": vehiculos
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    """Webhook de recepción POST para mensajes de WhatsApp (Meta Cloud API, Twilio y Evolution API)."""
    try:
        content_type = request.headers.get("Content-Type", "")
        phone_number = None
        sender_name = "Cliente WhatsApp"
        message_body = ""
        message_id = None
        
        if "application/json" in content_type:
            data = request.json
            if not data:
                return "OK", 200
            
            # Detectar Evolution API (MESSAGES_UPSERT)
            if "event" in data and "instance" in data and "data" in data:
                event_type = data.get("event")
                if event_type not in ["messages.upsert", "MESSAGES_UPSERT"]:
                    return "OK", 200 # Ignorar otros eventos como status, etc.
                
                evt_data = data.get("data", {})
                key = evt_data.get("key", {})
                from_me = key.get("fromMe", False)
                if from_me:
                    # Evitar bucle infinito
                    return "OK", 200
                
                remote_jid = key.get("remoteJid", "")
                if "@" in remote_jid:
                    phone_number = remote_jid.split("@")[0]
                else:
                    phone_number = remote_jid
                
                sender_name = evt_data.get("pushName", "Cliente WhatsApp")
                message_id = key.get("id")
                
                message_obj = evt_data.get("message", {})
                if not message_obj:
                    return "OK", 200
                
                message_body = message_obj.get("conversation", "")
                if not message_body and "extendedTextMessage" in message_obj:
                    message_body = message_obj.get("extendedTextMessage", {}).get("text", "")
            else:
                # Es el JSON original de Meta Cloud API
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
                message_id = message.get("id")
                
                contacts = value.get("contacts", [])
                if contacts:
                    sender_name = contacts[0].get("profile", {}).get("name", "Cliente WhatsApp")
                
        elif "application/x-www-form-urlencoded" in content_type:
            phone_number = request.form.get("From", "").replace("whatsapp:", "")
            message_body = request.form.get("Body", "")
            sender_name = request.form.get("ProfileName", "Cliente WhatsApp")
            message_id = request.form.get("MessageSid")
            
        else:
            data = request.json or {}
            phone_number = data.get("from")
            message_body = data.get("body", "")
            sender_name = data.get("name", "Cliente WhatsApp")
            message_id = data.get("id")
            
        if not phone_number or not message_body:
            return "Datos incompletos", 400

        # Filtro de de-duplicación para evitar respuestas repetidas (retries de Meta/Twilio)
        if message_id:
            if message_id in WHATSAPP_PROCESSED_MESSAGE_IDS:
                print(f"INFO (whatsapp): Ignorando mensaje duplicado ID: {message_id}")
                return "OK", 200
            WHATSAPP_PROCESSED_MESSAGE_IDS.append(message_id)
            if len(WHATSAPP_PROCESSED_MESSAGE_IDS) > 200:
                WHATSAPP_PROCESSED_MESSAGE_IDS.pop(0)
            
        ia_reply, result = process_whatsapp_ai_logic(phone_number, sender_name, message_body)
        
        # Enviar mensaje saliente
        send_outgoing_whatsapp(phone_number, ia_reply)
        
        return jsonify({"status": "sent", "reply": ia_reply}), 200
        
    except Exception as e:
        print("ERROR (whatsapp): Error en webhook POST:", e)
        return str(e), 500

@app.route("/admin/whatsapp")
@admin_required
def admin_whatsapp():
    """Renderiza el panel de estado y configuración de la integración de WhatsApp Real."""
    meta_access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    meta_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    meta_verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "carroqhatu_verify_token_2026")
    
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    meta_configured = bool(meta_access_token and meta_phone_id)
    twilio_configured = bool(twilio_sid and twilio_token)
    
    # Obtener el origen de datos activo para el badge del admin layout
    _, db_source = db_manager.get_all_cotizaciones()
    
    # Calcular la mejor URL pública del webhook (Auto-detectando ngrok si aplica)
    webhook_url = get_best_webhook_url(request.url_root)
    
    # Configuración de Evolution API
    evolution_status = get_evolution_status()
    # Si la Evolution API está configurada, aseguramos que el webhook esté actualizado con la URL pública
    if evolution_status.get("configured"):
        configure_evolution_webhook(webhook_url)
        
    return render_template(
        "admin/admin_whatsapp.html",
        db_source=db_source,
        meta_configured=meta_configured,
        twilio_configured=twilio_configured,
        verify_token=meta_verify_token,
        webhook_url=webhook_url,
        has_meta_token=bool(meta_access_token),
        has_meta_phone_id=bool(meta_phone_id),
        has_twilio_sid=bool(twilio_sid),
        has_twilio_token=bool(twilio_token),
        evolution_configured=evolution_status.get("configured"),
        evolution_connected=evolution_status.get("connected"),
        evolution_qr=evolution_status.get("qr"),
        evolution_error=evolution_status.get("error"),
        evolution_url=os.getenv("EVOLUTION_API_URL"),
        evolution_key=os.getenv("EVOLUTION_API_KEY"),
    )


@app.route("/admin/whatsapp/reset_instance", methods=["POST"])
@admin_required
def admin_whatsapp_reset_instance():
    """Limpia la sesión corrupta de WhatsApp y recrea la instancia para generar un QR fresco."""
    success, msg = reset_evolution_instance()
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for("admin_whatsapp"))


@app.route("/api/whatsapp/qr_status")
def api_whatsapp_qr_status():
    """Endpoint JSON para actualización en vivo del código QR y estado de WhatsApp en el frontend."""
    if not session.get("admin_logged_in"):
        return jsonify({"error": "No autorizado"}), 401
    return jsonify(get_evolution_status())



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
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

 


