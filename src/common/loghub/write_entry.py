"""write_entry.py — _write_entry(level, location, source, message) for LogHub."""
from datetime import datetime


class WriteEntryMixin:
    def _write_entry(self, level, location, source, message):
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{ts}] [{level:5s}] [{location}] [{source}] {message}\n"
        try:
            self._current_file.write(entry)
            self._current_file.flush()
        except Exception:
            pass
