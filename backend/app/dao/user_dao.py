# backend/app/dao/user_dao.py

# Quitamos la importación de User, ya que no la usaremos aquí todavía.
# from app.modelo.user import User
from app.conexionbd import ConexionBD

class UserDAO:
    def __init__(self):
        self.conexion = ConexionBD()

    def register_user(self, username, email, password):
        """
        Llama al procedimiento almacenado para registrar un nuevo usuario.
        Devuelve el ID del nuevo usuario si tiene éxito, o un mensaje de error si falla.
        """
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()

            # Preparamos la llamada al procedimiento almacenado
            sp_call = "{CALL sp_RegisterUser (?, ?, ?)}"
            params = (username, email, password)

            # Ejecutamos el procedimiento
            cursor.execute(sp_call, params)

            # Obtenemos el resultado (el NewUserID que devuelve el SP)
            new_user_id = cursor.fetchone()[0]

            # Confirmamos la transacción
            self.conexion.connection.commit()

            return {"success": True, "user_id": new_user_id}

        except Exception as e:
            # Si hay un error (ej. usuario duplicado), revertimos la transacción
            if self.conexion.connection:
                self.conexion.connection.rollback()
            print(f"Error al registrar usuario: {e}")
            return {"success": False, "error": str(e)}

        finally:
            # Cerramos la conexión
            self.conexion.cerrarConexionBD()