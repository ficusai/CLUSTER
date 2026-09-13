"""set_status_bar.py — set_status_bar() for MainWindow."""
from common.loghub import LogHub


class SetStatusBarMixin:
    @LogHub.log_call("GUI")
    def set_status_bar(self, text):
        self._status_bar_label.setText(text)
