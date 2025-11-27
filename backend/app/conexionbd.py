# backend/app/conexionbd.py

import pyodbc

class ConexionBD:
    def __init__(self):
        # OJO: El servidor ahora es 'db', el nombre del servicio en docker-compose
        self.server = 'db' 
        self.database = 'FilmTrackDB'
        self.username = 'sa'
        self.password = 'fuqtix-humke6-cukjYx' # La misma contraseña de docker-compose
        self.connection = None

    def establecerConexionBD(self):
        try:
            self.connection = pyodbc.connect(
                'DRIVER={ODBC Driver 18 for SQL Server};'
                f'SERVER={self.server};'
                f'DATABASE={self.database};'
                f'UID={self.username};'
                f'PWD={self.password};'
                'TrustServerCertificate=yes;'
            )
            print("¡Conexión a la BD exitosa desde el backend!")
        except Exception as e:
            print(f"Error al conectar a la BD: {e}")

    def cerrarConexionBD(self):
        if self.connection:
            self.connection.close()
            print("Conexión a la BD cerrada.")