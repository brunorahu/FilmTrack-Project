# desktop_client/load/details_window_loader.py

from PySide6.QtUiTools import QUiLoader
import requests

class DetailsWindow:
    def __init__(self):
        loader = QUiLoader()
        self.ui = loader.load("view/details_window.ui")

        # Variables para guardar la información
        self.movie_data = None
        self.user_id = None

        # Conectamos el nuevo botón
        self.ui.add_to_library_button.clicked.connect(self.handle_add_to_library)

    def populate_details(self, movie_data, user_id):
        # Guardamos los datos para usarlos después
        self.movie_data = movie_data
        self.user_id = user_id

        title = movie_data.get('title', 'N/A')
        release_date = movie_data.get('release_date', 'N/A')
        vote_average = movie_data.get('vote_average', 0)
        overview = movie_data.get('overview', '')

        if not overview:
            overview = 'Sin sinopsis disponible.'

        vote_average_str = f"{vote_average:.1f} / 10"

        self.ui.title_label.setText(title)
        self.ui.release_date_label.setText(f"{release_date}")
        self.ui.vote_average_label.setText(f"{vote_average_str}")
        self.ui.overview_label.setText(overview)

    def handle_add_to_library(self):
        if not self.movie_data or not self.user_id:
            print("Error: Faltan datos de la película o del usuario.")
            return

        api_url = "http://localhost:5000/api/library/add"

        payload = {
            "user_id": self.user_id,
            "content_id": self.movie_data.get('id'),
            "content_type": "movie", # Asumimos que es una película por ahora
            "status": "Plan to Watch" # Estado por defecto
        }

        print("Añadiendo a la librería:", payload)

        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 201:
                print("¡Película añadida a la librería exitosamente!")
                # Aquí podrías mostrar una notificación al usuario en la UI
                self.ui.add_to_library_button.setText("En tu librería")
                self.ui.add_to_library_button.setEnabled(False)
            else:
                print(f"Error al añadir a la librería: {response.text}")
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión: {e}")