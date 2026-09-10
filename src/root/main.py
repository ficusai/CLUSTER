import argparse
import json
import os
import platform as plat
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path as _PathForStatic
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common.protocol import (
    ControlProtocol, CTRL_PORT_DEFAULT, RPC_PORT_DEFAULT,
    MSG_REGISTER, MSG_REGISTER_ACK, MSG_TASK, MSG_TASK_RESULT,
    MSG_PING, MSG_PONG, MSG_DISCONNECT,
    make_msg, parse_msg, UDP_DISCOVERY_PORT, MDNS_ROOT_SERVICE_TYPE,
)

HEARTBEAT_TIMEOUT = 60
from common.discovery import (
    MDNSDiscovery, UDPBroadcastDiscovery, MDNSRootAdvertiser, _get_local_ip,
)
from common.progress_ui import send_notification
from common.loghub import LogHub


HAVE_PSUTIL = False
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    pass


@LogHub.log_call("ROOT")
def detect_cpu_cores():
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        pass
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except Exception:
        return 1


@LogHub.log_call("ROOT")
def detect_ram():
    if HAVE_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            return round(mem.total / 1024**3, 1), round(mem.available / 1024**3, 1)
        except Exception:
            LogHub().exception("DETECT")
    return 0, 0


class WorkerRegistry:
    @LogHub.log_call("ROOT")
    def __init__(self):
        self.workers = {}
        self.lock = threading.Lock()

    @LogHub.log_call("ROOT")
    def register(self, worker_id, info, conn):
        with self.lock:
            self.workers[worker_id] = {**info, "conn": conn, "last_seen": time.time(), "status": "active"}

    @LogHub.log_call("ROOT")
    def unregister(self, worker_id):
        with self.lock:
            self.workers.pop(worker_id, None)

    @LogHub.log_call("ROOT")
    def get_active(self):
        with self.lock:
            now = time.time()
            return {k: v for k, v in self.workers.items()
                   if v.get("status") == "active" and (now - v.get("last_seen", 0)) < HEARTBEAT_TIMEOUT}

    @LogHub.log_call("ROOT")
    def get_all(self):
        with self.lock:
            return {k: {kk: vv for kk, vv in v.items() if kk != "conn"}
                   for k, v in self.workers.items()}

    @LogHub.log_call("ROOT")
    def get_worker_count(self):
        with self.lock:
            return len(self.workers)

    @LogHub.log_call("ROOT")
    def get_connection(self, worker_id):
        with self.lock:
            w = self.workers.get(worker_id)
            return w.get("conn") if w else None

    @LogHub.log_call("ROOT")
    def contains(self, worker_id):
        with self.lock:
            return worker_id in self.workers

    @LogHub.log_call("ROOT")
    def get_info(self, worker_id):
        with self.lock:
            w = self.workers.get(worker_id)
            return w.get("hostname", worker_id) if w else worker_id

    @LogHub.log_call("ROOT")
    def update_last_seen(self, worker_id):
        with self.lock:
            if worker_id in self.workers:
                self.workers[worker_id]["last_seen"] = time.time()


class TaskManager:
    @LogHub.log_call("ROOT")
    def __init__(self, registry):
        self.registry = registry
        self.pending = {}
        self.results = {}
        self.lock = threading.Lock()
        self.next_id = 1

    @LogHub.log_call("ROOT")
    def dispatch_task(self, action, payload=None, worker_id=None, timeout=30):
        task_id = f"t-{int(time.time())}-{self.next_id}"
        self.next_id += 1
        payload = payload or {}

        workers = self.registry.get_active()
        if not workers:
            return None, "No active workers"

        if worker_id and worker_id in workers:
            targets = {worker_id: workers[worker_id]}
        else:
            targets = workers

        dispatched = []
        for wid, info in targets.items():
            conn = self.registry.get_connection(wid)
            if conn:
                try:
                    conn.send(MSG_TASK, id=task_id, action=action, payload=payload)
                    dispatched.append(wid)
                except Exception as e:
                    LogHub().exception("ROOT", f"Failed to send task to {wid}: {e}")

        with self.lock:
            self.pending[task_id] = {
                "action": action,
                "worker_ids": dispatched,
                "timeout": timeout,
                "started": time.time(),
                "responses": {},
            }

        return task_id, dispatched

    @LogHub.log_call("ROOT")
    def record_result(self, task_id, worker_id, result):
        with self.lock:
            if task_id in self.pending:
                self.pending[task_id]["responses"][worker_id] = result
                if len(self.pending[task_id]["responses"]) >= len(self.pending[task_id]["worker_ids"]):
                    self.results[task_id] = self.pending.pop(task_id)

    @LogHub.log_call("ROOT")
    def get_result(self, task_id):
        with self.lock:
            if task_id in self.results:
                return self.results[task_id]
            if task_id in self.pending:
                return self.pending[task_id]
        return None


