"""exception.py — exception(source, message) for LogHub."""
import traceback
import time


class ExceptionMixin:
    def exception(self, source, message=None):
        if not self._initialized:
            return
        loc = self._find_caller()
        tb = traceback.format_exc()
        if not message:
            if tb and tb.strip() not in ("", "NoneType: None\n", "NoneType: None"):
                lines = tb.strip().split('\n')
                message = lines[-1].strip() if lines else "Unknown exception"
            else:
                message = "Unknown exception"
        with self._lock:
            if self._stopped:
                return
            if time.time() >= self._next_rotation:
                self._rotate()
            self._write_entry("ERROR", loc, source, message)
            if tb and tb.strip() not in ("", "NoneType: None\n", "NoneType: None"):
                self._write_entry("ERROR", loc, source, f"Traceback:\n{tb.rstrip()}")
        self._write_to_real_stderr(f"[{source}] EXCEPTION: {message}\n")
