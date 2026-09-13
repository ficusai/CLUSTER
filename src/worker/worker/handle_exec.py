"""handle_exec.py — _handle_exec(payload) for ClusterWorker."""
import shlex
import subprocess
from common.loghub import LogHub


class HandleExecMixin:
    @LogHub.log_call("WORKER")
    def _handle_exec(self, payload):
        cmd = payload.get("command", "")
        timeout = payload.get("timeout", 30)
        argv = shlex.split(cmd)
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout, "stderr": r.stderr, "exit_code": r.returncode}
