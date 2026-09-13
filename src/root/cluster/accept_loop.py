"""accept_loop.py — _accept_loop() for ClusterRoot."""
import socket
import threading
from common.loghub import LogHub


class AcceptLoopMixin:
    @LogHub.log_call("ROOT")
    def _accept_loop(self):
        while self.running:
            try:
                sock, addr = self.server_sock.accept()
                threading.Thread(target=self._handle_worker, args=(sock, addr[0]), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.log(f"Accept error: {e}")
