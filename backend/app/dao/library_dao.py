# backend/app/dao/library_dao.py

from app.conexionbd import ConexionBD

class LibraryDAO:
    def __init__(self):
        self.conexion = ConexionBD()

    def add_movie_to_library(self, user_id, content_id, content_type, status):
        """
        Llama al procedimiento almacenado para añadir una película a la librería.
        """
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()

            sp_call = "{CALL sp_AddMovieToLibrary (?, ?, ?, ?)}"
            params = (user_id, content_id, content_type, status)

            cursor.execute(sp_call, params)
            result = cursor.fetchone()[0]

            self.conexion.connection.commit()

            if result == 'SUCCESS':
                return {"success": True, "message": "Contenido añadido a la librería."}
            else:
                return {"success": False, "error": result}

        except Exception as e:
            if self.conexion.connection:
                self.conexion.connection.rollback()
            return {"success": False, "error": str(e)}

        finally:
            self.conexion.cerrarConexionBD()