"""warn.py — warn(source, message) for LogHub."""
import time


class WarnMixin:
    def warn(self, source, message):
        if not self._initialized:
            return
        loc = self._find_caller()
        with self._lock:
            if self._stopped:
                return
            if time.time() >= self._next_rotation:
                self._rotate()
            self._write_entry("WARN", loc, source, message)
        self._write_to_real_stderr(f"[{source}] WARN: {message}\n")
