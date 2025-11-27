# desktop_client/load/details_window_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import Qt, QPoint
import requests
# Reutilizamos la lógica de carga de imágenes que ya escribimos
from load.movie_card_loader import ImageLoader 
from PySide6.QtCore import QThreadPool

class DetailsWindow(QWidget):
    def __init__(self):
        super().__init__()
        loader = QUiLoader()
        self.ui = loader.load("view/details_window.ui")
        
        # --- LÓGICA DE VENTANA SIN MARCO ---
        self.ui.setWindowFlag(Qt.FramelessWindowHint)   
             
        # Conectar botón de cerrar
        if hasattr(self.ui, 'btn_close'):
            self.ui.btn_close.clicked.connect(self.ui.close)

        # Variables para arrastrar la ventana
        self.drag_pos = QPoint(0, 0)
        if hasattr(self.ui, 'title_bar_frame'):
            self.ui.title_bar_frame.mouseMoveEvent = self.move_window
            self.ui.title_bar_frame.mousePressEvent = self.mouse_press
        # ------------------------------------

        self.movie_data = None
        self.user_id = None
        self.thread_pool = QThreadPool.globalInstance()
        
        # Conectamos los botones
        self.ui.add_to_library_button.clicked.connect(self.handle_add_to_library)
        self.ui.save_review_button.clicked.connect(self.handle_save_review)

    def mouse_press(self, event):
        self.drag_pos = event.globalPosition().toPoint()

    def move_window(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.drag_pos)
            self.ui.move(self.ui.x() + delta.x(), self.ui.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

    def populate_details(self, movie_data, user_id):
        self.movie_data = movie_data
        self.user_id = user_id
        
        title = movie_data.get('title', 'N/A')
        release_date = movie_data.get('release_date', 'N/A')
        vote_average = movie_data.get('vote_average', 0)
        overview = movie_data.get('overview', '')
        poster_path = movie_data.get('poster_path')
        
        if not overview:
            overview = 'Sin sinopsis disponible.'

        vote_average_str = f"{vote_average:.1f} / 10"

        self.ui.title_label.setText(title)
        if release_date and release_date != 'N/A':
            release_year = release_date.split('-')[0] # Toma la primera parte (el año)
            self.ui.release_date_label.setText(release_year)
        else:
            self.ui.release_date_label.setText('N/A')
        # self.ui.vote_average_label.setText(f"Calif: {vote_average_str}") # Si decides mantener este label
        self.ui.overview_label.setText(overview)

        # Cargar Póster
        if poster_path and hasattr(self.ui, 'poster_label'):
            image_loader = ImageLoader(poster_path)
            image_loader.signals.finished.connect(self.ui.poster_label.setPixmap)
            self.thread_pool.start(image_loader)

    # ... (handle_add_to_library y handle_save_review se quedan igual) ...
    def handle_add_to_library(self):
        if not self.movie_data or not self.user_id: return
        api_url = "http://localhost:5000/api/library/add"
        payload = {"user_id": self.user_id, "content_id": self.movie_data.get('id'), "content_type": "movie", "status": "Plan to Watch"}
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 201:
                QMessageBox.information(self.ui, "Éxito", "Película añadida a tu librería.")
                self.ui.add_to_library_button.setText("En tu librería")
                self.ui.add_to_library_button.setEnabled(False)
            else: QMessageBox.warning(self.ui, "Error", "No se pudo añadir la película.")
        except requests.exceptions.ConnectionError as e: QMessageBox.critical(self.ui, "Error", "No se pudo conectar a la API.")

    def handle_save_review(self):
        if not self.movie_data or not self.user_id: return
        api_url = "http://localhost:5000/api/library/review"
        payload = {"user_id": self.user_id, "content_id": self.movie_data.get('id'), "rating": self.ui.rating_spinbox.value(), "review_text": self.ui.review_textedit.toPlainText()}
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                QMessageBox.information(self.ui, "Éxito", "Guardado.")
                self.ui.close()
            else: QMessageBox.critical(self.ui, "Error", f"Error: {response.json().get('error')}")
        except requests.exceptions.ConnectionError as e: QMessageBox.critical(self.ui, "Error", "No se pudo conectar a la API.")