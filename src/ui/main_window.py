import os
import subprocess
import sys
from typing import Optional, List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QComboBox, QFileDialog, QSplitter,
    QGroupBox, QMessageBox, QProgressBar, QMenu, QAction, QMenuBar,
    QLineEdit, QToolButton
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon

from src.core.models import ConversionConfig, ConversionResult, FileEntry, FileStatus, ErrorStrategy, get_default_output_dir
from src.core.worker import ConversionWorker
from src.ui.widgets.encoding_combo import EncodingComboBox
from src.ui.widgets.file_list_table import FileListTable, FileListToolbar
from src.ui.widgets.status_bar import AppStatusBar
from src.ui.dialogs.preview_dialog import PreviewDialog
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.about_dialog import AboutDialog
from src.utils.config import AppConfig
from src.utils.encoding_list import get_display_name


class MainWindow(QMainWindow):

    def __init__(self):
        # type: () -> None
        super(MainWindow, self).__init__()
        self.setWindowTitle("编码转换器")
        self.setMinimumSize(800, 550)
        self.resize(950, 650)

        self._app_config = AppConfig()
        self._worker = None  # type: Optional[ConversionWorker]
        self._converting = False
        self._last_session_dir = ""  # type: str

        self._setup_menubar()
        self._setup_central_widget()
        self._setup_statusbar()
        self._connect_signals()
        self._restore_geometry()
        self._update_status_stats()

    def _setup_menubar(self):
        # type: () -> None
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&文件")
        add_files_action = QAction("添加文件...", self)
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self._on_add_files)
        file_menu.addAction(add_files_action)

        add_folder_action = QAction("添加文件夹...", self)
        add_folder_action.setShortcut("Ctrl+Shift+O")
        add_folder_action.triggered.connect(self._on_add_folder)
        file_menu.addAction(add_folder_action)

        file_menu.addSeparator()

        clear_action = QAction("清空全部", self)
        clear_action.triggered.connect(self._on_clear_all)
        file_menu.addAction(clear_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("&设置")
        prefs_action = QAction("首选项...", self)
        prefs_action.setShortcut("Ctrl+,")
        prefs_action.triggered.connect(self._show_settings)
        settings_menu.addAction(prefs_action)

        help_menu = menubar.addMenu("&帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_central_widget(self):
        # type: () -> None
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Encoding selection row
        enc_group = QGroupBox("编码选择")
        enc_layout = QHBoxLayout(enc_group)
        enc_layout.setSpacing(20)

        self.source_combo = EncodingComboBox("源编码:", mode="source")
        enc_layout.addWidget(self.source_combo, 1)

        arrow_label = QLabel("-->")
        arrow_label.setAlignment(Qt.AlignCenter)
        arrow_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        enc_layout.addWidget(arrow_label)

        self.target_combo = EncodingComboBox("目标编码:", mode="target")
        enc_layout.addWidget(self.target_combo, 1)

        main_layout.addWidget(enc_group)

        # File list
        file_group = QGroupBox("文件列表")
        file_layout = QVBoxLayout(file_group)

        self.file_toolbar = FileListToolbar()
        file_layout.addWidget(self.file_toolbar)

        self.file_table = FileListTable()
        file_layout.addWidget(self.file_table, 1)

        main_layout.addWidget(file_group, 1)

        # Output directory
        output_group = QGroupBox("导出目录")
        output_layout = QHBoxLayout(output_group)

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.setPlaceholderText("默认: 软件目录/导出目录")
        default_dir = get_default_output_dir()
        self.output_dir_edit.setText(self._app_config.get("output_dir") or default_dir)
        output_layout.addWidget(self.output_dir_edit, 1)

        self.browse_btn = QToolButton()
        self.browse_btn.setText("浏览...")
        self.browse_btn.clicked.connect(self._on_browse_output_dir)
        output_layout.addWidget(self.browse_btn)

        self.reset_dir_btn = QToolButton()
        self.reset_dir_btn.setText("重置")
        self.reset_dir_btn.clicked.connect(self._on_reset_output_dir)
        output_layout.addWidget(self.reset_dir_btn)

        main_layout.addWidget(output_group)

        # Options
        options_group = QGroupBox("选项")
        options_layout = QHBoxLayout(options_group)

        self.strip_bom_check = QCheckBox("去除 BOM")
        options_layout.addWidget(self.strip_bom_check)

        self.add_bom_check = QCheckBox("添加 BOM")
        options_layout.addWidget(self.add_bom_check)

        options_layout.addSpacing(20)

        error_label = QLabel("错误处理:")
        options_layout.addWidget(error_label)

        self.error_combo = QComboBox()
        self.error_combo.addItem("替换无效字符", "replace")
        self.error_combo.addItem("跳过无效字符", "ignore")
        self.error_combo.addItem("遇到错误停止", "strict")
        self.error_combo.addItem("反斜杠转义", "backslashreplace")
        self.error_combo.addItem("保留为代理字符", "surrogateescape")
        options_layout.addWidget(self.error_combo)

        options_layout.addStretch()

        main_layout.addWidget(options_group)

        # Action buttons
        action_layout = QHBoxLayout()

        self.preview_btn = QPushButton("预览")
        self.preview_btn.setObjectName("previewBtn")
        self.preview_btn.setMinimumWidth(100)
        action_layout.addWidget(self.preview_btn)

        action_layout.addStretch()

        self.overall_progress = QProgressBar()
        self.overall_progress.setObjectName("overallProgress")
        self.overall_progress.setVisible(False)
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setFormat("%v / %m 个文件")
        self.overall_progress.setFixedHeight(24)
        action_layout.addWidget(self.overall_progress)

        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setObjectName("convertBtn")
        self.convert_btn.setMinimumWidth(140)
        self.convert_btn.setDefault(True)
        action_layout.addWidget(self.convert_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        action_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(action_layout)

    def _setup_statusbar(self):
        # type: () -> None
        self.status_bar = AppStatusBar()
        self.setStatusBar(self.status_bar)

    def _connect_signals(self):
        # type: () -> None
        self.file_toolbar.add_files_clicked.connect(self._on_add_files)
        self.file_toolbar.add_folder_clicked.connect(self._on_add_folder)
        self.file_toolbar.remove_clicked.connect(self.file_table.remove_selected)
        self.file_toolbar.clear_clicked.connect(self._on_clear_all)
        self.file_table.count_changed.connect(self._on_file_count_changed)

        self.convert_btn.clicked.connect(self._on_convert)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.preview_btn.clicked.connect(self._on_preview)

        self.source_combo.encoding_changed.connect(
            lambda: self._update_status_stats()
        )
        self.target_combo.encoding_changed.connect(
            lambda: self._update_status_stats()
        )

    def _restore_geometry(self):
        # type: () -> None
        self._app_config.restore_geometry(self)

    def _on_browse_output_dir(self):
        # type: () -> None
        current = self.output_dir_edit.text()
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择导出目录", current
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self._app_config.set("output_dir", dir_path)

    def _on_reset_output_dir(self):
        # type: () -> None
        default_dir = get_default_output_dir()
        self.output_dir_edit.setText(default_dir)
        self._app_config.set("output_dir", "")

    def _on_add_files(self):
        # type: () -> None
        files, _ = QFileDialog.getOpenFileNames(
            self, "添加文件", "",
            "文本文件 (*.txt *.csv *.log *.xml *.json *.html *.htm *.py *.js *.css *.md *.ini *.cfg *.yml *.yaml *.properties *.nc *.c *.cpp *.h *.hpp *.java *.rb *.php *.go *.rs *.ts *.tsx *.jsx *.vue *.sql *.sh *.bat *.ps1 *.dockerfile *.makefile *.cmake *.toml *.conf *.env *.gitignore *.editorconfig *.srt *.vtt *.ass *.sub *.rst *.tex *.bib *.lhs *.hs *.ml *.lisp *.clj *.scala *.kt *.swift *.dart *.lua *.pl *.r *.m *.mm *.asm *.s *.v *.vhd *.tcl *.proto *.gradle *.cs *.vb *.fs *.xaml *.resx *.plist *.svg *.xhtml *.jsp *.asp *.aspx);;所有文件 (*)")
        if files:
            self.file_table.add_files(files)

    def _on_add_folder(self):
        # type: () -> None
        folder = QFileDialog.getExistingDirectory(self, "添加文件夹")
        if folder:
            self.file_table.add_folder(folder)

    def _on_clear_all(self):
        # type: () -> None
        if self.file_table.rowCount() == 0:
            return
        reply = QMessageBox.question(
            self, "清空全部",
            "确定要从列表中移除所有文件吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.file_table.clear_all()

    def _on_file_count_changed(self, count):
        # type: (int) -> None
        self._update_status_stats()
        self.convert_btn.setEnabled(count > 0 and not self._converting)

    def _update_status_stats(self):
        # type: () -> None
        entries = self.file_table.get_file_entries()
        total_size = sum(e.size for e in entries)
        encodings = set()
        for e in entries:
            if e.detected_encoding and e.detected_encoding != "unknown":
                encodings.add(e.detected_encoding)

        if len(encodings) == 0:
            source_summary = "-"
        elif len(encodings) == 1:
            source_summary = encodings.pop().upper()
        else:
            source_summary = "Mixed ({})".format(len(encodings))

        target = self.target_combo.current_encoding() or "UTF-8"
        self.status_bar.update_stats(len(entries), total_size, source_summary, target)

    def _get_config(self):
        # type: () -> ConversionConfig
        error_data = self.error_combo.currentData()
        error_strategy = ErrorStrategy.REPLACE
        for strat in ErrorStrategy:
            if strat.value == error_data:
                error_strategy = strat
                break

        output_dir = self.output_dir_edit.text().strip()

        return ConversionConfig(
            source_encoding=self.source_combo.current_encoding(),
            target_encoding=self.target_combo.current_encoding() or "utf-8",
            auto_detect=self.source_combo.is_auto_detect(),
            strip_bom=self.strip_bom_check.isChecked(),
            add_bom=self.add_bom_check.isChecked(),
            error_strategy=error_strategy,
            output_dir=output_dir,
        )

    def _on_convert(self):
        # type: () -> None
        entries = self.file_table.get_file_entries()
        if not entries:
            return

        ready_entries = [e for e in entries if e.status in (FileStatus.READY, FileStatus.FAILED, FileStatus.COMPLETED, FileStatus.SKIPPED)]
        if not ready_entries:
            QMessageBox.information(self, "没有文件", "没有准备好转换的文件。")
            return

        if not self.target_combo.current_encoding():
            QMessageBox.warning(self, "未选择目标编码", "请选择目标编码。")
            return

        self.file_table.reset_statuses()

        config = self._get_config()
        self._worker = ConversionWorker(config, entries)

        self._worker.file_progress.connect(self._on_file_progress)
        self._worker.file_completed.connect(self._on_file_completed)
        self._worker.overall_progress.connect(self._on_overall_progress)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.error.connect(self._on_worker_error)

        self._converting = True
        self.convert_btn.setEnabled(False)
        self.convert_btn.setVisible(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setVisible(True)
        self.preview_btn.setEnabled(False)
        self.overall_progress.setVisible(True)
        self.overall_progress.setMaximum(len(ready_entries))
        self.overall_progress.setValue(0)

        self.status_bar.showMessage("正在转换...")

        self._worker.start()

    def _on_cancel(self):
        # type: () -> None
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self, "取消转换",
                "确定要取消正在进行的转换吗？已完成的文件将保留更改。",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._worker.cancel()
                self.status_bar.showMessage("正在取消...")

    def _on_file_progress(self, row, progress, status_text):
        # type: (int, int, str) -> None
        self.file_table.update_progress(row, progress, status_text)

    def _on_file_completed(self, row, result):
        # type: (int, ConversionResult) -> None
        self.file_table.update_result(row, result)

    def _on_overall_progress(self, completed, total):
        # type: (int, int) -> None
        self.overall_progress.setValue(completed)
        self.overall_progress.setFormat("{} / {} 个文件".format(completed, total))

    def _on_all_done(self, results, session_dir):
        # type: (list, str) -> None
        self._finish_conversion()
        self._last_session_dir = session_dir

        success_count = sum(1 for r in results if r.success and not r.skipped)
        skip_count = sum(1 for r in results if r.skipped)
        fail_count = sum(1 for r in results if not r.success)

        msg = "转换完成！\n\n成功: {}\n跳过: {}\n失败: {}".format(
            success_count, skip_count, fail_count
        )
        if session_dir:
            msg += "\n\n导出目录: {}".format(session_dir)

        self.status_bar.showMessage(
            "完成 - 成功 {}, 跳过 {}, 失败 {}".format(success_count, skip_count, fail_count)
        )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("转换完成")
        msg_box.setText(msg)
        msg_box.setIcon(QMessageBox.Information)

        if session_dir and os.path.exists(session_dir):
            open_btn = msg_box.addButton("打开导出目录", QMessageBox.ActionRole)

        msg_box.addButton(QMessageBox.Ok)

        msg_box.exec_()

        if session_dir and os.path.exists(session_dir):
            if msg_box.clickedButton() == open_btn:
                self._open_directory(session_dir)

    def _open_directory(self, path):
        # type: (str) -> None
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])

    def _on_worker_error(self, error_msg):
        # type: (str) -> None
        self._finish_conversion()
        QMessageBox.critical(self, "错误", error_msg)

    def _finish_conversion(self):
        # type: () -> None
        self._converting = False
        self._worker = None
        self.convert_btn.setEnabled(True)
        self.convert_btn.setVisible(True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self.preview_btn.setEnabled(True)
        self.overall_progress.setVisible(False)
        self._update_status_stats()

    def _on_preview(self):
        # type: () -> None
        entries = self.file_table.get_file_entries()
        if not entries:
            QMessageBox.information(self, "预览", "请先添加文件以预览转换效果。")
            return

        selected_rows = self.file_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
        else:
            row = 0

        entry = entries[row]
        if not entry.detected_encoding or entry.detected_encoding == "unknown":
            QMessageBox.warning(
                self, "预览",
                "无法预览 - 未能检测到此文件的编码。"
            )
            return

        config = self._get_config()
        dialog = PreviewDialog(
            entry.path,
            entry.detected_encoding,
            config.target_encoding,
            config.error_strategy,
            config,
            parent=self
        )
        dialog.exec_()

    def _show_settings(self):
        # type: () -> None
        dialog = SettingsDialog(self._app_config, parent=self)
        dialog.exec_()

    def _show_about(self):
        # type: () -> None
        dialog = AboutDialog(parent=self)
        dialog.exec_()

    def closeEvent(self, event):
        # type: (object) -> None
        if self._converting and self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "转换正在进行中。确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self._worker.cancel()
            self._worker.wait(3000)

        self._app_config.save_geometry(self)
        event.accept()
