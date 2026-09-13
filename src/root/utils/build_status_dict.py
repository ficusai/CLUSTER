"""build_status_dict.py — build_status_dict(root) module-level function."""
import json
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def build_status_dict(root):
    workers = root.registry.get_active()
    status = {
        "hostname": root.hostname,
        "ai_mode": root.ai_mode,
        "worker_count": len(workers),
        "ollama_available": root.ollama_available(),
        "selected_model": root.selected_model,
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
    if root.llama_process and root.llama_process.poll() is None:
        status["llama_server"] = {"pid": root.llama_process.pid}
    if root.local_rpc_process and root.local_rpc_process.poll() is None:
        status.setdefault("local_rpc", {})
        status["local_rpc"]["pid"] = root.local_rpc_process.pid
    return status
