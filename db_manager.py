import os
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "local_db.sqlite3")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print("WARNING (db_manager): No se pudo inicializar el cliente de Supabase:", e)

def get_db_connection():
    """Returns a connection to the local SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_local_db():
    """Initializes the local SQLite database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Table for Cotizaciones (tasaciones)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT,
            modelo TEXT,
            year TEXT,
            km INTEGER,
            estado TEXT,
            precio_min INTEGER,
            precio_max INTEGER,
            created_at TEXT
        )
    """)
    
    # 2. Table for Solicitudes (Purchase requests, "Quiero mi servicio", etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT, -- 'compra', 'servicio', 'contacto'
            nombre TEXT,
            contacto TEXT,
            datos_vehiculo TEXT, -- JSON string or description
            estado TEXT DEFAULT 'Pendiente', -- 'Pendiente', 'Contactado', 'Finalizado'
            created_at TEXT
        )
    """)
    
    # 3. Table for Dynamic Site Configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_config (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    
    # 4. Table for Vehicle Catalog (Inventory)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT,
            modelo TEXT,
            year TEXT,
            motor TEXT,
            km INTEGER,
            transmision TEXT,
            precio TEXT, -- e.g. 'PEN S/.37,000' or 'USD $17,500'
            imagen_url TEXT,
            ciudad TEXT,
            estado TEXT,
            verificado INTEGER DEFAULT 1, -- 1 for True, 0 for False
            descripcion TEXT, -- Additional description
            created_at TEXT
        )
    """)
    
    # Safely migrate existing databases to add 'descripcion' and 'imagenes_extra' columns if not present
    try:
        cursor.execute("ALTER TABLE vehiculos ADD COLUMN descripcion TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE vehiculos ADD COLUMN imagenes_extra TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    # 5. Table for PDF Catalogs (Brochures)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalogos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            archivo_url TEXT,
            created_at TEXT
        )
    """)
    
    # 6. Table for Promotional Ads (Publicidad)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publicidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            imagen_url TEXT,
            enlace_url TEXT,
            activo INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    
    # 7. Table for Testimonios (Opiniones de clientes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS testimonios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            relacion TEXT,
            calificacion INTEGER,
            comentario TEXT,
            aprobado INTEGER DEFAULT 0, -- 1 for Approved, 0 for Pending
            created_at TEXT
        )
    """)
    
    # Pre-populate default testimonials if table is empty
    cursor.execute("SELECT COUNT(*) FROM testimonios")
    if cursor.fetchone()[0] == 0:
        default_testimonios = [
            ("Anderson Coaquira H.", "Vendió un Toyota Corolla 2020", 4, "Salió todo impecable, cumplieron 100% en todo lo pactado. Súper rápido todo y la gente siempre muy atenta.", 1),
            ("Adrian Ticona M.", "Vendió un Toyota Hilux SRV 2019", 5, "Me gustó el trato son muy confiables, vinieron a ver mi carro y me tasaron un buen precio, me mostraron todo detallado y con publicación en redes recibí muchas ofertas. Estoy muy agradecido CarroQhatu!", 1),
            ("Rosemary Palacios Quispe", "Vendió Kia Soluto Semifull 2022", 4, "Todo se cumplió en tiempo y forma. La atención es excelente, vendi mi auto y también pude renovar a uno mejor con la ayuda de CarroQhatu. Gracias...", 1)
        ]
        created_at_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for test in default_testimonios:
            cursor.execute("""
                INSERT INTO testimonios (nombre, relacion, calificacion, comentario, aprobado, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, test + (created_at_time,))
        conn.commit()
    # 8. Table for Videos y Tips
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            categoria TEXT DEFAULT 'Tip',
            video_url TEXT,
            miniatura_url TEXT,
            activo INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    
    # Pre-populate default videos if table is empty
    cursor.execute("SELECT COUNT(*) FROM videos")
    if cursor.fetchone()[0] == 0:
        default_videos = [
            ("Conócenos - CarroQhatu", "Presentación", "https://www.dropbox.com/scl/fi/tiysadbc5kk6ugyomliyp/video0.mp4?rlkey=d21x2uwi5ajprwuo9tykcrt6v&st=5jgp60a1&raw=1", "/static/img/miniaturasomos.svg", 1),
            ("Respondiendo a Haters", "Tip / Redes", "https://www.dropbox.com/scl/fi/6fvjdeufbf28v5axg9mlw/videohater.mp4?rlkey=6llmjudgksfxiohhs25bdaa68&st=dcn02wok&raw=1", "/static/img/miniaturahate.svg", 1),
            ("7 Años de Ahorros", "Testimonio", "https://www.dropbox.com/scl/fi/q82dy3hpbclvvwms4coqv/testimonioahorros.mp4?rlkey=u6lo7fntzs10mk4t0b2jyip9u&st=7m3cvwmy&dl=0&raw=1", "/static/img/7añosahorros.svg", 1),
            ("Opinión Cliente Arequipa", "Testimonio", "https://www.dropbox.com/scl/fi/05mupolm2ouf5qqqs6u5q/videoclienteaqp.mp4?rlkey=uuh6uedjptm6ttite6ucs277l&st=f0c0co2l&dl=0&raw=1", "/static/img/opinion2.svg", 1),
            ("Tailandés o Argentino", "Tip Vehicular", "https://www.dropbox.com/scl/fi/26tyhyucjeebyqdjmz0g3/tailandesoargentino.mp4?rlkey=aldwmmsvda39nc88zsx76oo9p&st=w7zyhx4b&dl=0&raw=1", "/static/img/TAIOARG.svg", 1)
        ]
        created_at_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for vid in default_videos:
            cursor.execute("""
                INSERT INTO videos (titulo, categoria, video_url, miniatura_url, activo, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, vid + (created_at_time,))
        conn.commit()
        print("INFO (db_manager): Pre-populados 5 videos por defecto en la base de datos.")
    
    # Populate default configurations if empty
    defaults = {
        "site_logo": "/static/img/CarroQhatuL.png",
        "banner_video": "/static/videos/Banner_carroqhatuprin.mp4",
        "contact_phone": "+51 972043502",
        "contact_email": "rbm.aracayo@gmail.com",
        "about_description": "Plataforma líder en la Compra y Venta de Vehículos Usados en el Perú."
    }
    
    for clave, valor in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO site_config (clave, valor) VALUES (?, ?)", (clave, valor))
        
    conn.commit()
    
    # Pre-populate 4 default vehicles if table is empty
    cursor.execute("SELECT COUNT(*) FROM vehiculos")
    if cursor.fetchone()[0] == 0:
        default_cars = [
            ("Honda", "HR-V EXL", "2022", "1.8 cc", 76000, "Secuencial", "USD $17,500", "/static/img/HONDA-HR-V.jpg", "Arequipa", "excelente", 1),
            ("Nissan", "Navara 4x4", "2011", "2.5L Turbo Intercooler", 226000, "Mecánica", "PEN S/.37,000", "/static/img/NAVARA1.jpg", "Juliaca", "bueno", 1),
            ("Toyota", "RAV4 4x4 Full", "2013", "2.5cc", 152000, "Automática", "PEN S/.50,000", "/static/img/RAV4-1.jpg", "Arequipa", "bueno", 1),
            ("Toyota", "Hilux 4x4 SR", "2017", "1.0L GD", 93000, "Mecánica", "USD $21,000", "/static/img/HILUX2017-1.jpg", "Juliaca", "excelente", 1)
        ]
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for car in default_cars:
            cursor.execute("""
                INSERT INTO vehiculos (marca, modelo, year, motor, km, transmision, precio, imagen_url, ciudad, estado, verificado, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, car + (created_at,))
        conn.commit()
        print("INFO (db_manager): Pre-populados 4 vehículos estáticos en la base de datos.")
        
    conn.close()
    print("Database SQLite local inicializada en:", DB_PATH)

_supabase_offline = False

def is_supabase_available():
    """Quick check if Supabase client is initialized and online."""
    global _supabase_offline
    if _supabase_offline:
        return False
    return supabase is not None

def mark_supabase_offline():
    """Marks Supabase as offline for the current process to avoid network timeout delays."""
    global _supabase_offline
    _supabase_offline = True

# =====================================================================
# 1. COTIZACIONES (TASACIONES)
# =====================================================================

def save_cotizacion(marca, modelo, year, km, estado, precio_min, precio_max):
    """Saves a valuation. Always saves to local SQLite and attempts Supabase if online."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasaciones (marca, modelo, year, km, estado, precio_min, precio_max, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (marca, modelo, str(year), km, estado, precio_min, precio_max, created_at))
        conn.commit()
        local_id = cursor.lastrowid
        conn.close()
    except Exception as e:
        print("ERROR (db_manager) al guardar tasación local:", e)
        local_id = None

    if is_supabase_available():
        try:
            supabase.table("tasaciones").insert({
                "marca": marca,
                "modelo": modelo,
                "year": str(year),
                "km": km,
                "estado": estado,
                "precio_min": precio_min,
                "precio_max": precio_max
            }).execute()
            print("INFO (db_manager): Tasación guardada en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): Supabase no disponible para guardar tasación. Usando fallback local. Detalle:", e)
            
    return local_id

def get_all_cotizaciones():
    """Returns all valuations. Tries Supabase first, falls back to SQLite."""
    if is_supabase_available():
        try:
            res = supabase.table("tasaciones").select("*").order("created_at", desc=True).execute()
            data = []
            for r in res.data:
                created_at_str = r.get("created_at", "")
                if created_at_str:
                    try:
                        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        created_at_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                data.append({
                    "id": r.get("id"),
                    "marca": r.get("marca"),
                    "modelo": r.get("modelo"),
                    "year": r.get("year"),
                    "km": r.get("km"),
                    "estado": r.get("estado"),
                    "precio_min": r.get("precio_min"),
                    "precio_max": r.get("precio_max"),
                    "created_at": created_at_str
                })
            return data, "Supabase"
        except Exception as e:
            print("WARNING (db_manager): Error leyendo de Supabase. Usando SQLite local. Detalle:", e)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasaciones ORDER BY datetime(created_at) DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows, "Local SQLite"

# =====================================================================
# 2. SOLICITUDES (COMPRA, SERVICIOS, CONTACTO)
# =====================================================================

def save_solicitud(tipo, nombre, contacto, datos_vehiculo):
    """Saves a customer request (purchase/service/contact)."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datos_str = json.dumps(datos_vehiculo) if isinstance(datos_vehiculo, (dict, list)) else str(datos_vehiculo)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO solicitudes (tipo, nombre, contacto, datos_vehiculo, estado, created_at)
            VALUES (?, ?, ?, ?, 'Pendiente', ?)
        """, (tipo, nombre, contacto, datos_str, created_at))
        conn.commit()
        local_id = cursor.lastrowid
        conn.close()
    except Exception as e:
        print("ERROR (db_manager) al guardar solicitud local:", e)
        local_id = None

    if is_supabase_available():
        try:
            supabase.table("solicitudes").insert({
                "tipo": tipo,
                "nombre": nombre,
                "contacto": contacto,
                "datos_vehiculo": datos_str,
                "estado": "Pendiente"
            }).execute()
            print("INFO (db_manager): Solicitud guardada en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo guardar solicitud en Supabase. Usando fallback local. Detalle:", e)
            
    return local_id

def get_all_solicitudes():
    """Returns all requests, trying Supabase first."""
    if is_supabase_available():
        try:
            res = supabase.table("solicitudes").select("*").order("created_at", desc=True).execute()
            data = []
            for r in res.data:
                created_at_str = r.get("created_at", "")
                if created_at_str:
                    try:
                        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        created_at_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                data.append({
                    "id": r.get("id"),
                    "tipo": r.get("tipo"),
                    "nombre": r.get("nombre"),
                    "contacto": r.get("contacto"),
                    "datos_vehiculo": r.get("datos_vehiculo"),
                    "estado": r.get("estado", "Pendiente"),
                    "created_at": created_at_str
                })
            return data, "Supabase"
        except Exception as e:
            print("WARNING (db_manager): Error leyendo solicitudes de Supabase. Usando SQLite local. Detalle:", e)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM solicitudes ORDER BY datetime(created_at) DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows, "Local SQLite"

def update_solicitud_status(solicitud_id, nuevo_estado):
    """Updates the status of a request."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE solicitudes SET estado = ? WHERE id = ?", (nuevo_estado, solicitud_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print("ERROR (db_manager) al actualizar estado en SQLite:", e)

    if is_supabase_available():
        try:
            supabase.table("solicitudes").update({"estado": nuevo_estado}).eq("id", solicitud_id).execute()
            print("INFO (db_manager): Estado de solicitud actualizado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo actualizar estado en Supabase:", e)

# =====================================================================
# 3. VEHÍCULOS (CATÁLOGO DE AUTOS)
# =====================================================================

def save_vehiculo(marca, modelo, year, motor, km, transmision, precio, imagen_url, ciudad, estado, verificado, descripcion="", imagenes_extra=""):
    """Saves a new vehicle to the catalog."""
    import re
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    verificado_val = 1 if int(verificado) == 1 else 0
    try:
        clean_km = int(re.sub(r'[^\d]', '', str(km)) or 0)
    except:
        clean_km = 0
    
    # 1. SQLite Local
    local_id = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vehiculos (marca, modelo, year, motor, km, transmision, precio, imagen_url, ciudad, estado, verificado, descripcion, imagenes_extra, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (marca, modelo, str(year), motor, clean_km, transmision, precio, imagen_url, ciudad, estado, verificado_val, descripcion, imagenes_extra, created_at))
        conn.commit()
        local_id = cursor.lastrowid
        conn.close()
        print("INFO (db_manager): Vehículo guardado en SQLite local con ID:", local_id)
    except Exception as e:
        print("ERROR (db_manager) al guardar vehículo en SQLite:", e)
        local_id = None

    # 2. Supabase (Optional)
    if is_supabase_available():
        try:
            supabase.table("vehiculos").insert({
                "marca": marca,
                "modelo": modelo,
                "year": str(year),
                "motor": motor,
                "km": clean_km,
                "transmision": transmision,
                "precio": precio,
                "imagen_url": imagen_url,
                "ciudad": ciudad,
                "estado": estado,
                "verificado": verificado_val,
                "descripcion": descripcion,
                "imagenes_extra": imagenes_extra
            }).execute()
            print("INFO (db_manager): Vehículo guardado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo guardar vehículo en Supabase con imagenes_extra, reintentando sin imagenes_extra:", e)
            try:
                supabase.table("vehiculos").insert({
                    "marca": marca,
                    "modelo": modelo,
                    "year": str(year),
                    "motor": motor,
                    "km": clean_km,
                    "transmision": transmision,
                    "precio": precio,
                    "imagen_url": imagen_url,
                    "ciudad": ciudad,
                    "estado": estado,
                    "verificado": verificado_val,
                    "descripcion": descripcion
                }).execute()
                print("INFO (db_manager): Vehículo guardado en Supabase (fallback).")
            except Exception as e2:
                print("ERROR (db_manager) Supabase insert fallback error:", e2)

    return local_id

def get_all_vehiculos():
    """Returns all vehicles in the catalog, prioritizing local SQLite so new entries display instantly."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehiculos ORDER BY id DESC")
    sqlite_rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if is_supabase_available():
        try:
            res = supabase.table("vehiculos").select("*").order("id", desc=True).execute()
            if res.data and len(res.data) > len(sqlite_rows):
                return res.data, "Supabase"
        except Exception as e:
            print("WARNING (db_manager): Error consultando vehiculos en Supabase:", e)
            
    return sqlite_rows, "Local SQLite"

def get_vehiculo_by_id(vehiculo_id):
    """Returns a single vehicle from the catalog by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehiculos WHERE id = ?", (vehiculo_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)

    if is_supabase_available():
        try:
            res = supabase.table("vehiculos").select("*").eq("id", vehiculo_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            pass

    return None

def delete_vehiculo(vehiculo_id):
    """Deletes a vehicle from the catalog by ID."""
    # SQLite
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vehiculos WHERE id = ?", (vehiculo_id,))
        conn.commit()
        conn.close()
        print("INFO (db_manager): Vehículo eliminado de SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al eliminar vehículo de SQLite:", e)

    # Supabase
    if is_supabase_available():
        try:
            supabase.table("vehiculos").delete().eq("id", vehiculo_id).execute()
            print("INFO (db_manager): Vehículo eliminado de Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo eliminar vehículo de Supabase:", e)

def update_vehiculo(vehiculo_id, marca, modelo, year, motor, km, transmision, precio, imagen_url, ciudad, verificado, descripcion="", imagenes_extra=""):
    """Updates an existing vehicle entry in the catalog."""
    import re
    verificado_val = 1 if int(verificado) == 1 else 0
    try:
        clean_km = int(re.sub(r'[^\d]', '', str(km)) or 0)
    except:
        clean_km = 0

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vehiculos
            SET marca = ?, modelo = ?, year = ?, motor = ?, km = ?, transmision = ?, precio = ?, imagen_url = ?, ciudad = ?, verificado = ?, descripcion = ?, imagenes_extra = ?
            WHERE id = ?
        """, (marca, modelo, str(year), motor, clean_km, transmision, precio, imagen_url, ciudad, verificado_val, descripcion, imagenes_extra, vehiculo_id))
        conn.commit()
        conn.close()
        print(f"INFO (db_manager): Vehículo {vehiculo_id} actualizado en SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al actualizar vehículo en SQLite:", e)

    if is_supabase_available():
        try:
            supabase.table("vehiculos").update({
                "marca": marca,
                "modelo": modelo,
                "year": str(year),
                "motor": motor,
                "km": clean_km,
                "transmision": transmision,
                "precio": precio,
                "imagen_url": imagen_url,
                "ciudad": ciudad,
                "verificado": verificado_val,
                "descripcion": descripcion,
                "imagenes_extra": imagenes_extra
            }).eq("id", vehiculo_id).execute()
            print("INFO (db_manager): Vehículo actualizado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo actualizar vehículo en Supabase con imagenes_extra, reintentando sin imagenes_extra:", e)
            try:
                supabase.table("vehiculos").update({
                    "marca": marca,
                    "modelo": modelo,
                    "year": str(year),
                    "motor": motor,
                    "km": clean_km,
                    "transmision": transmision,
                    "precio": precio,
                    "imagen_url": imagen_url,
                    "ciudad": ciudad,
                    "verificado": verificado_val,
                    "descripcion": descripcion
                }).eq("id", vehiculo_id).execute()
            except Exception as e2:
                print("ERROR (db_manager) Supabase update fallback error:", e2)




# =====================================================================
# 4. CATÁLOGOS PDF (FOLLETOS)
# =====================================================================

def save_catalog(titulo, archivo_url):
    """Saves a PDF catalog to the database."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO catalogos (titulo, archivo_url, created_at)
            VALUES (?, ?, ?)
        """, (titulo, archivo_url, created_at))
        conn.commit()
        local_id = cursor.lastrowid
        conn.close()
        print("INFO (db_manager): Catálogo guardado en SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al guardar catálogo en SQLite:", e)
        local_id = None

    if is_supabase_available():
        try:
            supabase.table("catalogos").insert({
                "titulo": titulo,
                "archivo_url": archivo_url
            }).execute()
            print("INFO (db_manager): Catálogo guardado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo guardar catálogo en Supabase:", e)
            
    return local_id

def get_all_catalogos():
    """Returns all PDF catalogs."""
    if is_supabase_available():
        try:
            res = supabase.table("catalogos").select("*").order("created_at", desc=True).execute()
            return res.data, "Supabase"
        except Exception as e:
            pass
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM catalogos ORDER BY datetime(created_at) DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows, "Local SQLite"

def delete_catalog(catalogo_id):
    """Deletes a PDF catalog by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM catalogos WHERE id = ?", (catalogo_id,))
        conn.commit()
        conn.close()
        print("INFO (db_manager): Catálogo eliminado de SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al eliminar catálogo de SQLite:", e)

    if is_supabase_available():
        try:
            supabase.table("catalogos").delete().eq("id", catalogo_id).execute()
            print("INFO (db_manager): Catálogo eliminado de Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo eliminar catálogo de Supabase:", e)

# =====================================================================
# 5. CONFIGURACION DINAMICA (SITE CONFIG)
# =====================================================================

def get_site_config():
    """Returns site configuration as a dictionary."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM site_config")
    rows = cursor.fetchall()
    conn.close()
    
    config = {}
    for row in rows:
        config[row["clave"]] = row["valor"]
    return config

def update_site_config(clave, valor):
    """Updates a site configuration key."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO site_config (clave, valor) VALUES (?, ?)", (clave, valor))
        conn.commit()
        conn.close()
        print(f"INFO (db_manager): Configuración actualizada localmente [{clave} -> {valor}]")
    except Exception as e:
        print("ERROR (db_manager) al actualizar configuración en SQLite:", e)

    if is_supabase_available():
        try:
            supabase.table("site_config").upsert({"clave": clave, "valor": valor}).execute()
        except Exception as e:
            pass

# =====================================================================
# 6. PUBLICIDAD Y BANNERS PROMOCIONALES
# =====================================================================

def save_publicidad(titulo, imagen_url, enlace_url):
    """Saves a new promotional ad banner to the database."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO publicidad (titulo, imagen_url, enlace_url, activo, created_at)
            VALUES (?, ?, ?, 1, ?)
        """, (titulo, imagen_url, enlace_url, created_at))
        conn.commit()
        local_id = cursor.lastrowid
        conn.close()
        print("INFO (db_manager): Publicidad guardada en SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al guardar publicidad en SQLite:", e)
        local_id = None

    if is_supabase_available():
        try:
            supabase.table("publicidad").insert({
                "titulo": titulo,
                "imagen_url": imagen_url,
                "enlace_url": enlace_url,
                "activo": 1
            }).execute()
            print("INFO (db_manager): Publicidad guardada en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo guardar publicidad en Supabase:", e)
            
    return local_id

def get_all_publicidad():
    """Returns all promotional ads."""
    if is_supabase_available():
        try:
            res = supabase.table("publicidad").select("*").order("created_at", desc=True).execute()
            return res.data, "Supabase"
        except Exception as e:
            pass
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM publicidad ORDER BY datetime(created_at) DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows, "Local SQLite"

def delete_publicidad(pub_id):
    """Deletes a promotional ad by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM publicidad WHERE id = ?", (pub_id,))
        conn.commit()
        conn.close()
        print("INFO (db_manager): Publicidad eliminada de SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al eliminar publicidad de SQLite:", e)

    if is_supabase_available():
        try:
            supabase.table("publicidad").delete().eq("id", pub_id).execute()
            print("INFO (db_manager): Publicidad eliminada de Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo eliminar publicidad de Supabase:", e)


# =====================================================================
# 7. TESTIMONIOS (OPINIONES DE CLIENTES)
# =====================================================================

def save_testimonio(nombre, relacion, calificacion, comentario, aprobado=0):
    """Saves a new customer testimonial."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    aprobado_val = 1 if int(aprobado) == 1 else 0
    
    # 1. SQLite Local
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO testimonios (nombre, relacion, calificacion, comentario, aprobado, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, relacion, int(calificacion), comentario, aprobado_val, created_at))
        conn.commit()
        local_id = cursor.lastrowid
        conn.close()
        print("INFO (db_manager): Testimonio guardado en SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al guardar testimonio en SQLite:", e)
        local_id = None

    # 2. Supabase (Optional)
    if is_supabase_available():
        try:
            supabase.table("testimonios").insert({
                "nombre": nombre,
                "relacion": relacion,
                "calificacion": int(calificacion),
                "comentario": comentario,
                "aprobado": aprobado_val
            }).execute()
            print("INFO (db_manager): Testimonio guardado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo guardar testimonio en Supabase:", e)

    return local_id

