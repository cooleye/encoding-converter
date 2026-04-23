from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionProgressBar, QApplication, QStyle
from PyQt5.QtCore import Qt, QModelIndex


class ProgressDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        # type: (object, object, QModelIndex) -> None
        progress = index.data(Qt.UserRole)
        status = index.data(Qt.DisplayRole)

        if progress is not None and isinstance(progress, int) and progress > 0:
            progress_option = QStyleOptionProgressBar()
            progress_option.minimum = 0
            progress_option.maximum = 100
            progress_option.progress = progress
            progress_option.rect = option.rect
            progress_option.text = "{}%".format(progress) if not status else str(status)
            progress_option.textVisible = True
            progress_option.state = QStyle.State_Enabled
            QApplication.style().drawControl(
                QStyle.CE_ProgressBar, progress_option, painter
            )
        else:
            super(ProgressDelegate, self).paint(painter, option, index)
