import sys
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.ui.main_window import MainWindow
from src.utils.logger import setup_logging


def create_app():
    # type: () -> tuple
    # High-DPI support - must be set before QApplication creation
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Encoding Converter")
    app.setOrganizationName("EncodingConverter")

    # Load stylesheet
    style_path = _get_resource_path("src/ui/resources/styles/style.qss")
    if style_path and os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    setup_logging()

    window = MainWindow()
    window.show()

    return app, window


def _get_resource_path(relative_path):
    # type: (str) -> str
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(base_path, relative_path)
    return path
