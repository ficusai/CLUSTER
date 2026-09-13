"""start_http_api.py — start_http_api() for ClusterRoot."""
import json
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from socketserver import ThreadingMixIn
from common.loghub import LogHub


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class StartHttpApiMixin:
    @LogHub.log_call("ROOT")
    def start_http_api(self):
        _root = self

        _dashboard_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dashboard", "build")
        _dashboard_dir = os.path.abspath(_dashboard_dir)

        class APIHandler(SimpleHTTPRequestHandler):
            @LogHub.log_call("ROOT")
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=_dashboard_dir, **kwargs)

            @LogHub.log_call("ROOT")
            def log_message(self, format, *args):
                pass

            @LogHub.log_call("ROOT")
            def _send_json(self, status_code, data):
                payload = json.dumps(data).encode("utf-8")
                try:
                    self.send_response(status_code)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            @LogHub.log_call("ROOT")
            def _require_auth(self):
                if not _root.api_token:
                    return self._send_json(501, {"error": "API token not configured. Set AI_CLUSTER_API_TOKEN or security.api_token in config.yaml."})
                auth_header = self.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer ") or auth_header[7:] != _root.api_token:
                    return self._send_json(401, {"error": "Unauthorized"})
                return None

            @LogHub.log_call("ROOT")
            def _send_text(self, status_code, text, content_type="text/plain"):
                payload = text.encode("utf-8")
                try:
                    self.send_response(status_code)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            @LogHub.log_call("ROOT")
            def do_GET(self):
                parsed = urlparse(self.path)
                path = parsed.path

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
                    return self._send_json(200, {
                        "available": _root.ollama_available(),
                        "base_url": _root.ollama_base_url,
                    })

                elif path == "/api/ollama/models":
                    models = _root.get_ollama_models() + _root.get_bundled_gguf_models()
                    return self._send_json(200, {"object": "list", "data": models})

                elif path == "/node_id":
                    return self._send_text(200, _root.hostname)

                elif path == "/v1/feature-flags":
                    return self._send_json(200, {})

                elif path == "/onboarding":
                    return self._send_json(200, {"complete": True})

                elif path == "/models" or path == "/v1/models":
                    return self._send_json(200, {"object": "list", "data": []})

                elif path.startswith("/models/search"):
                    return self._send_json(200, {"object": "list", "data": []})

                elif path.startswith("/state"):
                    workers = _root.registry.get_all()
                    nodes = {}
                    node_identities = {}
                    node_memory = {}
                    node_network = {}

                    for wid, info in workers.items():
                        friendly = info.get("hostname", wid)
                        platform = info.get("platform", "unknown")
                        cores = info.get("cpu_cores", 0)
                        ram_total = info.get("ram_total", 0)
                        ram_avail = info.get("ram_available", 0)
                        ip = info.get("ip", "")
                        device_type = "linux"
                        if "darwin" in platform.lower() or "mac" in platform.lower():
                            device_type = "macbook pro"
                        elif "win" in platform.lower():
                            device_type = "windows"

                        nodes[wid] = {
                            "system_info": {
                                "model_id": device_type,
                                "memory": ram_total * 1024 * 1024 * 1024 if ram_total else 0,
                            },
                            "network_interfaces": [{"name": "eth0", "addresses": [ip]}] if ip else [],
                            "ip_to_interface": {ip: "eth0"} if ip else {},
                            "macmon_info": {
                                "memory": {
                                    "ram_usage": max(ram_total - ram_avail, 0) * 1024**3 if ram_total and ram_avail else 0,
                                    "ram_total": ram_total * 1024**3 if ram_total else 0,
                                },
                            },
                            "last_macmon_update": time.time(),
                            "friendly_name": friendly,
                            "os_version": "Linux",
                        }

                        node_identities[wid] = {
                            "modelId": device_type,
                            "friendlyName": friendly,
                            "osVersion": "Linux",
                        }

                        node_memory[wid] = {
                            "ramTotal": {"inBytes": ram_total * 1024**3 if ram_total else 0},
                            "ramAvailable": {"inBytes": ram_avail * 1024**3 if ram_avail else 0},
                        }

                        node_network[wid] = {
                            "interfaces": [{"name": "eth0", "ipAddress": ip, "addresses": [ip] if ip else []}] if ip else {"interfaces": []}
                        }

                    state = {
                        "topology": {
                            "nodes": list(nodes.keys()),
                            "connections": {},
                        },
                        "nodeIdentities": node_identities,
                        "nodeMemory": node_memory,
                        "nodeNetwork": node_network,
                        "nodeSystem": {},
                        "nodeThunderbolt": {},
                        "nodeRdmaCtl": {},
                        "nodeThunderboltBridge": {},
                        "thunderboltBridgeCycles": [],
                        "nodeDisk": {},
                        "instances": {},
                        "runners": {},
                        "instanceLinks": {},
                        "downloads": {},
                    }
                    return self._send_json(200, state)

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
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "keep-alive")
                    self.end_headers()
                    with _root.sse_lock:
                        _root.sse_clients.append(self.wfile)
                    try:
                        initial = f"event: status\ndata: {json.dumps(_root._build_status_dict())}\n\n"
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

                # Fallback to static file serving
                return super().do_GET()

            @LogHub.log_call("ROOT")
            def do_POST(self):
                parsed = urlparse(self.path)
                path = parsed.path

                if path == "/api/task/exec":
                    content_len = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_len).decode() if content_len else "{}"
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        data = {}
                    cmd = data.get("command", "")
                    wid = data.get("worker_id")
                    if not _root.api_token:
                        return self._send_json(401, {"error": "API token not configured. Set AI_CLUSTER_API_TOKEN or security.api_token in config.yaml."})
                    auth_header = self.headers.get("Authorization", "")
                    if not auth_header.startswith("Bearer ") or auth_header[7:] != _root.api_token:
                        return self._send_json(401, {"error": "Unauthorized"})
                    task_id, result = _root.tasks.dispatch_task("exec", {"command": cmd}, worker_id=wid)
                    return self._send_json(200, {"task_id": task_id, "workers": result})

                elif path == "/api/rebuild":
                    if (r := self._require_auth()) is not None:
                        return r
                    threading.Thread(target=_root.rebuild_llama_server, daemon=True).start()
                    return self._send_json(200, {"status": "rebuilding"})

                elif path == "/api/stop":
                    if (r := self._require_auth()) is not None:
                        return r
                    try:
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", "23")
                        self.end_headers()
                        self.wfile.write(b'{"status":"shutting_down"}')
                    except (ConnectionResetError, BrokenPipeError):
                        pass
                    threading.Thread(target=_root.stop, daemon=True).start()
                    return

                elif path == "/api/model/select":
                    content_len = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_len).decode() if content_len else "{}"
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        data = {}
                    model = data.get("model")
                    if not model:
                        return self._send_json(400, {"error": "Missing model name"})
                    _root.selected_model = model
                    _root.log(f"Selected model: {model}")
                    return self._send_json(200, {"status": "ok", "selected_model": model})

                elif path in ("/v1/chat/completions", "/ollama/v1/chat/completions"):
                    content_len = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_len).decode() if content_len else "{}"
                    return self._send_json(501, {"error": "Chat completions not available in this build", "body": body})

                elif path == "/onboarding":
                    content_len = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_len).decode() if content_len else "{}"
                    return self._send_json(200, {"complete": True})

                return self._send_json(404, {"error": "Not found"})

            do_PUT = do_POST

        start_port = self.http_port
        server = None
        for offset in range(10):
            probe_port = start_port + offset
            try:
                server = ThreadingHTTPServer(("0.0.0.0", probe_port), APIHandler)
                if probe_port != start_port:
                    self.log(f"Port {start_port} in use; using fallback HTTP port {probe_port}")
                self.http_port = probe_port
                break
            except OSError as e:
                if offset == 9:
                    self.log(f"Failed to bind HTTP server on ports {start_port}-{probe_port}: {e}")
                    if self.ui:
                        self.ui.set_service("HTTP API", "error", str(e))
                    raise

        self.http_server = server
        t = threading.Thread(target=self.http_server.serve_forever, daemon=True)
        t.start()
        self.log(f"HTTP API: http://{self._get_local_ip()}:{self.http_port}")
        if self.ui:
            self.ui.set_service("HTTP API", "running", f"port {self.http_port}")