def get_all_testimonios():
    """Returns all testimonials (approved and pending) for admin panel."""
    if is_supabase_available():
        try:
            res = supabase.table("testimonios").select("*").order("created_at", desc=True).execute()
            return res.data, "Supabase"
        except Exception as e:
            pass
            
    # SQLite Fallback
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM testimonios ORDER BY datetime(created_at) DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows, "Local SQLite"

def get_approved_testimonios():
    """Returns only approved testimonials for the public website."""
    if is_supabase_available():
        try:
            res = supabase.table("testimonios").select("*").eq("aprobado", 1).order("created_at", desc=True).execute()
            return res.data, "Supabase"
        except Exception as e:
            pass
            
    # SQLite Fallback
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM testimonios WHERE aprobado = 1 ORDER BY datetime(created_at) DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows, "Local SQLite"

def update_testimonio_status(testimonio_id, aprobado):
    """Updates the approval status of a testimonial."""
    aprobado_val = 1 if int(aprobado) == 1 else 0
    
    # SQLite
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE testimonios SET aprobado = ? WHERE id = ?", (aprobado_val, testimonio_id))
        conn.commit()
        conn.close()
        print(f"INFO (db_manager): Estado de testimonio {testimonio_id} actualizado a {aprobado_val} en SQLite.")
    except Exception as e:
        print("ERROR (db_manager) al actualizar estado de testimonio en SQLite:", e)

    # Supabase
    if is_supabase_available():
        try:
            supabase.table("testimonios").update({"aprobado": aprobado_val}).eq("id", testimonio_id).execute()
            print("INFO (db_manager): Estado de testimonio actualizado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo actualizar estado de testimonio en Supabase:", e)

