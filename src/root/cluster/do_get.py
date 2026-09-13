"""do_get.py — do_GET() handler for APIHandler (inside ClusterRoot.start_http_api)."""
import time
from urllib.parse import urlparse, parse_qs


def _do_get(self):
    parsed = urlparse(self.path)
    path = parsed.path
    _root = self.__dict__.get('_root') or getattr(self, '_root', None)

    if path == "/api/status":
        return self._send_json(200, _root._build_status_dict())
    elif path == "/api/workers":
        workers = _root.registry.get_all()
        return self._send_json(200, workers)
    elif path == "/api/tasks":
        task_id = parse_qs(parsed.query).get("id", [None])[0]
        if task_id:
            result = _root.tasks.get_result(task_id)
        else:
            result = list(_root.tasks.results.values())[-10:] if _root.tasks.results else []
        return self._send_json(200, result)
    elif path == "/api/ollama/status":
        return self._send_json(200, {"available": _root.ollama_available(), "base_url": _root.ollama_base_url})
    elif path == "/api/ollama/models":
        models = _root.get_ollama_models() + _root.get_bundled_gguf_models()
        return self._send_json(200, {"object": "list", "data": models})
    elif path == "/node_id":
        return self._send_text(200, _root.hostname)
    elif path == "/v1/feature-flags":
        return self._send_json(200, {})
    elif path == "/onboarding":
        return self._send_json(200, {"complete": True})
    elif path in ("/models", "/v1/models"):
        return self._send_json(200, {"object": "list", "data": []})
    elif path.startswith("/models/search"):
        return self._send_json(200, {"object": "list", "data": []})
    elif path.startswith("/state"):
        return _handle_state(self, _root)
    elif path in ("/v1/chat/completions", "/ollama/v1/chat/completions",
                  "/ollama/api/chat", "/ollama/api/api/chat", "/ollama/api/v1/chat"):
        return self._send_json(501, {"error": "Chat completions not available in this build"})
    elif path in ("/v1/images/generations", "/v1/images/edits"):
        return self._send_json(501, {"error": "Image generation not available in this build"})
    elif path.startswith("/instance") or path.startswith("/place_instance"):
        return self._send_json(404, {"error": "Instance management not available"})
    elif path.startswith("/download/"):
        return self._send_json(404, {"error": "Download management not available"})
    elif path.startswith("/v1/traces"):
        return self._send_json(404, {"error": "Traces not available"})
    elif path == "/events":
        return _handle_events(self, _root)
    return super(type(self), self).do_GET()


def _handle_state(self, _root):
    workers = _root.registry.get_all()
    nodes = {}
    node_identities = {}
    node_memory = {}
    node_network = {}
    for wid, info in workers.items():
        friendly = info.get("hostname", wid)
        platform = info.get("platform", "unknown")
        ram_total = info.get("ram_total", 0)
        ram_avail = info.get("ram_available", 0)
        ip = info.get("ip", "")
        device_type = "linux"
        if "darwin" in platform.lower() or "mac" in platform.lower():
            device_type = "macbook pro"
        elif "win" in platform.lower():
            device_type = "windows"
        nodes[wid] = {
            "system_info": {"model_id": device_type, "memory": ram_total * 1024**3 if ram_total else 0},
            "network_interfaces": [{"name": "eth0", "addresses": [ip]}] if ip else [],
            "ip_to_interface": {ip: "eth0"} if ip else {},
            "macmon_info": {"memory": {"ram_usage": max(ram_total - ram_avail, 0) * 1024**3 if ram_total and ram_avail else 0,
                                        "ram_total": ram_total * 1024**3 if ram_total else 0}},
            "last_macmon_update": time.time(),
            "friendly_name": friendly,
            "os_version": "Linux",
        }
        node_identities[wid] = {"modelId": device_type, "friendlyName": friendly, "osVersion": "Linux"}
        node_memory[wid] = {"ramTotal": {"inBytes": ram_total * 1024**3 if ram_total else 0},
                            "ramAvailable": {"inBytes": ram_avail * 1024**3 if ram_avail else 0}}
        node_network[wid] = {
            "interfaces": [{"name": "eth0", "ipAddress": ip, "addresses": [ip] if ip else []}] if ip else {"interfaces": []}
        }
    state = {
        "topology": {"nodes": list(nodes.keys()), "connections": {}},
        "nodeIdentities": node_identities, "nodeMemory": node_memory,
        "nodeNetwork": node_network, "nodeSystem": {}, "nodeThunderbolt": {},
        "nodeRdmaCtl": {}, "nodeThunderboltBridge": {}, "thunderboltBridgeCycles": [],
        "nodeDisk": {}, "instances": {}, "runners": {}, "instanceLinks": {}, "downloads": {},
    }
    return self._send_json(200, state)


def _handle_events(self, _root):
    self.send_response(200)
    self.send_header("Content-Type", "text/event-stream")
    self.send_header("Cache-Control", "no-cache")
    self.send_header("Connection", "keep-alive")
    self.end_headers()
    with _root.sse_lock:
        _root.sse_clients.append(self.wfile)
    try:
        initial = f"event: status\ndata: {__import__('json').dumps(_root._build_status_dict())}\n\n"
        self.wfile.write(initial.encode("utf-8"))
        self.wfile.flush()
        while _root.running:
            time.sleep(30)
            try:
                self.wfile.write(b": keep-alive\n\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                break
    except Exception:
        pass
    finally:
        with _root.sse_lock:
            try:
                _root.sse_clients.remove(self.wfile)
            except ValueError:
                pass
    return
