# backend/main_api.py

import os
from werkzeug.utils import secure_filename
from app.dao.ml_dao import ML_DAO

from flask import Flask, request, jsonify, send_from_directory
from app.conexionbd import ConexionBD
from app.dao.user_dao import UserDAO
from app.dao.tmdb_dao import TMDB_DAO
from app.dao.library_dao import LibraryDAO 
import time

from app.dao.social_dao import SocialDAO

app = Flask(__name__)

# Configuración de subida de archivos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Nos aseguramos de que la carpeta exista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- LÓGICA DE REINTENTO DE CONEXIÓN A LA BD ---
max_retries = 5
retry_delay = 5

for attempt in range(max_retries):
    print(f"Iniciando API y conectando a la base de datos... (Intento {attempt + 1}/{max_retries})")
    db_connection = ConexionBD()
    db_connection.establecerConexionBD()
    if db_connection.connection:
        break
    print(f"La conexión falló. Reintentando en {retry_delay} segundos...")
    time.sleep(retry_delay)
else:
    print("No se pudo establecer conexión con la base de datos después de varios intentos.")

# --- ENDPOINTS DE LA API ---

@app.route('/')
def hello_world():
    return '¡La API de FilmTrack está funcionando!'

@app.route('/api/users/register', methods=['POST'])
def register_user_endpoint():
    data = request.get_json()
    if not data or not all(key in data for key in ['username', 'email', 'password']):
        return jsonify({"error": "Faltan datos requeridos (username, email, password)"}), 400

    user_dao = UserDAO()
    result = user_dao.register_user(data['username'], data['email'], data['password'])

    if result["success"]:
        return jsonify({"message": "Usuario registrado exitosamente", "user_id": result["user_id"]}), 201
    else:
        return jsonify({"error": f"No se pudo registrar el usuario: {result['error']}"}), 409

@app.route('/api/users/login', methods=['POST'])
def login_user_endpoint():
    data = request.get_json()
    if not data or not all(key in data for key in ['username_or_email', 'password']):
        return jsonify({"error": "Missing required data (username_or_email, password)"}), 400

    user_dao = UserDAO()
    result = user_dao.login_user(data['username_or_email'], data['password'])

    if result["success"]:
        return jsonify({"message": "Login successful", "user": result["user"]}), 200
    else:
        return jsonify({"error": result["error"]}), 401

@app.route('/api/movies/trending', methods=['GET'])
def get_trending_movies_endpoint():
    tmdb_dao = TMDB_DAO()
    result = tmdb_dao.get_trending_movies()

    if result["success"]:
        return jsonify(result["data"]), 200
    else:
        return jsonify({"error": f"No se pudo obtener datos de TMDB: {result['error']}"}), 503

@app.route('/api/movies/search', methods=['GET'])
def search_movies_endpoint():
    """
    Endpoint para buscar películas.
    Espera un parámetro 'query' en la URL (ej. /api/movies/search?query=Inception)
    """
    # Obtenemos el término de búsqueda de los parámetros de la URL
    query = request.args.get('query')

    if not query:
        return jsonify({"error": "El parámetro 'query' es requerido"}), 400

    tmdb_dao = TMDB_DAO()
    result = tmdb_dao.search_movies(query)

    if result["success"]:
        return jsonify(result["data"]), 200
    else:
        return jsonify({"error": f"No se pudieron obtener resultados de TMDB: {result['error']}"}), 503

@app.route('/api/movies/<int:movie_id>', methods=['GET'])
def get_movie_details_endpoint(movie_id):
    """
    Endpoint para obtener los detalles de una película por su ID.
    """
    tmdb_dao = TMDB_DAO()
    result = tmdb_dao.get_movie_details(movie_id)

    if result["success"]:
        return jsonify(result["data"]), 200
    else:
        return jsonify({"error": f"No se pudieron obtener detalles de TMDB: {result['error']}"}), 503

@app.route('/api/library/add', methods=['POST'])
def add_to_library_endpoint():
    """
    Endpoint para añadir una película a la librería de un usuario.
    Espera un JSON con: user_id, content_id, content_type, status.
    """
    data = request.get_json()
    required_keys = ['user_id', 'content_id', 'content_type', 'status']

    if not data or not all(key in data for key in required_keys):
        return jsonify({"error": "Faltan datos requeridos"}), 400

    library_dao = LibraryDAO()
    result = library_dao.add_movie_to_library(
        data['user_id'],
        data['content_id'],
        data['content_type'],
        data['status']
    )

    if result["success"]:
        return jsonify(result), 201 # 201 Created es apropiado aquí
    else:
        return jsonify(result), 500 # 500 Internal Server Error

@app.route('/api/library/<int:user_id>', methods=['GET'])
def get_library_endpoint(user_id):
    """
    Endpoint para obtener la librería de un usuario por su ID.
    """
    library_dao = LibraryDAO()
    result = library_dao.get_user_library(user_id)

    if result["success"]:
        return jsonify(result["data"]), 200
    else:
        return jsonify({"error": result["error"]}), 500

