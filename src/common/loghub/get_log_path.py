"""get_log_path.py — _get_log_path() for LogHub."""
import os
from datetime import datetime


class GetLogPathMixin:
    def _get_log_path(self):
        now = datetime.now()
        return os.path.join(self._log_dir, now.strftime("%Y-%m-%d-%H-%M-%S") + ".log")
