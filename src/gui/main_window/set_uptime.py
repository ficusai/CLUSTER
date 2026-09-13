"""set_uptime.py — set_uptime() for MainWindow."""
from common.loghub import LogHub


class SetUptimeMixin:
    @LogHub.log_call("GUI")
    def set_uptime(self, uptime_str):
        pass
