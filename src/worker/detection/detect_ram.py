"""detect_ram.py — detect_ram() function."""
import subprocess
from common.loghub import LogHub

HAVE_PSUTIL = False
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    pass


@LogHub.log_call("WORKER")
def detect_ram():
    if HAVE_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            return round(mem.total / 1024**3, 1), round(mem.available / 1024**3, 1)
        except Exception:
            LogHub().exception("DETECT")
    try:
        out = subprocess.check_output(["free", "-b"]).decode()
        lines = out.strip().split("\n")[1].split()
        total = int(lines[1])
        avail = int(lines[-1]) if lines[-1] != "available" else int(lines[3])
        return round(total / 1024**3, 1), round(avail / 1024**3, 1)
    except Exception:
        LogHub().exception("DETECT")
    return 0, 0
