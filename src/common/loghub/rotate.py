"""rotate.py — _rotate() for LogHub."""
import time


class RotateMixin:
    def _rotate(self):
        if self._current_file:
            try:
                self._current_file.close()
            except Exception:
                pass
        self._current_path = self._get_log_path()
        self._current_file = open(self._current_path, "a", encoding="utf-8")
        self._next_rotation = time.time() + self._rotation_interval
