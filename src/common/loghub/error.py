"""error.py — error(source, message) for LogHub."""
import traceback
import time


class ErrorMixin:
    def error(self, source, message):
        if not self._initialized:
            return
        loc = self._find_caller()
        tb = traceback.format_exc()
        with self._lock:
            if self._stopped:
                return
            if time.time() >= self._next_rotation:
                self._rotate()
            self._write_entry("ERROR", loc, source, message)
            if tb and tb.strip() not in ("", "NoneType: None\n", "NoneType: None"):
                self._write_entry("ERROR", loc, source, f"Traceback:\n{tb.rstrip()}")
        self._write_to_real_stderr(f"[{source}] ERROR: {message}\n")
