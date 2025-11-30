import reflex as rx
import requests

# --- STATE GLOBAL ---
class State(rx.State):
    # Variables de Sesión
    user_data: dict = {}
    error_message: str = ""
    
    # Variables del Dashboard
    trending_movies: list[dict] = []
    library_movies: list[dict] = []

    # Variables de Detalles de Película
    movie: dict = {}
    is_rating_open: bool = False
    rating_val: int = 0
    review_text: str = ""
    
    # Variables del Casting
    cast: list[dict] = []
    director: str = ""
    
    # Variables de LogIn/Registro
    auth_mode: str = "login" # "login" o "register"
    new_username: str = ""
    new_email: str = ""
    new_password: str = ""
    confirm_password: str = ""

    # --- VARIABLE CALCULADA (NUEVA): PELÍCULA DESTACADA ---
    # Esto soluciona el error VarTypeError. Calculamos la película "Hero" en el backend.
    @rx.var
    def hero_movie(self) -> dict:
        if self.trending_movies:
            return self.trending_movies[0]
        return {}
    
    def set_auth_mode(self, mode: str):
        self.auth_mode = mode
        self.error_message = "" # Limpiar errores al cambiar

    # --- LOGIN ---
    def handle_login(self, form_data: dict):
        api_url = "http://localhost:5000/api/users/login"
        # Nota: Reflex a veces envía todos los campos del formulario, filtramos los necesarios
        payload = {
            "username_or_email": form_data.get("username"),
            "password": form_data.get("password")
        }
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                self.user_data = response.json()['user']
                return rx.redirect("/")
            else:
                self.error_message = "Usuario o contraseña incorrectos."
        except Exception as e:
            self.error_message = f"Error: {e}"
            
    # --- REGISTRO (NUEVA FUNCIÓN) ---
    def handle_register(self, form_data: dict):
        if form_data.get("reg_password") != form_data.get("confirm_password"):
            self.error_message = "Las contraseñas no coinciden."
            return

        api_url = "http://localhost:5000/api/users/register"
        payload = {
            "username": form_data.get("reg_username"),
            "email": form_data.get("reg_email"),
            "password": form_data.get("reg_password")
        }
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 201:
                self.error_message = ""
                return rx.window_alert("¡Cuenta creada! Ahora inicia sesión.")
            else:
                self.error_message = "Error: El usuario o correo ya existen."
        except Exception as e:
            self.error_message = f"Error de conexión: {e}"

    # --- DASHBOARD ---
    def get_trending_movies(self):
        try:
            res = requests.get("http://localhost:5000/api/movies/trending")
            if res.status_code == 200: self.trending_movies = res.json()
        except: pass

    def get_user_library(self):
        if not self.user_data: return
        try:
            res = requests.get(f"http://localhost:5000/api/library/{self.user_data['user_id']}")
            if res.status_code == 200:
                self.library_movies = []
                for item in res.json():
                    det = requests.get(f"http://localhost:5000/api/movies/{item['content_id']}")
                    if det.status_code == 200: self.library_movies.append(det.json())
        except: pass

    # --- DETALLES Y ACCIONES ---
    def get_details(self):
        current_id = self.router.page.params.get("movie_id", "")
        if not current_id: return
        
        # 1. Obtener Detalles de la Película
        try:
            res = requests.get(f"http://localhost:5000/api/movies/{current_id}")
            if res.status_code == 200: self.movie = res.json()
        except: pass
        
        # 2. Obtener el Reparto (Cast) y Director - ¡ACTUALIZADO!
        try:
            res_credits = requests.get(f"http://localhost:5000/api/movies/{current_id}/credits")
            if res_credits.status_code == 200:
                data = res_credits.json()
                
                # Buscar Director
                crew = data.get('crew', [])
                director_item = next((member for member in crew if member['job'] == 'Director'), None)
                self.director = director_item['name'] if director_item else "N/A"
                
                # Guardar Cast
                self.cast = data.get('cast', [])[:6] 
            else:
                self.cast = []
                self.director = "N/A"
        except: 
            self.cast = []
            self.director = "N/A"
        
        # 3. Obtener el Reparto (Cast) - ¡NUEVO!
        try:
            res_credits = requests.get(f"http://localhost:5000/api/movies/{current_id}/credits")
            if res_credits.status_code == 200:
                # Guardamos solo los primeros 6 actores para no saturar la vista
                full_cast = res_credits.json().get('cast', [])
                self.cast = full_cast[:6] 
            else:
                self.cast = [] # Limpiamos si falla
        except: 
            self.cast = []

    def set_rating(self, val: int):
        self.rating_val = val

    def set_review_text_val(self, val: str):
        self.review_text = val

    def handle_add_to_library(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return rx.redirect("/login")

        payload = {
            "user_id": user_id, 
            "content_id": self.movie.get('id'), 
            "content_type": "movie", 
            "status": "Plan to Watch"
        }
        try:
            requests.post("http://localhost:5000/api/library/add", json=payload)
            return rx.window_alert("¡Añadido a tu librería!")
        except Exception as e:
            print(e)

    def handle_save_review(self):
        user_id = self.user_data.get('user_id')
        if not user_id: return rx.redirect("/login")
        
        payload = {
            "user_id": user_id,
            "content_id": self.movie.get('id'),
            "rating": self.rating_val,
            "review_text": self.review_text
        }
        try:
            requests.post("http://localhost:5000/api/library/review", json=payload)
            self.is_rating_open = False
            return rx.window_alert("¡Calificación guardada!")
        except: pass
        
    def handle_logout(self):
        """Cierra la sesión del usuario y redirige al inicio."""
        self.user_data = {}  # Borramos los datos del usuario
        return rx.redirect("/") # Redirigimos a la página principal

    def open_rating_modal(self):
        """Verifica sesión antes de abrir el modal"""
        user_id = self.user_data.get('user_id')
        
        if not user_id:
            # Si no hay usuario, nos vamos al login
            return rx.redirect("/login")
        
        # Si hay usuario, abrimos el modal
        self.is_rating_open = True


# --- COMPONENTES UI ---
def navbar():
    # Estilo base para botones de autenticación
    auth_btn_style = {
        "width": "130px", 
        "height": "40px",
        "display": "flex",
        "align_items": "center",
        "justify_content": "center",
        "font_weight": "600",
        "border_radius": "8px",
        "transition": "all 0.2s ease",
        "_hover": {"opacity": 0.9, "transform": "translateY(-1px)"}
    }

    return rx.hstack(
        # --- TÍTULO CLICKEABLE (HOME) ---
        rx.link(
                    rx.image(
                        src="/logo_clean.png", 
                        height="60px", # Ajusta este valor según necesites
                        width="auto",
                        alt="Logo FilmTrack"
                    ),
                    href="/", 
                    _hover={"opacity": 0.8}
                ),
        
        rx.spacer(),
        
        rx.cond(
            State.user_data,
            # --- USUARIO LOGUEADO ---
            rx.hstack(
                rx.text(f"Hola, {State.user_data['username']}", color="#888888", font_size="14px"),
                rx.link("Mi Librería", href="/library", color="white", font_weight="500", _hover={"text_decoration": "underline"}),
                rx.button("Salir", variant="ghost", color_scheme="red", size="2", on_click=State.handle_logout),
                spacing="5",
                align_items="center"
            ),
            
            # --- USUARIO PÚBLICO ---
            rx.hstack(
                rx.link(
                    "Iniciar Sesión", 
                    href="/login", 
                    color="white", 
                    bg="transparent", 
                    border="1px solid #333", 
                    **auth_btn_style,
                    text_decoration="none"
                ),
                rx.link( 
                    "Registrarse",
                    href="/login", 
                    color="black", 
                    bg="white", 
                    border="1px solid white",
                    **auth_btn_style,
                    text_decoration="none"
                ), 
                spacing="3",
                align_items="center"
            )
        ),
        
        width="100%", 
        height="80px", 
        padding_x="2em", 
        background_color="rgba(17, 17, 17, 0.95)",
        border_bottom="1px solid #222",
        position="sticky", top="0", z_index="100",
        align_items="center"
    )

def movie_card(movie: dict):
    poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
    
    # CORRECCIÓN 1: Quitamos .round(1) porque causa error en Reflex
    rating_val = movie["vote_average"].to(float) / 2

    return rx.link(
        rx.box(
            rx.image(
                src=poster_url, 
                width="160px", 
                height="240px", 
                border_radius="12px", 
                object_fit="cover", 
                _hover={"transform": "scale(1.05)", "transition": "0.2s"}
            ),
            rx.vstack(
                rx.text(
                    movie["title"], 
                    color="white", 
                    font_weight="bold", 
                    font_size="14px", 
                    width="160px", # Ancho fijo obligatorio
                    
                    # Estilos CSS para cortar texto con "..."
                    style={
                        "white-space": "nowrap",
                        "overflow": "hidden",
                        "text-overflow": "ellipsis",
                        "display": "block" 
                    },
                    
                    title=movie["title"] # Tooltip nativo del navegador
                ),
                
                rx.tooltip(
                    rx.hstack(
                        *[
                            rx.icon(
                                tag="star",
                                color=rx.cond(rating_val >= i, "gold", "gray"),
                                size=14,
                                fill=rx.cond(rating_val >= i, "gold", "none")
                            )
                            for i in range(1, 6)
                        ],
                        spacing="1"
                    ),
                    # CORRECCIÓN 2: Aplicamos el formato de 1 decimal aquí
                    content=f"Calificación: {rating_val:.1f}" 
                ),
                
                spacing="1", padding_top="8px"
            ),
            padding="8px", cursor="pointer"
        ),
        href=f"/movie/{movie['id']}", text_decoration="none"
    )
    
def actor_card(actor: dict):
    # Manejo seguro de la imagen de perfil (por si el actor no tiene foto)
    profile_url = rx.cond(
        actor["profile_path"],
        f"https://image.tmdb.org/t/p/w200{actor['profile_path']}",
        "https://via.placeholder.com/100x100?text=No+Img" # Imagen por defecto
    )
    
    return rx.vstack(
        rx.avatar(src=profile_url, size="6", radius="full", border="2px solid #333"),
        rx.text(actor["name"], color="white", font_size="14px", font_weight="bold", no_of_lines=1),
        rx.text(actor["character"], color="gray", font_size="12px", no_of_lines=1),
        align_items="center",
        text_align="center",
        width="120px" # Ancho fijo para alinear bien
    )
    
def rating_dialog():
    # URL del poster para el modal
    poster_url = f"https://image.tmdb.org/t/p/w500{State.movie.get('poster_path', '')}"

    return rx.dialog.root(
        # YA NO HAY TRIGGER AQUÍ (El botón estará fuera)
        
        rx.dialog.content(
            rx.flex(
                # --- COLUMNA IZQUIERDA: IMAGEN ---
                rx.box(
                    rx.image(
                        src=poster_url, width="230px", height="225px", border_radius="8px",
                        box_shadow="0 4px 12px rgba(0,0,0,0.5)"
                    ),
                    padding="20px", background_color="#222", border_radius="8px 0 0 8px",
                    display="flex", align_items="center", justify_content="center"
                ),
                
                # --- COLUMNA DERECHA: FORMULARIO ---
                rx.vstack(
                    rx.hstack(
                        rx.heading("¡Añadir a mi Tracking!", size="4", color="white"),
                        # Usamos set_is_rating_open(False) para cerrar manualmente
                        rx.icon("x", color="gray", cursor="pointer", _hover={"color": "white"}, 
                               on_click=State.set_is_rating_open(False)),
                        justify="between", width="100%", align_items="center"
                    ),
                    
                    rx.text(f"Estás calificando: {State.movie.get('title', '')}", color="#888", font_size="14px", margin_bottom="10px"),
                    
                    rx.hstack(
                        *[
                            rx.icon(
                                tag="star",
                                color=rx.cond(State.rating_val >= i, "gold", "#444"),
                                size=28, cursor="pointer", transition="color 0.2s",
                                on_click=lambda: State.set_rating(i)
                            ) for i in [1, 2, 3, 4, 5]
                        ],
                        spacing="2", padding_y="10px"
                    ),
                    
                    rx.text_area(
                        placeholder="Escribe tu reseña aquí...",
                        on_change=State.set_review_text_val,
                        background_color="#2a2a2a", color="white", border="1px solid #333",
                        border_radius="6px", min_height="120px", padding="12px",
                        _focus={"border_color": "#4a90e2", "outline": "none"}
                    ),
                    
                    rx.hstack(
                        rx.button("Cancelar", variant="outline", color_scheme="gray", color="white", border_color="#555", 
                                 _hover={"bg": "#333"}, on_click=State.set_is_rating_open(False)),
                        rx.button("Guardar", bg="#28a745", color="white", on_click=State.handle_save_review, padding_x="20px", font_weight="bold"),
                        spacing="3", justify="end", width="100%", margin_top="15px", align_items="center"
                    ),
                    
                    padding="25px", spacing="3", width="100%", align_items="stretch"
                ),
                direction="row", spacing="0", width="100%"
            ),
            background_color="#1e1e1e", border="1px solid #333", border_radius="12px",
            max_width="650px", padding="0", overflow="hidden"
        ),
        open=State.is_rating_open,
        on_open_change=State.set_is_rating_open
    )

# --- PÁGINAS ---
def login_page():
    # Imagen de fondo estilo "Collage de Películas"
    background_url = "/fondo_cine.jpg"

    return rx.center(
        rx.vstack(
            # Título Principal (Marca)
            rx.image(
                src="/logo_clean.png",
                height="150px", # Un poco más grande para el login
                width="auto",
                margin_bottom="-10px"
            ),
            
            # --- CAJA DE AUTENTICACIÓN ---
            rx.box(
                rx.vstack(
                    # Pestañas para cambiar entre Login y Registro
                    rx.hstack(
                        rx.text(
                            "Iniciar Sesión", 
                            color=rx.cond(State.auth_mode == "login", "white", "gray"),
                            font_weight="bold",
                            cursor="pointer",
                            on_click=lambda: State.set_auth_mode("login"),
                            border_bottom=rx.cond(State.auth_mode == "login", "2px solid white", "2px solid transparent"),
                            padding_bottom="5px"
                        ),
                        rx.text(
                            "Registrarse", 
                            color=rx.cond(State.auth_mode == "register", "white", "gray"),
                            font_weight="bold",
                            cursor="pointer",
                            on_click=lambda: State.set_auth_mode("register"),
                            border_bottom=rx.cond(State.auth_mode == "register", "2px solid white", "2px solid transparent"),
                            padding_bottom="5px"
                        ),
                        spacing="5",
                        width="100%",
                        margin_bottom="20px"
                    ),

                    # --- FORMULARIO DE LOGIN ---
                    rx.cond(
                        State.auth_mode == "login",
                        rx.form(
                            rx.vstack(
                                rx.input(placeholder="Usuario o Email", name="username", width="100%", bg="#333", border="none", color="white", padding="5px"),
                                rx.input(type="password", placeholder="Contraseña", name="password", width="100%", bg="#333", border="none", color="white", padding="5px"),
                                rx.button("Iniciar Sesión", width="100%", bg="white", color="black", size="3", margin_top="20px", type="submit"),
                                spacing="4",
                                width="100%"
                            ),
                            on_submit=State.handle_login,
                            width="100%"
                        )
                    ),

                    # --- FORMULARIO DE REGISTRO ---
                    rx.cond(
                        State.auth_mode == "register",
                        rx.form(
                            rx.vstack(
                                rx.input(placeholder="Elige un Usuario", name="reg_username", width="100%", bg="#333", border="none", color="white", padding="5px"),
                                rx.input(placeholder="Tu Correo", name="reg_email", width="100%", bg="#333", border="none", color="white", padding="5px"),
                                rx.input(type="password", placeholder="Contraseña", name="reg_password", width="100%", bg="#333", border="none", color="white", padding="5px"),
                                rx.input(type="password", placeholder="Confirmar Contraseña", name="confirm_password", width="100%", bg="#333", border="none", color="white", padding="5px"),
                                rx.button("Crear Cuenta", width="100%", bg="white", color="black", size="3", margin_top="20px", type="submit"),
                                spacing="4",
                                width="100%"
                            ),
                            on_submit=State.handle_register,
                            width="100%"
                        )
                    ),

                    # Mensaje de Error General
                    rx.cond(
                        State.error_message != "",
                        rx.text(State.error_message, color="#e87c03", font_size="14px", margin_top="15px")
                    ),
                    
                    align_items="start",
                    width="100%"
                ),
                # Estilos de la Caja "Glassmorphism" Oscura
                padding="60px",
                width="450px",
                background_color="rgba(0, 0, 0, 0.75)", # Negro semitransparente
                border_radius="10px",
                box_shadow="0 0 20px rgba(0,0,0,0.5)"
            ),
            align="center",
            spacing="0"
        ),
        # Fondo de Pantalla Completa con Superposición Oscura
        width="100%",
        height="100vh",
        background=f"linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 60%, rgba(0,0,0,0.8) 100%), url('{background_url}')",
        background_size="cover",
        background_position="center"
    )

def dashboard_page():
    # Construimos la URL de la imagen Hero usando la Variable Calculada State.hero_movie
    hero_backdrop = f"https://image.tmdb.org/t/p/original{State.hero_movie['backdrop_path']}"

    return rx.box(
        navbar(),
        rx.vstack(
            # --- HERO SECTION ---
            rx.cond(
                State.trending_movies, # Solo mostramos si hay películas
                rx.box(
                    rx.vstack(
                        # Usamos State.hero_movie en lugar de lógica python directa
                        rx.heading(State.hero_movie["title"], size="9", color="white", font_weight="black"),
                        rx.text(State.hero_movie["overview"], color="#dddddd", max_width="600px", no_of_lines=3),
                        rx.link(
                            rx.button("Más Información", bg="white", color="black", padding_x="24px", border_radius="20px", margin_top="20px"),
                            href=f"/movie/{State.hero_movie['id']}",
                            text_decoration="none"
                        ),
                        padding="60px", align_items="start", justify_content="end", height="500px", width="100%",
                        background=f"linear-gradient(to top, #111111 0%, transparent 100%), url('{hero_backdrop}')",
                        background_size="cover", background_position="center top", border_radius="0 0 20px 20px"
                    ),
                    width="100%",
                )
            ),
            
            # --- SECCIÓN: TRENDING ---
            rx.vstack(
                rx.heading("Tendencias Ahora", size="6", color="white", margin_bottom="10px"),
                rx.scroll_area(
                    rx.hstack(rx.foreach(State.trending_movies, movie_card), spacing="4", padding_bottom="20px"),
                    type="hover", scrollbars="horizontal", style={"width": "100%"}
                ),
                width="100%", padding_x="40px", margin_top="30px"
            ),
            min_height="100vh", background_color="#111111",
            on_mount=State.get_trending_movies
        )
    )

def library_page():
    return rx.box(
        navbar(),
        rx.vstack(
            rx.heading("Mi Librería", size="7", color="white", margin_bottom="20px"),
            rx.grid(rx.foreach(State.library_movies, movie_card), columns="5", spacing="4", width="100%"),
            padding="2em", max_width="1200px", margin="0 auto"
        ),
        min_height="100vh", background_color="#1e1e1e",
        on_mount=State.get_user_library
    )

def movie_detail_page():
    backdrop = f"https://image.tmdb.org/t/p/original{State.movie['backdrop_path']}"
    # Usamos la corrección de decimales que ya funcionaba
    rating_display = State.movie['vote_average'].to(float) / 2
    # Usamos la corrección de año que ya funcionaba
    release_year = State.movie['release_date'].to(str)[:4]

    return rx.box(
        navbar(),
        rx.cond(
            State.movie,
            rx.vstack(
                rx.box(
                    rx.vstack(
                        rx.heading(State.movie["title"], size="9", color="white"),
                        
                        # --- CORRECCIÓN PARA DIRECTOR EN NEGRITA ---
                        # Usamos un hstack para alinear textos con diferentes estilos
                        rx.hstack(
                            rx.text(f"{release_year} • Dirigida por", color="#cccccc", font_size="18px"),
                            rx.text(State.director, color="white", font_weight="bold", font_size="18px"),
                            rx.text(f"• ⭐ {rating_display:.1f} / 5", color="#cccccc", font_size="18px"),
                            spacing="2",
                            align_items="center"
                        ),
                        # -------------------------------------------
                        
                        rx.text(State.movie["overview"], color="white", max_width="800px", margin_top="20px", line_height="1.6"),
                        
                        rx.heading("Reparto Principal", size="6", color="white", margin_top="30px", margin_bottom="15px"),
                        rx.hstack(
                            rx.foreach(State.cast, actor_card),
                            spacing="5",
                            wrap="wrap"
                        ),

                        rx.hstack(
                            rx.button("Añadir a mi Librería", bg="#4a90e2", color="white", padding="1.5em", on_click=State.handle_add_to_library),
                            # BOTÓN CALIFICAR (Ahora independiente del diálogo)
                            rx.button(
                                "Calificar", 
                                variant="outline", 
                                color="white", 
                                padding="1.5em", 
                                border_color="#444",
                                on_click=State.open_rating_modal  # <-- Llama a la verificación
                            ),
                            rating_dialog(),
                            spacing="4", margin_top="40px"
                        ),

                        padding="60px", padding_top="150px", align_items="start", width="100%", min_height="60vh",
                        background=f"linear-gradient(to top, #111111 10%, rgba(0,0,0,0.6) 100%), url('{backdrop}')",
                        background_size="cover", background_position="center top"
                    ),
                    width="100%"
                ),
                width="100%", background_color="#111111", min_height="100vh"
            ),
            rx.center(rx.spinner(color="white"), height="100vh", bg="#111111")
        ),
        on_mount=State.get_details
    )

app = rx.App(theme=rx.theme(appearance="dark"))
app.add_page(dashboard_page, route="/")
app.add_page(login_page, route="/login")
app.add_page(library_page, route="/library")
app.add_page(movie_detail_page, route="/movie/[movie_id]")