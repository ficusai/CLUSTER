"""load_ai_config.py — _load_ai_config() for ClusterWorker."""
import os
from common.loghub import LogHub


class LoadAiConfigMixin:
    @LogHub.log_call("WORKER")
    def _load_ai_config(self):
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.yaml"),
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
