import argparse
import json
import os
import platform as plat
import shlex
import signal
import socket
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.protocol import (
    ControlProtocol, CTRL_PORT_DEFAULT, RPC_PORT_DEFAULT,
    MSG_REGISTER, MSG_REGISTER_ACK, MSG_TASK, MSG_TASK_RESULT,
    MSG_PING, MSG_PONG, MSG_DISCONNECT,
    make_msg, parse_msg
)
from common.discovery import MDNSAdvertiser, UDPBroadcastDiscovery, discover_roots_on_network
from common.progress_ui import send_notification
from common.loghub import LogHub


HAVE_PSUTIL = False
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    pass


@LogHub.log_call("WORKER")
def detect_platform():
    p = plat.system().lower()
    if p == "linux" and os.path.exists("/data/data/com.termux/files/usr"):
        return "android"
    if p == "darwin":
        machine = plat.machine().lower()
        platform_str = plat.platform().lower()
        if "iphone" in platform_str or "ipad" in platform_str:
            return "ios"
        if machine in ("arm64", "aarch64"):
            if os.path.exists("/usr/lib/libcryptex.dylib") or os.path.exists("/var/containers"):
                return "ios"
            if os.path.exists("/System/Library/CoreServices/SystemVersion.plist"):
                return "macos"
            return "ios"
        return "macos"
    if p == "windows":
        return "windows"
    return p


@LogHub.log_call("WORKER")
def detect_cpu_cores():
    if HAVE_PSUTIL:
        try:
            return psutil.cpu_count(logical=True) or 1
        except Exception:
            LogHub().exception("DETECT")
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        pass
    try:
        return int(subprocess.check_output(["nproc"]).strip())
    except Exception:
        pass
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except Exception:
        return 1


@LogHub.log_call("WORKER")
def detect_ram():
    if HAVE_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            return round(mem.total / 1024**3, 1), round(mem.available / 1024**3, 1)
        except Exception:
            LogHub().exception("DETECT")
    try:
        out = subprocess.check_output(["free", "-b"]).decode()
        lines = out.strip().split("\n")[1].split()
        total = int(lines[1])
        avail = int(lines[-1]) if lines[-1] != "available" else int(lines[3])
        return round(total / 1024**3, 1), round(avail / 1024**3, 1)
    except Exception:
        LogHub().exception("DETECT")
    return 0, 0


