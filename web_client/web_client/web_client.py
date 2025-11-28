import reflex as rx
import requests

# --- STATE UNIFICADO (Lógica Global) ---
class State(rx.State):
    # --- Variables de Sesión ---
    user_data: dict = {}  # Aquí guardaremos toda la info del usuario (id, nombre, email)
    error_message: str = ""
    
    # --- Variables de Datos ---
    trending_movies: list[dict] = []
    library_movies: list[dict] = []

    # --- Acciones de Login ---
    def handle_login(self, form_data: dict):
        api_url = "http://localhost:5000/api/users/login"
        # Reflex pasa los datos del formulario como un diccionario
        payload = {
            "username_or_email": form_data["username"],
            "password": form_data["password"]
        }

        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                self.user_data = response.json()['user']
                self.error_message = ""
                print(f"Login exitoso. User ID: {self.user_data['user_id']}")
                return rx.redirect("/dashboard")
            else:
                self.error_message = "Usuario o contraseña incorrectos."
        except Exception as e:
            self.error_message = f"Error de conexión: {e}"

    # --- Acciones de Películas ---
    def get_trending_movies(self):
        try:
            response = requests.get("http://localhost:5000/api/movies/trending")
            if response.status_code == 200:
                self.trending_movies = response.json()
        except Exception as e:
            print(f"Error cargando tendencias: {e}")

    def get_user_library(self):
        # Verificamos si tenemos un usuario logueado
        if not self.user_data:
            return
            
        user_id = self.user_data['user_id']
        api_url = f"http://localhost:5000/api/library/{user_id}"
        
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                library_items = response.json()
                # La API de librería devuelve IDs, necesitamos los detalles completos
                # Hacemos un pequeño truco: iteramos y pedimos detalles uno por uno (como en escritorio)
                # Nota: En una app real, optimizaríamos esto en el backend.
                details_list = []
                for item in library_items:
                    det_res = requests.get(f"http://localhost:5000/api/movies/{item['content_id']}")
                    if det_res.status_code == 200:
                        details_list.append(det_res.json())
                
                self.library_movies = details_list
        except Exception as e:
            print(f"Error cargando librería: {e}")

# --- COMPONENTES REUTILIZABLES ---

def navbar():
    """Barra de navegación superior"""
    return rx.hstack(
        rx.heading("FilmTrack", size="5", color="white"),
        rx.spacer(),
        rx.link("Tendencias", href="/dashboard", color="white", margin_right="20px"),
        rx.link("Mi Librería", href="/library", color="white"),
        width="100%",
        padding="1.5em",
        background_color="#111111", # Negro encabezado
        border_bottom="1px solid #333"
    )

def movie_card(movie: dict):
    """Tarjeta de película estilo 'CineConnect'"""
    poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
    return rx.box(
        rx.image(
            src=poster_url, 
            width="160px", 
            height="240px", 
            border_radius="12px",
            object_fit="cover",
            _hover={"transform": "scale(1.05)", "transition": "transform 0.2s ease-in-out"}
        ),
        rx.vstack(
            rx.text(movie["title"], color="white", font_weight="bold", font_size="14px", no_of_lines=1, width="160px"),
            rx.hstack(
                rx.icon(tag="star", color="gold", size=14),
                rx.text(f"{movie['vote_average']:.1f}", color="#cccccc", font_size="12px"),
                spacing="1"
            ),
            spacing="1",
            padding_top="8px"
        ),
        padding="8px",
        cursor="pointer"
    )

# --- PÁGINAS ---

