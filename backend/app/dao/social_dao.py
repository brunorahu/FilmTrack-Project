# backend/app/dao/social_dao.py
from app.conexionbd import ConexionBD

class SocialDAO:
    def __init__(self):
        self.conexion = ConexionBD()

    def follow_user(self, follower_id, following_id):
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            cursor.execute("{CALL sp_FollowUser (?, ?)}", (follower_id, following_id))
            self.conexion.connection.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()

    def unfollow_user(self, follower_id, following_id):
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            cursor.execute("{CALL sp_UnfollowUser (?, ?)}", (follower_id, following_id))
            self.conexion.connection.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()

    # En backend/app/dao/social_dao.py

    def search_users(self, current_user_id, query):
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            
            # --- CORRECCIÓN AQUÍ: Usamos EXEC en lugar de CALL ---
            cursor.execute("EXEC sp_SearchUsersToFollow ?, ?", (current_user_id, query))
            
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append({
                    "user_id": row.UserID,
                    "username": row.Username,
                    "avatar": row.Avatar,
                    # Convertimos explícitamente a bool para evitar problemas en el JSON
                    "is_following": True if row.IsFollowing == 1 else False 
                })
            return {"success": True, "data": users}
        except Exception as e:
            print(f"Error en search_users DAO: {e}") # Importante imprimir el error real en consola
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()

    def get_activity_feed(self, current_user_id):
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            cursor.execute("{CALL sp_GetFriendActivity (?)}", (current_user_id,))
            rows = cursor.fetchall()
            feed = []
            for row in rows:
                feed.append({
                    "username": row.Username,
                    "avatar": row.Avatar,
                    "content_id": row.ContentID,
                    "content_type": row.ContentType, # Agregado
                    "status": row.Status,
                    "rating": row.Rating,
                    "date": str(row.ActivityDate),
                    "review": row.ReviewText
                })
            return {"success": True, "data": feed}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()

    def get_following(self, user_id):
        """Obtiene la lista de usuarios que sigo."""
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            
            query = """
            SELECT u.UserID, u.Username, u.Avatar
            FROM Users u
            INNER JOIN Follows f ON u.UserID = f.FollowingID
            WHERE f.FollowerID = ?
            """
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            following = []
            for row in rows:
                following.append({
                    "user_id": row.UserID,
                    "username": row.Username,
                    "avatar": row.Avatar
                })
            return {"success": True, "data": following}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()

    def get_recommendations(self, user_id):
        """Obtiene recomendaciones basadas en amigos."""
        try:
            self.conexion.establecerConexionBD()
            cursor = self.conexion.connection.cursor()
            
            # Ejecutamos el SP
            cursor.execute("EXEC sp_GetSocialRecommendations ?", (user_id,))
            rows = cursor.fetchall()
            
            recommendations = []
            for row in rows:
                recommendations.append({
                    "content_id": row.ContentID,
                    "friend_count": row.FriendCount,
                    "avg_rating": float(row.AvgFriendRating)
                })
            return {"success": True, "data": recommendations}
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {"success": False, "error": str(e)}
        finally:
            self.conexion.cerrarConexionBD()