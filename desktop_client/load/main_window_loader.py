# desktop_client/load/main_window_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt, QPoint, QSize
import requests
from load.details_window_loader import DetailsWindow
from load.movie_card_loader import MovieCard

class MainWindow:
    def __init__(self):
        loader = QUiLoader()
        self.ui = loader.load("view/main_window.ui")
        
        # --- LÓGICA DE VENTANA SIN MARCO ---
        self.ui.setWindowFlag(Qt.FramelessWindowHint)
        
        # Conectamos los nuevos botones de la barra de título
        self.ui.btn_close.clicked.connect(self.ui.close)
        self.ui.btn_minimize.clicked.connect(self.ui.showMinimized)
        self.ui.btn_maximize.clicked.connect(self.toggle_maximize)

        # Preparamos las variables para poder arrastrar la ventana
        self.drag_pos = QPoint(0, 0)
        
        # Conectamos los eventos del mouse de nuestra barra de título
        self.ui.title_bar_frame.mouseMoveEvent = self.move_window
        self.ui.title_bar_frame.mousePressEvent = self.mouse_press

        # --- FIN DE LA LÓGICA ---
        
        self.details_window = None
        self.user_id = None
        
        self.ui.search_button.setVisible(False)
        self.ui.btn_trending.clicked.connect(self.load_trending_movies)
        self.ui.btn_my_library.clicked.connect(self.handle_my_library)
        self.ui.search_bar.returnPressed.connect(self.handle_search)
        self.ui.movie_list_widget.itemDoubleClicked.connect(self.handle_item_double_click)
        
        self.load_trending_movies()

    # --- NUEVAS FUNCIONES PARA EL MANEJO DE LA VENTANA ---
    def toggle_maximize(self):
        if self.ui.isMaximized():
            self.ui.showNormal()
        else:
            self.ui.showMaximized()

    def mouse_press(self, event):
        self.drag_pos = event.globalPosition().toPoint()

    def move_window(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.drag_pos)
            self.ui.move(self.ui.x() + delta.x(), self.ui.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

    # --- EL RESTO DE LAS FUNCIONES SE QUEDAN IGUAL ---
    def set_user_info(self, user_data):
        self.user_id = user_data.get('user_id')
        username = user_data.get('username', 'Usuario')
        self.ui.welcome_label.setText(f"¡Bienvenido, {username}!")

    def _populate_movie_list(self, movies):
        self.ui.movie_list_widget.clear()
        if not movies:
            item = QListWidgetItem("No se encontraron resultados.")
            self.ui.movie_list_widget.addItem(item)
            return
        for movie in movies:
            movie_id = movie.get('id')
            
            # Esta línea ahora funcionará porque MovieCard está importada
            card_widget = MovieCard(movie)
            
            list_item = QListWidgetItem()
            # Esta línea ahora funcionará porque QSize está importada
            list_item.setSizeHint(QSize(180, 280))
                        
            if movie_id:
                list_item.setData(Qt.UserRole, movie_id)
                
            self.ui.movie_list_widget.addItem(list_item)
            self.ui.movie_list_widget.setItemWidget(list_item, card_widget)

    def load_trending_movies(self):
        print("Cargando películas en tendencia...")
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
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión al obtener detalles: {e}")