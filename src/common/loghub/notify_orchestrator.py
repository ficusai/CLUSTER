"""notify_orchestrator.py — notify_orchestrator(message, urgency) for LogHub."""


class NotifyOrchestratorMixin:
    def notify_orchestrator(self, message, urgency="normal"):
        """Best-effort notification to the root device (or local fallback)."""
        try:
            from common.progress_ui import send_notification
            send_notification("Cluster", message, urgency=urgency)
        except Exception:
            pass
