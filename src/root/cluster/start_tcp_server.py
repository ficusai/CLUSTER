"""start_tcp_server.py — start_tcp_server() for ClusterRoot."""
import socket
import sys
import threading
from common.loghub import LogHub


class StartTcpServerMixin:
    @LogHub.log_call("ROOT")
    def start_tcp_server(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_sock.bind(("0.0.0.0", self.ctrl_port))
        except OSError as e:
            self.log(f"Failed to bind TCP port {self.ctrl_port}: {e}")
            self.log("Try a different port with --port")
            if self.ui:
                self.ui.set_service("TCP server", "error", str(e))
            sys.exit(1)
        self.server_sock.listen(20)
        self.server_sock.settimeout(1)
        self.log(f"TCP control server listening on port {self.ctrl_port}")
        if self.ui:
            self.ui.set_service("TCP server", "running", f"port {self.ctrl_port}")

        self.server_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.server_thread.start()
