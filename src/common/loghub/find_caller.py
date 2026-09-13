"""find_caller.py — _find_caller() for LogHub."""
import traceback
import os


class FindCallerMixin:
    def _find_caller(self):
        try:
            stack = traceback.extract_stack()
            for frame in reversed(stack):
                fn = os.path.basename(frame.filename)
                if fn != "loghub.py":
                    return f"{fn}:{frame.lineno}"
        except Exception:
            pass
        return "unknown"
