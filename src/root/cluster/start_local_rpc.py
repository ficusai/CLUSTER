"""start_local_rpc.py — start_local_rpc() for ClusterRoot."""
import os
import subprocess
import time
from common.loghub import LogHub


class StartLocalRpcMixin:
    @LogHub.log_call("ROOT")
    def start_local_rpc(self):
        rpc_bin = self._find_rpc_bin()
        if not rpc_bin:
            self.log("No rpc-server binary found; local RPC disabled")
            if self.ui:
                self.ui.set_service("local RPC", "stopped", "binary not found")
            self.notify("Local RPC", "binary not found", urgency="low")
            return False
        os.makedirs(self._log_dir, exist_ok=True)
        rpc_log = os.path.join(self._log_dir, "rpc-server.log")
        with open(rpc_log, "a") as rpc_log_f:
            self.local_rpc_process = subprocess.Popen(
                [rpc_bin, "-H", "127.0.0.1", "-p", str(self.rpc_port), "-t", "4"],
                stdout=rpc_log_f,
                stderr=subprocess.STDOUT,
                env=self._env_with_libpath(),
                text=True,
                start_new_session=True,
            )
        time.sleep(1)
        if self.local_rpc_process.poll() is None:
            self.log(f"Local rpc-server started (PID {self.local_rpc_process.pid})")
            if self.ui:
                self.ui.set_service("local RPC", "running", f"PID {self.local_rpc_process.pid}")
            self._sse_broadcast("status", self._build_status_dict())
            return True
        self.log("Local rpc-server failed to start")
        self.log(f"LD_LIBRARY_PATH={self._env_with_libpath().get('LD_LIBRARY_PATH', '')}")
        self._tail_log(rpc_log)
        if self.ui:
            self.ui.set_service("local RPC", "error", "failed to start")
        self.notify("Local RPC", "failed to start", urgency="critical")
        return False