def delete_testimonio(testimonio_id):
    """Permanently deletes a testimonial."""
    # SQLite
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM testimonios WHERE id = ?", (testimonio_id,))
        conn.commit()
        conn.close()
        print(f"INFO (db_manager): Testimonio {testimonio_id} eliminado de SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al eliminar testimonio de SQLite:", e)

    # Supabase
    if is_supabase_available():
        try:
            supabase.table("testimonios").delete().eq("id", testimonio_id).execute()
            print("INFO (db_manager): Testimonio eliminado de Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo eliminar testimonio de Supabase:", e)


# =====================================================================
#  VIDEOS Y TIPS MANAGEMENT
# =====================================================================

def save_video(titulo, categoria, video_url, miniatura_url, activo=1):
    """Saves a new video or tip to the database."""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO videos (titulo, categoria, video_url, miniatura_url, activo, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (titulo, categoria, video_url, miniatura_url, activo, created_at))
        conn.commit()
        local_id = cursor.lastrowid
        conn.close()
        print("INFO (db_manager): Video guardado en SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al guardar video en SQLite:", e)
        local_id = None

    if is_supabase_available():
        try:
            supabase.table("videos").insert({
                "titulo": titulo,
                "categoria": categoria,
                "video_url": video_url,
                "miniatura_url": miniatura_url,
                "activo": activo
            }).execute()
            print("INFO (db_manager): Video guardado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo guardar video en Supabase:", e)

    return local_id

