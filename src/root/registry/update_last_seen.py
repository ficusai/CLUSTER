"""update_last_seen.py — update_last_seen(worker_id) for WorkerRegistry."""
import time
from common.loghub import LogHub


class UpdateLastSeenMixin:
    @LogHub.log_call("ROOT")
    def update_last_seen(self, worker_id):
        with self.lock:
            if worker_id in self.workers:
                self.workers[worker_id]["last_seen"] = time.time()
