"""detect_cpu_cores.py — detect_cpu_cores() function."""
import os
import subprocess
from common.loghub import LogHub

HAVE_PSUTIL = False
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    pass


@LogHub.log_call("WORKER")
def detect_cpu_cores():
    if HAVE_PSUTIL:
        try:
            return psutil.cpu_count(logical=True) or 1
        except Exception:
            LogHub().exception("DETECT")
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        pass
    try:
        return int(subprocess.check_output(["nproc"]).strip())
    except Exception:
        pass
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except Exception:
        return 1