@LogHub.log_call("WORKER")
def _get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 53))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class ClusterWorker:
    @LogHub.log_call("WORKER")
    def __init__(self, ctrl_port=CTRL_PORT_DEFAULT, rpc_port=RPC_PORT_DEFAULT,
                 root_ip=None, ai_mode=False, ui=None):
        self.ctrl_port = ctrl_port
        self.rpc_port = rpc_port
        self.root_ip = root_ip
        self.ai_mode = ai_mode
        self.ui = ui
        self.running = True
        self.registered = False
        self.hostname = socket.gethostname()
        self.platform = detect_platform()
        self.cpu_cores = detect_cpu_cores()
        self.ram_total, self.ram_available = detect_ram()
        self.conn = None
        self.rpc_process = None
        self.task_handlers = {
            "exec": self._handle_exec,
            "exec_async": self._handle_exec_async,
            "start_rpc": self._handle_start_rpc,
            "stop_rpc": self._handle_stop_rpc,
            "ping": self._handle_ping,
        }
        self._reconnect_attempts = 0
        self._stopped = False

    @LogHub.log_call("WORKER")
    def log(self, msg, notify=False):
        LogHub().info("WORKER", msg)
        print(f"[worker] {msg}")
        if self.ui:
            self.ui.add_event(msg)
        if notify:
            send_notification("Cluster Worker", msg)

    @LogHub.log_call("WORKER")
    def notify(self, title, message, urgency="normal"):
        send_notification(title, message, urgency)
        if self.ui:
            self.ui.add_event(f"{title}: {message}", notify=False)

    @LogHub.log_call("WORKER")
    def start_advertising(self):
        self.mdns = MDNSAdvertiser(
            hostname=self.hostname,
            port=self.ctrl_port,
            platform=self.platform,
            cpu_cores=self.cpu_cores,
            ram_total=self.ram_total,
            ram_available=self.ram_available,
            rpc_port=self.rpc_port,
        )
        started = self.mdns.start()
        if started:
            self.log("Advertising via mDNS")
            if self.ui:
                self.ui.set_service("mDNS", "running")
        else:
            if self.ui:
                self.ui.set_service("mDNS", "idle", "zeroconf not available")

    @LogHub.log_call("WORKER")
    def stop_advertising(self):
        if hasattr(self, "mdns"):
            self.mdns.stop()

    @LogHub.log_call("WORKER")
    def discover_root(self, timeout=5, force=False):
        """Discover root via mDNS + UDP broadcast. Returns root IP or None."""
        if self.root_ip and not force:
            return self.root_ip

        self.log(f"Scanning for root devices (timeout: {timeout}s)...")
        self.notify("Looking for root", "Scanning network for root device...", urgency="low")
        if self.ui:
            self.ui.set_connection("discovering")
            self.ui.set_service("discovery", "discovering", f"timeout: {timeout}s")

        roots = discover_roots_on_network(timeout=timeout)

        if roots:
            root = roots[0]
            source = root.get('source', 'discovery')
            self.log(f"Found root via {source}: {root['hostname']} at {root['ip']}")
            self.notify("Root found", f"{root['hostname']} at {root['ip']} via {source}")
            if self.ui:
                self.ui.set_connection("discovering", root_ip=root["ip"])
                self.ui.set_service("discovery", "running")
            return root["ip"]

        # Last resort: direct UDP broadcast one-shot
        self.log("No root found via mDNS+UDP, trying direct broadcast...")
        if self.ui:
            self.ui.set_service("discovery", "discovering", "direct UDP broadcast")
        udp = UDPBroadcastDiscovery()
        found = [None]

        @LogHub.log_call("WORKER")
        def on_udp_response(data, addr):
            try:
                msg = parse_msg(data)
                if msg.get("type") == "root_announce":
                    found[0] = addr[0]
            except Exception:
                LogHub().exception("WORKER", "UDP response parse failed")

        udp.start_listener(on_udp_response)
        # Send multiple discovery requests to cover root announce interval (5s)
        for _ in range(3):
            udp.broadcast(make_msg("worker_discover",
                hostname=self.hostname, platform=self.platform))
            time.sleep(2)
        udp.stop()

        if found[0]:
            self.log(f"Found root via UDP broadcast: {found[0]}")
            self.notify("Root found", f"Root at {found[0]} via UDP broadcast")
        return found[0]

    @LogHub.log_call("WORKER")
    def register_with_root(self, root_ip):
        if root_ip is None:
            return False
        try:
            self.conn = ControlProtocol()
            self.conn.connect(root_ip, self.ctrl_port)
            if self.ui:
                self.ui.set_connection("connecting", root_ip=root_ip)

            self.conn.send(MSG_REGISTER,
                hostname=self.hostname,
                platform=self.platform,
                arch=plat.machine(),
                cpu_cores=self.cpu_cores,
                ram_total=self.ram_total,
                ram_available=self.ram_available,
                rpc_port=self.rpc_port,
            )

            resp = self.conn.recv()
            if resp and resp.get("type") == MSG_REGISTER_ACK:
                self.registered = True
                self.root_ip = root_ip
                self.log(f"Registered with root at {root_ip}", notify=True)
                if self.ui:
                    self.ui.set_connection("connected", root_ip=root_ip, registered=True)
                    self.ui.set_service("connection", "running", f"root: {root_ip}")
                return True
            self.log(f"Registration rejected by root at {root_ip}")
            if self.ui:
                self.ui.set_connection("error", root_ip=root_ip)
            return False
        except Exception as e:
            self.log(f"Registration failed: {e}")
            if self.ui:
                self.ui.set_connection("error", root_ip=root_ip)
            return False

    @LogHub.log_call("WORKER")
    def handle_connection(self):
        t = threading.Thread(target=self._read_loop, daemon=True)
        t.start()
        while self.running and self.registered:
            self._heartbeat()
            time.sleep(15)

    @LogHub.log_call("WORKER")
    def _heartbeat(self):
        try:
            self.conn.send(MSG_PING)
        except Exception:
            self.log("Heartbeat lost")
            self.notify("Heartbeat lost", f"Connection to root at {self.root_ip} lost", urgency="critical")
            self.registered = False

    @LogHub.log_call("WORKER")
    def _read_loop(self):
        while self.running and self.registered:
            try:
                msg = self.conn.recv()
                if msg is None:
                    self.log("Connection closed by root")
                    self.registered = False
                    break
                self._handle_message(msg)
            except Exception as e:
                self.log(f"Connection error: {e}")
                self.registered = False
                break

    @LogHub.log_call("WORKER")
    def _handle_message(self, msg):
        msg_type = msg.get("type")
        if msg_type == MSG_TASK:
            threading.Thread(target=self._execute_task, args=(msg,), daemon=True).start()
        elif msg_type == MSG_PING:
            self.conn.send(MSG_PONG)
        elif msg_type == MSG_DISCONNECT:
            self.registered = False

    @LogHub.log_call("WORKER")
    def _execute_task(self, msg):
        task_id = msg.get("id", "")
        action = msg.get("action", "")
        payload = msg.get("payload", {})
        handler = self.task_handlers.get(action)
        if not handler:
            self.conn.send(MSG_TASK_RESULT,
                id=task_id, success=False, error=f"Unknown action: {action}")
            return
        try:
            result = handler(payload)
            self.conn.send(MSG_TASK_RESULT, id=task_id, success=True, **result)
        except Exception as e:
            self.conn.send(MSG_TASK_RESULT, id=task_id, success=False, error=str(e))

    @LogHub.log_call("WORKER")
    def _handle_exec(self, payload):
        cmd = payload.get("command", "")
        timeout = payload.get("timeout", 30)
        argv = shlex.split(cmd)
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout, "stderr": r.stderr, "exit_code": r.returncode}

    @LogHub.log_call("WORKER")
    def _handle_exec_async(self, payload):
        cmd = payload.get("command", "")
        argv = shlex.split(cmd)
        proc = subprocess.Popen(argv)
        return {"pid": proc.pid}

    @LogHub.log_call("WORKER")
    def _handle_ping(self, payload):
        return {"pong": True, "ts": time.time()}

    @LogHub.log_call("WORKER")
    def _load_ai_config(self):
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.yaml"),
            os.path.expanduser("~/ai-cluster/config.yaml"),
            "./config.yaml",
        ]
        for c in candidates:
            if os.path.isfile(c):
                try:
                    import yaml
                    return yaml.safe_load(open(c)) or {}
                except Exception:
                    return {}
        return {}

    @LogHub.log_call("WORKER")
    def _find_model(self, payload):
        model = payload.get("model_path") if isinstance(payload, dict) else None
        if model and os.path.isfile(model):
            return model
        cfg = self._load_ai_config()
        cfg_model = cfg.get("ai", {}).get("model")
        if cfg_model:
            base = os.path.dirname(os.path.abspath(__file__))
            for c in [
                cfg_model,
                os.path.join(base, "..", "..", cfg_model),
                os.path.join(base, "..", cfg_model),
            ]:
                ap = os.path.abspath(c)
                if os.path.isfile(ap):
                    return ap
        search_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "legacy", "models"),
            os.path.expanduser("~/ai-cluster/legacy/models"),
            "./legacy/models",
        ]
        for p in search_paths:
            ap = os.path.abspath(p)
            if os.path.isdir(ap):
                for f in os.listdir(ap):
                    if f.endswith(".gguf"):
                        return os.path.join(ap, f)
        return None

    @LogHub.log_call("WORKER")
    def _handle_start_rpc(self, payload):
        self.log("[AI_MODE] _handle_start_rpc entered")
        if self.rpc_process and self.rpc_process.poll() is None:
            return {"status": "already_running", "pid": self.rpc_process.pid}
        rpc_bin = None
        search_paths = [
            payload.get("rpc_bin"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "legacy", "bin", "rpc-server"),
            os.path.expanduser("~/ai-cluster/bin/rpc-server"),
            os.path.expanduser("~/ai-cluster/rpc-server"),
            "./rpc-server",
        ]
        for p in search_paths:
            if p and os.path.isfile(p) and os.access(p, os.X_OK):
                rpc_bin = os.path.abspath(p)
                break
        if not rpc_bin:
            return {"status": "error", "error": "rpc-server binary not found"}
        threads = payload.get("threads", self.cpu_cores)
        model_path = self._find_model(payload)
        context_size = 4096
        cfg = self._load_ai_config()
        context_size = cfg.get("ai", {}).get("context_size", context_size)
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        rpc_log = os.path.join(log_dir, "rpc-server.log")
        cmd = [rpc_bin, "-H", "0.0.0.0", "-p", str(self.rpc_port), "-t", str(threads)]
        if model_path:
            cmd.extend(["-m", model_path, "-c", str(context_size)])
        with open(rpc_log, "a") as rpc_log_f:
            self.rpc_process = subprocess.Popen(
                cmd,
                stdout=rpc_log_f,
                stderr=subprocess.STDOUT,
                text=True,
            )
        time.sleep(1)
        if self.rpc_process.poll() is None:
            return {"status": "started", "pid": self.rpc_process.pid, "rpc_port": self.rpc_port, "model": model_path, "threads": threads}
        return {"status": "failed", "error": "rpc-server exited immediately"}

    @LogHub.log_call("WORKER")
    def _handle_stop_rpc(self, payload):
        if self.rpc_process and self.rpc_process.poll() is None:
            self.rpc_process.terminate()
            try:
                self.rpc_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.rpc_process.kill()
            return {"status": "stopped"}
        return {"status": "not_running"}

    @LogHub.log_call("WORKER")
    def _reconnect(self):
        """Try to reconnect to root with exponential backoff."""
        delay = 2
        max_delay = 60
        while self.running and not self.registered:
            self._reconnect_attempts += 1
            self.log(f"Reconnection attempt {self._reconnect_attempts} in {delay}s...")
            if self._reconnect_attempts == 1:
                self.notify("Reconnecting", f"Connection lost, retrying in {delay}s...", urgency="critical")
            if self.ui:
                self.ui.set_connection("connecting", registered=False)
                self.ui.set_service("discovery", "discovering",
                                   f"attempt {self._reconnect_attempts}")
            time.sleep(delay)

            # Force rediscovery every attempt in case root IP changed or went down
            root_ip = self.discover_root(timeout=min(5, delay), force=True)

            if root_ip and self.register_with_root(root_ip):
                self._reconnect_attempts = 0
                return True

            delay = min(delay * 1.5, max_delay)
        return False

    @LogHub.log_call("WORKER")
    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        if self.rpc_process and self.rpc_process.poll() is None:
            self.rpc_process.terminate()
        self.stop_advertising()
        send_notification("Cluster Worker", "Shutting down")
        if self.ui:
            self.ui.stop()

    @LogHub.log_call("WORKER")
    def run(self):
        self.log(f"Starting on {self.platform} ({self.hostname})")
        self.log(f"CPU: {self.cpu_cores} cores | RAM: {self.ram_available}/{self.ram_total} GB")
        self.log(f"[AI_MODE] self.ai_mode={self.ai_mode!r}")

        if self.ui:
            self.ui.set_system_info(
                hostname=self.hostname,
                platform=self.platform,
                cpu_cores=self.cpu_cores,
                ram_total=self.ram_total,
                ram_available=self.ram_available,
                ai_mode=self.ai_mode,
            )
            self.ui.set_service("discovery", "idle", "")
            self.ui.set_service("connection", "idle", "")
            self.ui.set_connection("idle")

        self.start_advertising()

        if not self.root_ip:
            self.root_ip = self.discover_root(timeout=5)

        if not self.root_ip:
            self.log("No root found on network. Retrying in background...")
            self.notify("No root found", "Retrying discovery in background...")
            if self.ui:
                self.ui.set_connection("discovering", registered=False)
                self.ui.set_service("discovery", "discovering", "retrying...")
            if not self._reconnect():
                self.log("Could not discover any root device.")
                self.notify("No root found", "No root device on network. Start root with --root first.")
                self.log("Make sure a root device is running on the network.")
                self.log("Run this app with --root on the coordinator device first.")
                if self.ui:
                    self.ui.set_connection("error")
                    self.ui.set_service("discovery", "error", "no root found")
                try:
                    while self.running:
                        time.sleep(10)
                        if not self.registered:
                            self._reconnect()
                except KeyboardInterrupt:
                    pass
                self.stop()
                return

        if self.register_with_root(self.root_ip):
            self.notify("Connected to root", f"Root IP: {self.root_ip}")
            self.log(f"[AI_MODE] after register: ai_mode={self.ai_mode!r}")
            if self.ai_mode:
                try:
                    start_result = self._handle_start_rpc({"rpc_port": self.rpc_port})
                    self.log(f"Auto-started rpc-server: {start_result}")
                except Exception:
                    LogHub().exception("WORKER", "Failed to auto_start_rpc after register")
            self.handle_connection()

        # Connection lost — try to reconnect
        if self.running and not self.registered:
            self.log("Connection lost. Attempting reconnect...", notify=True)
            self.notify("Connection lost", f"Lost connection to root at {self.root_ip}", urgency="critical")
            if self.ui:
                self.ui.set_connection("disconnected")
                self.ui.set_service("connection", "error", "lost connection")
            self.conn = None
            if self._reconnect():
                self.notify("Reconnected", f"Root IP: {self.root_ip}")
                if self.ai_mode:
                    try:
                        self.conn.send(MSG_TASK, id="auto_start_rpc", action="start_rpc",
                                      payload={"rpc_port": self.rpc_port})
                    except Exception:
                        LogHub().exception("WORKER", "Failed to send auto_start_rpc after reconnect")
                self.handle_connection()

        self.stop()


