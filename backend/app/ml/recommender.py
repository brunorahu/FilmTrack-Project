# backend/app/ml/recommender.py
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ContentBasedRecommender:
    def __init__(self):
        pass

    def _get_genre_vector(self, genres_list, all_genres):
        """Convierte una lista de géneros en un vector binario (One-Hot Encoding)."""
        vector = [0] * len(all_genres)
        for genre in genres_list:
            if genre['id'] in all_genres:
                index = all_genres.index(genre['id'])
                vector[index] = 1
        return vector

    def recommend(self, user_liked_movies, candidate_movies):
        """
        user_liked_movies: Lista de dicts con metadata de pelis que le gustaron al usuario.
        candidate_movies: Lista de dicts (ej. tendencias) para evaluar.
        """
        if not user_liked_movies:
            return candidate_movies # Si no sabemos qué le gusta, devolvemos las tendencias tal cual.

        # 1. Obtener universo de géneros únicos presentes en los datos
        all_genre_ids = set()
        
        for m in user_liked_movies + candidate_movies:
            for g in m.get('genres', []):
                all_genre_ids.add(g['id'])
        
        all_genre_ids = sorted(list(all_genre_ids)) # Lista fija para índices

        # 2. Crear el "Vector de Perfil de Usuario" (Promedio de lo que le gusta)
        user_vectors = []
        for m in user_liked_movies:
            user_vectors.append(self._get_genre_vector(m.get('genres', []), all_genre_ids))
        
        # El perfil es el promedio de todos sus gustos (Centroide)
        user_profile_vector = np.mean(user_vectors, axis=0).reshape(1, -1)

        # 3. Vectorizar candidatos y calcular similitud
        scored_candidates = []
        
        for m in candidate_movies:
            candidate_vector = np.array(self._get_genre_vector(m.get('genres', []), all_genre_ids)).reshape(1, -1)
            
            # CÁLCULO DE MACHINE LEARNING: Similitud de Coseno
            similarity_score = cosine_similarity(user_profile_vector, candidate_vector)[0][0]
            
            # Guardamos la peli con su score
            m['ml_score'] = similarity_score
            scored_candidates.append(m)

        # 4. Ordenar por score descendente (Los más parecidos primero)
        scored_candidates.sort(key=lambda x: x['ml_score'], reverse=True)
        
        return scored_candidates