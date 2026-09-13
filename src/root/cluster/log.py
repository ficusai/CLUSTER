"""log.py — log(msg) for ClusterRoot."""
from common.loghub import LogHub


class LogMixin:
    @LogHub.log_call("ROOT")
    def log(self, msg):
        print(f"[root] {msg}")
        if self.ui:
            self.ui.add_event(msg)
