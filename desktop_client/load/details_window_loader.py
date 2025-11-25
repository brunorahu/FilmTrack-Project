# desktop_client/load/details_window_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMessageBox
import requests

class DetailsWindow:
    def __init__(self):
        loader = QUiLoader()
        self.ui = loader.load("view/details_window.ui")
        
        self.movie_data = None
        self.user_id = None
        
        # Conectamos los botones existentes y el nuevo
        self.ui.add_to_library_button.clicked.connect(self.handle_add_to_library)
        self.ui.save_review_button.clicked.connect(self.handle_save_review)

    def populate_details(self, movie_data, user_id):
        # ... (este método se queda igual) ...
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
        self.ui.release_date_label.setText(release_date)
        self.ui.vote_average_label.setText(f"Calificación: {vote_average_str}")
        self.ui.overview_label.setText(overview)

    def handle_add_to_library(self):
        # ... (este método se queda igual) ...
        if not self.movie_data or not self.user_id:
            return
        api_url = "http://localhost:5000/api/library/add"
        payload = {
            "user_id": self.user_id,
            "content_id": self.movie_data.get('id'),
            "content_type": "movie",
            "status": "Plan to Watch"
        }
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 201:
                QMessageBox.information(self.ui, "Éxito", "Película añadida a tu librería.")
                self.ui.add_to_library_button.setText("En tu librería")
                self.ui.add_to_library_button.setEnabled(False)
            else:
                QMessageBox.warning(self.ui, "Error", "No se pudo añadir la película.")
        except requests.exceptions.ConnectionError as e:
            QMessageBox.critical(self.ui, "Error de Conexión", "No se pudo conectar a la API.")

    # --- ¡NUEVA FUNCIÓN PARA GUARDAR CALIFICACIÓN! ---
    def handle_save_review(self):
        if not self.movie_data or not self.user_id:
            QMessageBox.warning(self.ui, "Error", "No hay datos de película o usuario.")
            return

        api_url = "http://localhost:5000/api/library/review"
        
        payload = {
            "user_id": self.user_id,
            "content_id": self.movie_data.get('id'),
            "rating": self.ui.rating_spinbox.value(),
            "review_text": self.ui.review_textedit.toPlainText()
        }

        print("Guardando calificación/reseña:", payload)
        
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                QMessageBox.information(self.ui, "Éxito", "Tu calificación y reseña han sido guardadas.")
                self.ui.close() # Cerramos la ventana después de guardar
            else:
                error_data = response.json()
                QMessageBox.critical(self.ui, "Error", f"No se pudo guardar: {error_data.get('error')}")
        except requests.exceptions.ConnectionError as e:
            QMessageBox.critical(self.ui, "Error de Conexión", "No se pudo conectar a la API.")