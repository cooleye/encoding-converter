import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QComboBox, QGroupBox, QFormLayout,
    QLineEdit, QToolButton, QFileDialog
)
from PyQt5.QtCore import Qt

from src.utils.config import AppConfig
from src.core.models import get_default_output_dir


class SettingsDialog(QDialog):

    def __init__(self, app_config, parent=None):
        # type: (AppConfig, object) -> None
        super(SettingsDialog, self).__init__(parent)
        self._app_config = app_config
        self.setWindowTitle("首选项")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        # type: () -> None
        layout = QVBoxLayout(self)

        # General
        general_group = QGroupBox("常规")
        general_layout = QFormLayout(general_group)

        self.auto_detect_check = QCheckBox("默认自动检测源编码")
        general_layout.addRow(self.auto_detect_check)

        layout.addWidget(general_group)

        # Output directory
        output_group = QGroupBox("导出目录")
        output_layout = QHBoxLayout()

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        output_layout.addWidget(self.output_dir_edit, 1)

        self.browse_btn = QToolButton()
        self.browse_btn.setText("浏览...")
        self.browse_btn.clicked.connect(self._on_browse_output_dir)
        output_layout.addWidget(self.browse_btn)

        self.reset_dir_btn = QToolButton()
        self.reset_dir_btn.setText("重置默认")
        self.reset_dir_btn.clicked.connect(self._on_reset_output_dir)
        output_layout.addWidget(self.reset_dir_btn)

        output_form = QFormLayout(output_group)
        output_form.addRow("默认导出路径:", output_layout)

        layout.addWidget(output_group)

        # Default error strategy
        error_group = QGroupBox("默认错误处理")
        error_layout = QFormLayout(error_group)

        self.error_combo = QComboBox()
        self.error_combo.addItem("替换无效字符", "replace")
        self.error_combo.addItem("跳过无效字符", "ignore")
        self.error_combo.addItem("遇到错误停止", "strict")
        self.error_combo.addItem("反斜杠转义", "backslashreplace")
        error_layout.addRow("策略:", self.error_combo)

        layout.addWidget(error_group)

        # BOM
        bom_group = QGroupBox("BOM (字节顺序标记)")
        bom_layout = QFormLayout(bom_group)

        self.strip_bom_check = QCheckBox("默认从源文件中去除 BOM")
        bom_layout.addRow(self.strip_bom_check)

        self.add_bom_check = QCheckBox("默认向目标文件添加 BOM")
        bom_layout.addRow(self.add_bom_check)

        layout.addWidget(bom_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setObjectName("convertBtn")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_browse_output_dir(self):
        # type: () -> None
        current = self.output_dir_edit.text()
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择默认导出目录", current
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def _on_reset_output_dir(self):
        # type: () -> None
        default_dir = get_default_output_dir()
        self.output_dir_edit.setText(default_dir)

    def _load_settings(self):
        # type: () -> None
        self.auto_detect_check.setChecked(
            self._app_config.get("auto_detect") is True or
            self._app_config.get("auto_detect") == "true"
        )
        self.strip_bom_check.setChecked(
            self._app_config.get("strip_bom") is True or
            self._app_config.get("strip_bom") == "true"
        )
        self.add_bom_check.setChecked(
            self._app_config.get("add_bom") is True or
            self._app_config.get("add_bom") == "true"
        )

        error_strategy = self._app_config.get("error_strategy") or "replace"
        idx = self.error_combo.findData(error_strategy)
        if idx >= 0:
            self.error_combo.setCurrentIndex(idx)

        saved_output_dir = self._app_config.get("output_dir")
        if saved_output_dir:
            self.output_dir_edit.setText(str(saved_output_dir))
        else:
            self.output_dir_edit.setText(get_default_output_dir())

    def _save_settings(self):
        # type: () -> None
        self._app_config.set("auto_detect", self.auto_detect_check.isChecked())
        self._app_config.set("strip_bom", self.strip_bom_check.isChecked())
        self._app_config.set("add_bom", self.add_bom_check.isChecked())
        self._app_config.set("error_strategy", self.error_combo.currentData() or "replace")

        output_dir = self.output_dir_edit.text().strip()
        default_dir = get_default_output_dir()
        if output_dir == default_dir:
            self._app_config.set("output_dir", "")
        else:
            self._app_config.set("output_dir", output_dir)

        self.accept()

    def _reset_defaults(self):
        # type: () -> None
        self.auto_detect_check.setChecked(True)
        self.strip_bom_check.setChecked(False)
        self.add_bom_check.setChecked(False)
        self.error_combo.setCurrentIndex(0)
        self.output_dir_edit.setText(get_default_output_dir())
