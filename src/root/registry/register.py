"""register.py — register(worker_id, info, conn) for WorkerRegistry."""
import time
from common.loghub import LogHub


class RegisterMixin:
    @LogHub.log_call("ROOT")
    def register(self, worker_id, info, conn):
        with self.lock:
            self.workers[worker_id] = {**info, "conn": conn, "last_seen": time.time(), "status": "active"}
