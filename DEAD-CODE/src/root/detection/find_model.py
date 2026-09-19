"""find_model.py — find_model() function."""
import os
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def find_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    search_paths = [
        os.path.join(script_dir, "..", "..", "legacy", "models"),
        "./legacy/models",
        "./models",
    ]
    for sp in search_paths:
        if os.path.isdir(sp):
            for f in os.listdir(sp):
                if f.endswith(".gguf"):
                    return os.path.join(sp, f)
    return None