def login_page():
    return rx.center(
        rx.vstack(
            rx.heading("FilmTrack", size="9", margin_bottom="20px"),
            rx.card(
                rx.form(
                    rx.vstack(
                        rx.heading("Iniciar Sesión", size="5"),
                        rx.text("Usuario o Email", size="2", mb="1"),
                        rx.input(placeholder="Ej. brunorahu", name="username", width="100%"),
                        rx.text("Contraseña", size="2", mb="1", mt="3"),
                        rx.input(type="password", placeholder="••••••••", name="password", width="100%"),
                        
                        rx.cond(
                            State.error_message != "",
                            rx.callout(State.error_message, icon="alert_triangle", color_scheme="red", width="100%"),
                        ),
                        rx.button("Entrar", width="100%", size="3", margin_top="20px", type="submit"),
                        align_items="start",
                        width="100%"
                    ),
                    on_submit=State.handle_login,
                ),
                size="4", width="400px"
            ),
            align="center", spacing="5", margin_top="10vh"
        ),
        height="100vh",
        background="radial-gradient(circle at center, #1e1e1e 0%, #000000 100%)"
    )

def dashboard_page():
    return rx.box(
        navbar(),
        rx.vstack(
            # --- HERO SECTION (BANNER PRINCIPAL) ---
            rx.box(
                rx.vstack(
                    rx.heading("Wicked", size="9", color="white", font_weight="black"), # Título de ejemplo
                    rx.text("Descubre la historia no contada de las brujas de Oz.", color="#dddddd", max_width="600px"),
                    rx.hstack(
                        rx.button("Reproducir", bg="white", color="black", padding_x="24px", border_radius="20px"),
                        rx.button("Más Información", bg="rgba(255,255,255,0.2)", color="white", padding_x="24px", border_radius="20px"),
                        spacing="4",
                        margin_top="20px"
                    ),
                    padding="60px",
                    align_items="start",
                    justify_content="end",
                    height="500px",
                    width="100%",
                    # Fondo degradado sobre una imagen (puedes cambiar la URL por una de tus películas)
                    background="linear-gradient(to top, #111111 0%, transparent 100%), url('https://image.tmdb.org/t/p/original/2ha0wAOqrUcLScStWQcgeOOXapQ.jpg')",
                    background_size="cover",
                    background_position="center top",
                    border_radius="0 0 20px 20px"
                ),
                width="100%",
            ),
            
            # --- SECCIÓN: TRENDING NOW (SCROLL HORIZONTAL) ---
            rx.vstack(
                rx.heading("Tendencias Ahora", size="6", color="white", margin_bottom="10px"),
                rx.scroll_area(
                    rx.hstack(
                        rx.foreach(State.trending_movies, movie_card),
                        spacing="4",
                        padding_bottom="20px" # Espacio para la barra de scroll
                    ),
                    type="hover", # La barra de scroll aparece al pasar el mouse
                    scrollbars="horizontal",
                    style={"width": "100%"}
                ),
                width="100%",
                padding_x="40px",
                margin_top="30px"
            ),

            # --- SECCIÓN: MI LIBRERÍA (VISTA RÁPIDA) ---
            # (Podemos añadir una sección similar para la librería aquí abajo)
            
            width="100%",
            spacing="0",
            background_color="#111111",
            min_height="100vh"
        ),
        on_mount=State.get_trending_movies
    )

def library_page(): # <-- ¡NUEVA PÁGINA!
    return rx.box(
        navbar(),
        rx.vstack(
            rx.heading("Mi Librería Personal", size="7", color="white", margin_bottom="20px"),
            
            # Mostramos un mensaje si la librería está vacía
            rx.cond(
                State.library_movies,
                rx.grid(
                    rx.foreach(State.library_movies, movie_card),
                    columns="5", spacing="4", width="100%"
                ),
                rx.text("Aún no has añadido películas.", color="gray")
            ),
            padding="2em", max_width="1200px", margin="0 auto"
        ),
        min_height="100vh", background_color="#1e1e1e",
        on_mount=State.get_user_library # Carga la librería al abrir la página
    )

# --- APP CONFIG ---
app = rx.App(theme=rx.theme(appearance="dark"))
app.add_page(login_page, route="/")
app.add_page(dashboard_page, route="/dashboard")
app.add_page(library_page, route="/library")