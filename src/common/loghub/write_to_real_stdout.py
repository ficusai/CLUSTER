"""write_to_real_stdout.py — _write_to_real_stdout(text) for LogHub."""


class WriteToRealStdoutMixin:
    def _write_to_real_stdout(self, text):
        try:
            if self._real_stdout is not None:
                self._real_stdout.write(text)
                self._real_stdout.flush()
        except Exception:
            pass
