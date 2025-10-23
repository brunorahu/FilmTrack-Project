# desktop_client/load/details_window_loader.py

from PySide6.QtUiTools import QUiLoader

class DetailsWindow:
    def __init__(self):
        # Cargamos el archivo .ui de la ventana de detalles
        loader = QUiLoader()
        self.ui = loader.load("view/details_window.ui")

    def populate_details(self, movie_data):
        """
        Rellena los labels de la ventana con los datos de la película.
        """
        title = movie_data.get('title', 'N/A')
        release_date = movie_data.get('release_date', 'N/A')
        vote_average = movie_data.get('vote_average', 0)

        # --- LÓGICA MEJORADA PARA LA SINOPSIS ---
        overview = movie_data.get('overview', '') # Obtenemos la sinopsis

        # Si el texto de la sinopsis está vacío, usamos un mensaje por defecto
        if not overview:
            overview = 'Sin sinópsis disponible.'
        # --- FIN DE LA MEJORA ---

        vote_average_str = f"{vote_average:.1f} / 10"

        self.ui.title_label.setText(title)
        self.ui.release_date_label.setText(release_date)
        self.ui.vote_average_label.setText(vote_average_str)
        self.ui.overview_label.setText(overview)