# desktop_client/load/main_window_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt
import requests
from load.details_window_loader import DetailsWindow # <-- ¡NUEVA IMPORTACIÓN!

class MainWindow:
    def __init__(self):
        loader = QUiLoader()
        self.ui = loader.load("view/main_window.ui")

        self.details_window = None # Para mantener una referencia a la ventana de detalles

        self.ui.search_button.clicked.connect(self.handle_search)
        self.ui.movie_list_widget.itemDoubleClicked.connect(self.handle_item_double_click)

        self.load_trending_movies()
        
        self.user_id = None

    # ... (los otros métodos como set_welcome_message, _populate_movie_list, etc., se quedan igual)
    def set_user_info(self, user_data):
        """
        Guarda la información del usuario y personaliza el mensaje de bienvenida.
        """
        self.user_id = user_data.get('user_id') # <-- AÑADE ESTA LÍNEA
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
        # ... (se queda igual)
        print("Cargando películas en tendencia...")
        api_url = "http://localhost:5000/api/movies/trending"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                movies = response.json()
                self._populate_movie_list(movies)
                print(f"Se cargaron {len(movies)} películas en la lista.")
            else:
                print(f"Error al obtener las películas de la API: {response.text}")
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión al cargar películas: {e}")

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