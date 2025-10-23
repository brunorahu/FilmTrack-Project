# desktop_client/load/main_window_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt
import requests
from load.details_window_loader import DetailsWindow

class MainWindow:
    def __init__(self):
        loader = QUiLoader()
        self.ui = loader.load("view/main_window.ui")
        
        self.details_window = None
        self.user_id = None
        
        # Conectamos los botones
        self.ui.search_button.clicked.connect(self.handle_search)
        self.ui.my_library_button.clicked.connect(self.handle_my_library) # <-- NUEVA CONEXIÓN
        self.ui.movie_list_widget.itemDoubleClicked.connect(self.handle_item_double_click)
        
        # Al iniciar, seguimos mostrando las tendencias
        self.load_trending_movies()

    def set_user_info(self, user_data):
        self.user_id = user_data.get('user_id')
        username = user_data.get('username', 'Usuario')
        self.ui.welcome_label.setText(f"¡Bienvenido, {username}!")

    def _populate_movie_list(self, movies):
        self.ui.movie_list_widget.clear()
        if not movies:
            self.ui.movie_list_widget.addItem("No se encontraron resultados.")
            return
        for movie in movies:
            title = movie.get('title', 'Título no disponible')
            release_date = movie.get('release_date', '')
            movie_id = movie.get('id')
            year = f"({release_date.split('-')[0]})" if release_date else ""
            display_text = f"{title} {year}"
            list_item = QListWidgetItem(display_text)
            if movie_id:
                list_item.setData(Qt.UserRole, movie_id)
            self.ui.movie_list_widget.addItem(list_item)

    def load_trending_movies(self):
        print("Cargando películas en tendencia...")
        api_url = "http://localhost:5000/api/movies/trending"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                self._populate_movie_list(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al cargar películas: {e}")

    # --- ¡NUEVA FUNCIÓN! ---
    def handle_my_library(self):
        if not self.user_id:
            print("No se ha iniciado sesión, no se puede cargar la librería.")
            return

        print(f"Cargando la librería del usuario ID: {self.user_id}")
        api_url = f"http://localhost:5000/api/library/{self.user_id}"
        
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                library_items = response.json()
                
                # Como la librería solo nos da IDs, necesitamos obtener los detalles de cada película
                movies_details = []
                for item in library_items:
                    details_url = f"http://localhost:5000/api/movies/{item['content_id']}"
                    details_response = requests.get(details_url)
                    if details_response.status_code == 200:
                        movies_details.append(details_response.json())
                
                self._populate_movie_list(movies_details)
            else:
                print(f"Error al obtener la librería: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al cargar la librería: {e}")

    def handle_search(self):
        # ... (se queda igual)
        search_text = self.ui.search_bar.text()
        if not search_text:
            self.load_trending_movies()
            return
        print(f"Buscando: {search_text}")
        api_url = f"http://localhost:5000/api/movies/search?query={search_text}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                movies = response.json()
                self._populate_movie_list(movies)
                print(f"Se encontraron {len(movies)} resultados.")
            else:
                print(f"Error en la búsqueda: {response.text}")
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión en la búsqueda: {e}")


    # --- ¡FUNCIÓN ACTUALIZADA! ---
    def handle_item_double_click(self, item):
        movie_id = item.data(Qt.UserRole)

        if not movie_id:
            print("Este elemento no tiene un ID de película asociado.")
            return

        print(f"Obteniendo detalles para la película con ID: {movie_id}")
        api_url = f"http://localhost:5000/api/movies/{movie_id}"

        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                movie_details = response.json()

                # Creamos y mostramos la ventana de detalles
                self.details_window = DetailsWindow()
                self.details_window.populate_details(movie_details, self.user_id)
                self.details_window.ui.show()
            else:
                print(f"Error al obtener los detalles de la película: {response.text}")
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión al obtener detalles: {e}")