"""kill_process_tree.py — _kill_process_tree(proc) for ClusterRoot."""
import os
import signal
import subprocess
from common.loghub import LogHub


class KillProcessTreeMixin:
    @LogHub.log_call("ROOT")
    def _kill_process_tree(self, proc):
        if proc is None or not hasattr(proc, "pid") or not isinstance(proc.pid, int) or proc.pid <= 0:
            return
        try:
            if proc.poll() is None:
                try:
                    pg = os.getpgid(proc.pid)
                    os.killpg(pg, signal.SIGTERM)
                except ProcessLookupError:
                    return
                except OSError as exc:
                    LogHub().warn("ROOT", f"SIGTERM to pgid {proc.pid} failed: {exc}")
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        pg = os.getpgid(proc.pid)
                        os.killpg(pg, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    except OSError as exc:
                        LogHub().warn("ROOT", f"SIGKILL to pgid {proc.pid} failed: {exc}")
        except OSError as exc:
            LogHub().warn("ROOT", f"_kill_process_tree failed for PID {proc.pid}: {exc}")
