# backend/app/dao/tmdb_dao.py

import requests

class TMDB_DAO:
    def __init__(self):
        # Reemplaza esto con tu propia clave de API
        self.api_key = 'b7ab64906311f8d228a5e12b8ecf8ac1'
        self.base_url = 'https://api.themoviedb.org/3'

    def get_trending_movies(self):
        """
        Obtiene la lista de películas en tendencia desde la API de TMDB.
        """
        # La URL específica del endpoint de 'trending' de TMDB
        endpoint = f'{self.base_url}/trending/movie/week'
        
        # Parámetros para la petición, incluyendo nuestra clave de API
        params = {
            'api_key': self.api_key,
            'language': 'es-MX' # Para obtener los resultados en español
        }
        
        try:
            response = requests.get(endpoint, params=params)
            # a_raise_for_status() lanzará un error si la petición no fue exitosa (ej. 404, 401)
            response.raise_for_status() 
            
            # Devolvemos los resultados en formato JSON
            return {"success": True, "data": response.json()['results']}
        
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con la API de TMDB: {e}")
            return {"success": False, "error": str(e)}