"""sse_broadcast.py — sse_broadcast(root, event, data) module-level function."""
import json
import threading
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def sse_broadcast(root, event, data):
    msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
    with root.sse_lock:
        dead = []
        for w in root.sse_clients:
            try:
                w.write(msg.encode("utf-8"))
                w.flush()
            except Exception:
                dead.append(w)
        for w in dead:
            try:
                root.sse_clients.remove(w)
            except ValueError:
                pass
