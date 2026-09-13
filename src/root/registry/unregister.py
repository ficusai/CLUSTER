"""unregister.py — unregister(worker_id) for WorkerRegistry."""
from common.loghub import LogHub


class UnregisterMixin:
    @LogHub.log_call("ROOT")
    def unregister(self, worker_id):
        with self.lock:
            self.workers.pop(worker_id, None)
