"""get_bundled_gguf_models.py — get_bundled_gguf_models() for ClusterRoot."""
import os
from common.loghub import LogHub


class GetBundledGgufModelsMixin:
    @LogHub.log_call("ROOT")
    def get_bundled_gguf_models(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths = [
            os.path.join(script_dir, "..", "..", "legacy", "models"),
            "./legacy/models",
            "./models",
        ]
        models = []
        seen = set()
        for sp in search_paths:
            ap = os.path.abspath(sp)
            if not os.path.isdir(ap):
                continue
            for f in os.listdir(ap):
                if f.endswith(".gguf"):
                    name = f[:-5]
                    if name not in seen:
                        seen.add(name)
                        path = os.path.join(ap, f)
                        try:
                            size = os.path.getsize(path)
                        except OSError:
                            size = 0
                        models.append({
                            "name": name,
                            "source": "bundled",
                            "size": size,
                            "family": "",
                        })
        return models
