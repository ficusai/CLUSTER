"""notify.py — notify(title, message, urgency) for ClusterWorker."""
from common.loghub import LogHub
from common.progress_ui import send_notification


class NotifyMixin:
    @LogHub.log_call("WORKER")
    def notify(self, title, message, urgency="normal"):
        send_notification(title, message, urgency)
        if self.ui:
            self.ui.add_event(f"{title}: {message}", notify=False)
