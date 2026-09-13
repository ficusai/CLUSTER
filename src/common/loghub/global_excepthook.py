"""global_excepthook.py — _global_excepthook(exc_type, exc_value, exc_tb) for LogHub."""
import traceback
from datetime import datetime


class GlobalExceptHookMixin:
    def _global_excepthook(self, exc_type, exc_value, exc_tb):
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{ts}] [FATAL] [GLOBAL] [UNHANDLED] {exc_type.__name__}: {exc_value}\n{tb_str}\n"
        try:
            with self._lock:
                if self._current_file:
                    self._current_file.write(entry)
                    self._current_file.flush()
        except Exception:
            pass
        self._write_to_real_stderr(entry)
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_tb)
