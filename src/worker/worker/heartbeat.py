"""heartbeat.py — _heartbeat() for ClusterWorker."""
from common.loghub import LogHub
from common.protocol import MSG_PING


class HeartbeatMixin:
    @LogHub.log_call("WORKER")
    def _heartbeat(self):
        try:
            self.conn.send(MSG_PING)
        except Exception:
            self.log("Heartbeat lost")
            self.notify("Heartbeat lost", f"Connection to root at {self.root_ip} lost", urgency="critical")
            self.registered = False
