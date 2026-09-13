"""add_event.py — add_event() for MainWindow."""
from common.loghub import LogHub


class AddEventMixin:
    @LogHub.log_call("GUI")
    def add_event(self, message):
        pass
