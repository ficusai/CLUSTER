"""init_loghub.py — __new__ and __init__ for LogHub."""
import os
import sys
import threading
import atexit
from .log_writer import LogWriter


class InitLogHubMixin:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_dir=None):
        if self._initialized:
            return
        self._initialized = True

        if log_dir is None:
            try:
                p = os.path.dirname(os.path.abspath(__file__))
                for _ in range(3):
                    parent = os.path.dirname(p)
                    if parent == p:
                        break
                    p = parent
                if os.path.isfile(os.path.join(p, "cluster.py")):
                    log_dir = os.path.join(p, "logs")
                else:
                    log_dir = os.path.join(os.getcwd(), "logs")
            except Exception:
                log_dir = os.path.join(os.getcwd(), "logs")

        self._log_dir = log_dir
        os.makedirs(self._log_dir, exist_ok=True)

        self._lock = threading.Lock()
        self._current_file = None
        self._current_path = None
        self._rotation_interval = 30 * 60
        self._next_rotation = 0
        self._stopped = False
        self._capture_buf = {"OUT": "", "ERR": ""}

        self._real_stdout = sys.stdout
        self._real_stderr = sys.stderr

        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_excepthook

        self._original_thread_excepthook = getattr(threading, 'excepthook', None)
        if hasattr(threading, 'excepthook'):
            threading.excepthook = self._thread_excepthook

        sys.stdout = LogWriter(self, "OUT")
        sys.stderr = LogWriter(self, "ERR")

        self._rotate()
        self._write_entry("INFO", "loghub.py", "LOGHUB",
                         f"Session started. Log dir: {self._log_dir}")

        atexit.register(self.stop)
