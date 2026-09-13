"""contains.py — contains(worker_id) for WorkerRegistry."""
from common.loghub import LogHub


class ContainsMixin:
    @LogHub.log_call("ROOT")
    def contains(self, worker_id):
        with self.lock:
            return worker_id in self.workers
