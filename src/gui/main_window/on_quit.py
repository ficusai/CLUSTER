"""on_quit.py — _on_quit() for MainWindow."""
from PySide6.QtWidgets import QApplication
from common.loghub import LogHub


class OnQuitMixin:
    @LogHub.log_call("GUI")
    def _on_quit(self):
        QApplication.instance().quit()
