"""ollama_available.py — ollama_available(base_url) module-level function."""
from common.loghub import LogHub
from .ollama_get import ollama_get


@LogHub.log_call("ROOT")
def ollama_available(base_url="http://localhost:11434", cache=None):
    if cache is not None:
        return cache
    data = ollama_get("/api_tags", base_url=base_url)
    result = isinstance(data, dict) and "models" in data
    return result
