"""loghub.py — LogHub class composed from per-method mixins."""
from .init_loghub import InitLogHubMixin
from .get_log_path import GetLogPathMixin
from .rotate import RotateMixin
from .find_caller import FindCallerMixin
from .write_entry import WriteEntryMixin
from .write_to_real_stdout import WriteToRealStdoutMixin
from .write_to_real_stderr import WriteToRealStderrMixin
from .capture_write import CaptureWriteMixin
from .capture_flush import CaptureFlushMixin
from .info import InfoMixin
from .warn import WarnMixin
from .error import ErrorMixin
from .exception import ExceptionMixin
from .global_excepthook import GlobalExceptHookMixin
from .thread_excepthook import ThreadExceptHookMixin
from .log_call_decorator import LogCallMixin
from .notify_orchestrator import NotifyOrchestratorMixin
from .stop import StopMixin


class LogHub(
    InitLogHubMixin,
    GetLogPathMixin,
    RotateMixin,
    FindCallerMixin,
    WriteEntryMixin,
    WriteToRealStdoutMixin,
    WriteToRealStderrMixin,
    CaptureWriteMixin,
    CaptureFlushMixin,
    InfoMixin,
    WarnMixin,
    ErrorMixin,
    ExceptionMixin,
    GlobalExceptHookMixin,
    ThreadExceptHookMixin,
    LogCallMixin,
    NotifyOrchestratorMixin,
    StopMixin,
):
    pass
