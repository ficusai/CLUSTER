"""worker_registry.py — WorkerRegistry class composed from per-method mixins."""
import threading
from common.loghub import LogHub
from .register import RegisterMixin
from .unregister import UnregisterMixin
from .get_active import GetActiveMixin
from .get_all import GetAllMixin
from .get_worker_count import GetWorkerCountMixin
from .get_connection import GetConnectionMixin
from .get_info import GetInfoMixin
from .update_last_seen import UpdateLastSeenMixin


class WorkerRegistry(RegisterMixin, UnregisterMixin, GetActiveMixin, GetAllMixin,
                     GetWorkerCountMixin, GetConnectionMixin,
                     GetInfoMixin, UpdateLastSeenMixin):
    @LogHub.log_call("ROOT")
    def __init__(self):
        self.workers = {}
        self.lock = threading.Lock()
