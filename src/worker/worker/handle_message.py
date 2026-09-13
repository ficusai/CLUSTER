"""handle_message.py — _handle_message(msg) for ClusterWorker."""
import threading
from common.loghub import LogHub
from common.protocol import MSG_TASK, MSG_PING, MSG_PONG, MSG_DISCONNECT


class HandleMessageMixin:
    @LogHub.log_call("WORKER")
    def _handle_message(self, msg):
        msg_type = msg.get("type")
        if msg_type == MSG_TASK:
            threading.Thread(target=self._execute_task, args=(msg,), daemon=True).start()
        elif msg_type == MSG_PING:
            self.conn.send(MSG_PONG)
        elif msg_type == MSG_DISCONNECT:
            self.registered = False
