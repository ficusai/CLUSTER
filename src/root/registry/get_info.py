"""get_info.py — get_info(worker_id) for WorkerRegistry."""
from common.loghub import LogHub


class GetInfoMixin:
    @LogHub.log_call("ROOT")
    def get_info(self, worker_id):
        with self.lock:
            w = self.workers.get(worker_id)
            return w.get("hostname", worker_id) if w else worker_id
