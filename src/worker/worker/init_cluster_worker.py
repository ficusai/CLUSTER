"""init_cluster_worker.py — __init__ logic for ClusterWorker."""
import socket
from common.loghub import LogHub
from common.protocol import CTRL_PORT_DEFAULT, RPC_PORT_DEFAULT
from ..detection import detect_platform, detect_cpu_cores, detect_ram


class InitClusterWorkerMixin:
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
