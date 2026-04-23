"""Build Windows .exe with PyInstaller."""
import PyInstaller.__main__
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    path_sep = ';'
else:
    path_sep = ':'

SPEC_ARGS = [
    os.path.join(PROJECT_ROOT, "run.py"),
    "--name=EncodingConverter",
    "--windowed",
    "--onedir",
    "--add-data=" + os.path.join(PROJECT_ROOT, "src", "ui", "resources") + path_sep + "src/ui/resources",
    "--add-data=" + os.path.join(PROJECT_ROOT, "logo.png") + path_sep + ".",
    "--hidden-import=charset_normalizer",
    "--hidden-import=PyQt5.QtCore",
    "--hidden-import=PyQt5.QtGui",
    "--hidden-import=PyQt5.QtWidgets",
    "--noconfirm",
    "--clean",
    "--distpath=" + os.path.join(PROJECT_ROOT, "dist"),
    "--workpath=" + os.path.join(PROJECT_ROOT, "build"),
]

icon_path = os.path.join(PROJECT_ROOT, "packaging", "assets", "app_icon.ico")
if os.path.exists(icon_path):
    SPEC_ARGS.insert(3, "--icon=" + icon_path)

if __name__ == "__main__":
    PyInstaller.__main__.run(SPEC_ARGS)
