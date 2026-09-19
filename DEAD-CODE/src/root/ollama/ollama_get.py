"""ollama_get.py — _ollama_get(path, timeout) module-level function."""
import json
import urllib.request
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def ollama_get(path, timeout=2, base_url="http://localhost:11434"):
    url = f"{base_url}{path}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
