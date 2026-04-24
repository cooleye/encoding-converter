import os
from typing import List, Optional

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QAction, QFileDialog, QWidget, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent

from src.core.models import FileEntry, FileStatus, ConversionResult
from src.core.detector import EncodingDetector
from src.core.bom_handler import has_bom
from src.ui.widgets.progress_delegate import ProgressDelegate

BINARY_EXTENSIONS = frozenset({
    '.exe', '.dll', '.so', '.dylib', '.ocx', '.sys', '.drv',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.zst', '.cab',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.tif', '.tiff', '.webp', '.heic', '.raw',
    '.mp3', '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.wav', '.flac', '.aac', '.ogg', '.wma',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
    '.db', '.sqlite', '.mdb', '.dbf',
    '.class', '.o', '.obj', '.lib', '.a', '.la',
    '.pyc', '.pyd', '.pyo', '.so',
    '.woff', '.woff2', '.ttf', '.otf', '.eot',
    '.bin', '.dat', '.iso', '.img', '.dmg', '.pkg', '.deb', '.rpm', '.msi',
    '.jar', '.war', '.ear', '.apk', '.ipa',
    '.node', '.wasm',
})

MAX_BINARY_CHECK_SIZE = 512 * 1024


def _is_likely_text_file(file_path):
    # type: (str) -> bool
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext in BINARY_EXTENSIONS:
        return False
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return True
        check_size = min(file_size, MAX_BINARY_CHECK_SIZE)
        with open(file_path, 'rb') as f:
            chunk = f.read(check_size)
        if b'\x00' in chunk:
            return False
        return True
    except (OSError, IOError):
        return False


