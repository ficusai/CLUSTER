"""dispatch_task.py — dispatch_task(action, payload=None, worker_id=None, timeout=30) for TaskManager."""
import time
from common.loghub import LogHub
from common.protocol import MSG_TASK


class DispatchTaskMixin:
    @LogHub.log_call("ROOT")
    def dispatch_task(self, action, payload=None, worker_id=None, timeout=30):
        task_id = f"t-{int(time.time())}-{self.next_id}"
        self.next_id += 1
        payload = payload or {}

        workers = self.registry.get_active()
        if not workers:
            return None, "No active workers"

        if worker_id and worker_id in workers:
            targets = {worker_id: workers[worker_id]}
        else:
            targets = workers

        dispatched = []
        for wid, info in targets.items():
            conn = self.registry.get_connection(wid)
            if conn:
                try:
                    conn.send(MSG_TASK, id=task_id, action=action, payload=payload)
                    dispatched.append(wid)
                except Exception as e:
                    LogHub().exception("ROOT", f"Failed to send task to {wid}: {e}")

        with self.lock:
            self.pending[task_id] = {
                "action": action,
                "worker_ids": dispatched,
                "timeout": timeout,
                "started": time.time(),
                "responses": {},
            }

        return task_id, dispatched
