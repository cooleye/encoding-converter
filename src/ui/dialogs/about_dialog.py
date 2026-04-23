from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton
)
from PyQt5.QtCore import Qt


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        # type: (object) -> None
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle("关于编码转换器")
        self.setFixedSize(400, 280)
        self._setup_ui()

    def _setup_ui(self):
        # type: () -> None
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("编码转换器")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2196F3;")
        layout.addWidget(title)

        version = QLabel("版本 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("font-size: 13px; color: #666;")
        layout.addWidget(version)

        desc = QLabel(
            "一款跨平台的桌面工具，用于批量\n"
            "文本文件编码转换。\n\n"
            "支持 40 多种编码，包括 Unicode、\n"
            "中文 (GBK, GB2312, GB18030, Big5)、\n"
            "日文、韩文等。"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #444; line-height: 1.5;")
        layout.addWidget(desc)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
