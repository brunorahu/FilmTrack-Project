# desktop_client/load/movie_card_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QRunnable, QThreadPool, Slot, Signal, QObject
import requests

class ImageLoader(QRunnable):
    """
    Clase trabajadora (worker) que descarga una imagen en un hilo separado.
    """
    def __init__(self, image_url):
        super().__init__()
        self.image_url = image_url
        self.signals = self.Signals()

    class Signals(QObject):
        # Señal que se emite cuando la imagen está lista (QPixmap)
        finished = Signal(QPixmap)

    @Slot()
    def run(self):
        try:
            # Construimos la URL completa del póster
            full_url = f"https://image.tmdb.org/t/p/w200{self.image_url}"
            response = requests.get(full_url)
            response.raise_for_status()
            
            pixmap = QPixmap()
            pixmap.loadFromData(response.content) # Cargamos la imagen desde los datos descargados
            
            # Emitimos la señal con la imagen lista
            self.signals.finished.emit(pixmap)
            
        except Exception as e:
            print(f"Error descargando imagen: {e}")
            # Podríamos emitir una imagen de "error" por defecto
            self.signals.finished.emit(QPixmap()) # Emitimos un pixmap vacío

class MovieCard(QWidget):
    """
    Controlador para nuestra plantilla movie_card.ui.
    """
    def __init__(self, movie_data):
        super().__init__()
        
        # Cargamos el diseño .ui
        self.ui = QUiLoader().load("view/movie_card.ui", self)
        
        # Configuramos el hilo de la piscina para descargas
        self.thread_pool = QThreadPool.globalInstance()

        # Rellenamos los datos de la película
        self.set_movie_data(movie_data)

    def set_movie_data(self, movie_data):
        # Seteamos el título y la calificación
        self.ui.title_label.setText(movie_data.get('title', 'N/A'))
        rating = movie_data.get('vote_average', 0)
        self.ui.rating_label.setText(f"⭐ {rating:.1f}")
        
        # Iniciamos la descarga de la imagen en segundo plano
        poster_path = movie_data.get('poster_path')
        if poster_path:
            # Creamos el worker y lo ponemos en la cola
            image_loader = ImageLoader(poster_path)
            # Conectamos la señal 'finished' a nuestra función 'set_poster'
            image_loader.signals.finished.connect(self.set_poster)
            self.thread_pool.start(image_loader)

    @Slot(QPixmap)
    def set_poster(self, pixmap):
        """
        Esta función se llama cuando la imagen se ha terminado de descargar.
        """
        if not pixmap.isNull():
            self.ui.poster_label.setPixmap(pixmap)