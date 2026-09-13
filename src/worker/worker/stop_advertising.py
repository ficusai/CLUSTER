"""stop_advertising.py — stop_advertising() for ClusterWorker."""
from common.loghub import LogHub


class StopAdvertisingMixin:
    @LogHub.log_call("WORKER")
    def stop_advertising(self):
        if hasattr(self, "mdns"):
            self.mdns.stop()
