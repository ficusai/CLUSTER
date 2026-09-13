"""cluster_worker.py — ClusterWorker class composed from per-method mixins."""
from .init_cluster_worker import InitClusterWorkerMixin
from .log import LogMixin
from .notify import NotifyMixin
from .start_advertising import StartAdvertisingMixin
from .stop_advertising import StopAdvertisingMixin
from .discover_root import DiscoverRootMixin
from .register_with_root import RegisterWithRootMixin
from .handle_connection import HandleConnectionMixin
from .heartbeat import HeartbeatMixin
from .read_loop import ReadLoopMixin
from .handle_message import HandleMessageMixin
from .execute_task import ExecuteTaskMixin
from .handle_exec import HandleExecMixin
from .handle_exec_async import HandleExecAsyncMixin
from .handle_ping import HandlePingMixin
from .load_ai_config import LoadAiConfigMixin
from .find_model import FindModelMixin
from .kill_process_tree import KillProcessTreeMixin
from .handle_start_rpc import HandleStartRpcMixin
from .handle_stop_rpc import HandleStopRpcMixin
from .reconnect import ReconnectMixin
from .stop import StopMixin
from .run import RunMixin


class ClusterWorker(
    InitClusterWorkerMixin,
    LogMixin,
    NotifyMixin,
    StartAdvertisingMixin,
    StopAdvertisingMixin,
    DiscoverRootMixin,
    RegisterWithRootMixin,
    HandleConnectionMixin,
    HeartbeatMixin,
    ReadLoopMixin,
    HandleMessageMixin,
    ExecuteTaskMixin,
    HandleExecMixin,
    HandleExecAsyncMixin,
    HandlePingMixin,
    LoadAiConfigMixin,
    FindModelMixin,
    KillProcessTreeMixin,
    HandleStartRpcMixin,
    HandleStopRpcMixin,
    ReconnectMixin,
    StopMixin,
    RunMixin,
):
    pass
