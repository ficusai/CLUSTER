"""stop.py — stop() for LogHub."""
import atexit


class StopMixin:
    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        self._capture_flush("OUT")
        self._capture_flush("ERR")

        self._write_entry("INFO", "loghub.py", "LOGHUB", "Session ended")

        import sys
        self._real_stdout = getattr(self, '_real_stdout', sys.stdout)
        self._real_stderr = getattr(self, '_real_stderr', sys.stderr)
        sys.stdout = self._real_stdout
        sys.stderr = self._real_stderr
        sys.excepthook = getattr(self, '_original_excepthook', sys.excepthook)
        if hasattr(__import__("threading"), 'excepthook'):
            threading = __import__("threading")
            threading.excepthook = getattr(self, '_original_thread_excepthook', getattr(threading, 'excepthook', None))

        with self._lock:
            if self._current_file:
                try:
                    self._current_file.close()
                except Exception:
                    pass
                self._current_file = None

        try:
            atexit.unregister(self.stop)
        except Exception:
            pass
