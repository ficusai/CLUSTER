"""get_ollama_models.py — get_ollama_models() for ClusterRoot."""
from common.loghub import LogHub


class GetOllamaModelsMixin:
    @LogHub.log_call("ROOT")
    def get_ollama_models(self):
        data = self._ollama_get("/api/tags")
        models = []
        if isinstance(data, dict):
            for m in data.get("models", []):
                models.append({
                    "name": m.get("name"),
                    "source": "ollama",
                    "size": m.get("size"),
                    "family": ((m.get("details") or {}).get("family") or ""),
                })
        return models
