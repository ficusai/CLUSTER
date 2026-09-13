"""get_result.py — get_result(task_id) for TaskManager."""
from common.loghub import LogHub


class GetResultMixin:
    @LogHub.log_call("ROOT")
    def get_result(self, task_id):
        with self.lock:
            if task_id in self.results:
                return self.results[task_id]
            if task_id in self.pending:
                return self.pending[task_id]
        return None
