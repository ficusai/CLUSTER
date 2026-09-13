"""detect_cpu_cores.py — detect_cpu_cores() function."""
import os
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def detect_cpu_cores():
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        pass
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except Exception:
        return 1
