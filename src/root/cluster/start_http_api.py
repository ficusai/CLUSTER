"""start_http_api.py — start_http_api() for ClusterRoot."""
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from common.loghub import LogHub
from .do_get import _do_get
from .do_post import _do_post


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
                    return self._send_json(501, {"error": "API token not configured."})
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

            do_GET = _do_get
            do_POST = _do_post
            do_PUT = _do_post

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
