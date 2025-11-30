# desktop_client/load/details_window_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import Qt, QPoint, QThreadPool
import requests

# Importamos nuestras clases personalizadas
from load.movie_card_loader import ImageLoader 
from load.star_rating_widget import StarRatingWidget

class DetailsWindow(QWidget):
    def __init__(self):
        super().__init__()
        loader = QUiLoader()
        # 1. Cargamos la interfaz
        self.ui = loader.load("view/details_window.ui")
        
        # --- LÓGICA DE VENTANA SIN MARCO ---
        self.ui.setWindowFlag(Qt.FramelessWindowHint)
        # self.ui.setAttribute(Qt.WA_TranslucentBackground) # Comentado para evitar fondo transparente
        self.ui.setWindowState(Qt.WindowMaximized) # Iniciar maximizada
        
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
        
        # --- INTEGRACIÓN DE ESTRELLAS (RATING) ---
        # 1. Ocultamos el SpinBox original si existe
        if hasattr(self.ui, 'rating_spinbox'):
            self.ui.rating_spinbox.setVisible(False)
        
        # 2. Creamos e insertamos el Widget de Estrellas
        self.star_widget = StarRatingWidget()
        # Intentamos insertarlo en el layout del frame izquierdo inferior
        if hasattr(self.ui, 'frame_izquierdo_inferior') and self.ui.frame_izquierdo_inferior.layout():
            # Insertamos en la posición 2 (ajusta si es necesario)
            self.ui.frame_izquierdo_inferior.layout().insertWidget(2, self.star_widget)
        else:
            print("Advertencia: No se encontró el layout para insertar las estrellas.")
        # -----------------------------------------

        # Conectamos los botones de acción
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
        overview = movie_data.get('overview', '')
        poster_path = movie_data.get('poster_path')
        movie_id = movie_data.get('id')
        
        if not overview: overview = 'Sin sinopsis disponible.'

        # --- 1. GÉNEROS Y TAGLINE (NUEVO) ---
        tagline = movie_data.get('tagline', '')
        # Verificamos si existe el label en la UI antes de setear el texto
        if hasattr(self.ui, 'tagline_label'):
            self.ui.tagline_label.setText(f'"{tagline}"' if tagline else "")

        genres_list = movie_data.get('genres', [])
        # genres es una lista de dicts: [{'id': 28, 'name': 'Action'}, ...]
        genres_str = " | ".join([g['name'] for g in genres_list])
        
        if hasattr(self.ui, 'genres_label'):
            self.ui.genres_label.setText(genres_str)
        # ------------------------------------

        # Año
        if release_date and release_date != 'N/A':
            release_year = release_date.split('-')[0]
        else:
            release_year = 'N/A'
            
        # Obtener el Director
        director_name = "Desconocido"
        try:
            credits_url = f"http://localhost:5000/api/movies/{movie_id}/credits"
            credits_res = requests.get(credits_url)
            if credits_res.status_code == 200:
                data = credits_res.json()
                crew = data.get('crew', [])
                cast = data.get('cast', [])
                
                # Director
                director_data = next((m for m in crew if m['job'] == 'Director'), None)
                if director_data: director_name = director_data['name']
                
                # Reparto (Cast)
                top_actors = [actor['name'] for actor in cast[:3]]
                cast_string = ", ".join(top_actors)
                
                if hasattr(self.ui, 'cast_label'):
                    self.ui.cast_label.setText(f"Reparto: {cast_string}")

        except Exception as e:
            print(f"Error obteniendo director/reparto: {e}")

        self.ui.title_label.setText(title)
        
        # Actualizamos el label de fecha para incluir al director
        self.ui.release_date_label.setText(f"{release_year} • Dirigida por {director_name}")
        
        self.ui.overview_label.setText(overview)

        # Cargar Póster
        if poster_path and hasattr(self.ui, 'poster_label'):
            image_loader = ImageLoader(poster_path)
            image_loader.signals.finished.connect(self.ui.poster_label.setPixmap)
            self.thread_pool.start(image_loader)
        
        # Descargar Backdrop (Opcional, si decides implementarlo)
        # backdrop_path = movie_data.get('backdrop_path')
        # if backdrop_path: ...

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
        
        rating_val = self.star_widget.rating 
        
        if rating_val == 0:
            QMessageBox.warning(self.ui, "Falta Calificación", "Por favor selecciona una calificación (estrellas).")
            return

        api_url = "http://localhost:5000/api/library/review"
        payload = {
            "user_id": self.user_id, 
            "content_id": self.movie.get('id'), 
            "rating": rating_val, 
            "review_text": self.ui.review_textedit.toPlainText()
        }
        
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                QMessageBox.information(self.ui, "Éxito", "Tu calificación y reseña han sido guardadas.")
                self.ui.close()
            else: QMessageBox.critical(self.ui, "Error", f"Error: {response.json().get('error')}")
        except requests.exceptions.ConnectionError as e: QMessageBox.critical(self.ui, "Error", "No se pudo conectar a la API.")