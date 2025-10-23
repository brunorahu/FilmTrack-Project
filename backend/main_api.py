# backend/main_api.py

from flask import Flask, request, jsonify
from app.conexionbd import ConexionBD
from app.dao.user_dao import UserDAO
from app.dao.tmdb_dao import TMDB_DAO
import time

app = Flask(__name__)

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)