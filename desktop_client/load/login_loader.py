# desktop_client/load/login_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMessageBox # Para mostrar mensajes de alerta
import requests
from load.main_window_loader import MainWindow

class LoginWindow:
    def __init__(self):
        loader = QUiLoader()
        self.ui = loader.load("view/login_window.ui")
        
        self.main_window = None
        
        # Ocultamos los campos de registro al iniciar la ventana
        self.ui.le_signup_username.setVisible(False)
        self.ui.le_signup_password.setVisible(False)
        self.ui.le_signup_confirm_password.setVisible(False)
        
        # Conectamos los dos botones a sus respectivas funciones
        self.ui.btn_login.clicked.connect(self.handle_login)
        self.ui.btn_create_account.clicked.connect(self.handle_create_account)
        
        # Conectamos la señal de cambio de texto del email
        self.ui.le_signup_email.textChanged.connect(self.toggle_signup_fields)
            
    def handle_login(self):
        username = self.ui.le_username_email.text()
        password = self.ui.le_password.text()
        
        print(f"Intentando iniciar sesión con usuario: {username}")
        api_url = "http://localhost:5000/api/users/login"
        payload = {"username_or_email": username, "password": password}
        
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                user_info = response_data['user']
                print("¡Inicio de sesión exitoso!")
                self.main_window = MainWindow()
                self.main_window.set_user_info(user_info)
                self.main_window.ui.show()
                self.ui.accept()
            else:
                QMessageBox.warning(self.ui, "Error de Login", "Usuario o contraseña incorrectos.")
        except requests.exceptions.ConnectionError as e:
            QMessageBox.critical(self.ui, "Error de Conexión", "No se pudo conectar a la API.")

    def handle_create_account(self):
        username = self.ui.le_signup_username.text()
        email = self.ui.le_signup_email.text()
        password = self.ui.le_signup_password.text()
        confirm_password = self.ui.le_signup_confirm_password.text()
        
        if not all([username, email, password, confirm_password]):
            QMessageBox.warning(self.ui, "Campos Vacíos", "Por favor, rellena todos los campos.")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self.ui, "Error de Contraseña", "Las contraseñas no coinciden.")
            return

        api_url = "http://localhost:5000/api/users/register"
        payload = {"username": username, "email": email, "password": password}
        
        print(f"Intentando registrar al nuevo usuario: {username}")
        
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 201:
                QMessageBox.information(self.ui, "Registro Exitoso", "¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.")
                self.ui.le_signup_username.clear()
                self.ui.le_signup_email.clear()
                self.ui.le_signup_password.clear()
                self.ui.le_signup_confirm_password.clear()
            else:
                QMessageBox.critical(self.ui, "Error de Registro", "No se pudo crear la cuenta. El usuario o email ya podrían existir.")
        except requests.exceptions.ConnectionError as e:
            QMessageBox.critical(self.ui, "Error de Conexión", "No se pudo conectar a la API.")

    def toggle_signup_fields(self, text):
        """
        Muestra los campos adicionales de registro si el campo de email tiene texto.
        """
        is_visible = bool(text)
        
        self.ui.le_signup_username.setVisible(is_visible)
        self.ui.le_signup_password.setVisible(is_visible)
        self.ui.le_signup_confirm_password.setVisible(is_visible)