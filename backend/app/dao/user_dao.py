# backend/app/dao/user_dao.py

from app.modelo.user import User
from app.conexionbd import ConexionBD

class UserDAO:
    def __init__(self):
        self.conexion = ConexionBD()
        self.user = User()

    def register_user(self, username, email, password):
        # Lógica para llamar al sp_RegisterUser...
        print(f"Registrando al usuario {username}...")
        # Esta funcionalidad la implementaremos más adelante.
        pass