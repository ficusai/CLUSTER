"""handle_exec_async.py — _handle_exec_async(payload) for ClusterWorker."""
import shlex
import subprocess
from common.loghub import LogHub


class HandleExecAsyncMixin:
    @LogHub.log_call("WORKER")
    def _handle_exec_async(self, payload):
        cmd = payload.get("command", "")
        argv = shlex.split(cmd)
        proc = subprocess.Popen(argv)
        return {"pid": proc.pid}
