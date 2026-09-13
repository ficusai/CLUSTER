"""capture_write.py — _capture_write(stream, text) for LogHub."""
import time


class CaptureWriteMixin:
    def _capture_write(self, stream, text):
        with self._lock:
            if self._stopped:
                self._write_to_real_stdout(text)
                return
            if time.time() >= self._next_rotation:
                self._rotate()
            buf = self._capture_buf[stream]
            buf += text
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if line:
                    loc = self._find_caller()
                    self._write_entry("INFO", loc, f"STD{stream}", line)
            self._capture_buf[stream] = buf
        self._write_to_real_stdout(text)
