"""task_manager.py — TaskManager class composed from per-method mixins."""
import threading
from common.loghub import LogHub
from .dispatch_task import DispatchTaskMixin
from .record_result import RecordResultMixin
from .get_result import GetResultMixin


class TaskManager(DispatchTaskMixin, RecordResultMixin, GetResultMixin):
    @LogHub.log_call("ROOT")
    def __init__(self, registry):
        self.registry = registry
        self.pending = {}
        self.results = {}
        self.lock = threading.Lock()
        self.next_id = 1
