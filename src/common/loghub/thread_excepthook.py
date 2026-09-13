"""thread_excepthook.py — _thread_excepthook(args) for LogHub."""
import traceback
from datetime import datetime


class ThreadExceptHookMixin:
    def _thread_excepthook(self, args):
        tb_str = "".join(traceback.format_exception(args.exc_type, args.exc_value, getattr(args, 'exc_traceback', args.exc_tb)))
        thread_name = args.thread.name if args.thread else "unknown"
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = (f"[{ts}] [FATAL] [THREAD-{thread_name}] [UNHANDLED] "
                f"{args.exc_type.__name__}: {args.exc_value}\n{tb_str}\n")
        try:
            with self._lock:
                if self._current_file:
                    self._current_file.write(entry)
                    self._current_file.flush()
        except Exception:
            pass
        self._write_to_real_stderr(entry)
        if self._original_thread_excepthook:
            self._original_thread_excepthook(args)
