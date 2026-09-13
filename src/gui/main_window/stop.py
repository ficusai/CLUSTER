"""stop.py — stop() for MainWindow."""
from common.loghub import LogHub


class StopMixin:
    @LogHub.log_call("GUI")
    def stop(self):
        self._tray.stop()
