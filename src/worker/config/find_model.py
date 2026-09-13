"""find_model.py — _find_model(payload) helper for ClusterWorker."""
import os
from common.loghub import LogHub
from .load_ai_config import load_ai_config


@LogHub.log_call("WORKER")
def find_model(payload):
    model = payload.get("model_path") if isinstance(payload, dict) else None
    if model and os.path.isfile(model):
        return model
    cfg = load_ai_config()
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
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "legacy", "models"),
        os.path.expanduser("~/ai-cluster/legacy/models"),
        "./legacy/models",
    ]
    for p in search_paths:
        ap = os.path.abspath(p)
        if os.path.isdir(ap):
            for f in os.listdir(ap):
                if f.endswith(".gguf"):
                    return os.path.join(ap, f)
    return None
