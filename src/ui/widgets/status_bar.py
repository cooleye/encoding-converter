from PyQt5.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt


class AppStatusBar(QStatusBar):

    def __init__(self, parent=None):
        # type: (object) -> None
        super(AppStatusBar, self).__init__(parent)

        self._file_count_label = QLabel("Files: 0")
        self._total_size_label = QLabel("Total: 0 B")
        self._source_label = QLabel("Source: -")
        self._target_label = QLabel("Target: UTF-8")

        for label in [self._file_count_label, self._total_size_label,
                      self._source_label, self._target_label]:
            label.setStyleSheet("padding: 0 8px; font-size: 12px;")
            self.addPermanentWidget(label)

        self.showMessage("就绪")

    def update_stats(self, file_count, total_size, source_summary="", target_encoding=""):
        # type: (int, int, str, str) -> None
        self._file_count_label.setText("文件数: {}".format(file_count))
        self._total_size_label.setText("总大小: {}".format(self._format_size(total_size)))
        if source_summary:
            self._source_label.setText("Source: {}".format(source_summary))
        if target_encoding:
            self._target_label.setText("目标编码: {}".format(target_encoding.upper()))

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
