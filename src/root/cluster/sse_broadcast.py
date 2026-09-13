"""sse_broadcast.py — _sse_broadcast(event, data) for ClusterRoot."""
import json
import threading
from common.loghub import LogHub


class SseBroadcastMixin:
    @LogHub.log_call("ROOT")
    def _sse_broadcast(self, event, data):
        msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        with self.sse_lock:
            dead = []
            for w in self.sse_clients:
                try:
                    w.write(msg.encode("utf-8"))
                    w.flush()
                except Exception:
                    dead.append(w)
            for w in dead:
                try:
                    self.sse_clients.remove(w)
                except ValueError:
                    pass
