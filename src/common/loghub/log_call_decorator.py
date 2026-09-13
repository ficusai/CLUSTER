"""log_call_decorator.py — log_call static method for LogHub."""
import functools
import traceback


class LogCallMixin:
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
                    from common.loghub import LogHub as _LH
                    _LH().error(source or "CORE", f"{name} FAILED: {exc}\n{tb}")
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
                    from common.loghub import LogHub as _LH
                    _LH().info(
                        source or "CORE", f"{name} SUCCESS -> {val}"
                    )
                    return result
            return wrapper
        return decorator
