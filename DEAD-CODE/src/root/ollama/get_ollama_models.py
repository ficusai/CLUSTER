"""get_ollama_models.py — get_ollama_models(base_url) module-level function."""
from common.loghub import LogHub
from .ollama_get import ollama_get


@LogHub.log_call("ROOT")
def get_ollama_models(base_url="http://localhost:11434"):
    data = ollama_get("/api/tags", base_url=base_url)
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
