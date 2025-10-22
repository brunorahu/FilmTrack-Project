# backend/app/dao/user_dao.py

from app.conexionbd import ConexionBD

class UserDAO:
    def __init__(self):
        self.conexion = ConexionBD()

    def register_user(self, username, email, password):
        # (The register_user method stays the same)
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            sp_call = "{CALL sp_RegisterUser (?, ?, ?)}"
            params = (username, email, password)
            cursor.execute(sp_call, params)
            new_user_id = cursor.fetchone()[0]
            self.conexion.connection.commit()
            return {"success": True, "user_id": new_user_id}
        except Exception as e:
            if self.conexion.connection:
                self.conexion.connection.rollback()
            print(f"Error al registrar usuario: {e}")
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()

    def login_user(self, username_or_email, password):
        """
        Calls the stored procedure to log in a user.
        Returns user data if successful, or an error message if it fails.
        """
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            sp_call = "{CALL sp_LoginUser (?, ?)}"
            params = (username_or_email, password)
            cursor.execute(sp_call, params)

            # fetchone() will return a row if login is successful, or None if it fails
            user_row = cursor.fetchone()

            if user_row:
                user_data = {
                    "user_id": user_row[0],
                    "username": user_row[1],
                    "email": user_row[2]
                }
                return {"success": True, "user": user_data}
            else:
                return {"success": False, "error": "Invalid credentials"}

        except Exception as e:
            print(f"Error during login: {e}")
            return {"success": False, "error": str(e)}

        finally:
            self.conexion.cerrarConexionBD()