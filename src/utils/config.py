from PyQt5.QtCore import QSettings


class AppConfig(object):
    DEFAULTS = {
        "source_encoding": "",
        "target_encoding": "utf-8",
        "auto_detect": True,
        "keep_per_file_encoding": False,
        "strip_bom": False,
        "add_bom": False,
        "error_strategy": "replace",
        "window_width": 950,
        "window_height": 650,
        "recent_source_encodings": [],
        "recent_target_encodings": [],
        "output_dir": "",
    }

    def __init__(self):
        # type: () -> None
        self.settings = QSettings("EncodingConverter", "EncodingConverter")

    def get(self, key):
        default = self.DEFAULTS.get(key)
        return self.settings.value(key, default)

    def set(self, key, value):
        # type: (str, object) -> None
        self.settings.setValue(key, value)

    def save_geometry(self, window):
        # type: (object) -> None
        self.settings.setValue("window_geometry", window.saveGeometry())

    def restore_geometry(self, window):
        # type: (object) -> None
        geo = self.settings.value("window_geometry")
        if geo:
            window.restoreGeometry(geo)

    def add_recent_encoding(self, key, encoding, max_items=5):
        # type: (str, str, int) -> None
        recent = self.get(key)
        if not isinstance(recent, list):
            recent = []
        if encoding in recent:
            recent.remove(encoding)
        recent.insert(0, encoding)
        recent = recent[:max_items]
        self.set(key, recent)
