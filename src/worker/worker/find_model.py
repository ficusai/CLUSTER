"""find_model.py — _find_model(payload) for ClusterWorker."""
import os
from common.loghub import LogHub


class FindModelMixin:
    @LogHub.log_call("WORKER")
    def _find_model(self, payload):
        model = payload.get("model_path") if isinstance(payload, dict) else None
        if model and os.path.isfile(model):
            return model
        cfg = self._load_ai_config()
        cfg_model = cfg.get("ai", {}).get("model")
        if cfg_model:
            base = os.path.dirname(os.path.abspath(__file__))
            for c in [
                cfg_model,
                os.path.join(base, "..", "..", cfg_model),
                os.path.join(base, "..", cfg_model),
            ]:
                ap = os.path.abspath(c)
                if os.path.isfile(ap):
                    return ap
        search_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models"),
            os.path.expanduser("~/ai-cluster/models"),
            "./models",
        ]
        for p in search_paths:
            ap = os.path.abspath(p)
            if os.path.isdir(ap):
                for f in os.listdir(ap):
                    if f.endswith(".gguf"):
                        return os.path.join(ap, f)
        return None
