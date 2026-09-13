"""execute_task.py — _execute_task(msg) for ClusterWorker."""
from common.loghub import LogHub
from common.protocol import MSG_TASK_RESULT


class ExecuteTaskMixin:
    @LogHub.log_call("WORKER")
    def _execute_task(self, msg):
        task_id = msg.get("id", "")
        action = msg.get("action", "")
        payload = msg.get("payload", {})
        handler = self.task_handlers.get(action)
        if not handler:
            self.conn.send(MSG_TASK_RESULT,
                id=task_id, success=False, error=f"Unknown action: {action}")
            return
        try:
            result = handler(payload)
            self.conn.send(MSG_TASK_RESULT, id=task_id, success=True, **result)
        except Exception as e:
            self.conn.send(MSG_TASK_RESULT, id=task_id, success=False, error=str(e))
