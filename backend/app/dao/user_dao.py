# backend/app/dao/user_dao.py

from app.conexionbd import ConexionBD

class UserDAO:
    def __init__(self):
        self.conexion = ConexionBD()

    def register_user(self, username, email, password):
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
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            sp_call = "{CALL sp_LoginUser (?, ?)}"
            params = (username_or_email, password)
            cursor.execute(sp_call, params)
            user_row = cursor.fetchone()
            
            if user_row:
                user_data = {
                    "user_id": user_row[0],
                    "username": user_row[1],
                    "email": user_row[2]
                }
                return {"success": True, "user": user_data}
            else:
                return {"success": False, "error": "Credenciales inválidas"}
        except Exception as e:
            print(f"Error durante login: {e}")
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()

    # --- NUEVOS MÉTODOS PARA PERFIL ---

    def get_user_profile(self, user_id):
        """Obtiene la información completa del perfil de un usuario."""
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            sp_call = "{CALL sp_GetUserProfile (?)}"
            cursor.execute(sp_call, (user_id,))
            row = cursor.fetchone()
            
            if row:
                profile_data = {
                    "user_id": row.UserID,
                    "username": row.Username,
                    "email": row.Email,
                    "bio": row.Bio,
                    "avatar": row.Avatar,
                    "created_at": str(row.CreatedAt) # Convertimos fecha a string
                }
                return {"success": True, "profile": profile_data}
            else:
                return {"success": False, "error": "Usuario no encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()

    def update_user_profile(self, user_id, username, bio, avatar):
        """Actualiza la información del perfil."""
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            sp_call = "{CALL sp_UpdateUserProfile (?, ?, ?, ?)}"
            params = (user_id, username, bio, avatar)
            
            cursor.execute(sp_call, params)
            result = cursor.fetchone()[0]
            self.conexion.connection.commit()
            
            if result == 'SUCCESS':
                return {"success": True, "message": "Perfil actualizado correctamente"}
            else:
                return {"success": False, "error": result} # Error de BD (ej. usuario duplicado)
        except Exception as e:
            if self.conexion.connection:
                self.conexion.connection.rollback()
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()