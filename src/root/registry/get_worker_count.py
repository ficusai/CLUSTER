"""get_worker_count.py — get_worker_count() for WorkerRegistry."""
from common.loghub import LogHub


class GetWorkerCountMixin:
    @LogHub.log_call("ROOT")
    def get_worker_count(self):
        with self.lock:
            return len(self.workers)
