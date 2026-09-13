"""record_result.py — record_result(task_id, worker_id, result) for TaskManager."""
from common.loghub import LogHub


class RecordResultMixin:
    @LogHub.log_call("ROOT")
    def record_result(self, task_id, worker_id, result):
        with self.lock:
            if task_id in self.pending:
                self.pending[task_id]["responses"][worker_id] = result
                if len(self.pending[task_id]["responses"]) >= len(self.pending[task_id]["worker_ids"]):
                    self.results[task_id] = self.pending.pop(task_id)
