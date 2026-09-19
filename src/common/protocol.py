import json
import socket
import time

from .loghub import LogHub
from functools import wraps

MSG_REGISTER = "register"
MSG_REGISTER_ACK = "register_ack"
MSG_TASK = "task"
MSG_TASK_RESULT = "result"
MSG_PING = "ping"
MSG_PONG = "pong"
MSG_DISCONNECT = "disconnect"

RPC_PORT_DEFAULT = 50052
CTRL_PORT_DEFAULT = 52053
UDP_DISCOVERY_PORT = 52052
MDNS_SERVICE_TYPE = "_cluster-worker._tcp.local."
MDNS_ROOT_SERVICE_TYPE = "_cluster-root._tcp.local."


def _log_call(source=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = func.__name__
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                LogHub().error(source or "PROTOCOL", f"{name} FAILED: {exc}")
                raise
            else:
                LogHub().info(source or "PROTOCOL", f"{name} SUCCESS")
                return result
        return wrapper
    return decorator

def make_msg(msg_type, **kwargs):
    msg = {"type": msg_type, "ts": time.time(), **kwargs}
    return json.dumps(msg).encode("utf-8") + b"\n"

def parse_msg(data):
    return json.loads(data.decode("utf-8").strip())

class ControlProtocol:
    def __init__(self, sock=None):
        self.sock = sock
        self._recv_buf = b""

    @_log_call("PROTOCOL")
    def connect(self, host, port=CTRL_PORT_DEFAULT, timeout=10):
        if not host:
            raise ValueError("host must not be empty")
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f"invalid port: {port}")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((host, port))
        self.sock.settimeout(None)
        return self

    @_log_call("PROTOCOL")
    def send(self, msg_type, **kwargs):
        self.sock.sendall(make_msg(msg_type, **kwargs))

    @_log_call("PROTOCOL")
    def recv(self):
        while True:
            idx = self._recv_buf.find(b"\n")
            if idx >= 0:
                line = self._recv_buf[:idx]
                self._recv_buf = self._recv_buf[idx + 1:]
                return parse_msg(line)
            chunk = self.sock.recv(4096)
            if not chunk:
                return None
            self._recv_buf += chunk

    @_log_call("PROTOCOL")
    def close(self):
        try:
            self.send(MSG_DISCONNECT)
        except Exception:
            LogHub().exception("PROTOCOL", "send disconnect failed during close")
        self.sock.close()
