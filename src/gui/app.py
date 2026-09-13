import os
import sys
import threading
import time
import signal

from common.loghub import LogHub
from PySide6.QtCore import QTimer, Signal, QObject, Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from .main_window.main_window import MainWindow
from .resources import APP_ICON_SVG
from .system_tray import SystemTray


class ClusterBridge(QObject):
    status_changed = Signal(str, int)
    worker_updated = Signal(object)
    worker_removed = Signal(str)
    service_updated = Signal(str, str, str)
    event_added = Signal(str)
    system_info_updated = Signal(object)
    uptime_updated = Signal(str)
    status_bar_updated = Signal(str)
    error_occurred = Signal(str)

    @LogHub.log_call("GUI")
    def __init__(self, mode="root"):
        super().__init__()
        self._mode = mode
        self._cluster = None
        self._running = False
        self._start_time = time.time()

    @LogHub.log_call("GUI")
    def set_cluster(self, cluster):
        self._cluster = cluster
        cluster.ui = self

    @LogHub.log_call("GUI")
    def log(self, msg):
        LogHub().info(self._mode.upper(), msg)
        print(f"[{self._mode}] {msg}")
        self.event_added.emit(msg)

    @LogHub.log_call("GUI")
    def notify(self, title, message, urgency="normal"):
        self.event_added.emit(f"{title}: {message}")
        self.status_bar_updated.emit(message)

    @LogHub.log_call("GUI")
    def set_service(self, name, status, detail=""):
        if self._mode == "worker" and name == "mDNS":
            pass
        self.service_updated.emit(name, status, detail)

    @LogHub.log_call("GUI")
    def add_event(self, message, notify=True):
        self.event_added.emit(message)

    @LogHub.log_call("GUI")
    def update_worker(self, worker_id, info):
        self.worker_updated.emit({worker_id: info})

    @LogHub.log_call("GUI")
    def remove_worker(self, worker_id):
        self.worker_removed.emit(worker_id)

    @LogHub.log_call("GUI")
    def set_connection(self, status, root_ip=None, registered=False):
        self.status_changed.emit(status, 0)
        if root_ip:
            self.system_info_updated.emit({"Root IP": root_ip})
        if registered:
            self.system_info_updated.emit({"Registered": "Yes"})

    @LogHub.log_call("GUI")
    def set_system_info(self, **kwargs):
        self.system_info_updated.emit(kwargs)

    @LogHub.log_call("GUI")
    def run_cluster(self, cluster_fn, **kwargs):
        @LogHub.log_call("GUI")
        def target():
            self._running = True
            try:
                cluster_fn(**kwargs)
            except Exception as e:
                self.error_occurred.emit(str(e))
                import traceback
                traceback.print_exc()
                LogHub().exception("GUI", "cluster_fn failed")
            finally:
                self._running = False
        t = threading.Thread(target=target, daemon=True)
        t.start()

    @LogHub.log_call("GUI")
    def stop_cluster(self):
        if self._cluster:
            try:
                self._cluster.stop()
            except Exception:
                pass

    @LogHub.log_call("GUI")
    def get_uptime(self):
        elapsed = int(time.time() - self._start_time)
        return f"{elapsed // 60}m {elapsed % 60}s"


@LogHub.log_call("GUI")
def run_gui(mode, cluster_fn=None, **cluster_kwargs):
    app = QApplication(sys.argv)
    app.setApplicationName("AI Cluster Auto-Connect")
    app.setOrganizationName("AICluster")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(mode=mode)
    bridge = ClusterBridge(mode=mode)

    window.set_system_info(version=cluster_kwargs.get("version", ""))
    window.update_status("starting")

    bridge.status_changed.connect(window.update_status)
    bridge.worker_updated.connect(window.update_worker_table)
    bridge.service_updated.connect(window.set_service)
    bridge.event_added.connect(window.add_event)
    bridge.system_info_updated.connect(window.set_system_info)
    bridge.uptime_updated.connect(window.set_uptime)
    bridge.status_bar_updated.connect(window.set_status_bar)

    @LogHub.log_call("GUI")
    def on_worker_removed(wid):
        pass
    bridge.worker_removed.connect(on_worker_removed)

    uptime_timer = QTimer()
    uptime_timer.timeout.connect(lambda: window.set_uptime(bridge.get_uptime()))
    uptime_timer.start(1000)

    @LogHub.log_call("GUI")
    def on_error(msg):
        window.set_status_bar(f"Error: {msg}")
        window._tray.show_message(
            "Cluster Error", msg,
            QSystemTrayIcon.MessageIcon.Critical,
        )
    bridge.error_occurred.connect(on_error)

    @LogHub.log_call("GUI")
    def on_cluster_exit():
        if not bridge._running:
            window.update_status("stopped")
            window.set_status_bar("Cluster stopped")
            window._tray.show_message(
                "Cluster Stopped", "The cluster process has stopped.",
                QSystemTrayIcon.MessageIcon.Information,
            )
    exit_checker = QTimer()
    exit_checker.timeout.connect(on_cluster_exit)
    exit_checker.start(2000)

    if cluster_fn:
        bridge.run_cluster(cluster_fn, **cluster_kwargs)

    @LogHub.log_call("GUI")
    def cleanup():
        bridge.stop_cluster()
        window.stop()
    app.aboutToQuit.connect(cleanup)

    window.show()
    sys.exit(app.exec())