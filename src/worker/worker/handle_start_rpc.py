"""handle_start_rpc.py — _handle_start_rpc(payload) for ClusterWorker."""
import os
import subprocess
import time
from common.loghub import LogHub


class HandleStartRpcMixin:
    @LogHub.log_call("WORKER")
    def _handle_start_rpc(self, payload):
        self.log("[AI_MODE] _handle_start_rpc entered")
        if self.rpc_process and self.rpc_process.poll() is None:
            return {"status": "already_running", "pid": self.rpc_process.pid}
        rpc_bin = None
        search_paths = [
            payload.get("rpc_bin"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "legacy", "bin", "rpc-server"),
            os.path.expanduser("~/ai-cluster/bin/rpc-server"),
            os.path.expanduser("~/ai-cluster/rpc-server"),
            "./rpc-server",
        ]
        for p in search_paths:
            if p and os.path.isfile(p) and os.access(p, os.X_OK):
                rpc_bin = os.path.abspath(p)
                break
        if not rpc_bin:
            return {"status": "error", "error": "rpc-server binary not found"}
        threads = payload.get("threads", self.cpu_cores)
        model_path = self._find_model(payload)
        context_size = 4096
        cfg = self._load_ai_config()
        context_size = cfg.get("ai", {}).get("context_size", context_size)
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        rpc_log = os.path.join(log_dir, "rpc-server.log")
        cmd = [rpc_bin, "-H", "0.0.0.0", "-p", str(self.rpc_port), "-t", str(threads)]
        if model_path:
            cmd.extend(["-m", model_path, "-c", str(context_size)])
        with open(rpc_log, "a") as rpc_log_f:
            self.rpc_process = subprocess.Popen(
                cmd,
                stdout=rpc_log_f,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        time.sleep(1)
        if self.rpc_process.poll() is None:
            return {"status": "started", "pid": self.rpc_process.pid, "rpc_port": self.rpc_port, "model": model_path, "threads": threads}
        return {"status": "failed", "error": "rpc-server exited immediately"}
