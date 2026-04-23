from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QPlainTextEdit, QSplitter, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt

from src.core.converter import EncodingConverter
from src.core.models import ConversionConfig, ErrorStrategy
from src.utils.encoding_list import get_display_name


class PreviewDialog(QDialog):

    def __init__(self, file_path, source_enc, target_enc, error_strategy, config, parent=None):
        # type: (str, str, str, ErrorStrategy, ConversionConfig, object) -> None
        super(PreviewDialog, self).__init__(parent)
        self.file_path = file_path
        self.source_enc = source_enc
        self.target_enc = target_enc
        self.config = config
        self.setMinimumSize(800, 500)
        self._setup_ui()
        self._load_preview()

    def _setup_ui(self):
        # type: () -> None
        self.setWindowTitle("预览: {}".format(self.file_path))

        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        src_label = QLabel("源编码: {}".format(get_display_name(self.source_enc)))
        src_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(src_label)

        arrow = QLabel("-->")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        header_layout.addWidget(arrow)

        tgt_label = QLabel("目标编码: {}".format(get_display_name(self.target_enc)))
        tgt_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(tgt_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Side-by-side editors
        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_title = QLabel("原始内容 ({})".format(get_display_name(self.source_enc)))
        left_title.setAlignment(Qt.AlignCenter)
        left_title.setStyleSheet("font-weight: bold; padding: 4px; background: #f0f0f0; border-radius: 4px;")
        left_layout.addWidget(left_title)
        self.original_edit = QPlainTextEdit()
        self.original_edit.setReadOnly(True)
        self.original_edit.setFontFamily("Menlo, Consolas, monospace")
        self.original_edit.setStyleSheet("font-size: 13px; line-height: 1.4;")
        left_layout.addWidget(self.original_edit)
        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_title = QLabel("转换后 ({})".format(get_display_name(self.target_enc)))
        right_title.setAlignment(Qt.AlignCenter)
        right_title.setStyleSheet("font-weight: bold; padding: 4px; background: #E3F2FD; border-radius: 4px;")
        right_layout.addWidget(right_title)
        self.converted_edit = QPlainTextEdit()
        self.converted_edit.setReadOnly(True)
        self.converted_edit.setFontFamily("Menlo, Consolas, monospace")
        self.converted_edit.setStyleSheet("font-size: 13px; line-height: 1.4;")
        right_layout.addWidget(self.converted_edit)
        splitter.addWidget(right_widget)

        splitter.setSizes([400, 400])
        layout.addWidget(splitter, 1)

        # Stats
        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 12px; color: #666; padding: 4px;")
        layout.addWidget(self.stats_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_preview(self):
        # type: () -> None
        converter = EncodingConverter(self.config)
        original_lines, converted_lines, problem_count = converter.preview(
            self.file_path, self.source_enc
        )

        self.original_edit.setPlainText("".join(original_lines))
        self.converted_edit.setPlainText("".join(converted_lines))

        total_lines = len(original_lines)
        stats_text = "显示行数: {}".format(total_lines)
        if problem_count > 0:
            stats_text += "  |  问题行数: {} (包含无效字符)".format(problem_count)
            self.stats_label.setStyleSheet(
                "font-size: 12px; color: #F44336; padding: 4px; font-weight: bold;"
            )
        else:
            stats_text += "  |  未检测到问题"
            self.stats_label.setStyleSheet(
                "font-size: 12px; color: #4CAF50; padding: 4px;"
            )
        self.stats_label.setText(stats_text)
