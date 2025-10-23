# desktop_client/load/login_loader.py

from PySide6.QtUiTools import QUiLoader
import requests
from load.main_window_loader import MainWindow # <-- ¡NUEVA IMPORTACIÓN!

class LoginWindow:
    def __init__(self):
        loader = QUiLoader()
        self.ui = loader.load("view/login_window.ui")

        self.main_window = None # Para mantener una referencia a la ventana principal

        self.ui.btn_login.clicked.connect(self.handle_login)

    def handle_login(self):
        username = self.ui.le_username_email.text()
        password = self.ui.le_password.text()

        print(f"Intentando iniciar sesión con usuario: {username}")

        api_url = "http://localhost:5000/api/users/login"

        payload = {
            "username_or_email": username,
            "password": password
        }

        try:
            # Hacemos la petición POST a la API (solo una vez)
            response = requests.post(api_url, json=payload)
            
            # --- ¡PASO DE DEPURACIÓN! ---
            # Imprimimos la respuesta cruda para verla
            print("--- RESPUESTA CRUDA DE LA API ---")
            print(response.text)
            print("---------------------------------")
            # --- FIN DEL PASO DE DEPURACIÓN ---

            if response.status_code == 200:
                response_data = response.json()
                user_info = response_data['user']
                
                print("¡Inicio de sesión exitoso!")
                print("Datos del usuario:", user_info)
                
                self.main_window = MainWindow()
                self.main_window.set_user_info(user_info)
                self.main_window.ui.show()
                self.ui.close() 

            else:
                error_data = response.json()
                print("Error de inicio de sesión:", error_data.get("error"))

        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión: No se pudo conectar a la API. {e}")