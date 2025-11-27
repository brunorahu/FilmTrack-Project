# desktop_client/main_desktop.py
import sys
from PySide6.QtWidgets import QApplication
from load.login_loader import LoginWindow
from PySide6.QtCore import Qt

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    login_window = LoginWindow()

    if login_window.ui.exec() == 1:
        # Obtenemos la ventana principal que el login creó
        main_window = login_window.main_window
        
        main_window.ui.setWindowState(Qt.WindowMaximized) # Inicia maximizada
        
        main_window.ui.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)