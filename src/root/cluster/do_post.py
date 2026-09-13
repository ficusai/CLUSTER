"""do_post.py — do_POST() handler for APIHandler (inside ClusterRoot.start_http_api)."""
import json
import threading
from urllib.parse import urlparse


def _do_post(self):
    parsed = urlparse(self.path)
    path = parsed.path
    _root = getattr(self, '_root', None)

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