@LogHub.log_call("WORKER")
def main(ui=None, **kwargs):
    parser = argparse.ArgumentParser(description="cluster-worker — auto-connect worker node")
    parser.add_argument("--port", type=int, default=CTRL_PORT_DEFAULT,
                       help=f"Control port (default: {CTRL_PORT_DEFAULT})")
    parser.add_argument("--rpc-port", type=int, default=RPC_PORT_DEFAULT,
                       help=f"RPC port for llama.cpp (default: {RPC_PORT_DEFAULT})")
    parser.add_argument("--root-ip", default=None,
                       help="Root IP (skip discovery)")
    parser.add_argument("--ai-mode", action="store_true",
                       help="Auto-start rpc-server for AI cluster")
    args = parser.parse_args()

    worker = ClusterWorker(
        ctrl_port=kwargs.get("ctrl_port", args.port),
        rpc_port=kwargs.get("rpc_port", args.rpc_port),
        root_ip=kwargs.get("root_ip", args.root_ip),
        ai_mode=kwargs.get("ai_mode", args.ai_mode),
        ui=ui,
    )

    @LogHub.log_call("WORKER")
    def handle_sig(sig, frame):
        LogHub().info("WORKER", "Shutting down...")
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    worker.run()


if __name__ == "__main__":
    main()