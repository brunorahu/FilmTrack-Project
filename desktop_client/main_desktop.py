# desktop_client/main_desktop.py

import sys
from PySide6.QtWidgets import QApplication
from load.login_loader import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Creamos una instancia de nuestro controlador
    login_controller = LoginWindow()
    
    # Le pedimos al controlador que muestre la ventana que cargó (self.ui)
    login_controller.ui.show()
    
    sys.exit(app.exec())