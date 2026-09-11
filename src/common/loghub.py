#!/usr/bin/env python3
import os
import sys
import io
import time
import threading
import traceback
import atexit
import functools
import inspect
from datetime import datetime


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


class LogHub:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_dir=None):
        if self._initialized:
            return
        self._initialized = True

        if log_dir is None:
            try:
                p = os.path.dirname(os.path.abspath(__file__))
                for _ in range(3):
                    parent = os.path.dirname(p)
                    if parent == p:
                        break
                    p = parent
                if os.path.isfile(os.path.join(p, "cluster.py")):
                    log_dir = os.path.join(p, "logs")
                else:
                    log_dir = os.path.join(os.getcwd(), "logs")
            except Exception:
                log_dir = os.path.join(os.getcwd(), "logs")

        self._log_dir = log_dir
        os.makedirs(self._log_dir, exist_ok=True)

        self._lock = threading.Lock()
        self._current_file = None
        self._current_path = None
        self._rotation_interval = 30 * 60
        self._next_rotation = 0
        self._stopped = False
        self._capture_buf = {"OUT": "", "ERR": ""}

        self._real_stdout = sys.stdout
        self._real_stderr = sys.stderr

        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_excepthook

        self._original_thread_excepthook = getattr(threading, 'excepthook', None)
        if hasattr(threading, 'excepthook'):
            threading.excepthook = self._thread_excepthook

        sys.stdout = LogWriter(self, "OUT")
        sys.stderr = LogWriter(self, "ERR")

        self._rotate()
        self._write_entry("INFO", "loghub.py", "LOGHUB",
                         f"Session started. Log dir: {self._log_dir}")

        atexit.register(self.stop)

    def _get_log_path(self):
        now = datetime.now()
        return os.path.join(self._log_dir, now.strftime("%Y-%m-%d-%H-%M-%S") + ".log")

    def _rotate(self):
        if self._current_file:
            try:
                self._current_file.close()
            except Exception:
                pass
        self._current_path = self._get_log_path()
        self._current_file = open(self._current_path, "a", encoding="utf-8")
        self._next_rotation = time.time() + self._rotation_interval

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

    def _write_entry(self, level, location, source, message):
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{ts}] [{level:5s}] [{location}] [{source}] {message}\n"
        try:
            self._current_file.write(entry)
            self._current_file.flush()
        except Exception:
            pass

    def _write_to_real_stdout(self, text):
        try:
            if self._real_stdout is not None:
                self._real_stdout.write(text)
                self._real_stdout.flush()
        except Exception:
            pass

    def _write_to_real_stderr(self, text):
        try:
            if self._real_stderr is not None:
                self._real_stderr.write(text)
                self._real_stderr.flush()
        except Exception:
            pass

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

    def info(self, source, message):
        if not self._initialized:
            return
        loc = self._find_caller()
        with self._lock:
            if self._stopped:
                return
            if time.time() >= self._next_rotation:
                self._rotate()
            self._write_entry("INFO", loc, source, message)
        self._write_to_real_stdout(f"[{source}] {message}\n")

    def warn(self, source, message):
        if not self._initialized:
            return
        loc = self._find_caller()
        with self._lock:
            if self._stopped:
                return
            if time.time() >= self._next_rotation:
                self._rotate()
            self._write_entry("WARN", loc, source, message)
        self._write_to_real_stderr(f"[{source}] WARN: {message}\n")

    def error(self, source, message):
        if not self._initialized:
            return
        loc = self._find_caller()
        tb = traceback.format_exc()
        with self._lock:
            if self._stopped:
                return
            if time.time() >= self._next_rotation:
                self._rotate()
            self._write_entry("ERROR", loc, source, message)
            if tb and tb.strip() not in ("", "NoneType: None\n", "NoneType: None"):
                self._write_entry("ERROR", loc, source, f"Traceback:\n{tb.rstrip()}")
        self._write_to_real_stderr(f"[{source}] ERROR: {message}\n")

    def exception(self, source, message=None):
        if not self._initialized:
            return
        loc = self._find_caller()
        tb = traceback.format_exc()
        if not message:
            if tb and tb.strip() not in ("", "NoneType: None\n", "NoneType: None"):
                lines = tb.strip().split('\n')
                message = lines[-1].strip() if lines else "Unknown exception"
            else:
                message = "Unknown exception"
        with self._lock:
            if self._stopped:
                return
            if time.time() >= self._next_rotation:
                self._rotate()
            self._write_entry("ERROR", loc, source, message)
            if tb and tb.strip() not in ("", "NoneType: None\n", "NoneType: None"):
                self._write_entry("ERROR", loc, source, f"Traceback:\n{tb.rstrip()}")
        self._write_to_real_stderr(f"[{source}] EXCEPTION: {message}\n")

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

    @staticmethod
    def log_call(source=None):
        """Decorator. Logs entry, SUCCESS/FAILED + exception traceback, and emits
        a root notification on failure when running as root."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                name = func.__name__
                try:
                    result = func(*args, **kwargs)
                except Exception as exc:
                    tb = traceback.format_exc()
                    LogHub().error(source or "CORE", f"{name} FAILED: {exc}\n{tb}")
                    try:
                        from common.progress_ui import send_notification
                        send_notification(
                            source or "CORE",
                            f"{name} FAILED: {exc}",
                            urgency="critical",
                        )
                    except Exception:
                        pass
                    raise
                else:
                    val = ""
                    try:
                        if result is None:
                            val = "None"
                        else:
                            val = repr(result)
                            if len(val) > 200:
                                val = val[:200] + "..."
                    except Exception:
                        val = "<unreprable>"
                    LogHub().info(
                        source or "CORE", f"{name} SUCCESS -> {val}"
                    )
                    return result
            return wrapper
        return decorator

    def notify_orchestrator(self, message, urgency="normal"):
        """Best-effort notification to the root device (or local fallback)."""
        try:
            from common.progress_ui import send_notification
            send_notification("Cluster", message, urgency=urgency)
        except Exception:
            pass

    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        self._capture_flush("OUT")
        self._capture_flush("ERR")

        self._write_entry("INFO", "loghub.py", "LOGHUB", "Session ended")

        sys.stdout = self._real_stdout
        sys.stderr = self._real_stderr
        sys.excepthook = self._original_excepthook
        if hasattr(threading, 'excepthook') and self._original_thread_excepthook:
            threading.excepthook = self._original_thread_excepthook

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