class ClusterRoot:
    @LogHub.log_call("ROOT")
    def __init__(self, ctrl_port=CTRL_PORT_DEFAULT, rpc_port=RPC_PORT_DEFAULT,
                 ai_mode=False, model_path=None, http_port=8080, ui=None, api_token=None):
        self.ctrl_port = ctrl_port
        self.rpc_port = rpc_port
        self.ai_mode = ai_mode
        self.model_path = model_path
        self.http_port = http_port
        self.api_token = os.environ.get("AI_CLUSTER_API_TOKEN") or api_token
        self.llama_http_port = http_port + 1
        self.running = True
        self.hostname = socket.gethostname()
        self.ui = ui

        self.registry = WorkerRegistry()
        self.tasks = TaskManager(self.registry)

        self.server_sock = None
        self.server_thread = None
        self.http_server = None

        self.llama_process = None
        self.local_rpc_process = None

        self._discovered_via_udp = set()
        self._discovered_via_udp_max = 512
        self.last_rpc_arg = ""
        self.mdns = None
        self.mdns_root = None
        self.udp = None
        self.udp_listener = None
        self.udp_running = False
        self._stopped = False
        self._log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        self.sse_clients = []
        self.sse_lock = threading.Lock()

        self.ollama_base_url = "http://localhost:11434"
        self.selected_model = None

    @LogHub.log_call("ROOT")
    def log(self, msg):
        print(f"[root] {msg}")
        if self.ui:
            self.ui.add_event(msg)

    @LogHub.log_call("ROOT")
    def notify(self, title, message, urgency="normal"):
        send_notification(title, message, urgency)
        if self.ui:
            self.ui.add_event(f"{title}: {message}", notify=False)

    @LogHub.log_call("ROOT")
    def _build_status_dict(self):
        workers = self.registry.get_active()
        status = {
            "hostname": self.hostname,
            "ai_mode": self.ai_mode,
            "worker_count": len(workers),
            "ollama_available": self.ollama_available(),
            "selected_model": self.selected_model,
            "workers": [
                {
                    "ip": w["ip"],
                    "hostname": w["hostname"],
                    "platform": w["platform"],
                    "cpu_cores": w["cpu_cores"],
                    "ram_available": w["ram_available"],
                }
                for w in workers.values()
            ],
        }
        if self.llama_process and self.llama_process.poll() is None:
            status["llama_server"] = {"pid": self.llama_process.pid}
        if self.local_rpc_process and self.local_rpc_process.poll() is None:
            status.setdefault("local_rpc", {})
            status["local_rpc"]["pid"] = self.local_rpc_process.pid
        return status

    @LogHub.log_call("ROOT")
    def _sse_broadcast(self, event, data):
        msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        with self.sse_lock:
            dead = []
            for w in self.sse_clients:
                try:
                    w.write(msg.encode("utf-8"))
                    w.flush()
                except Exception:
                    dead.append(w)
            for w in dead:
                try:
                    self.sse_clients.remove(w)
                except ValueError:
                    pass

    @LogHub.log_call("ROOT")
    def _get_local_ip(self):
        return _get_local_ip()

    @LogHub.log_call("ROOT")
    def _find_bin_dir(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths = [
            os.path.join(script_dir, "..", "..", "legacy", "bin"),
            "./legacy/bin",
            "./bin",
        ]
        for p in search_paths:
            ap = os.path.abspath(p)
            if os.path.isdir(ap):
                return ap
        return None

    @LogHub.log_call("ROOT")
    def _find_llama_bin(self):
        bin_dir = self._find_bin_dir()
        if bin_dir:
            p = os.path.join(bin_dir, "llama-server")
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p
        return None

    @LogHub.log_call("ROOT")
    def _find_rpc_bin(self):
        bin_dir = self._find_bin_dir()
        if bin_dir:
            p = os.path.join(bin_dir, "rpc-server")
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p
        return None

    @LogHub.log_call("ROOT")
    def _env_with_libpath(self):
        env = os.environ.copy()
        bin_dir = self._find_bin_dir()
        if bin_dir:
            lp = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = f"{bin_dir}:{lp}" if lp else bin_dir
        return env

    @LogHub.log_call("ROOT")
    def _find_model(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths = [
            os.path.join(script_dir, "..", "..", "legacy", "models"),
            "./legacy/models",
            "./models",
        ]
        for sp in search_paths:
            if os.path.isdir(sp):
                for f in os.listdir(sp):
                    if f.endswith(".gguf"):
                        return os.path.join(sp, f)
        return None

    @LogHub.log_call("ROOT")
    def _ollama_get(self, path, timeout=2):
        import urllib.request
        url = f"{self.ollama_base_url}{path}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    @LogHub.log_call("ROOT")
    def ollama_available(self):
        if getattr(self, "_ollama_available", None) is not None:
            return self._ollama_available
        data = self._ollama_get("/api/tags")
        self._ollama_available = isinstance(data, dict) and "models" in data
        return self._ollama_available

    @LogHub.log_call("ROOT")
    def get_ollama_models(self):
        data = self._ollama_get("/api/tags")
        models = []
        if isinstance(data, dict):
            for m in data.get("models", []):
                models.append({
                    "name": m.get("name"),
                    "source": "ollama",
                    "size": m.get("size"),
                    "family": ((m.get("details") or {}).get("family") or ""),
                })
        return models

    @LogHub.log_call("ROOT")
    def get_bundled_gguf_models(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths = [
            os.path.join(script_dir, "..", "..", "legacy", "models"),
            "./legacy/models",
            "./models",
        ]
        models = []
        seen = set()
        for sp in search_paths:
            ap = os.path.abspath(sp)
            if not os.path.isdir(ap):
                continue
            for f in os.listdir(ap):
                if f.endswith(".gguf"):
                    name = f[:-5]
                    if name not in seen:
                        seen.add(name)
                        path = os.path.join(ap, f)
                        try:
                            size = os.path.getsize(path)
                        except OSError:
                            size = 0
                        models.append({
                            "name": name,
                            "source": "bundled",
                            "size": size,
                            "family": "",
                        })
        return models

    @LogHub.log_call("ROOT")
    def _kill_process_tree(self, proc):
        if proc is None or not hasattr(proc, "pid") or not isinstance(proc.pid, int) or proc.pid <= 0:
            return
        try:
            if proc.poll() is None:
                try:
                    pg = os.getpgid(proc.pid)
                    os.killpg(pg, signal.SIGTERM)
                except ProcessLookupError:
                    return
                except OSError as exc:
                    LogHub().warn("ROOT", f"SIGTERM to pgid {proc.pid} failed: {exc}")
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        pg = os.getpgid(proc.pid)
                        os.killpg(pg, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    except OSError as exc:
                        LogHub().warn("ROOT", f"SIGKILL to pgid {proc.pid} failed: {exc}")
        except OSError as exc:
            LogHub().warn("ROOT", f"_kill_process_tree failed for PID {proc.pid}: {exc}")

    @LogHub.log_call("ROOT")
    def start_root_advertising(self):
        self.mdns_root = MDNSRootAdvertiser(
            hostname=self.hostname,
            port=self.ctrl_port,
            platform=plat.system().lower(),
            cpu_cores=detect_cpu_cores(),
            ram_total=detect_ram()[0],
            ram_available=detect_ram()[1],
            http_port=self.http_port,
        )
        if self.mdns_root.start():
            self.log(f"mDNS advertising as root on {MDNS_ROOT_SERVICE_TYPE}")
            if self.ui:
                self.ui.set_service("mDNS", "running", MDNS_ROOT_SERVICE_TYPE)
        else:
            if self.ui:
                self.ui.set_service("mDNS", "stopped", "zeroconf not installed")

        self.udp = UDPBroadcastDiscovery()
        self.udp_running = True
        t = threading.Thread(target=self._announce_loop, daemon=True)
        t.start()
        if self.ui:
            self.ui.set_service("UDP broadcast", "running", f"port {UDP_DISCOVERY_PORT}")

        self.udp_listener = UDPBroadcastDiscovery()
        err = self.udp_listener.start_listener(self._handle_udp_message)
        if err:
            self.log(err)

        local_ip = self._get_local_ip()
        self.notify("Root on network", f"Announcing as root on {local_ip}:{self.ctrl_port}")

    @LogHub.log_call("ROOT")
    def _announce_loop(self):
        while self.udp_running:
            self.udp.broadcast(make_msg("root_announce",
                hostname=self.hostname, port=self.ctrl_port,
                platform=plat.system().lower(), http_port=self.http_port))
            time.sleep(5)

    @LogHub.log_call("ROOT")
    def _handle_udp_message(self, data, addr):
        try:
            msg = parse_msg(data)
            if msg.get("type") == "worker_discover":
                worker_ip = addr[0]
                if worker_ip not in self._discovered_via_udp:
                    if len(self._discovered_via_udp) >= self._discovered_via_udp_max:
                        self._discovered_via_udp.clear()
                    self._discovered_via_udp.add(worker_ip)
                    hostname = msg.get("hostname", worker_ip)
                    platform = msg.get("platform", "unknown")
                    self.log(f"UDP discovery: worker {hostname} at {worker_ip}")
                    self.notify("Worker looking for root", f"{hostname} ({platform}) at {worker_ip}", urgency="low")
        except Exception as exc:
            LogHub().warn("ROOT", f"UDP message parse failed from {addr[0]}: {exc}")

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

    @LogHub.log_call("ROOT")
    def _handle_worker(self, sock, ip):
        conn = ControlProtocol(sock)
        worker_id = None
        try:
            msg = conn.recv()
            if msg and msg.get("type") == MSG_REGISTER:
                worker_id = f"{ip}:{msg.get('hostname', 'unknown')}"
                info = {
                    "ip": ip,
                    "hostname": msg.get("hostname", "unknown"),
                    "platform": msg.get("platform", "unknown"),
                    "arch": msg.get("arch", "unknown"),
                    "cpu_cores": msg.get("cpu_cores", 0),
                    "ram_total": msg.get("ram_total", 0),
                    "ram_available": msg.get("ram_available", 0),
                    "rpc_port": msg.get("rpc_port", 50052),
                }
                self.registry.register(worker_id, info, conn)
                conn.send(MSG_REGISTER_ACK, worker_id=worker_id, status="active",
                         root_ip=self._get_local_ip())
                self.log(f"Worker registered: {worker_id} ({info['platform']}, "
                      f"{info['cpu_cores']} cores, {info['ram_available']} GB free)")
                if self.ui:
                    self.ui.update_worker(worker_id, info)
                    count = self.registry.get_worker_count()
                    self.ui.set_service("workers", "running", f"{count} connected")
                    self.notify("Worker connected", f"{info['hostname']} ({info['platform']}, {info['cpu_cores']} cores)")
                self._sse_broadcast("status", self._build_status_dict())
                self._worker_comm_loop(conn, worker_id)
        except Exception as e:
            self.log(f"Error handling worker {ip}: {e}")
        finally:
            if worker_id:
                hostname = self.registry.get_info(worker_id)
                self.registry.unregister(worker_id)
                self.log(f"Worker disconnected: {worker_id}")
                if self.ui:
                    self.ui.remove_worker(worker_id)
                    count = self.registry.get_worker_count()
                    self.ui.set_service("workers", "running" if count > 0 else "idle",
                                       f"{count} connected")
                    self.notify("Worker disconnected", hostname)
                self._sse_broadcast("status", self._build_status_dict())

    @LogHub.log_call("ROOT")
    def _worker_comm_loop(self, conn, worker_id):
        while self.running:
            try:
                msg = conn.recv()
                if msg is None:
                    break
                self._handle_worker_message(msg, worker_id)
            except Exception:
                LogHub().exception("ROOT", f"Worker comm error for {worker_id}")
                break

    @LogHub.log_call("ROOT")
    def _handle_worker_message(self, msg, worker_id):
        msg_type = msg.get("type")
        if msg_type == MSG_PING:
            self.registry.update_last_seen(worker_id)
        elif msg_type == MSG_PONG:
            pass
        elif msg_type == MSG_TASK_RESULT:
            task_id = msg.get("id", "")
            self.tasks.record_result(task_id, worker_id, msg)
        elif msg_type == MSG_DISCONNECT:
            self.registry.unregister(worker_id)

    @LogHub.log_call("ROOT")
    def start_mdns_discovery(self):
        self.mdns = MDNSDiscovery(on_worker_found=self._on_mdns_worker_found)
        if self.mdns.start():
            self.log("mDNS discovery started for workers")
        else:
            self.log("mDNS not available (zeroconf not installed)")

    @LogHub.log_call("ROOT")
    def _on_mdns_worker_found(self, worker):
        self.log(f"mDNS found worker: {worker['hostname']} at {worker['ip']}")
        self.notify("Worker discovered", f"{worker['hostname']} ({worker['platform']}) at {worker['ip']}", urgency="low")

    @LogHub.log_call("ROOT")
    def _tail_log(self, log_path, max_lines=40):
        try:
            if not os.path.isfile(log_path):
                return
            with open(log_path, "r", errors="replace") as f:
                lines = f.readlines()
            tail = lines[-max_lines:]
            if tail:
                self.log(f"--- begin tail of {os.path.basename(log_path)} ---")
                for line in tail:
                    self.log(line.rstrip("\n"))
                self.log(f"--- end tail of {os.path.basename(log_path)} ---")
        except Exception as e:
            self.log(f"Could not read log {log_path}: {e}")

    @LogHub.log_call("ROOT")
    def start_local_rpc(self):
        rpc_bin = self._find_rpc_bin()
        if not rpc_bin:
            self.log("No rpc-server binary found; local RPC disabled")
            if self.ui:
                self.ui.set_service("local RPC", "stopped", "binary not found")
            self.notify("Local RPC", "binary not found", urgency="low")
            return False
        os.makedirs(self._log_dir, exist_ok=True)
        rpc_log = os.path.join(self._log_dir, "rpc-server.log")
        with open(rpc_log, "a") as rpc_log_f:
            self.local_rpc_process = subprocess.Popen(
                [rpc_bin, "-H", "127.0.0.1", "-p", str(self.rpc_port), "-t", "4"],
                stdout=rpc_log_f,
                stderr=subprocess.STDOUT,
                env=self._env_with_libpath(),
                text=True,
                start_new_session=True,
            )
        time.sleep(1)
        if self.local_rpc_process.poll() is None:
            self.log(f"Local rpc-server started (PID {self.local_rpc_process.pid})")
            if self.ui:
                self.ui.set_service("local RPC", "running", f"PID {self.local_rpc_process.pid}")
            self._sse_broadcast("status", self._build_status_dict())
            return True
        self.log("Local rpc-server failed to start")
        self.log(f"LD_LIBRARY_PATH={self._env_with_libpath().get('LD_LIBRARY_PATH', '')}")
        self._tail_log(rpc_log)
        if self.ui:
            self.ui.set_service("local RPC", "error", "failed to start")
        self.notify("Local RPC", "failed to start", urgency="critical")
        return False

    @LogHub.log_call("ROOT")
    def start_llama_server(self):
        llama_bin = self._find_llama_bin()
        if not llama_bin:
            self.log("No llama-server binary found; AI mode disabled")
            if self.ui:
                self.ui.set_service("AI server", "stopped", "binary not found")
            self.notify("AI Server", "binary not found", urgency="low")
            return

        model = self.model_path or self._find_model()
        if not model:
            self.log("No GGUF model found; AI mode disabled")
            if self.ui:
                self.ui.set_service("AI server", "stopped", "model not found")
            self.notify("AI Server", "model not found", urgency="low")
            return

        workers = self.registry.get_active()
        endpoints = [f"127.0.0.1:{self.rpc_port}"]
        for wid, info in workers.items():
            endpoints.append(f"{info['ip']}:{info.get('rpc_port', 50052)}")

        rpc_arg = ",".join(endpoints)
        cmd = [
            llama_bin,
            "-m", model,
            "--host", "0.0.0.0",
            "--port", str(self.llama_http_port),
            "--rpc", rpc_arg,
            "-c", "4096",
            "--no-mmap",
            "-ngl", "0",
        ]
        self.log(f"Starting llama-server with {len(endpoints)-1} remote workers...")
        self.log(f"RPC endpoints: {rpc_arg}")
        self.log(f"Command: {' '.join(cmd)}")

        os.makedirs(self._log_dir, exist_ok=True)
        llama_log = os.path.join(self._log_dir, "llama-server.log")

        desired_port = self.llama_http_port
        for _ in range(20):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if s.connect_ex(("127.0.0.1", desired_port)) != 0:
                    break
                desired_port += 1
        if desired_port != self.llama_http_port:
            self.log(f"Port {self.llama_http_port} busy; using fallback HTTP port {desired_port}")
            self.llama_http_port = desired_port
            cmd[cmd.index("--port") + 1] = str(desired_port)

        with open(llama_log, "a") as llama_log_f:
            self.llama_process = subprocess.Popen(
                cmd,
                stdout=llama_log_f,
                stderr=subprocess.STDOUT,
                env=self._env_with_libpath(),
                text=True,
                start_new_session=True,
            )
        time.sleep(3)
        if self.llama_process.poll() is None:
            self.log(f"llama-server running (PID {self.llama_process.pid})")
            self.log(f"LLaMA API: http://{self._get_local_ip()}:{self.llama_http_port}/v1/chat/completions")
            if self.ui:
                self.ui.set_service("AI server", "running", f"PID {self.llama_process.pid}")
            self._sse_broadcast("status", self._build_status_dict())
        else:
            self.log("llama-server failed to start")
            self.log(f"LD_LIBRARY_PATH={self._env_with_libpath().get('LD_LIBRARY_PATH', '')}")
            self._tail_log(llama_log)
            if self.ui:
                self.ui.set_service("AI server", "error", "failed to start")
            self.notify("AI Server", "failed to start", urgency="critical")

    @LogHub.log_call("ROOT")
    def rebuild_llama_server(self):
        if not self.ai_mode:
            self.log("AI mode disabled, skipping rebuild")
            return
        if self.llama_process and self.llama_process.poll() is None:
            self.llama_process.terminate()
            try:
                self.llama_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.llama_process.kill()
        self.start_llama_server()

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

    @LogHub.log_call("ROOT")
    def check_llama_workers(self):
        while self.running and self.ai_mode:
            time.sleep(15)
            active = self.registry.get_active()
            if self.llama_process and self.llama_process.poll() is None:
                endpoints = [f"127.0.0.1:{self.rpc_port}"]
                for wid, info in active.items():
                    endpoints.append(f"{info['ip']}:{info.get('rpc_port', 50052)}")
                rpc_arg = ",".join(endpoints)
                if self.last_rpc_arg != rpc_arg:
                    self.log("Topology changed, rebuilding llama-server...")
                    self.rebuild_llama_server()
                    self.last_rpc_arg = rpc_arg

    @LogHub.log_call("ROOT")
    def run(self):
        self.log(f"Cluster Root starting on {self.hostname}")
        local_ip = self._get_local_ip()
        self.log(f"IP: {local_ip}")

        if self.ui:
            self.ui.set_system_info(
                hostname=self.hostname,
                local_ip=local_ip,
                ai_mode=self.ai_mode,
                platform=plat.system().lower(),
                cpu_cores=detect_cpu_cores(),
                ram_total=detect_ram()[0],
                ram_available=detect_ram()[1],
                http_port=self.http_port,
            )
            self.ui.set_service("TCP server", "starting", f"port {self.ctrl_port}")
            self.ui.set_service("mDNS", "starting", "")
            self.ui.set_service("HTTP API", "starting", f"port {self.http_port}")
            if self.ai_mode:
                self.ui.set_service("AI server", "starting", "")

        if self.ai_mode:
            self.start_local_rpc()

        self.start_mdns_discovery()
        self.start_root_advertising()
        self.start_tcp_server()
        self.start_http_api()

        if self.ai_mode:
            threading.Thread(target=self.check_llama_workers, daemon=True).start()

        self.log(f"Ready. Workers can connect to {local_ip}:{self.ctrl_port}")
        self.log(f"API: http://{local_ip}:{self.http_port}/api/status")
        self.notify("Root ready", f"Workers can connect to {local_ip}:{self.ctrl_port}")

        if self.ai_mode:
            time.sleep(5)
            self.start_llama_server()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.stop()

    @LogHub.log_call("ROOT")
    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        LogHub().info("ROOT", "Shutting down...")
        self.running = False

        if self.llama_process:
            self._kill_process_tree(self.llama_process)
        if self.local_rpc_process:
            self._kill_process_tree(self.local_rpc_process)

        if self.mdns:
            self.mdns.stop()
        if self.mdns_root:
            self.mdns_root.stop()
        self.udp_running = False
        if self.udp_listener:
            self.udp_listener.stop()

        if self.http_server:
            self.http_server.shutdown()

        if self.server_sock:
            self.server_sock.close()

        self.log("Goodbye.")
        send_notification("Cluster Root", "Shutting down")
        if self.ui:
            self.ui.stop()
        LogHub().stop()


@LogHub.log_call("ROOT")
def main(ui=None, **kwargs):
    parser = argparse.ArgumentParser(description="cluster-root — main coordinator")
    parser.add_argument("--port", type=int, default=CTRL_PORT_DEFAULT,
                       help=f"Control port (default: {CTRL_PORT_DEFAULT})")
    parser.add_argument("--rpc-port", type=int, default=RPC_PORT_DEFAULT,
                       help=f"Local RPC port (default: {RPC_PORT_DEFAULT})")
    parser.add_argument("--ai-mode", action="store_true",
                       help="Enable AI inference cluster mode")
    parser.add_argument("--model", default=None,
                       help="Path to GGUF model file")
    parser.add_argument("--http-port", type=int, default=8080,
                       help="HTTP API port (default: 8080)")
    parser.add_argument("--api-token", default=None,
                       help="Bearer token for /api/task/exec (env: AI_CLUSTER_API_TOKEN)")
    args = parser.parse_args()

    ctrl_port = kwargs.get("ctrl_port", args.port)
    rpc_port = kwargs.get("rpc_port", args.rpc_port)
    ai_mode = kwargs.get("ai_mode", args.ai_mode)
    model_path = kwargs.get("model_path", args.model)
    http_port = kwargs.get("http_port", args.http_port) or 8080
    api_token = kwargs.get("api_token", args.api_token)

    root = ClusterRoot(
        ctrl_port=ctrl_port,
        rpc_port=rpc_port,
        ai_mode=ai_mode,
        model_path=model_path,
        http_port=http_port,
        ui=ui,
        api_token=api_token,
    )

    signal.signal(signal.SIGINT, lambda s, f: root.stop())
    signal.signal(signal.SIGTERM, lambda s, f: root.stop())

    root.run()


if __name__ == "__main__":
    main()