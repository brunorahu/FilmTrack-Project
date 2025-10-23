# backend/app/dao/tmdb_dao.py

import requests

class TMDB_DAO:
    def __init__(self):
        self.api_key = 'b7ab64906311f8d228a5e12b8ecf8ac1' # Asegúrate de que tu clave esté aquí
        self.base_url = 'https://api.themoviedb.org/3'

    def get_trending_movies(self):
        # ... (este método se queda igual)
        endpoint = f'{self.base_url}/trending/movie/week'
        params = {'api_key': self.api_key, 'language': 'es-MX'}
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return {"success": True, "data": response.json()['results']}
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con la API de TMDB: {e}")
            return {"success": False, "error": str(e)}

    def search_movies(self, query):
        """
        Busca películas en la API de TMDB según un término de búsqueda (query).
        """
        endpoint = f'{self.base_url}/search/movie'
        params = {
            'api_key': self.api_key,
            'query': query,
            'language': 'es-MX'
        }
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return {"success": True, "data": response.json()['results']}
        except requests.exceptions.RequestException as e:
            print(f"Error en la búsqueda con TMDB: {e}")
            return {"success": False, "error": str(e)}
        
    def get_movie_details(self, movie_id):
        """
        Obtiene los detalles completos de una película específica usando su ID.
        """
        endpoint = f'{self.base_url}/movie/{movie_id}'
        params = {
            'api_key': self.api_key,
            'language': 'es-MX'
        }
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener detalles de TMDB: {e}")
            return {"success": False, "error": str(e)}