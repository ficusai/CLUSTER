"""close_event.py — closeEvent() for MainWindow."""
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QSystemTrayIcon
from common.loghub import LogHub


class CloseEventMixin:
    @LogHub.log_call("GUI")
    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.hide()
        self._tray.show_message(
            "CLUSTER Control Plane",
            "Still running in system tray. Double-click to restore.",
            QSystemTrayIcon.MessageIcon.Information,
        )