@app.route('/api/library/review', methods=['POST'])
def rate_review_endpoint():
    """
    Endpoint para que un usuario califique y/o deje una reseña de una película.
    Espera un JSON con: user_id, content_id, rating, y opcionalmente review_text.
    """
    data = request.get_json()
    required_keys = ['user_id', 'content_id', 'rating']
    
    if not data or not all(key in data for key in required_keys):
        return jsonify({"error": "Faltan datos requeridos (user_id, content_id, rating)"}), 400

    library_dao = LibraryDAO()
    result = library_dao.rate_and_review_movie(
        data['user_id'],
        data['content_id'],
        data['rating'],
        data.get('review_text') # .get() para manejar el campo opcional
    )

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/api/movies/<int:movie_id>/credits', methods=['GET'])
def get_movie_credits_endpoint(movie_id):
    tmdb_dao = TMDB_DAO()
    result = tmdb_dao.get_movie_credits(movie_id)

    if result["success"]:
        return jsonify(result["data"]), 200
    else:
        return jsonify({"error": result["error"]}), 503
    
# --- ENDPOINTS DE PERFIL DE USUARIO ---

@app.route('/api/users/profile/<int:user_id>', methods=['GET'])
def get_user_profile_endpoint(user_id):
    user_dao = UserDAO()
    result = user_dao.get_user_profile(user_id)
    if result["success"]:
        return jsonify(result["profile"]), 200
    else:
        return jsonify({"error": result["error"]}), 404

@app.route('/api/users/profile/<int:user_id>', methods=['PUT'])
def update_user_profile_endpoint(user_id):
    data = request.get_json()
    # Username es obligatorio, Bio y Avatar son opcionales
    if not data or 'username' not in data:
        return jsonify({"error": "El nombre de usuario es obligatorio"}), 400

    user_dao = UserDAO()
    result = user_dao.update_user_profile(
        user_id,
        data['username'],
        data.get('bio'),   # .get() devuelve None si no existe
        data.get('avatar')
    )

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 409 # 409 Conflict (ej. nombre de usuario ya existe)
    
# --- ENDPOINTS PARA IMÁGENES ---

# 1. Ruta para VER las imágenes (Servir archivos)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 2. Ruta para SUBIR las imágenes
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # Limpiamos el nombre del archivo por seguridad
        filename = secure_filename(file.filename)
        # Guardamos el archivo en la carpeta uploads
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Devolvemos la URL relativa del archivo
        return jsonify({"success": True, "filename": filename}), 201

    return jsonify({"error": "File type not allowed"}), 400

# --- ENDPOINTS SOCIALES ---

@app.route('/api/social/follow', methods=['POST'])
def follow_user_endpoint():
    data = request.get_json()
    social_dao = SocialDAO()
    # Espera: { "follower_id": 1, "following_id": 2 }
    result = social_dao.follow_user(data['follower_id'], data['following_id'])
    if result["success"]:
        return jsonify({"message": "Seguido correctamente"}), 200
    else:
        return jsonify(result), 500

@app.route('/api/social/unfollow', methods=['POST'])
def unfollow_user_endpoint():
    data = request.get_json()
    social_dao = SocialDAO()
    result = social_dao.unfollow_user(data['follower_id'], data['following_id'])
    if result["success"]:
        return jsonify({"message": "Dejado de seguir"}), 200
    else:
        return jsonify(result), 500

@app.route('/api/social/search', methods=['GET'])
def search_users_endpoint():
    user_id = request.args.get('user_id')
    query = request.args.get('query', '')
    if not user_id: return jsonify({"error": "Falta user_id"}), 400
    
    social_dao = SocialDAO()
    result = social_dao.search_users(user_id, query)
    if result["success"]:
        return jsonify(result["data"]), 200
    else:
        return jsonify(result), 500

@app.route('/api/social/feed/<int:user_id>', methods=['GET'])
def get_feed_endpoint(user_id):
    social_dao = SocialDAO()
    # Primero obtenemos la actividad cruda de la BD
    result = social_dao.get_activity_feed(user_id)
    
    if result["success"]:
        feed_data = result["data"]
        # ENRIQUECIMIENTO: Necesitamos títulos y pósters de TMDB
        # Esto podría ser lento si son muchos, idealmente cachear o hacer en frontend
        # Por ahora, para simplificar, devolvemos la data cruda y dejamos 
        # que el Frontend (Reflex/PySide) consulte los detalles de la película.
        return jsonify(feed_data), 200
    else:
        return jsonify(result), 500

@app.route('/api/social/following/<int:user_id>', methods=['GET'])
def get_following_endpoint(user_id):
    social_dao = SocialDAO()
    result = social_dao.get_following(user_id)
    if result["success"]:
        return jsonify(result["data"]), 200
    else:
        return jsonify(result), 500
    
# --- ENDPOINT DE RECOMENDACIONES ---

@app.route('/api/social/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations_endpoint(user_id):
    social_dao = SocialDAO()
    # 1. Intentamos obtener recomendaciones sociales
    result = social_dao.get_recommendations(user_id)
    
    if result["success"]:
        rec_data = result["data"]
        
        # 2. ENRIQUECIMIENTO (Igual que en el feed)
        # Si la lista está vacía (no tienes amigos o coincidencia),
        # aquí podríamos implementar el Fallback a TMDB.
        # Por ahora, devolvemos la lista (vacía o llena) para que el frontend la procese.
        
        return jsonify(rec_data), 200
    else:
        return jsonify(result), 500

@app.route('/api/ml/recommendations/<int:user_id>', methods=['GET'])
def get_ml_recommendations_endpoint(user_id):
    dao = ML_DAO()
    result = dao.get_ml_recommendations(user_id)
    if result["success"]:
        return jsonify(result["data"]), 200
    else:
        return jsonify(result), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)