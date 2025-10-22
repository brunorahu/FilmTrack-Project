# backend/main_api.py

from flask import Flask
from app.conexionbd import ConexionBD
import time

# Creamos la instancia de la aplicación Flask
app = Flask(__name__)

# --- LÓGICA DE REINTENTO DE CONEXIÓN A LA BD ---
max_retries = 5
retry_delay = 5  # segundos

for attempt in range(max_retries):
    print(f"Iniciando API y conectando a la base de datos... (Intento {attempt + 1}/{max_retries})")
    db_connection = ConexionBD()
    db_connection.establecerConexionBD()
    
    # Si la conexión tiene éxito, salimos del bucle
    if db_connection.connection:
        break
    
    print(f"La conexión falló. Reintentando en {retry_delay} segundos...")
    time.sleep(retry_delay)
else:
    # Este bloque se ejecuta si el bucle termina sin un 'break'
    print("No se pudo establecer conexión con la base de datos después de varios intentos. Saliendo.")
    # En una aplicación real, podrías querer que el programa termine aquí.
    # Por ahora, dejaremos que Flask continúe para poder depurar.

# Creamos una ruta de prueba para ver que la API funciona
@app.route('/')
def hello_world():
    return '¡La API de FilmTrack está funcionando!'

# Este bloque asegura que el servidor se ejecute solo cuando corremos este script directamente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)