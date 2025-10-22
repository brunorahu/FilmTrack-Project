# desktop_client/load/main_window_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QListWidgetItem # <-- ¡NUEVA IMPORTACIÓN!
import requests # <-- ¡NUEVA IMPORTACIÓN!

class MainWindow:
    def __init__(self):
        # Cargamos el archivo .ui
        loader = QUiLoader()
        self.ui = loader.load("view/main_window.ui")
        
        # Conectamos el botón de búsqueda
        self.ui.search_button.clicked.connect(self.handle_search)
        
        # ¡NUEVO! Llamamos a la función para cargar las películas al iniciar
        self.load_trending_movies()

    def set_welcome_message(self, username):
        """
        Personaliza el mensaje de bienvenida.
        """
        self.ui.welcome_label.setText(f"¡Bienvenido, {username}!")

    def load_trending_movies(self):
        """
        Llama al endpoint de la API para obtener las películas en tendencia
        y las muestra en el movie_list_widget.
        """
        print("Cargando películas en tendencia...")
        api_url = "http://localhost:5000/api/movies/trending"
        
        try:
            response = requests.get(api_url)
            
            # Si la petición fue exitosa
            if response.status_code == 200:
                movies = response.json()
                
                # Limpiamos la lista por si tenía algo antes
                self.ui.movie_list_widget.clear()
                
                # Recorremos cada película recibida
                for movie in movies:
                    title = movie.get('title', 'Título no disponible')
                    
                    # Creamos un nuevo item para la lista
                    list_item = QListWidgetItem(title)
                    
                    # Añadimos el item al widget de la lista
                    self.ui.movie_list_widget.addItem(list_item)
                
                print(f"Se cargaron {len(movies)} películas en la lista.")
            else:
                print(f"Error al obtener las películas de la API: {response.text}")

        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión al cargar películas: {e}")
            # Podríamos mostrar un mensaje de error en la UI
            self.ui.movie_list_widget.addItem("Error: No se pudo conectar a la API.")

    def handle_search(self):
        """
        Función para el botón de búsqueda (a implementar).
        """
        search_text = self.ui.search_bar.text()
        print(f"Buscando: {search_text}")