"""log.py — log(msg, notify) for ClusterWorker."""
from common.loghub import LogHub
from common.progress_ui import send_notification


class LogMixin:
    @LogHub.log_call("WORKER")
    def log(self, msg, notify=False):
        LogHub().info("WORKER", msg)
        print(f"[worker] {msg}")
        if self.ui:
            self.ui.add_event(msg)
        if notify:
            send_notification("Cluster Worker", msg)
