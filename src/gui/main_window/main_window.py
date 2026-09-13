"""main_window.py — MainWindow class composed from per-method mixins."""
from .init_main_window import InitMainWindowMixin
from .setup_ui import SetupUiMixin
from .setup_connections import SetupConnectionsMixin
from .show_window import ShowWindowMixin
from .on_quit import OnQuitMixin
from .update_status import UpdateStatusMixin
from .update_worker_table import UpdateWorkerTableMixin
from .clear_workers import ClearWorkersMixin
from .add_event import AddEventMixin
from .set_service import SetServiceMixin
from .set_system_info import SetSystemInfoMixin
from .set_uptime import SetUptimeMixin
from .set_status_bar import SetStatusBarMixin
from .stop import StopMixin
from .close_event import CloseEventMixin


class MainWindow(
    InitMainWindowMixin,
    SetupUiMixin,
    SetupConnectionsMixin,
    ShowWindowMixin,
    OnQuitMixin,
    UpdateStatusMixin,
    UpdateWorkerTableMixin,
    ClearWorkersMixin,
    AddEventMixin,
    SetServiceMixin,
    SetSystemInfoMixin,
    SetUptimeMixin,
    SetStatusBarMixin,
    StopMixin,
    CloseEventMixin,
):
    pass
