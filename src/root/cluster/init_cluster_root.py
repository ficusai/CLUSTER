"""init_cluster_root.py — __init__ logic for ClusterRoot."""
import os
import socket
import threading
from common.loghub import LogHub
from common.protocol import CTRL_PORT_DEFAULT, RPC_PORT_DEFAULT
from ..registry.worker_registry import WorkerRegistry
from ..tasks.task_manager import TaskManager


class InitClusterRootMixin:
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
