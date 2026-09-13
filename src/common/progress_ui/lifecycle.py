"""lifecycle.py — start/stop/_refresh_loop/_update_display for ProgressUI."""
import time
from .notifier import send_notification
from ..loghub import LogHub


class LifecycleMixin:
    def start(self):
        self._running = True
        self._live = Live(self._render(), refresh_per_second=4, screen=True)
        self._live.start()
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()
        send_notification(
            "AI Cluster Auto-Connect",
            f"Starting in {self.mode.upper()} mode...",
        )

    def stop(self):
        self._running = False
        if self._live:
            try:
                self._live.stop()
            except Exception:
                LogHub().exception("UI", "Failed to stop live display")

    def _refresh_loop(self):
        while self._running:
            time.sleep(0.5)
            self._update_display()

    def _update_display(self):
        if self._live and self._running:
            try:
                self._live.update(self._render())
            except Exception:
                LogHub().exception("UI", "Failed to update live display")