class FileListTable(QTableWidget):
    file_added = pyqtSignal(str)
    files_added = pyqtSignal(list)
    file_removed = pyqtSignal(int)
    count_changed = pyqtSignal(int)

    COLUMNS = ["#", "文件路径", "大小", "编码", "状态"]
    COL_WIDTHS = [40, 400, 80, 100, 200]

    def __init__(self, parent=None):
        # type: (Optional[QWidget]) -> None
        super(FileListTable, self).__init__(0, len(self.COLUMNS), parent)
        self._file_entries = []  # type: List[FileEntry]
        self._detector = EncodingDetector()
        self._setup_headers()
        self._setup_drag_drop()
        self._setup_context_menu()
        self._progress_delegate = ProgressDelegate(self)
        self.setItemDelegateForColumn(4, self._progress_delegate)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSortingEnabled(False)

    def _setup_headers(self):
        # type: () -> None
        for i, (name, width) in enumerate(zip(self.COLUMNS, self.COL_WIDTHS)):
            item = QTableWidgetItem(name)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.setHorizontalHeaderItem(i, item)
            self.setColumnWidth(i, width)
        header = self.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setStretchLastSection(True)

    def _setup_drag_drop(self):
        # type: () -> None
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setDefaultDropAction(Qt.CopyAction)

    def _setup_context_menu(self):
        # type: () -> None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        # type: (object) -> None
        menu = QMenu(self)
        selected = self.selectionModel().selectedRows()

        if selected:
            remove_action = QAction("移除选中", self)
            remove_action.triggered.connect(self.remove_selected)
            menu.addAction(remove_action)

        open_folder_action = QAction("打开所在文件夹", self)
        open_folder_action.triggered.connect(self._open_containing_folder)
        menu.addAction(open_folder_action)

        menu.addSeparator()

        clear_action = QAction("清空全部", self)
        clear_action.triggered.connect(self.clear_all)
        menu.addAction(clear_action)

        menu.exec_(self.viewport().mapToGlobal(pos))

    def _open_containing_folder(self):
        # type: () -> None
        selected = self.selectionModel().selectedRows()
        if not selected:
            return
        row = selected[0].row()
        if row < len(self._file_entries):
            path = self._file_entries[row].path
            folder = os.path.dirname(path)
            if os.path.isdir(folder):
                from PyQt5.QtGui import QDesktopServices
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def dragEnterEvent(self, event):
        # type: (QDragEnterEvent) -> None
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        # type: (object) -> None
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        # type: (QDropEvent) -> None
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        event.acceptProposedAction()
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                if _is_likely_text_file(path):
                    paths.append(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for fname in files:
                        fpath = os.path.join(root, fname)
                        if os.path.isfile(fpath) and _is_likely_text_file(fpath):
                            paths.append(fpath)
        for p in paths:
            self.add_file(p)

    def add_file(self, file_path):
        # type: (str) -> None
        file_path = os.path.abspath(file_path)
        for entry in self._file_entries:
            if entry.path == file_path:
                return

        if not _is_likely_text_file(file_path):
            return

        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            return

        entry = FileEntry(path=file_path, size=file_size)
        entry.status = FileStatus.DETECTING
        entry.status_text = "检测中..."
        self._file_entries.append(entry)

        row = self.rowCount()
        self.insertRow(row)
        self._populate_row(row, entry)
        self.count_changed.emit(self.rowCount())

        self._detect_encoding_async(row, entry)

    def add_files(self, file_paths):
        # type: (List[str]) -> None
        for path in file_paths:
            self.add_file(path)

    def add_folder(self, folder_path, recursive=True):
        # type: (str, bool) -> None
        if not os.path.isdir(folder_path):
            return
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for fname in files:
                    self.add_file(os.path.join(root, fname))
        else:
            for fname in os.listdir(folder_path):
                fpath = os.path.join(folder_path, fname)
                if os.path.isfile(fpath):
                    self.add_file(fpath)

    def _detect_encoding_async(self, row, entry):
        # type: (int, FileEntry) -> None
        try:
            encoding, confidence = self._detector.detect(entry.path)
            entry.detected_encoding = encoding
            entry.encoding_confidence = confidence
            entry.has_bom = has_bom(entry.path)
            entry.status = FileStatus.READY
            entry.status_text = "就绪"
        except Exception as e:
            entry.status = FileStatus.FAILED
            entry.status_text = "检测失败"
            entry.error_message = str(e)

        if row < self.rowCount():
            self._update_row(row, entry)

    def _populate_row(self, row, entry):
        # type: (int, FileEntry) -> None
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignCenter)
        num_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.setItem(row, 0, num_item)

        path_item = QTableWidgetItem(entry.path)
        path_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        path_item.setToolTip(entry.path)
        self.setItem(row, 1, path_item)

        size_item = QTableWidgetItem(self._format_size(entry.size))
        size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        size_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.setItem(row, 2, size_item)

        enc_text = entry.detected_encoding or "未知"
        if entry.encoding_confidence > 0 and entry.encoding_confidence < 1.0:
            enc_text += " ({:.0%})".format(entry.encoding_confidence)
        if entry.has_bom:
            enc_text += " [含BOM]"
        enc_item = QTableWidgetItem(enc_text)
        enc_item.setTextAlignment(Qt.AlignCenter)
        enc_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.setItem(row, 3, enc_item)

        status_item = QTableWidgetItem(entry.status_text)
        status_item.setData(Qt.UserRole, None)
        status_item.setTextAlignment(Qt.AlignCenter)
        status_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.setItem(row, 4, status_item)

    def _update_row(self, row, entry):
        # type: (int, FileEntry) -> None
        if row >= self.rowCount():
            return

        num_item = self.item(row, 0)
        if num_item:
            num_item.setText(str(row + 1))

        enc_text = entry.detected_encoding or "未知"
        if entry.encoding_confidence > 0 and entry.encoding_confidence < 1.0:
            enc_text += " ({:.0%})".format(entry.encoding_confidence)
        if entry.has_bom:
            enc_text += " [BOM]"
        enc_item = self.item(row, 3)
        if enc_item:
            enc_item.setText(enc_text)

        status_item = self.item(row, 4)
        if status_item:
            progress = entry.progress if entry.status == FileStatus.CONVERTING else None
            status_item.setText(entry.status_text)
            status_item.setData(Qt.UserRole, progress)
            if entry.status == FileStatus.COMPLETED:
                status_item.setForeground(QColor("#4CAF50"))
            elif entry.status == FileStatus.FAILED:
                status_item.setForeground(QColor("#F44336"))
            elif entry.status == FileStatus.SKIPPED:
                status_item.setForeground(QColor("#FF9800"))
            else:
                status_item.setForeground(QColor())

    def update_progress(self, row, progress, status_text):
        # type: (int, int, str) -> None
        if row >= self.rowCount():
            return
        entry = self._file_entries[row]
        entry.status = FileStatus.CONVERTING
        entry.progress = progress
        entry.status_text = status_text

        status_item = self.item(row, 4)
        if status_item:
            status_item.setText(status_text)
            status_item.setData(Qt.UserRole, progress if progress > 0 else None)

    def update_result(self, row, result):
        # type: (int, ConversionResult) -> None
        if row >= self.rowCount():
            return
        entry = self._file_entries[row]
        if result.success:
            if result.skipped:
                entry.status = FileStatus.SKIPPED
                entry.status_text = "已跳过 ({})".format(result.skip_reason)
            else:
                entry.status = FileStatus.COMPLETED
                entry.status_text = "成功 - 已转换"
        else:
            entry.status = FileStatus.FAILED
            entry.status_text = "失败: {}".format(result.error_message or "未知错误")
        entry.progress = 100 if result.success else 0
        self._update_row(row, entry)

    def remove_selected(self):
        # type: () -> None
        selected = self.selectionModel().selectedRows()
        rows = sorted([idx.row() for idx in selected], reverse=True)
        for row in rows:
            if 0 <= row < len(self._file_entries):
                del self._file_entries[row]
            self.removeRow(row)
        self._renumber_rows()
        self.count_changed.emit(self.rowCount())

    def clear_all(self):
        # type: () -> None
        self.setRowCount(0)
        self._file_entries = []
        self.count_changed.emit(0)

    def _renumber_rows(self):
        # type: () -> None
        for i in range(self.rowCount()):
            item = self.item(i, 0)
            if item:
                item.setText(str(i + 1))

    def get_file_entries(self):
        # type: () -> List[FileEntry]
        return list(self._file_entries)

    def get_file_paths(self):
        # type: () -> List[str]
        return [e.path for e in self._file_entries]

    def reset_statuses(self):
        # type: () -> None
        for i, entry in enumerate(self._file_entries):
            if entry.status in (FileStatus.COMPLETED, FileStatus.FAILED,
                                FileStatus.SKIPPED, FileStatus.CANCELLED):
                entry.status = FileStatus.READY
                entry.status_text = "就绪"
                entry.progress = 0
                entry.error_message = None
                self._update_row(i, entry)

    @staticmethod
    def _format_size(size_bytes):
        # type: (int) -> str
        if size_bytes < 1024:
            return "{} B".format(size_bytes)
        elif size_bytes < 1024 * 1024:
            return "{:.1f} KB".format(size_bytes / 1024)
        elif size_bytes < 1024 * 1024 * 1024:
            return "{:.1f} MB".format(size_bytes / (1024 * 1024))
        else:
            return "{:.1f} GB".format(size_bytes / (1024 * 1024 * 1024))


class FileListToolbar(QWidget):
    add_files_clicked = pyqtSignal()
    add_folder_clicked = pyqtSignal()
    remove_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()

    def __init__(self, parent=None):
        # type: (Optional[QWidget]) -> None
        super(FileListToolbar, self).__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        self.add_files_btn = QPushButton("添加文件")
        self.add_files_btn.clicked.connect(self.add_files_clicked.emit)
        layout.addWidget(self.add_files_btn)

        self.add_folder_btn = QPushButton("添加文件夹")
        self.add_folder_btn.clicked.connect(self.add_folder_clicked.emit)
        layout.addWidget(self.add_folder_btn)

        self.remove_btn = QPushButton("移除")
        self.remove_btn.clicked.connect(self.remove_clicked.emit)
        layout.addWidget(self.remove_btn)

        self.clear_btn = QPushButton("清空全部")
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        layout.addWidget(self.clear_btn)

        layout.addStretch()
