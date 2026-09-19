"""load_ai_config.py — _load_ai_config() helper for ClusterWorker."""
import os
from common.loghub import LogHub


@LogHub.log_call("WORKER")
def load_ai_config():
    candidates = [
        os.path.join(os.getcwd(), "config.yaml"),
        os.path.expanduser("~/ai-cluster/config.yaml"),
        "./config.yaml",
    ]
    for c in candidates:
        if os.path.isfile(c):
            try:
                import yaml
                return yaml.safe_load(open(c)) or {}
            except Exception:
                return {}
    return {}
