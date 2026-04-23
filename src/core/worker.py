from PyQt5.QtCore import QThread, pyqtSignal
from typing import List, Optional

from .converter import EncodingConverter
from .models import ConversionConfig, ConversionResult, FileEntry


class ConversionWorker(QThread):
    file_progress = pyqtSignal(int, int, str)
    file_completed = pyqtSignal(int, object)
    overall_progress = pyqtSignal(int, int)
    all_done = pyqtSignal(list, str)
    error = pyqtSignal(str)

    def __init__(self, config, file_entries, parent=None):
        # type: (ConversionConfig, List[FileEntry], object) -> None
        super(ConversionWorker, self).__init__(parent)
        self.config = config
        self.file_entries = file_entries
        self.converter = EncodingConverter(config)
        self._cancelled = False

    def run(self):
        # type: () -> None
        results = []
        total = len(self.file_entries)

        for i, entry in enumerate(self.file_entries):
            if self._cancelled:
                for j in range(i, total):
                    self.file_progress.emit(j, 0, "Cancelled")
                break

            self.file_progress.emit(i, 0, "Reading...")

            def progress_cb(pct, _i=i):
                # type: (int, int) -> None
                labels = [
                    (0, "Reading..."),
                    (20, "Decoding..."),
                    (60, "Encoding..."),
                    (80, "Writing..."),
                    (100, "Done"),
                ]
                label = "Processing..."
                for threshold, lbl in labels:
                    if pct >= threshold:
                        label = lbl
                self.file_progress.emit(_i, pct, label)

            result = self.converter.convert_file(
                entry.path,
                detected_encoding=entry.detected_encoding,
                progress_callback=progress_cb,
            )

            results.append(result)
            self.file_completed.emit(i, result)
            self.overall_progress.emit(i + 1, total)

        if not self._cancelled:
            session_dir = self.converter.get_session_dir() if self.converter._session_dir else ""
            self.all_done.emit(results, session_dir)

    def cancel(self):
        # type: () -> None
        self._cancelled = True
        self.converter.cancel()
