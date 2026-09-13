"""setup_connections.py — _setup_connections() for MainWindow."""
from PySide6.QtWidgets import QApplication
from common.loghub import LogHub


class SetupConnectionsMixin:
    @LogHub.log_call("GUI")
    def _setup_connections(self):
        self._btn_tray.clicked.connect(self.hide)
        self._tray.show_window_requested.connect(self.show_window)
        self._tray.quit_requested.connect(self._on_quit)
