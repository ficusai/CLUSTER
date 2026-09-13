"""broadcast_discovery.py — UDPBroadcastDiscovery class."""
import socket
import threading
import json
from common.loghub import LogHub
from common.protocol import UDP_DISCOVERY_PORT


class UDPBroadcastDiscovery:
    @LogHub.log_call("DISCOVERY")
    def __init__(self, port=UDP_DISCOVERY_PORT):
        self.port = port
        self.sock = None
        self.running = False

    @LogHub.log_call("DISCOVERY")
    def start_listener(self, on_message):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass
        self.sock.settimeout(1)
        try:
            self.sock.bind(("0.0.0.0", self.port))
        except OSError as e:
            self.sock.close()
            self.sock = None
            LogHub().exception("DISCOVERY", f"Failed to bind UDP listener on port {self.port}: {e}")
            return f"Failed to bind UDP listener on port {self.port}: {e}"
        self.running = True
        t = threading.Thread(target=self._listen_loop, args=(on_message,), daemon=True)
        t.start()

    @LogHub.log_call("DISCOVERY")
    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RD)
            except OSError:
                pass
            self.sock.close()
            self.sock = None

    @LogHub.log_call("DISCOVERY")
    def _listen_loop(self, on_message):
        while self.running and self.sock:
            try:
                data, addr = self.sock.recvfrom(4096)
                on_message(data, addr)
            except socket.timeout:
                continue
            except OSError as e:
                if e.errno == 9:
                    break
                LogHub().exception("DISCOVERY", f"UDP listen loop failed: {e}")
                break

    @LogHub.log_call("DISCOVERY")
    def broadcast(self, message, broadcast_ip="255.255.255.255"):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        data = message if isinstance(message, bytes) else json.dumps(message).encode()
        try:
            s.sendto(data, (broadcast_ip, self.port))
        except Exception:
            LogHub().exception("DISCOVERY", f"UDP broadcast to {broadcast_ip}:{self.port} failed")
        finally:
            s.close()
