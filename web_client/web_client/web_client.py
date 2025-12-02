import reflex as rx
import requests
import time
import asyncio

# --- STATE GLOBAL ---
class State(rx.State):
    # Variables de Sesión
    user_data: dict = {}
    error_message: str = ""
    
    # Variables del Dashboard
    trending_movies: list[dict] = []
    social_recommendations: list[dict] = []
    ml_recommendations: list[dict] = []
    
    # --- VARIABLES DE LIBRERÍA ---
    library_movies: list[dict] = [] 
    library_filter_mode: str = "Todos"
    library_search_query: str = ""
    
    # --- VARIABLES DE BÚSQUEDA DE PELÍCULAS ---
    search_movie_query: str = ""
    search_movie_results: list[dict] = []
    is_searching: bool = False 

    # Variables Generales de UI
    is_page_loading: bool = False 
    is_loading_details: bool = False 

    # Variables de Detalles de Película
    movie: dict = {}
    is_rating_open: bool = False
    rating_val: int = 0
    review_text: str = ""
    
    # --- NUEVAS VARIABLES DE ESTADO (FEEDBACK VISUAL) ---
    current_movie_status: str = "" 
    current_user_rating: int = 0
    
    # Variables del Casting
    cast: list[dict] = []
    director: str = ""
    
    # Variables de LogIn/Registro
    auth_mode: str = "login"
    
    # Variables del usuario (Perfil)
    profile_username: str = ""
    profile_bio: str = ""
    profile_avatar: str = "" 
    is_uploading: bool = False
    img_timestamp: float = 0 

    # --- VARIABLES SOCIALES ---
    search_query: str = ""
    search_results: list[dict] = [] 
    activity_feed: list[dict] = []  
    following_list: list[dict] = []
    is_loading_feed: bool = False
    has_searched: bool = False

    # --- SETTERS EXPLÍCITOS ---
    def set_is_rating_open(self, val: bool): self.is_rating_open = val
    def set_profile_username(self, val): self.profile_username = val
    def set_profile_bio(self, val): self.profile_bio = val
    def set_rating(self, val: int): self.rating_val = val
    def set_review_text_val(self, val: str): self.review_text = val
    def set_auth_mode(self, mode: str): self.auth_mode = mode
    def set_search_movie_query(self, val: str): self.search_movie_query = val
    def set_library_filter_mode(self, mode: str): self.library_filter_mode = mode
    def set_library_search_query(self, val: str): self.library_search_query = val

    # --- VARIABLE CALCULADA: LIBRERÍA FILTRADA ---
    @rx.var
    def filtered_library(self) -> list[dict]:
        items = self.library_movies
        if self.library_filter_mode == "Vistos":
            items = [m for m in items if m.get('status') == 'Completed']
        elif self.library_filter_mode == "Por Ver":
            items = [m for m in items if m.get('status') == 'Plan to Watch']
        if self.library_search_query:
            query = self.library_search_query.lower()
            items = [m for m in items if query in m.get('title', '').lower()]
        return items

    @rx.var
    def user_avatar_url(self) -> str:
        avatar_file = self.user_data.get("avatar")
        if not avatar_file: avatar_file = self.profile_avatar
        if avatar_file and avatar_file != "default":
            return f"http://localhost:5000/uploads/{avatar_file}?t={self.img_timestamp}"
        return ""

    @rx.var
    def hero_movie(self) -> dict:
        if self.search_movie_query and len(self.search_movie_results) > 0:
            return self.search_movie_results[0]
        if self.trending_movies and len(self.trending_movies) > 0:
            return self.trending_movies[0]
        return {"title": "Cargando...", "overview": "...", "backdrop_path": "", "id": 0}
    
    # --- CARGA LIBRERÍA ---
    async def get_user_library(self):
        if not self.user_data: return
        self.is_page_loading = True
        yield 
        try:
            res = requests.get(f"http://localhost:5000/api/library/{self.user_data['user_id']}")
            if res.status_code == 200:
                raw_items = res.json()
                enriched_list = []
                for item in raw_items:
                    try:
                        det = requests.get(f"http://localhost:5000/api/movies/{item['content_id']}")
                        if det.status_code == 200:
                            movie_data = det.json()
                            movie_data['status'] = item['status'] 
                            movie_data['user_rating'] = item['rating']
                            enriched_list.append(movie_data)
                    except: continue
                self.library_movies = enriched_list
        except Exception as e:
            print(f"Error loading library: {e}")
        finally:
            self.is_page_loading = False

    # --- LÓGICA DE BÚSQUEDA ---
    async def handle_movie_search(self, query: str):
        self.search_movie_query = query
        if not query:
            self.search_movie_results = []
            return
        self.is_searching = True
        yield 
        try:
            res = requests.get(f"http://localhost:5000/api/movies/search?query={query}")
            if res.status_code == 200: self.search_movie_results = res.json()
            else: self.search_movie_results = []
        except Exception as e: print(f"Error searching movies: {e}")
        finally: self.is_searching = False 

    # --- LÓGICA DE DETALLES ---
    async def get_details(self):
        current_id = self.router.page.params.get("movie_id", "")
        if not current_id: return
        
        self.is_loading_details = True
        self.movie = {} 
        self.cast = []
        self.current_movie_status = "" 
        self.current_user_rating = 0   
        yield 

        try:
            res = requests.get(f"http://localhost:5000/api/movies/{current_id}")
            if res.status_code == 200: 
                self.movie = res.json()
                await self.check_movie_status(current_id)
        except: pass
        
        try:
            res_credits = requests.get(f"http://localhost:5000/api/movies/{current_id}/credits")
            if res_credits.status_code == 200:
                data = res_credits.json()
                crew = data.get('crew', [])
                director_item = next((member for member in crew if member['job'] == 'Director'), None)
                self.director = director_item['name'] if director_item else "N/A"
                self.cast = data.get('cast', [])[:6] 
            else: self.cast = [], "N/A"
        except: self.cast = [], "N/A"
        
        self.is_loading_details = False

    async def check_movie_status(self, movie_id):
        user_id = self.user_data.get('user_id')
        if not user_id: return
        try:
            res = requests.get(f"http://localhost:5000/api/library/{user_id}")
            if res.status_code == 200:
                library_items = res.json()
                for item in library_items:
                    if str(item['content_id']) == str(movie_id):
                        self.current_movie_status = item['status']
                        self.current_user_rating = item['rating'] or 0
                        break
        except Exception as e:
            print(f"Error checking status: {e}")

    # --- ACCIONES ---
    def handle_add_to_library(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return rx.redirect("/login")
        payload = {"user_id": user_id, "content_id": self.movie.get('id'), "content_type": "movie", "status": "Plan to Watch"}
        try:
            requests.post("http://localhost:5000/api/library/add", json=payload)
            self.current_movie_status = "Plan to Watch"
            return rx.window_alert("¡Añadido a tu librería!")
        except Exception as e: print(e)

    def handle_mark_as_watched(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return rx.redirect("/login")
        payload = {"user_id": user_id, "content_id": self.movie.get('id'), "content_type": "movie", "status": "Completed"}
        try:
            requests.post("http://localhost:5000/api/library/add", json=payload)
            self.current_movie_status = "Completed"
            return rx.window_alert("¡Marcada como Vista!")
        except Exception as e: print(e)

    def handle_save_review(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return rx.redirect("/login")
        payload = {"user_id": user_id, "content_id": self.movie.get('id'), "rating": self.rating_val, "review_text": self.review_text}
        try:
            requests.post("http://localhost:5000/api/library/review", json=payload)
            self.set_is_rating_open(False)
            self.current_movie_status = "Completed" 
            self.current_user_rating = self.rating_val
            return rx.window_alert("¡Calificación guardada!")
        except: pass

    # --- LÓGICA SOCIAL ---
    async def handle_live_search(self, query: str):
        self.search_query = query
        self.has_searched = True
        if not query:
            self.search_results = []
            self.has_searched = False
            return
        await asyncio.sleep(0.3) 
        if self.search_query != query: return
        user_id = self.user_data.get('user_id')
        if not user_id: return
        try:
            res = requests.get(f"http://localhost:5000/api/social/search?user_id={user_id}&query={query}")
            if res.status_code == 200: self.search_results = res.json()
            else: self.search_results = []
        except Exception as e: print(e)

    async def follow_user(self, target_user_id: int):
        my_id = self.user_data.get('user_id')
        if not my_id: return
        try:
            payload = {"follower_id": my_id, "following_id": target_user_id}
            res = requests.post("http://localhost:5000/api/social/follow", json=payload)
            if res.status_code == 200:
                for user in self.search_results:
                    if user["user_id"] == target_user_id: user["is_following"] = True
                await self.get_activity_feed_silent()
                await self.get_following_list_silent() 
        except Exception as e: print(e)

    async def unfollow_user(self, target_user_id: int):
        my_id = self.user_data.get('user_id')
        if not my_id: return
        try:
            payload = {"follower_id": my_id, "following_id": target_user_id}
            res = requests.post("http://localhost:5000/api/social/unfollow", json=payload)
            if res.status_code == 200:
                for user in self.search_results:
                    if user["user_id"] == target_user_id: user["is_following"] = False
                await self.get_activity_feed_silent()
                await self.get_following_list_silent()
        except Exception as e: print(e)

    async def get_activity_feed_silent(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return
        self.is_loading_feed = True 
        try:
            res = requests.get(f"http://localhost:5000/api/social/feed/{user_id}")
            if res.status_code == 200:
                raw_feed = res.json()
                enriched_feed = []
                for item in raw_feed:
                    try:
                        movie_res = requests.get(f"http://localhost:5000/api/movies/{item['content_id']}")
                        if movie_res.status_code == 200:
                            movie_data = movie_res.json()
                            item['movie_title'] = movie_data.get('title', 'Desconocido')
                            item['poster_path'] = movie_data.get('poster_path')
                            enriched_feed.append(item)
                    except: continue 
                self.activity_feed = enriched_feed
        except: pass
        finally: self.is_loading_feed = False

    async def get_following_list_silent(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return
        try:
            res = requests.get(f"http://localhost:5000/api/social/following/{user_id}")
            if res.status_code == 200: self.following_list = res.json()
        except: pass

    async def load_social_data(self):
        self.is_page_loading = True
        yield 
        await self.get_activity_feed_silent()
        await self.get_following_list_silent()
        self.is_page_loading = False

    # --- DASHBOARD LOADERS ---
    def get_trending_movies(self):
        try:
            res = requests.get("http://localhost:5000/api/movies/trending")
            if res.status_code == 200: self.trending_movies = res.json()
        except: pass

    async def get_social_recommendations(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return
        try:
            res = requests.get(f"http://localhost:5000/api/social/recommendations/{user_id}")
            if res.status_code == 200:
                raw_recs = res.json()
                enriched_recs = []
                for item in raw_recs:
                    try:
                        movie_res = requests.get(f"http://localhost:5000/api/movies/{item['content_id']}")
                        if movie_res.status_code == 200:
                            movie_data = movie_res.json()
                            movie_data['friend_count'] = item['friend_count'] 
                            movie_data['avg_rating'] = item['avg_rating']
                            enriched_recs.append(movie_data)
                    except: continue
                self.social_recommendations = enriched_recs
        except Exception as e: print(e)
        
    async def get_ml_recommendations(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return
        try:
            res = requests.get(f"http://localhost:5000/api/ml/recommendations/{user_id}")
            if res.status_code == 200:
                self.ml_recommendations = res.json()
        except Exception as e: print(e)

    async def load_dashboard_data(self):
        self.get_trending_movies() 
        await self.get_social_recommendations()
        await self.get_ml_recommendations() 

    # --- LOGIN ---
    async def handle_login(self, form_data: dict):
        self.is_page_loading = True 
        api_url = "http://localhost:5000/api/users/login"
        payload = {"username_or_email": form_data.get("username"), "password": form_data.get("password")}
        yield 

        try:
            await asyncio.sleep(0.5) 
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                self.user_data = response.json()['user']
                self.img_timestamp = time.time()
                self.get_user_profile_sync(self.user_data.get('user_id'))
                self.is_page_loading = False
                yield rx.redirect("/") 
            else: 
                self.error_message = "Usuario o contraseña incorrectos."
                self.is_page_loading = False
        except Exception as e: 
            self.error_message = f"Error: {e}"
            self.is_page_loading = False

    def get_user_profile_sync(self, user_id):
        try:
            res = requests.get(f"http://localhost:5000/api/users/profile/{user_id}")
            if res.status_code == 200:
                full_data = res.json()
                self.user_data['avatar'] = full_data.get('avatar')
                self.profile_avatar = full_data.get('avatar')
        except: pass
            
    def handle_register(self, form_data: dict):
        if form_data.get("reg_password") != form_data.get("confirm_password"):
            self.error_message = "Las contraseñas no coinciden."
            return
        api_url = "http://localhost:5000/api/users/register"
        payload = {"username": form_data.get("reg_username"), "email": form_data.get("reg_email"), "password": form_data.get("reg_password")}
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 201:
                self.error_message = ""
                return rx.window_alert("¡Cuenta creada! Ahora inicia sesión.")
            else: self.error_message = "Error: El usuario o correo ya existen."
        except Exception as e: self.error_message = f"Error de conexión: {e}"
            
    def get_user_profile(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return
        try:
            res = requests.get(f"http://localhost:5000/api/users/profile/{user_id}")
            if res.status_code == 200:
                data = res.json()
                self.profile_username = data.get('username', '')
                self.profile_bio = data.get('bio') or ""
                self.profile_avatar = data.get('avatar') or "default"
                self.user_data['avatar'] = self.profile_avatar
        except Exception as e: print(e)

    async def update_profile(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return
        payload = {"username": self.profile_username, "bio": self.profile_bio, "avatar": self.profile_avatar}
        try:
            res = requests.put(f"http://localhost:5000/api/users/profile/{user_id}", json=payload)
            if res.status_code == 200:
                self.user_data['username'] = self.profile_username
                self.user_data['avatar'] = self.profile_avatar
                self.img_timestamp = time.time()
                return rx.window_alert("Perfil actualizado correctamente")
            elif res.status_code == 409: return rx.window_alert("Ese nombre de usuario ya existe.")
            else: return rx.window_alert("Error al actualizar.")
        except Exception as e: print(e)

    async def handle_avatar_upload(self, files: list[rx.UploadFile]):
        if not files: return
        self.is_uploading = True
        file = files[0]
        try:
            file_content = await file.read()
            files_payload = {'file': (file.filename, file_content, file.content_type)}
            response = requests.post("http://localhost:5000/api/upload", files=files_payload)
            if response.status_code == 201:
                new_filename = response.json()['filename']
                self.profile_avatar = new_filename
                self.user_data['avatar'] = new_filename
                await self.update_profile()
            else: rx.window_alert("Error al subir la imagen.")
        except Exception as e:
            print(f"Error upload: {e}")
            rx.window_alert("Error de conexión al subir imagen.")
        finally: self.is_uploading = False
        
    def handle_logout(self):
        self.user_data = {} 
        self.profile_username = "" 
        return rx.redirect("/")

    def open_rating_modal(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return rx.redirect("/login")
        self.set_is_rating_open(True)
        
    


# --- COMPONENTES UI ---

def user_card(user: dict):
    avatar_url = rx.cond(user['avatar'] != "default", f"http://localhost:5000/uploads/{user['avatar']}", "")
    fallback_char = user['username'].to(str)[0]
    return rx.vstack(
        rx.box(
            rx.avatar(src=avatar_url, fallback=fallback_char, size="5", radius="full", border="2px solid #333"),
            rx.cond(
                user['is_following'],
                rx.icon("check", color="white", bg="#444", border_radius="full", padding="4px", size=24, position="absolute", bottom="0", right="0", cursor="pointer", _hover={"transform": "scale(1.1)", "bg": "#e53e3e"}, on_click=lambda: State.unfollow_user(user['user_id'])),
                rx.icon("plus", color="white", bg="#4a90e2", border_radius="full", padding="4px", size=24, position="absolute", bottom="0", right="0", cursor="pointer", _hover={"transform": "scale(1.1)", "bg": "#357abd"}, on_click=lambda: State.follow_user(user['user_id']))
            ), position="relative", margin_bottom="5px"
        ),
        rx.text(user['username'], color="#eee", font_weight="bold", font_size="14px", text_align="center", width="100%", style={"white-space": "nowrap", "overflow": "hidden", "text-overflow": "ellipsis"}),
        align_items="center", padding="10px", width="100px", transition="all 0.2s", _hover={"transform": "translateY(-2px)"}
    )

def following_avatar(user: dict):
    avatar_url = rx.cond(user['avatar'] != "default", f"http://localhost:5000/uploads/{user['avatar']}", "")
    fallback_char = user['username'].to(str)[0]
    return rx.tooltip(
        rx.avatar(src=avatar_url, fallback=fallback_char, size="4", radius="full", border="2px solid #4a90e2", cursor="pointer", _hover={"transform": "scale(1.1)", "transition": "0.2s"}),
        content=user['username']
    )

def feed_card(activity: dict):
    poster_url = f"https://image.tmdb.org/t/p/w200{activity['poster_path']}"
    user_avatar = rx.cond(activity['avatar'] != "default", f"http://localhost:5000/uploads/{activity['avatar']}", "")
    fallback_char = activity['username'].to(str)[0]
    rating_val = activity['rating'].to(int)
    return rx.card(
        rx.hstack(
            rx.image(src=poster_url, height="120px", width="80px", border_radius="6px", object_fit="cover"),
            rx.vstack(
                rx.hstack(
                    rx.avatar(src=user_avatar, fallback=fallback_char, size="2", radius="full"),
                    rx.text(f"{activity['username']}", font_weight="bold", color="white"),
                    rx.text("ha calificado", color="gray"),
                    rx.text(f"{activity['movie_title']}", color="#4a90e2", font_weight="bold"),
                    align_items="center", spacing="2"
                ),
                rx.hstack(*[rx.icon(tag="star", color=rx.cond(rating_val >= i, "gold", "gray"), size=14) for i in range(1, 6)], spacing="1"),
                rx.cond(activity['review'], rx.text(f"\"{activity['review']}\"", color="#ccc", font_style="italic", font_size="14px", border_left="3px solid #4a90e2", padding_left="10px")),
                rx.text(activity['date'].to(str)[:10], color="#555", font_size="12px", margin_top="5px"),
                align_items="start", spacing="2", width="100%"
            ), align_items="start", spacing="4"
        ), background_color="rgba(26, 26, 26, 0.9)", border="1px solid #333", padding="15px", width="100%"
    )
    
# --- COMPONENTE PROMOCIONAL  ---
# --- COMPONENTE PROMOCIONAL (VERSIÓN HTML PURO PARA ESTABILIDAD) ---
def desktop_promo_section():
    return rx.box(
        # 1. CAPA DE VIDEO (HTML Puro)
        # Usamos rx.html para forzar los atributos de video sin interferencia de React
        rx.html('''
            <video 
                src="/visual_filmtrack.mp4" 
                autoplay 
                loop 
                muted 
                playsinline 
                style="width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; opacity: 0.5; z-index: 0;"
            ></video>
        '''),
        
        # 2. CAPA DE FUSIÓN (Máscara de Degradado)
        rx.box(
            position="absolute", top="0", left="0", width="100%", height="100%",
            background="linear-gradient(to bottom, #111111 5%, rgba(17,17,17,0.0) 40%, rgba(17,17,17,0.0) 60%, #111111 95%)",
            z_index="1",
            pointer_events="none"
        ),

        # 3. CAPA DE CONTENIDO
        rx.vstack(
            rx.divider(color="#333", margin_y="60px", width="100%", opacity="0.0"),
            
            # Títulos
            rx.vstack(
                rx.heading("FilmTrack Desktop", size="9", font_weight="900", letter_spacing="-1px", color="white"),
                rx.text("El cine como nunca lo has visto.", size="6", color="gray", font_weight="medium"),
                align_items="center", spacing="2", margin_bottom="40px", width="100%"
            ),
            
            # Imagen Hero
            rx.box(
                rx.image(
                    src="/desktop_hero.png", 
                    width="100%", height="auto", 
                    border_radius="12px",
                    box_shadow="0 20px 80px -20px rgba(255, 100, 90, 0.3)" 
                ),
                padding="10px", border="1px solid rgba(255,255,255,0.1)", border_radius="16px",
                background="rgba(20, 20, 20, 0.6)", backdrop_filter="blur(10px)",
                max_width="1000px", margin_bottom="60px"
            ),
            
            # Grid de Características
            rx.grid(
                # Tarjeta 1
                rx.card(
                    rx.vstack(
                        rx.icon("zap", size=40, color="#F5D90A"),
                        rx.heading("Velocidad Pura", size="5", color="white"),
                        rx.text("Rendimiento nativo instantáneo.", color="gray", size="2"),
                        align_items="start", spacing="3"
                    ),
                    background="rgba(26, 26, 26, 0.8)", border="1px solid #333", padding="30px", backdrop_filter="blur(5px)"
                ),
                # Tarjeta 2
                rx.card(
                    rx.vstack(
                        rx.icon("maximize", size=40, color="#4a90e2"),
                        rx.heading("Inmersión Total", size="5", color="white"),
                        rx.text("Interfaz diseñada para desaparecer.", color="gray", size="2"),
                        rx.image(src="/desktop_detail.png", width="100%", height="150px", object_fit="cover", border_radius="8px", margin_top="10px", opacity="0.8"),
                        align_items="start", spacing="3"
                    ),
                    background="rgba(26, 26, 26, 0.8)", border="1px solid #333", padding="30px", backdrop_filter="blur(5px)",
                    grid_column="span 2"
                ),
                # Tarjeta 3
                rx.card(
                    rx.vstack(
                        rx.icon("folder-heart", size=40, color="#E53E3E"),
                        rx.heading("Tu Colección", size="5", color="white"),
                        rx.text("Organiza tu librería localmente.", color="gray", size="2"),
                        rx.image(src="/desktop_library.png", width="100%", height="100px", object_fit="cover", border_radius="8px", margin_top="10px", opacity="0.8"),
                        align_items="start", spacing="3"
                    ),
                    background="rgba(26, 26, 26, 0.8)", border="1px solid #333", padding="30px", backdrop_filter="blur(5px)"
                ),
                # HUECO PARA VER EL VIDEO

                columns="3", spacing="5", width="100%", max_width="1000px"
            ),
            
            # Call to Action
            rx.vstack(
                rx.text("Disponible para Windows", color="gray", margin_top="60px"),
                rx.button(
                    rx.icon("download", size=20), "Descargar la App de Escritorio",
                    size="4", padding="25px", radius="full", bg="white", color="black", font_weight="bold",
                    _hover={"transform": "scale(1.05)", "box_shadow": "0 0 20px rgba(255,255,255,0.4)"}, transition="all 0.2s ease"
                ),
                align_items="center", spacing="3", margin_bottom="100px"
            ),
            
            position="relative", z_index="2", width="100%", align_items="center", padding_x="20px"
        ),
        
        # Contenedor Principal
        position="relative", width="100%", background_color="#111111", overflow="hidden"
    )
    
# --- TARJETA DE LIBRERÍA (CON ICONOS) ---
def library_card(movie: dict):
    poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
    badge_color = rx.cond(movie['status'] == 'Completed', "green", "blue")
    
    return rx.link(
        rx.box(
            rx.box(
                rx.image(src=poster_url, width="160px", height="240px", border_radius="12px", object_fit="cover"),
                rx.cond(
                    movie['status'] == 'Completed',
                    rx.badge(rx.icon("check", size=16), color_scheme="green", variant="solid", position="absolute", top="10px", right="10px", z_index="10", border_radius="full", padding="5px"),
                    rx.badge(rx.icon("eye", size=16), color_scheme="blue", variant="solid", position="absolute", top="10px", right="10px", z_index="10", border_radius="full", padding="5px")
                ),
                position="relative", _hover={"transform": "scale(1.05)", "transition": "0.2s"}
            ),
            rx.text(movie["title"], color="white", font_weight="bold", font_size="14px", width="160px", style={"white-space": "nowrap", "overflow": "hidden", "text-overflow": "ellipsis", "display": "block"}, margin_top="8px"),
            padding="8px", cursor="pointer"
        ), href=f"/movie/{movie['id']}", text_decoration="none"
    )

def navbar(show_search: bool = False):
    auth_btn_style = {
        "width": "130px", "height": "40px", "display": "flex", "align_items": "center", "justify_content": "center",
        "font_weight": "600", "border_radius": "8px", "transition": "all 0.2s ease", "_hover": {"opacity": 0.9, "transform": "translateY(-1px)"}
    }
    return rx.hstack(
        rx.link(rx.image(src="/logo_clean.png", height="60px", width="auto", alt="Logo"), href="/", _hover={"opacity": 0.8}),
        rx.cond(
            show_search,
            rx.box(
                rx.input(
                    placeholder="Buscar película...", on_change=State.handle_movie_search, value=State.search_movie_query, debounce_timeout=500,
                    bg="rgba(255, 255, 255, 0.08)", border="1px solid rgba(255, 255, 255, 0.1)", color="white", width="400px", height="40px", radius="full", padding_left="20px",
                    _placeholder={"color": "#888"}, _focus={"bg": "rgba(255, 255, 255, 0.15)", "border_color": "#4a90e2", "outline": "none"}
                ), margin_left="30px"
            ), rx.spacer()
        ),
        rx.spacer(),
        rx.cond(
            State.user_data,
            rx.hstack(
                rx.tooltip(rx.link(rx.icon("users", color="white", size=28, stroke_width=1.0, _hover={"transform": "scale(1.1)", "transition": "0.2s"}), href="/social"), content="Social y Amigos"),
                rx.tooltip(rx.link(rx.image(src="/library_icon.png", height="40px", width="auto", _hover={"transform": "scale(1.1)", "transition": "0.2s"}), href="/library"), content="Mi librería"),
                rx.divider(orientation="vertical", height="30px", color="#444", margin_x="15px"),
                rx.link(rx.hstack(rx.avatar(src=State.user_avatar_url, name=State.user_data['username'], size="2"), rx.text(f"{State.user_data['username']}", color="white", font_weight="bold"), spacing="2", align_items="center"), href="/profile", text_decoration="none"),
                rx.text("Salir", color="#e53e3e", font_weight="bold", cursor="pointer", margin_left="15px", _hover={"text_decoration": "underline"}, on_click=State.handle_logout),
                align_items="center"
            ),
            rx.hstack(
                rx.link("Iniciar Sesión", href="/login", color="white", bg="transparent", border="1px solid #333", **auth_btn_style, text_decoration="none"),
                rx.link("Registrarse", href="/login", color="black", bg="white", border="1px solid white", **auth_btn_style, text_decoration="none"), 
                spacing="3", align_items="center"
            )
        ), width="100%", height="80px", padding_x="2em", background_color="rgba(17, 17, 17, 0.95)", border_bottom="1px solid #222", position="sticky", top="0", z_index="100", align_items="center"
    )

def movie_card(movie: dict):
    poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
    rating_val = movie["vote_average"].to(float) / 2
    return rx.link(
        rx.box(
            rx.image(src=poster_url, width="160px", height="240px", border_radius="12px", object_fit="cover", _hover={"transform": "scale(1.05)", "transition": "0.2s"}),
            rx.vstack(
                rx.text(movie["title"], color="white", font_weight="bold", font_size="14px", width="160px", style={"white-space": "nowrap", "overflow": "hidden", "text-overflow": "ellipsis", "display": "block"}, title=movie["title"]),
                rx.tooltip(rx.hstack(*[rx.icon(tag="star", color=rx.cond(rating_val >= i, "gold", "gray"), size=14, fill=rx.cond(rating_val >= i, "gold", "none")) for i in range(1, 6)], spacing="1"), content=f"Calificación: {rating_val:.1f}"),
                spacing="1", padding_top="8px"
            ), padding="8px", cursor="pointer"
        ), href=f"/movie/{movie['id']}", text_decoration="none"
    )
    
def actor_card(actor: dict):
    profile_url = rx.cond(actor["profile_path"], f"https://image.tmdb.org/t/p/w200{actor['profile_path']}", "https://via.placeholder.com/100x100?text=No+Img")
    return rx.vstack(rx.avatar(src=profile_url, size="6", radius="full", border="2px solid #333"), rx.text(actor["name"], color="white", font_size="14px", font_weight="bold", no_of_lines=1), rx.text(actor["character"], color="gray", font_size="12px", no_of_lines=1), align_items="center", text_align="center", width="120px")
    
# --- FUNCIÓN RESTAURADA Y CORREGIDA ---
def rating_dialog():
    poster_url = f"https://image.tmdb.org/t/p/w500{State.movie.get('poster_path', '')}"
    return rx.dialog.root(
        rx.dialog.content(
            rx.flex(
                rx.box(rx.image(src=poster_url, width="230px", height="225px", border_radius="8px", box_shadow="0 4px 12px rgba(0,0,0,0.5)"), padding="20px", background_color="#222", border_radius="8px 0 0 8px", display="flex", align_items="center", justify_content="center"),
                rx.vstack(
                    rx.hstack(rx.heading("¡Añadir a mi Tracking!", size="4", color="white"), rx.icon("x", color="gray", cursor="pointer", _hover={"color": "white"}, on_click=State.set_is_rating_open(False)), justify="between", width="100%", align_items="center"),
                    rx.text(f"Estás calificando: {State.movie.get('title', '')}", color="#888", font_size="14px", margin_bottom="10px"),
                    rx.hstack(*[rx.icon(tag="star", color=rx.cond(State.rating_val >= i, "gold", "#444"), size=28, cursor="pointer", transition="color 0.2s", on_click=lambda: State.set_rating(i)) for i in [1, 2, 3, 4, 5]], spacing="2", padding_y="10px"),
                    rx.text_area(placeholder="Escribe tu reseña aquí...", on_change=State.set_review_text_val, background_color="#2a2a2a", color="white", border="1px solid #333", border_radius="6px", min_height="120px", padding="12px", _focus={"border_color": "#4a90e2", "outline": "none"}),
                    rx.hstack(rx.button("Cancelar", variant="outline", color_scheme="gray", color="white", border_color="#555", _hover={"bg": "#333"}, on_click=State.set_is_rating_open(False)), rx.button("Guardar", bg="#28a745", color="white", on_click=State.handle_save_review, padding_x="20px", font_weight="bold"), spacing="3", justify="end", width="100%", margin_top="15px", align_items="center"),
                    padding="25px", spacing="3", width="100%", align_items="stretch"
                ), direction="row", spacing="0", width="100%"
            ), background_color="#1e1e1e", border="1px solid #333", border_radius="12px", max_width="650px", padding="0", overflow="hidden"
        ), open=State.is_rating_open, on_open_change=State.set_is_rating_open
    )

# --- PÁGINAS ---

def social_page():
    return rx.box(
        navbar(show_search=False),
        rx.cond(
            State.is_page_loading,
            rx.center(rx.spinner(color="white", size="3"), height="80vh", width="100%"),
            rx.flex(
                rx.vstack(
                    rx.vstack(
                        rx.hstack(rx.text("SIGUIENDO:", color="#c8c8c8", font_weight="bold", letter_spacing="2px"), rx.text(f"{State.following_list.length()}", color="#ffffff", font_weight="bold"), spacing="2", align_items="center", margin_bottom="10px"),
                        rx.hstack(rx.foreach(State.following_list, following_avatar), spacing="3", wrap="wrap"),
                        rx.divider(color="#444", margin_y="20px"), width="100%"
                    ),
                    rx.heading("Actividad de Amigos", color="white", size="6", margin_bottom="20px"),
                    rx.cond(State.is_loading_feed, rx.spinner(), rx.vstack(rx.foreach(State.activity_feed, feed_card), width="100%", spacing="4")),
                    width="65%", padding="40px", background="linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.7)), url('/background.jpg')", background_size="cover", background_attachment="fixed"
                ),
                rx.vstack(
                    rx.heading("Buscar Personas", color="white", size="4", margin_bottom="15px"),
                    rx.input(placeholder="Escribe un nombre...", on_change=State.handle_live_search, color="white", bg="#222", border="1px solid #444", width="100%"),
                    rx.divider(margin_y="20px", color="#444"),
                    rx.flex(rx.foreach(State.search_results, user_card), wrap="wrap", spacing="4", width="100%"),
                    rx.cond(State.has_searched & (State.search_results.length() == 0), rx.text("No se encontraron usuarios...", color="gray", font_style="italic", margin_top="20px")),
                    width="30%", padding="30px", border_left="1px solid #333", min_height="100vh", background_color="#111"
                ), width="100%", max_width="1600px", margin="0 auto", justify="between", min_height="100vh"
            )
        ), min_height="100vh", background_color="#000", on_mount=State.load_social_data, max_width="100vw", overflow_x="hidden"
    )

def login_page():
    background_url = "/fondo_cine.jpg"
    return rx.center(
        rx.vstack(
            rx.image(src="/logo_clean.png", height="150px", width="auto", margin_bottom="-10px"),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("Iniciar Sesión", color=rx.cond(State.auth_mode == "login", "white", "gray"), font_weight="bold", cursor="pointer", on_click=lambda: State.set_auth_mode("login"), border_bottom=rx.cond(State.auth_mode == "login", "2px solid white", "2px solid transparent"), padding_bottom="5px"),
                        rx.text("Registrarse", color=rx.cond(State.auth_mode == "register", "white", "gray"), font_weight="bold", cursor="pointer", on_click=lambda: State.set_auth_mode("register"), border_bottom=rx.cond(State.auth_mode == "register", "2px solid white", "2px solid transparent"), padding_bottom="5px"),
                        spacing="5", width="100%", margin_bottom="20px"
                    ),
                    rx.cond(
                        State.auth_mode == "login",
                        rx.form(
                            rx.vstack(rx.input(placeholder="Usuario o Email", name="username", width="100%", bg="#333", border="none", color="white", padding="5px"), rx.input(type="password", placeholder="Contraseña", name="password", width="100%", bg="#333", border="none", color="white", padding="5px"), 
                            rx.cond(State.is_page_loading, rx.button(rx.spinner(color="black", size="2"), width="100%", bg="white", size="3", margin_top="20px", disabled=True), rx.button("Iniciar Sesión", width="100%", bg="white", color="black", size="3", margin_top="20px", type="submit")),
                            spacing="4", width="100%"),
                            on_submit=State.handle_login, width="100%"
                        )
                    ),
                    rx.cond(
                        State.auth_mode == "register",
                        rx.form(
                            rx.vstack(rx.input(placeholder="Elige un Usuario", name="reg_username", width="100%", bg="#333", border="none", color="white", padding="5px"), rx.input(placeholder="Tu Correo", name="reg_email", width="100%", bg="#333", border="none", color="white", padding="5px"), rx.input(type="password", placeholder="Contraseña", name="reg_password", width="100%", bg="#333", border="none", color="white", padding="5px"), rx.input(type="password", placeholder="Confirmar Contraseña", name="confirm_password", width="100%", bg="#333", border="none", color="white", padding="5px"), rx.button("Crear Cuenta", width="100%", bg="white", color="black", size="3", margin_top="20px", type="submit"), spacing="4", width="100%"),
                            on_submit=State.handle_register, width="100%"
                        )
                    ),
                    rx.cond(State.error_message != "", rx.text(State.error_message, color="#e87c03", font_size="14px", margin_top="15px")),
                    align_items="start", width="100%"
                ), padding="60px", width="450px", background_color="rgba(0, 0, 0, 0.75)", border_radius="10px", box_shadow="0 0 20px rgba(0,0,0,0.5)"
            ), align="center", spacing="0"
        ), width="100%", height="100vh", background=f"linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 60%, rgba(0,0,0,0.8) 100%), url('{background_url}')", background_size="cover", background_position="center"
    )

def dashboard_page():
    hero_backdrop = rx.cond(State.hero_movie["backdrop_path"], f"https://image.tmdb.org/t/p/original{State.hero_movie['backdrop_path']}", "")
    return rx.box(
        navbar(show_search=True),
        rx.vstack(
            rx.cond(
                State.trending_movies | State.search_movie_results, 
                rx.box(
                    rx.vstack(
                        rx.heading(State.hero_movie["title"], size="9", color="white", font_weight="black"),
                        rx.text(State.hero_movie["overview"], color="#dddddd", max_width="600px", no_of_lines=3),
                        rx.link(rx.button("Más Información", bg="white", color="black", padding_x="24px", border_radius="20px", margin_top="20px", transition="all 0.2s ease", _hover={"transform": "scale(1.05)", "opacity": 0.9}), href=f"/movie/{State.hero_movie['id']}", text_decoration="none"),
                        padding="60px", align_items="start", justify_content="end", height="500px", width="100%",
                        background=f"linear-gradient(to top, #111111 0%, transparent 100%), url('{hero_backdrop}')", background_size="cover", background_position="center top", border_radius="0 0 20px 20px"
                    ), width="100%"
                )
            ),
            rx.cond(
                State.search_movie_query != "",
                rx.vstack(
                    rx.hstack(
                        rx.heading("Resultados de Búsqueda", size="6", color="white", margin_bottom="10px"),
                        rx.cond(State.is_searching, rx.spinner(color="white", size="2"), rx.box())
                    ),
                    rx.scroll_area(rx.hstack(rx.foreach(State.search_movie_results, movie_card), spacing="4", padding_bottom="20px"), type="hover", scrollbars="horizontal", style={"width": "100%", "white-space": "nowrap"}), width="100%", padding_x="40px", margin_top="30px"
                ),
                rx.vstack(
                    rx.cond(State.social_recommendations, rx.vstack(rx.heading("Recomendado por tus Amigos", size="6", color="white", margin_bottom="-5px"), rx.text("Películas que tus amigos amaron y tú aún no ves.", color="#888", margin_bottom="15px"), rx.scroll_area(rx.hstack(rx.foreach(State.social_recommendations, movie_card), spacing="4", padding_bottom="20px"), type="hover", scrollbars="horizontal", style={"width": "100%", "white-space": "nowrap"}), width="100%", padding_x="40px", margin_top="40px")),
                    # --- NUEVA SECCIÓN ML ---
                    rx.cond(
                        State.ml_recommendations,
                        rx.vstack(
                            rx.hstack(
                                rx.heading("Para ti - ", size="6", color="white"),
                                rx.badge("ML Powered", color_scheme="purple", variant="solid"),
                                align_items="center", spacing="2", margin_bottom="-5px"
                            ),
                            rx.text("Basado en tus gustos y análisis de contenido.", color="#888", margin_bottom="15px"),
                            rx.scroll_area(
                                rx.hstack(rx.foreach(State.ml_recommendations, movie_card), spacing="4", padding_bottom="20px"), 
                                type="hover", scrollbars="horizontal", style={"width": "100%", "white-space": "nowrap"}
                            ),
                            width="100%", padding_x="40px", margin_top="40px"
                        )
                    ),
                    rx.vstack(rx.heading("Tendencias Ahora", size="6", color="white", margin_bottom="-5px"), rx.text("De lo que todos hablan", color="#888", margin_bottom="15px"), rx.scroll_area(rx.hstack(rx.foreach(State.trending_movies, movie_card), spacing="4", padding_bottom="20px"), type="hover", scrollbars="horizontal", style={"width": "100%", "white-space": "nowrap"}), width="100%", padding_x="40px", margin_top="30px")
                )
            ),
            desktop_promo_section(),
            min_height="100vh", background_color="#111111", on_mount=State.load_dashboard_data, max_width="100vw", overflow_x="hidden"
        )
    )

def library_page():
    return rx.box(
        navbar(show_search=False),
        rx.cond(
            State.is_page_loading,
            rx.center(rx.spinner(color="white", size="3"), height="80vh", width="100%"),
            rx.vstack(
                rx.box(
                    rx.hstack(
                        rx.heading("Mi Colección", size="7", color="white", font_weight="black"),
                        rx.spacer(),
                        rx.hstack(
                            rx.button("Todos", on_click=lambda: State.set_library_filter_mode("Todos"), bg=rx.cond(State.library_filter_mode == "Todos", "white", "rgba(255,255,255,0.1)"), color=rx.cond(State.library_filter_mode == "Todos", "black", "white"), radius="full", size="2"),
                            rx.button("Vistos", on_click=lambda: State.set_library_filter_mode("Vistos"), bg=rx.cond(State.library_filter_mode == "Vistos", "#48bb78", "rgba(255,255,255,0.1)"), color="white", radius="full", size="2"),
                            rx.button("Por Ver", on_click=lambda: State.set_library_filter_mode("Por Ver"), bg=rx.cond(State.library_filter_mode == "Por Ver", "#4299e1", "rgba(255,255,255,0.1)"), color="white", radius="full", size="2"),
                            spacing="3"
                        ),
                        # CORRECCIÓN radius="medium"
                        rx.input(placeholder="Filtrar...", on_change=State.set_library_search_query, width="200px", bg="rgba(0,0,0,0.5)", border="1px solid #444", color="white", radius="medium", margin_left="20px")
                    ),
                    padding="30px", width="100%", background="rgba(20,20,20,0.9)", border_bottom="1px solid #333", sticky="top", z_index="50"
                ),
                rx.box(
                    rx.cond(
                        State.filtered_library,
                        rx.grid(rx.foreach(State.filtered_library, library_card), columns="5", spacing="5", width="100%"),
                        rx.center(rx.vstack(rx.icon("film", size=48, color="#444"), rx.text("No hay películas en esta categoría", color="#666"), spacing="2", align_items="center", margin_top="50px"), width="100%")
                    ),
                    padding="40px", width="100%"
                ),
                width="100%", min_height="100vh", background="linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.8)), url('/background.jpg')", background_size="cover", background_attachment="fixed"
            )
        ),
        min_height="100vh", background_color="#1e1e1e", on_mount=State.get_user_library
    )

def movie_detail_page():
    backdrop = f"https://image.tmdb.org/t/p/original{State.movie['backdrop_path']}"
    rating_display = State.movie['vote_average'].to(float) / 2
    release_year = State.movie['release_date'].to(str)[:4]
    return rx.box(
        navbar(show_search=False),
        rx.cond(
            State.is_loading_details,
            rx.center(rx.spinner(color="white", size="3"), height="80vh", width="100%"),
            rx.cond(
                State.movie,
                rx.vstack(
                    rx.box(
                        rx.vstack(
                            rx.heading(State.movie["title"], size="9", color="white"),
                            rx.hstack(rx.text(f"{release_year} • Dirigida por", color="#cccccc", font_size="18px"), rx.text(State.director, color="white", font_weight="bold", font_size="18px"), rx.text(f"• ⭐ {rating_display:.1f} / 5", color="#cccccc", font_size="18px"), spacing="2", align_items="center"),
                            rx.text(State.movie["overview"], color="white", max_width="800px", margin_top="20px", line_height="1.6"),
                            rx.heading("Reparto Principal", size="6", color="white", margin_top="30px", margin_bottom="15px"),
                            rx.hstack(rx.foreach(State.cast, actor_card), spacing="5", wrap="wrap"),
                            rx.hstack(
                                # --- BOTONES DINÁMICOS MEJORADOS ---
                                rx.cond(
                                    State.current_movie_status == "Plan to Watch",
                                    # CORREGIDO: Icono como hijo
                                    rx.button(rx.icon("check", size=18), "En tu lista", variant="solid", bg="#2c5282", color="#90cdf4", padding="1.5em", cursor="default"),
                                    rx.cond(
                                        State.current_movie_status == "Completed",
                                        # CORREGIDO: Icono como hijo
                                        rx.button(rx.icon("check-double", size=18), "Visto", variant="solid", bg="#276749", color="#9ae6b4", padding="1.5em", cursor="default"),
                                        # Estado Normal: Botón Añadir
                                        rx.button("Añadir a mi Librería", bg="#4a90e2", color="white", padding="1.5em", on_click=State.handle_add_to_library, transition="all 0.2s ease", _hover={"transform": "scale(1.05)", "bg": "#357abd"})
                                    )
                                ),
                                # Botón "Ya la vi" (Solo si no está completada)
                                rx.cond(
                                    State.current_movie_status != "Completed",
                                    # CORREGIDO: Icono como hijo
                                    rx.button(rx.icon("check", size=20), "Ya la vi", on_click=State.handle_mark_as_watched, variant="outline", color="white", padding="1.5em", border_color="#28a745", _hover={"bg": "#28a745"})
                                ),
                                rx.button("Calificar", variant="outline", color="white", padding="1.5em", border_color="#444", on_click=State.open_rating_modal, transition="all 0.2s ease", _hover={"transform": "scale(1.05)", "bg": "#222"}), 
                                rating_dialog(), spacing="4", margin_top="40px"
                            ),
                            padding="60px", padding_top="150px", align_items="start", width="100%", min_height="60vh", background=f"linear-gradient(to top, #111111 10%, rgba(0,0,0,0.6) 100%), url('{backdrop}')", background_size="cover", background_position="center top"
                        ), width="100%"
                    ), width="100%", background_color="#111111", min_height="100vh"
                ), rx.center(rx.spinner(color="white"), height="100vh", bg="#111111")
            )
        ), on_mount=State.get_details
    )
    
def profile_page():
    return rx.box(
        navbar(show_search=False),
        rx.flex(
            rx.vstack(
                rx.heading("Configuración de Perfil", size="8", color="white", font_weight="bold", margin_bottom="10px"),
                rx.text("Actualiza tu información pública y privada", color="gray", margin_bottom="30px"),
                rx.card(
                    rx.vstack(
                        rx.center(
                            rx.avatar(src=State.user_avatar_url, fallback=rx.cond(State.profile_username != "", State.profile_username[0], "?"), size="8", size_px=120, radius="full", border="4px solid #2b2b2b"),
                            rx.vstack(
                                rx.upload(rx.button("Seleccionar nueva foto", size="1", variant="outline"), id="avatar_upload", accept={"image/png": [], "image/jpeg": [], "image/jpg": []}, max_files=1, border="1px dotted #4a90e2", padding="10px", border_radius="8px"),
                                rx.foreach(rx.selected_files("avatar_upload"), lambda file: rx.text(f"Archivo seleccionado: {file}", color="#4a90e2", font_size="12px")),
                                rx.cond(State.is_uploading, rx.spinner(size="1"), rx.button("Subir y Actualizar", size="1", on_click=State.handle_avatar_upload(rx.upload_files("avatar_upload")), bg="#4a90e2", color="white")),
                                spacing="2", margin_top="15px", align_items="center"
                            ), width="100%", margin_bottom="30px", flex_direction="column"
                        ),
                        rx.vstack(rx.text("Nombre de Usuario", color="#cccccc", size="2", weight="bold"), rx.input(value=State.profile_username, on_change=State.set_profile_username, bg="#1a1a1a", color="white", border="1px solid #333", width="100%", padding="10px", border_radius="8px"), spacing="2", width="100%"),
                        rx.vstack(rx.text("Biografía", color="#cccccc", size="2", weight="bold", margin_top="15px"), rx.text_area(value=State.profile_bio, on_change=State.set_profile_bio, placeholder="Cuéntanos sobre ti...", bg="#1a1a1a", color="white", border="1px solid #333", width="100%", min_height="150px", padding="10px", border_radius="8px"), spacing="2", width="100%"),
                        rx.button("Guardar Cambios", bg="linear-gradient(45deg, #4a90e2, #63b3ed)", color="white", width="100%", size="3", margin_top="40px", padding="20px", border_radius="8px", font_weight="bold", _hover={"opacity": 0.9, "transform": "scale(1.02)"}, on_click=State.update_profile),
                        spacing="0", width="100%"
                    ), background_color="#2b2b2b", border="1px solid #444", width="100%", max_width="600px", padding="40px", box_shadow="0 10px 25px rgba(0,0,0,0.5)"
                ), align_items="center", width="100%"
            ), width="100%", min_height="calc(100vh - 80px)", justify="center", align="center", padding_y="60px", padding_x="20px"
        ), background="radial-gradient(circle at top right, #2c3e50 0%, #000000 100%)", min_height="100vh", on_mount=State.get_user_profile
    )

app = rx.App(theme=rx.theme(appearance="dark"))
app.add_page(dashboard_page, route="/")
app.add_page(login_page, route="/login")
app.add_page(library_page, route="/library")
app.add_page(movie_detail_page, route="/movie/[movie_id]")
app.add_page(profile_page, route="/profile")
app.add_page(social_page, route="/social")