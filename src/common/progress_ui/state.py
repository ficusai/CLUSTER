"""state.py — state mutation methods for ProgressUI."""
from datetime import datetime
from .notifier import send_notification


class StateMixin:
    def set_service(self, name, status, detail=""):
        with self._lock:
            self._state["services"][name] = {"status": status, "detail": detail}

    def add_event(self, message, notify=False):
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self._state["events"].append((ts, message))
            if len(self._state["events"]) > 100:
                self._state["events"].pop(0)
        if notify:
            send_notification("Cluster", message)

    def update_worker(self, wid, info):
        with self._lock:
            self._state["workers"][wid] = info

    def remove_worker(self, wid):
        with self._lock:
            self._state["workers"].pop(wid, None)

    def set_connection(self, status, root_ip=None, registered=False):
        with self._lock:
            self._state["connection_status"] = status
            if root_ip is not None:
                self._state["root_ip"] = root_ip
            self._state["registered"] = registered

    _ALLOWED_SYSTEM_KEYS = {
        "platform", "hostname", "cpu_cores", "ram_total", "ram_available",
        "http_port", "local_ip", "ai_mode", "version",
    }

    def set_system_info(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                if k in self._ALLOWED_SYSTEM_KEYS:
                    self._state[k] = v

    def notify_once(self, event_key, title, message, urgency="normal"):
        if event_key not in self._notified_events:
            self._notified_events.add(event_key)
            send_notification(title, message, urgency)
