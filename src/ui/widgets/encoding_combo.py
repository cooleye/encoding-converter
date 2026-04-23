from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QLabel, QCompleter
)
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QStringListModel

from src.utils.encoding_list import ENCODING_GROUPS


class EncodingComboBox(QWidget):
    encoding_changed = pyqtSignal(str)

    AUTO_DETECT_TEXT = "自动检测"

    def __init__(self, label_text="Encoding:", mode="target", parent=None):
        # type: (str, str, object) -> None
        super(EncodingComboBox, self).__init__(parent)
        self.mode = mode
        self._block_signals = False
        self._setup_ui(label_text)
        self._populate_encodings()

    def _setup_ui(self, label_text):
        # type: (str) -> None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.label = QLabel(label_text)
        self.label.setFixedWidth(50)
        layout.addWidget(self.label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索编码...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_edit, 1)

        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self.combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.combo, 2)

        completer = QCompleter(self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.search_edit.setCompleter(completer)
        self._completer = completer

    def _populate_encodings(self):
        # type: () -> None
        self.combo.clear()
        all_names = []

        if self.mode == "source":
            self.combo.addItem(self.AUTO_DETECT_TEXT, "")
            self.combo.insertSeparator(self.combo.count())
            all_names.append(self.AUTO_DETECT_TEXT)

        for group_name, encodings in ENCODING_GROUPS:
            for display_name, codec_name in encodings:
                self.combo.addItem(display_name, codec_name)
                all_names.append(display_name)
            if group_name != ENCODING_GROUPS[-1][0]:
                self.combo.insertSeparator(self.combo.count())

        model = QStringListModel(all_names, self)
        self._completer.setModel(model)

        if self.mode == "source":
            self.combo.setCurrentIndex(0)
        else:
            idx = self.combo.findData("utf-8")
            if idx >= 0:
                self.combo.setCurrentIndex(idx)

    def _on_search_changed(self, text):
        # type: (str) -> None
        search = text.strip().lower()
        if not search:
            for i in range(self.combo.count()):
                self.combo.model().item(i).setEnabled(True) if hasattr(self.combo.model(), 'item') else None
            return

        for i in range(self.combo.count()):
            item_text = self.combo.itemText(i).lower()
            item_data = self.combo.itemData(i)
            if not item_data and item_data != "":
                continue
            match = search in item_text or search in str(item_data).lower()
            try:
                from PyQt5.QtGui import QStandardItemModel
                if isinstance(self.combo.model(), QStandardItemModel):
                    item = self.combo.model().item(i)
                    if item:
                        item.setEnabled(match)
            except ImportError:
                pass

        for i in range(self.combo.count()):
            item_text = self.combo.itemText(i).lower()
            item_data = str(self.combo.itemData(i) or "").lower()
            if search in item_text or search in item_data:
                self._block_signals = True
                self.combo.setCurrentIndex(i)
                self._block_signals = False
                break

    def _on_selection_changed(self, index):
        # type: (int) -> None
        if self._block_signals or index < 0:
            return
        data = self.combo.currentData()
        if data is not None:
            self.encoding_changed.emit(str(data) if data else "")

    def current_encoding(self):
        # type: () -> str
        data = self.combo.currentData()
        return str(data) if data else ""

    def set_encoding(self, encoding):
        # type: (str) -> None
        self._block_signals = True
        if not encoding and self.mode == "source":
            self.combo.setCurrentIndex(0)
        else:
            idx = self.combo.findData(encoding)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)
        self._block_signals = False

    def is_auto_detect(self):
        # type: () -> bool
        return self.mode == "source" and self.combo.currentIndex() == 0
