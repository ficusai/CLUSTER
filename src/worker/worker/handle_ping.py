"""handle_ping.py — _handle_ping(payload) for ClusterWorker."""
import time
from common.loghub import LogHub


class HandlePingMixin:
    @LogHub.log_call("WORKER")
    def _handle_ping(self, payload):
        return {"pong": True, "ts": time.time()}
