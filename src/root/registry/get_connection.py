"""get_connection.py — get_connection(worker_id) for WorkerRegistry."""
from common.loghub import LogHub


class GetConnectionMixin:
    @LogHub.log_call("ROOT")
    def get_connection(self, worker_id):
        with self.lock:
            w = self.workers.get(worker_id)
            return w.get("conn") if w else None
