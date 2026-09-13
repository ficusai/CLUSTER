"""handle_worker.py — _handle_worker(sock, ip) for ClusterRoot."""
import sys
from common.loghub import LogHub
from common.protocol import ControlProtocol, MSG_REGISTER
from ..detection import get_local_ip


class HandleWorkerMixin:
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
                         root_ip=get_local_ip())
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
