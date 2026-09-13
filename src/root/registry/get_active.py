"""get_active.py — get_active() for WorkerRegistry."""
import time
from common.loghub import LogHub

HEARTBEAT_TIMEOUT = 60


class GetActiveMixin:
    @LogHub.log_call("ROOT")
    def get_active(self):
        with self.lock:
            now = time.time()
            return {k: v for k, v in self.workers.items()
                    if v.get("status") == "active" and (now - v.get("last_seen", 0)) < HEARTBEAT_TIMEOUT}
