"""init_main_window.py — __init__ for MainWindow."""
from common.loghub import LogHub
from .dark_theme_qss import DARK_THEME_QSS


class InitMainWindowMixin:
    @LogHub.log_call("GUI")
    def __init__(self, mode="root"):
        super().__init__()
        self._mode = mode
        from ..system_tray import SystemTray
        self._tray = SystemTray(self)
        self.setStyleSheet(DARK_THEME_QSS)
        self._setup_ui()
        self._setup_connections()
