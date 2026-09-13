"""show_window.py — show_window() for MainWindow."""
from common.loghub import LogHub


class ShowWindowMixin:
    @LogHub.log_call("GUI")
    def show_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()
