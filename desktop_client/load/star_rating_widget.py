from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QPixmap, QIcon

class StarRatingWidget(QWidget):
    ratingChanged = Signal(int) # Señal que avisa cuando cambia la calificación

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rating = 0
        self.max_rating = 5
        self.stars = []
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Creamos las 5 etiquetas de estrella
        for i in range(1, self.max_rating + 1):
            label = QLabel("★") # Usamos el carácter de estrella
            label.setStyleSheet("color: #555; font-size: 24px;") # Gris por defecto
            label.setCursor(Qt.PointingHandCursor)
            # Hacemos que la etiqueta sea clickeable
            label.mousePressEvent = lambda event, rate=i: self.set_rating(rate)
            
            self.stars.append(label)
            layout.addWidget(label)
            
        self.setLayout(layout)

    def set_rating(self, rating):
        self.rating = rating
        self.update_stars()
        self.ratingChanged.emit(self.rating)

    def update_stars(self):
        for i, label in enumerate(self.stars):
            if i < self.rating:
                label.setStyleSheet("color: #FFD700; font-size: 24px;") # Dorado
            else:
                label.setStyleSheet("color: #555; font-size: 24px;") # Gris