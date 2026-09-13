"""ollama_get.py — _ollama_get(path, timeout) for ClusterRoot."""
import json
import urllib.request
from common.loghub import LogHub


class OllamaGetMixin:
    @LogHub.log_call("ROOT")
    def _ollama_get(self, path, timeout=2):
        url = f"{self.ollama_base_url}{path}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