def get_all_videos():
    """Returns all videos (active and hidden)."""
    if is_supabase_available():
        try:
            res = supabase.table("videos").select("*").order("id", desc=True).execute()
            return res.data, "Supabase"
        except Exception as e:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows, "Local SQLite"

def get_active_videos():
    """Returns only active videos for public display."""
    if is_supabase_available():
        try:
            res = supabase.table("videos").select("*").eq("activo", 1).order("id", desc=True).execute()
            return res.data, "Supabase"
        except Exception as e:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE activo = 1 ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows, "Local SQLite"

def toggle_video_status(video_id, activo):
    """Toggles active/hidden status of a video."""
    activo_val = 1 if int(activo) == 1 else 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET activo = ? WHERE id = ?", (activo_val, video_id))
        conn.commit()
        conn.close()
        print(f"INFO (db_manager): Estado de video {video_id} actualizado a {activo_val} en SQLite.")
    except Exception as e:
        print("ERROR (db_manager) al actualizar estado de video en SQLite:", e)

    if is_supabase_available():
        try:
            supabase.table("videos").update({"activo": activo_val}).eq("id", video_id).execute()
            print("INFO (db_manager): Estado de video actualizado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo actualizar estado de video en Supabase:", e)

def delete_video(video_id):
    """Permanently deletes a video entry."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()
        conn.close()
        print(f"INFO (db_manager): Video {video_id} eliminado de SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al eliminar video de SQLite:", e)

    if is_supabase_available():
        try:
            supabase.table("videos").delete().eq("id", video_id).execute()
            print("INFO (db_manager): Video eliminado de Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo eliminar video de Supabase:", e)

def get_video_by_id(video_id):
    """Retrieves a single video entry by ID."""
    if is_supabase_available():
        try:
            res = supabase.table("videos").select("*").eq("id", video_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_video(video_id, titulo, categoria, video_url, miniatura_url, activo=1):
    """Updates an existing video entry."""
    activo_val = 1 if int(activo) == 1 else 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE videos
            SET titulo = ?, categoria = ?, video_url = ?, miniatura_url = ?, activo = ?
            WHERE id = ?
        """, (titulo, categoria, video_url, miniatura_url, activo_val, video_id))
        conn.commit()
        conn.close()
        print(f"INFO (db_manager): Video {video_id} actualizado en SQLite local.")
    except Exception as e:
        print("ERROR (db_manager) al actualizar video en SQLite:", e)

    if is_supabase_available():
        try:
            supabase.table("videos").update({
                "titulo": titulo,
                "categoria": categoria,
                "video_url": video_url,
                "miniatura_url": miniatura_url,
                "activo": activo_val
            }).eq("id", video_id).execute()
            print("INFO (db_manager): Video actualizado en Supabase.")
        except Exception as e:
            print("WARNING (db_manager): No se pudo actualizar video en Supabase:", e)


