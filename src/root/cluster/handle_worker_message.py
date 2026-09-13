"""handle_worker_message.py — _handle_worker_message(msg, worker_id) for ClusterRoot."""
from common.loghub import LogHub
from common.protocol import MSG_PING, MSG_PONG, MSG_TASK_RESULT, MSG_DISCONNECT, MSG_REGISTER_ACK


class HandleWorkerMessageMixin:
    @LogHub.log_call("ROOT")
    def _handle_worker_message(self, msg, worker_id):
        msg_type = msg.get("type")
        if msg_type == MSG_PING:
            self.registry.update_last_seen(worker_id)
        elif msg_type == MSG_PONG:
            pass
        elif msg_type == MSG_TASK_RESULT:
            task_id = msg.get("id", "")
            self.tasks.record_result(task_id, worker_id, msg)
        elif msg_type == MSG_DISCONNECT:
            self.registry.unregister(worker_id)
