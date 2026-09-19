"""build_status_dict.py — _build_status_dict() for ClusterRoot."""
from common.loghub import LogHub


class BuildStatusDictMixin:
    @LogHub.log_call("ROOT")
    def _build_status_dict(self):
        workers = self.registry.get_active()
        status = {
            "hostname": self.hostname,
            "ai_mode": self.ai_mode,
            "worker_count": len(workers),
            "ollama_available": self.ollama_available(),
            "selected_model": self.selected_model,
            "workers": [
                {
                    "ip": w["ip"],
                    "hostname": w["hostname"],
                    "platform": w["platform"],
                    "cpu_cores": w["cpu_cores"],
                    "ram_available": w["ram_available"],
                }
                for w in workers.values()
            ],
        }
        if self.llama_process and self.llama_process.poll() is None:
            status["llama_server"] = {"pid": self.llama_process.pid}
        if self.local_rpc_process and self.local_rpc_process.poll() is None:
            status.setdefault("local_rpc", {})
            status["local_rpc"]["pid"] = self.local_rpc_process.pid
        return status
