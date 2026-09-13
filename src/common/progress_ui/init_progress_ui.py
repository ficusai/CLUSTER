"""init_progress_ui.py — __init__ for ProgressUI."""
import threading
import time
from datetime import datetime
from .constants import STATUS_ICONS, _COLORS_SERVICES as COLORS_SERVICES
from .notifier import send_notification


class InitProgressUIMixin:
    def __init__(self, mode="root"):
        self.mode = mode
        self._state = {
            "services": {},
            "events": [],
            "workers": {},
            "connection_status": "idle",
            "root_ip": None,
            "registered": False,
            "platform": "",
            "hostname": "",
            "cpu_cores": 0,
            "ram_total": 0,
            "ram_available": 0,
            "http_port": None,
            "local_ip": None,
            "ai_mode": False,
            "version": "",
        }
        self._lock = threading.Lock()
        self._running = False
        self._live = None
        self._refresh_thread = None
        self._start_time = time.time()
        self._notified_events = set()
