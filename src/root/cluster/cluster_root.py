"""cluster_root.py — ClusterRoot class composed from per-method mixins."""
from .init_cluster_root import InitClusterRootMixin
from .log import LogMixin
from .notify import NotifyMixin
from .build_status_dict import BuildStatusDictMixin
from .sse_broadcast import SseBroadcastMixin
from .get_local_ip import GetLocalIpMixin
from .find_bin_dir import FindBinDirMixin
from .find_llama_bin import FindLlamaBinMixin
from .find_rpc_bin import FindRpcBinMixin
from .env_with_libpath import EnvWithLibpathMixin
from .find_model import FindModelMixin
from .ollama_get import OllamaGetMixin
from .ollama_available import OllamaAvailableMixin
from .get_ollama_models import GetOllamaModelsMixin
from .get_bundled_gguf_models import GetBundledGgufModelsMixin
from .kill_process_tree import KillProcessTreeMixin
from .start_root_advertising import StartRootAdvertisingMixin
from .announce_loop import AnnounceLoopMixin
from .handle_udp_message import HandleUdpMessageMixin
from .start_tcp_server import StartTcpServerMixin
from .accept_loop import AcceptLoopMixin
from .handle_worker import HandleWorkerMixin
from .worker_comm_loop import WorkerCommLoopMixin
from .handle_worker_message import HandleWorkerMessageMixin
from .start_mdns_discovery import StartMdnsDiscoveryMixin
from .on_mdns_worker_found import OnMdnsWorkerFoundMixin
from .tail_log import TailLogMixin
from .start_local_rpc import StartLocalRpcMixin
from .start_llama_server import StartLlamaServerMixin
from .rebuild_llama_server import RebuildLlamaServerMixin
from .start_http_api import StartHttpApiMixin
from .check_llama_workers import CheckLlamaWorkersMixin
from .run import RunMixin
from .stop import StopMixin


class ClusterRoot(
    InitClusterRootMixin,
    LogMixin,
    NotifyMixin,
    BuildStatusDictMixin,
    SseBroadcastMixin,
    GetLocalIpMixin,
    FindBinDirMixin,
    FindLlamaBinMixin,
    FindRpcBinMixin,
    EnvWithLibpathMixin,
    FindModelMixin,
    OllamaGetMixin,
    OllamaAvailableMixin,
    GetOllamaModelsMixin,
    GetBundledGgufModelsMixin,
    KillProcessTreeMixin,
    StartRootAdvertisingMixin,
    AnnounceLoopMixin,
    HandleUdpMessageMixin,
    StartTcpServerMixin,
    AcceptLoopMixin,
    HandleWorkerMixin,
    WorkerCommLoopMixin,
    HandleWorkerMessageMixin,
    StartMdnsDiscoveryMixin,
    OnMdnsWorkerFoundMixin,
    TailLogMixin,
    StartLocalRpcMixin,
    StartLlamaServerMixin,
    RebuildLlamaServerMixin,
    StartHttpApiMixin,
    CheckLlamaWorkersMixin,
    RunMixin,
    StopMixin,
):
    pass
