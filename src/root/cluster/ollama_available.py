"""ollama_available.py — ollama_available() for ClusterRoot."""
from common.loghub import LogHub


class OllamaAvailableMixin:
    @LogHub.log_call("ROOT")
    def ollama_available(self):
        if getattr(self, "_ollama_available", None) is not None:
            return self._ollama_available
        data = self._ollama_get("/api/tags")
        self._ollama_available = isinstance(data, dict) and "models" in data
        return self._ollama_available
