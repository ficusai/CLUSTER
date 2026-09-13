"""check_llama_workers.py — check_llama_workers() for ClusterRoot."""
import time
from common.loghub import LogHub


class CheckLlamaWorkersMixin:
    @LogHub.log_call("ROOT")
    def check_llama_workers(self):
        while self.running and self.ai_mode:
            time.sleep(15)
            active = self.registry.get_active()
            if self.llama_process and self.llama_process.poll() is None:
                endpoints = [f"127.0.0.1:{self.rpc_port}"]
                for wid, info in active.items():
                    endpoints.append(f"{info['ip']}:{info.get('rpc_port', 50052)}")
                rpc_arg = ",".join(endpoints)
                if self.last_rpc_arg != rpc_arg:
                    self.log("Topology changed, rebuilding llama-server...")
                    self.rebuild_llama_server()
                    self.last_rpc_arg = rpc_arg
