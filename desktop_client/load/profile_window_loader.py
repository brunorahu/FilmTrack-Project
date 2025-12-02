# desktop_client/load/profile_window_loader.py

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QBrush
import requests
from load.utils import resource_path
import os

class ProfileWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        loader = QUiLoader()
        self.ui = loader.load("view/profile_window.ui")
        self.user_id = user_id
        
        self.avatar_path = None # Ruta local si seleccionamos una nueva
        self.server_avatar_filename = None # Nombre del archivo en el servidor
        
        # --- VENTANA SIN MARCO ---
        self.ui.setWindowFlag(Qt.FramelessWindowHint)
        
        if hasattr(self.ui, 'btn_close'):
            self.ui.btn_close.clicked.connect(self.ui.close)
            icon_path = resource_path("assets/cerrar.png")
            self.ui.btn_close.setIcon(QIcon(icon_path))

        self.drag_pos = QPoint(0, 0)
        if hasattr(self.ui, 'title_bar_frame'):
            self.ui.title_bar_frame.mouseMoveEvent = self.move_window
            self.ui.title_bar_frame.mousePressEvent = self.mouse_press
        # -------------------------

        if hasattr(self.ui, 'btn_save'):
            self.ui.btn_save.clicked.connect(self.handle_save_profile)
            
        if hasattr(self.ui, 'btn_change_avatar'):
            self.ui.btn_change_avatar.clicked.connect(self.select_avatar)
        
        self.load_profile_data()

    def mouse_press(self, event):
        self.drag_pos = event.globalPosition().toPoint()

    def move_window(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.drag_pos)
            self.ui.move(self.ui.x() + delta.x(), self.ui.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

    # --- FUNCIÓN AUXILIAR PARA RECORTAR EN CÍRCULO ---
    def set_circular_avatar(self, pixmap):
        """Recibe un QPixmap, lo recorta en círculo y lo pone en el label."""
        size = 140
        target_size = QSize(size, size)
        
        scaled_pixmap = pixmap.scaled(
            target_size, 
            Qt.KeepAspectRatioByExpanding, 
            Qt.SmoothTransformation
        )
        
        final_pixmap = QPixmap(target_size)
        final_pixmap.fill(Qt.transparent)
        
        painter = QPainter(final_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        brush = QBrush(scaled_pixmap)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        
        center_x = (scaled_pixmap.width() - size) / 2
        center_y = (scaled_pixmap.height() - size) / 2
        
        painter.translate(-center_x, -center_y)
        painter.drawEllipse(center_x, center_y, size, size)
        painter.end()
        
        self.ui.avatar_label.setPixmap(final_pixmap)

    # --- SELECCIÓN DE IMAGEN LOCAL ---
    def select_avatar(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Avatar", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_name:
            self.avatar_path = file_name # Guardamos ruta local para subirla luego
            # Mostramos preview
            self.set_circular_avatar(QPixmap(file_name))

    # --- CARGAR DATOS DEL SERVIDOR ---
    def load_profile_data(self):
        api_url = f"http://localhost:5000/api/users/profile/{self.user_id}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                profile = response.json()
                
                if hasattr(self.ui, 'le_username'):
                    self.ui.le_username.setText(profile.get('username', ''))
                if hasattr(self.ui, 'txt_bio'):
                    self.ui.txt_bio.setPlainText(profile.get('bio') or "")
                
                # --- CARGAR AVATAR REMOTO ---
                self.server_avatar_filename = profile.get('avatar')
                if self.server_avatar_filename and self.server_avatar_filename != "default":
                    avatar_url = f"http://localhost:5000/uploads/{self.server_avatar_filename}"
                    try:
                        img_response = requests.get(avatar_url)
                        if img_response.status_code == 200:
                            pixmap = QPixmap()
                            pixmap.loadFromData(img_response.content)
                            self.set_circular_avatar(pixmap)
                    except Exception as e:
                        print(f"No se pudo descargar el avatar: {e}")

            else:
                print(f"Error cargando perfil: {response.text}")
        except requests.exceptions.ConnectionError:
            print("Error de conexión al cargar perfil.")

    # --- GUARDAR Y SUBIR ---
    def handle_save_profile(self):
        username = self.ui.le_username.text()
        bio = self.ui.txt_bio.toPlainText()
        
        if not username:
            QMessageBox.warning(self.ui, "Error", "El nombre de usuario es obligatorio.")
            return

        # 1. Si hay una nueva imagen seleccionada, la subimos primero
        new_avatar_filename = self.server_avatar_filename # Por defecto mantenemos la actual
        
        if self.avatar_path:
            try:
                print("Subiendo imagen al servidor...")
                upload_url = "http://localhost:5000/api/upload"
                files = {'file': open(self.avatar_path, 'rb')}
                upload_res = requests.post(upload_url, files=files)
                
                if upload_res.status_code == 201:
                    new_avatar_filename = upload_res.json()['filename']
                    print(f"Imagen subida con éxito: {new_avatar_filename}")
                else:
                    QMessageBox.warning(self.ui, "Error", "No se pudo subir la imagen.")
                    return
            except Exception as e:
                print(f"Error subiendo imagen: {e}")
                QMessageBox.critical(self.ui, "Error", "Error de conexión al subir imagen.")
                return

        # 2. Actualizamos el perfil con el nombre del archivo (nuevo o viejo)
        api_url = f"http://localhost:5000/api/users/profile/{self.user_id}"
        payload = {
            "username": username,
            "bio": bio,
            "avatar": new_avatar_filename
        }
        
        try:
            response = requests.put(api_url, json=payload)
            if response.status_code == 200:
                QMessageBox.information(self.ui, "Éxito", "Perfil actualizado correctamente.")
                self.ui.close()
            elif response.status_code == 409:
                QMessageBox.warning(self.ui, "Error", "Ese nombre de usuario ya está en uso.")
            else:
                QMessageBox.critical(self.ui, "Error", f"No se pudo guardar: {response.text}")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self.ui, "Error de Conexión", "No se pudo conectar a la API.")