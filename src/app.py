import sys
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.utils.logger import setup_logging


def create_app():
    # type: () -> tuple
    # High-DPI support - must be set before QApplication creation
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    except AttributeError:
        pass
    try:
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Encoding Converter")
    app.setOrganizationName("EncodingConverter")

    # Set application icon
    icon_path = _get_resource_path("logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Load stylesheet
    style_path = _get_resource_path("src/ui/resources/styles/style.qss")
    if style_path and os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    setup_logging()

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    return app, window


def _get_resource_path(relative_path):
    # type: (str) -> str
    """获取资源文件路径，支持开发环境和 PyInstaller 打包后的环境"""
    # PyInstaller 打包后的临时目录
    if hasattr(sys, '_MEIPASS'):
        # 打包后的环境：_MEIPASS 指向临时解压目录
        base_path = sys._MEIPASS
    else:
        # 开发环境：从 src/app.py 向上两级到项目根目录
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    path = os.path.join(base_path, relative_path)
    return path
