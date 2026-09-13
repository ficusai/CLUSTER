"""log_writer.py — LogWriter class."""
import io


class LogWriter(io.TextIOBase):
    def __init__(self, hub, stream_name):
        super().__init__()
        self._hub = hub
        self._stream = stream_name

    def write(self, text):
        if not text:
            return len(text)
        self._hub._capture_write(self._stream, text)
        return len(text)

    def flush(self):
        self._hub._capture_flush(self._stream)
