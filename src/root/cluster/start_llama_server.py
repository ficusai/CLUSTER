"""start_llama_server.py — start_llama_server() for ClusterRoot."""
import os
import socket
import subprocess
import time
from common.loghub import LogHub


class StartLlamaServerMixin:
    @LogHub.log_call("ROOT")
    def start_llama_server(self):
        llama_bin = self._find_llama_bin()
        if not llama_bin:
            self.log("No llama-server binary found; AI mode disabled")
            if self.ui:
                self.ui.set_service("AI server", "stopped", "binary not found")
            self.notify("AI Server", "binary not found", urgency="low")
            return

        model = self.model_path or self._find_model()
        if not model:
            self.log("No GGUF model found; AI mode disabled")
            if self.ui:
                self.ui.set_service("AI server", "stopped", "model not found")
            self.notify("AI Server", "model not found", urgency="low")
            return

        workers = self.registry.get_active()
        endpoints = [f"127.0.0.1:{self.rpc_port}"]
        for wid, info in workers.items():
            endpoints.append(f"{info['ip']}:{info.get('rpc_port', 50052)}")

        rpc_arg = ",".join(endpoints)
        cmd = [
            llama_bin,
            "-m", model,
            "--host", "0.0.0.0",
            "--port", str(self.llama_http_port),
            "--rpc", rpc_arg,
            "-c", "4096",
            "--no-mmap",
            "-ngl", "0",
        ]
        self.log(f"Starting llama-server with {len(endpoints)-1} remote workers...")
        self.log(f"RPC endpoints: {rpc_arg}")
        self.log(f"Command: {' '.join(cmd)}")

        os.makedirs(self._log_dir, exist_ok=True)
        llama_log = os.path.join(self._log_dir, "llama-server.log")

        desired_port = self.llama_http_port
        for _ in range(20):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if s.connect_ex(("127.0.0.1", desired_port)) != 0:
                    break
                desired_port += 1
        if desired_port != self.llama_http_port:
            self.log(f"Port {self.llama_http_port} busy; using fallback HTTP port {desired_port}")
            self.llama_http_port = desired_port
            cmd[cmd.index("--port") + 1] = str(desired_port)

        with open(llama_log, "a") as llama_log_f:
            self.llama_process = subprocess.Popen(
                cmd,
                stdout=llama_log_f,
                stderr=subprocess.STDOUT,
                env=self._env_with_libpath(),
                text=True,
                start_new_session=True,
            )
        time.sleep(3)
        if self.llama_process.poll() is None:
            self.log(f"llama-server running (PID {self.llama_process.pid})")
            self.log(f"LLaMA API: http://{self._get_local_ip()}:{self.llama_http_port}/v1/chat/completions")
            if self.ui:
                self.ui.set_service("AI server", "running", f"PID {self.llama_process.pid}")
            self._sse_broadcast("status", self._build_status_dict())
        else:
            self.log("llama-server failed to start")
            self.log(f"LD_LIBRARY_PATH={self._env_with_libpath().get('LD_LIBRARY_PATH', '')}")
            self._tail_log(llama_log)
            if self.ui:
                self.ui.set_service("AI server", "error", "failed to start")
            self.notify("AI Server", "failed to start", urgency="critical")
