# backend/main_api.py

from flask import Flask, request, jsonify
from app.conexionbd import ConexionBD
from app.dao.user_dao import UserDAO
import time

app = Flask(__name__)

# --- LÓGICA DE REINTENTO DE CONEXIÓN A LA BD ---
# (Esta parte se queda igual)
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
    """
    Endpoint para registrar un nuevo usuario.
    Espera un JSON con 'username', 'email' y 'password'.
    """
    # Obtenemos los datos del cuerpo de la petición
    data = request.get_json()

    # Validamos que los datos necesarios estén presentes
    if not data or not all(key in data for key in ['username', 'email', 'password']):
        return jsonify({"error": "Faltan datos requeridos (username, email, password)"}), 400

    user_dao = UserDAO()
    result = user_dao.register_user(data['username'], data['email'], data['password'])

    if result["success"]:
        return jsonify({"message": "Usuario registrado exitosamente", "user_id": result["user_id"]}), 201
    else:
        # El error 409 (Conflict) es ideal para cuando un recurso ya existe (ej. email duplicado)
        return jsonify({"error": f"No se pudo registrar el usuario: {result['error']}"}), 409


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)