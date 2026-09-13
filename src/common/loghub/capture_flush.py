"""capture_flush.py — _capture_flush(stream) for LogHub."""


class CaptureFlushMixin:
    def _capture_flush(self, stream):
        buf = None
        with self._lock:
            b = self._capture_buf[stream]
            if b:
                self._capture_buf[stream] = ""
                buf = b
                loc = self._find_caller()
                self._write_entry("INFO", loc, f"STD{stream}", b)
        if buf is not None:
            try:
                self._write_to_real_stdout(buf + "\n")
            except Exception:
                pass
