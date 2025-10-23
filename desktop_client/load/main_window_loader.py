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
        
        # --- ¡CONEXIONES ACTUALIZADAS! ---
        # Conectamos los botones de la barra lateral a sus funciones correspondientes
        self.ui.btn_trending.clicked.connect(self.load_trending_movies)
        self.ui.btn_my_library.clicked.connect(self.handle_my_library)
        
        # El resto de las conexiones se quedan igual
        self.ui.search_button.clicked.connect(self.handle_search)
        self.ui.movie_list_widget.itemDoubleClicked.connect(self.handle_item_double_click)
        
        # Al iniciar, por defecto mostramos las tendencias
        self.load_trending_movies()

    # El resto de las funciones (set_user_info, _populate_movie_list, 
    # load_trending_movies, handle_my_library, etc.) se quedan
    # exactamente igual que en la versión anterior.
    
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
        # Lógica para cambiar a la página 0 del Stacked Widget
        self.ui.main_stacked_widget.setCurrentIndex(0)
        api_url = "http://localhost:5000/api/movies/trending"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                self._populate_movie_list(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al cargar películas: {e}")

    def handle_my_library(self):
        if not self.user_id:
            return
        print(f"Cargando la librería del usuario ID: {self.user_id}")
        # Lógica para cambiar a la página 0 del Stacked Widget
        self.ui.main_stacked_widget.setCurrentIndex(0)
        api_url = f"http://localhost:5000/api/library/{self.user_id}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                library_items = response.json()
                movies_details = []
                for item in library_items:
                    details_url = f"http://localhost:5000/api/movies/{item['content_id']}"
                    details_response = requests.get(details_url)
                    if details_response.status_code == 200:
                        movies_details.append(details_response.json())
                self._populate_movie_list(movies_details)
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al cargar la librería: {e}")

    def handle_search(self):
        search_text = self.ui.search_bar.text()
        if not search_text:
            self.load_trending_movies()
            return
        print(f"Buscando: {search_text}")
        api_url = f"http://localhost:5000/api/movies/search?query={search_text}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                self._populate_movie_list(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error en la búsqueda: {e}")

    def handle_item_double_click(self, item):
        movie_id = item.data(Qt.UserRole)
        if not movie_id:
            return
        api_url = f"http://localhost:5000/api/movies/{movie_id}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                movie_details = response.json()
                self.details_window = DetailsWindow()
                self.details_window.populate_details(movie_details, self.user_id)
                self.details_window.ui.show()
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al obtener detalles: {e}")