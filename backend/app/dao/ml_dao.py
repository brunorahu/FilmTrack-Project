# backend/app/dao/ml_dao.py
from app.conexionbd import ConexionBD
from app.dao.tmdb_dao import TMDB_DAO
from app.ml.recommender import ContentBasedRecommender

class ML_DAO:
    def __init__(self):
        self.conexion = ConexionBD()
        self.tmdb = TMDB_DAO()
        self.engine = ContentBasedRecommender()

    def get_ml_recommendations(self, user_id):
        try:
            # 1. Obtener IDs de películas que el usuario calificó alto (4 o 5)
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            cursor.execute("SELECT ContentID FROM UserLibrary WHERE UserID = ? AND Rating >= 4", (user_id,))
            rows = cursor.fetchall()
            liked_ids = [row.ContentID for row in rows]
            self.conexion.cerrarConexionBD()

            # 2. Obtener detalles completos (Géneros) de esas películas desde TMDB
            user_liked_movies = []
            for mid in liked_ids[:10]: # Limitamos a las últimas 10 para no saturar
                details = self.tmdb.get_movie_details(mid)
                if details['success']:
                    user_liked_movies.append(details['data'])

            # 3. Obtener candidatos (Usamos "Popular" de TMDB como piscina de candidatos)
            # Nota: En un sistema real, tendrías una BD local, aquí usamos la API como fuente.
            candidates_res = self.tmdb.get_trending_movies() # O usar 'popular'
            candidates = []
            if candidates_res['success']:
                # Enriquecer candidatos con géneros detallados (Trend solo trae IDs)
                # Para simplificar y hacerlo rápido, asumiremos que 'genre_ids' sirve, 
                # pero el engine espera una lista de dicts [{'id': 1}, ...]. Lo adaptamos:
                for c in candidates_res['data']:
                    # Excluir las que ya vio (si está en liked_ids)
                    if c['id'] not in liked_ids:
                        # Adaptar formato de géneros para el motor ML
                        c['genres'] = [{'id': gid} for gid in c.get('genre_ids', [])]
                        candidates.append(c)

            # 4. EJECUTAR MODELO DE ML
            recommendations = self.engine.recommend(user_liked_movies, candidates)

            return {"success": True, "data": recommendations[:10]} # Top 10

        except Exception as e:
            return {"success": False, "error": str(e)}