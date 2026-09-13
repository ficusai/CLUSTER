"""detect_ram.py — detect_ram() function."""
import os
from common.loghub import LogHub

HAVE_PSUTIL = False
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    pass


@LogHub.log_call("ROOT")
def detect_ram():
    if HAVE_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            return round(mem.total / 1024**3, 1), round(mem.available / 1024**3, 1)
        except Exception:
            LogHub().exception("DETECT")
    return 0, 0
