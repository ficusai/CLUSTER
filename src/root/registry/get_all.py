"""get_all.py — get_all() for WorkerRegistry."""
from common.loghub import LogHub


class GetAllMixin:
    @LogHub.log_call("ROOT")
    def get_all(self):
        with self.lock:
            return {k: {kk: vv for kk, vv in v.items() if kk != "conn"}
                    for k, v in self.workers.items()}
