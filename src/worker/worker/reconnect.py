"""reconnect.py — _reconnect() for ClusterWorker."""
import time
from common.loghub import LogHub


class ReconnectMixin:
    @LogHub.log_call("WORKER")
    def _reconnect(self):
        """Try to reconnect to root with exponential backoff."""
        delay = 2
        max_delay = 60
        while self.running and not self.registered:
            self._reconnect_attempts += 1
            self.log(f"Reconnection attempt {self._reconnect_attempts} in {delay}s...")
            if self._reconnect_attempts == 1:
                self.notify("Reconnecting", f"Connection lost, retrying in {delay}s...", urgency="critical")
            if self.ui:
                self.ui.set_connection("connecting", registered=False)
                self.ui.set_service("discovery", "discovering",
                                   f"attempt {self._reconnect_attempts}")
            time.sleep(delay)

            # Force rediscovery every attempt in case root IP changed or went down
            root_ip = self.discover_root(timeout=min(5, delay), force=True)

            if root_ip and self.register_with_root(root_ip):
                self._reconnect_attempts = 0
                return True

            delay = min(delay * 1.5, max_delay)
        return False
