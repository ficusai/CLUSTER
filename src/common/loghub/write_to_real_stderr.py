"""write_to_real_stderr.py — _write_to_real_stderr(text) for LogHub."""


class WriteToRealStderrMixin:
    def _write_to_real_stderr(self, text):
        try:
            if self._real_stderr is not None:
                self._real_stderr.write(text)
                self._real_stderr.flush()
        except Exception:
            pass
