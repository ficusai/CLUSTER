import time
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Slot, Signal, QObject
from PySide6.QtGui import QFont, QColor, QPalette, QBrush, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QTextEdit, QGroupBox, QGridLayout, QFrame, QSplitter, QStatusBar,
    QMessageBox, QApplication, QSystemTrayIcon,
)

from .resources import APP_ICON_SVG, ICON_COLORS
from .system_tray import SystemTray, get_tray_icon
from common.loghub import LogHub

from .tabs.overview_tab import OverviewTab
from .tabs.topology_tab import TopologyTab
from .tabs.model_tab import ModelTab
from .tabs.playground_tab import PlaygroundTab
from .tabs.deploy_tab import DeployTab
from .tabs.logs_tab import LogsTab
from .tabs.settings_tab import SettingsTab


DARK_THEME_QSS = """
    QMainWindow, QWidget#CentralWidget {
        background-color: #1a1a2e;
        color: #e0e0e6;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    QFrame#HeaderBar {
        background-color: #16213e;
        border-bottom: 1px solid #0f3460;
        border-radius: 6px;
        padding: 6px 12px;
    }
    QLabel {
        color: #d1d5db;
        font-size: 13px;
    }
    QLabel#AppTitle {
        font-weight: 700;
        font-size: 14px;
        color: #ffffff;
        letter-spacing: 0.5px;
    }
    QLabel#BadgeLive {
        background-color: #0f3460;
        color: #4ade80;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #16537e;
    }
    QLabel#BadgeMode {
        background-color: #0f3460;
        color: #60a5fa;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
    }
    /* Minimal Tab Styling */
    QTabWidget::pane {
        border: 1px solid #0f3460;
        background-color: #16213e;
        border-radius: 6px;
        margin-top: -1px;
    }
    QTabBar::tab {
        background-color: transparent;
        color: #9ca3af;
        padding: 10px 18px;
        margin-right: 2px;
        font-weight: 500;
        border-bottom: 2px solid transparent;
    }
    QTabBar::tab:selected {
        color: #ffffff;
        font-weight: 600;
        border-bottom: 2px solid #e94560;
        background-color: #16213e;
    }
    QTabBar::tab:hover:!selected {
        color: #e2e8f0;
        background-color: rgba(15, 52, 96, 0.3);
    }
    /* Action Buttons */
    QPushButton {
        background-color: #0f3460;
        color: #ffffff;
        border: 1px solid #1a4f8b;
        border-radius: 4px;
        padding: 6px 14px;
        font-weight: 500;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #174276;
    }
    QPushButton#StopBtn {
        background-color: #e94560;
        border: 1px solid #ff5a77;
    }
    QPushButton#StopBtn:hover {
        background-color: #d13b53;
    }
    /* KPI Cards */
    QFrame#KPICard {
        background-color: #1a1a2e;
        border: 1px solid #0f3460;
        border-radius: 6px;
        padding: 12px;
    }
    QStatusBar {
        background-color: #16213e;
        color: #9ca3af;
        border-top: 1px solid #0f3460;
        font-size: 11px;
    }
"""


class MainWindow(QMainWindow):
    @LogHub.log_call("GUI")
    def __init__(self, mode="root"):
        super().__init__()
        self._mode = mode
        self._tray = SystemTray(self)
        self.setStyleSheet(DARK_THEME_QSS)
        self._setup_ui()
        self._setup_connections()

    @LogHub.log_call("GUI")
    def _setup_ui(self):
        self.setWindowTitle("CLUSTER Control Plane")
        self.setMinimumSize(1000, 680)
        self.resize(1120, 720)

        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # 1. Top Control Header Bar
        header = QFrame()
        header.setObjectName("HeaderBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title = QLabel("CLUSTER // CONTROL PLANE")
        title.setObjectName("AppTitle")

        self._status_badge = QLabel("● IDLE")
        self._status_badge.setObjectName("BadgeLive")

        self._mode_badge = QLabel(f"{self._mode.upper()} COORDINATOR" if self._mode == "root" else f"{self._mode.upper()} NODE")
        self._mode_badge.setObjectName("BadgeMode")

        header_layout.addWidget(title)
        header_layout.addSpacing(8)
        header_layout.addWidget(self._status_badge)
        header_layout.addWidget(self._mode_badge)
        header_layout.addStretch()

        self._btn_start = QPushButton("Start Cluster")
        self._btn_stop = QPushButton("Stop")
        self._btn_stop.setObjectName("StopBtn")
        self._btn_reload = QPushButton("Reload Model")
        self._btn_tray = QPushButton("Minimize to Tray")

        header_layout.addWidget(self._btn_start)
        header_layout.addWidget(self._btn_stop)
        header_layout.addWidget(self._btn_reload)
        header_layout.addWidget(self._btn_tray)
        root_layout.addWidget(header)

        # 2. Minimal Multi-Tab Hub
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self.tab_overview = OverviewTab()
        self.tab_topology = TopologyTab()
        self.tab_model = ModelTab()
        self.tab_playground = PlaygroundTab()
        self.tab_deploy = DeployTab()
        self.tab_logs = LogsTab()
        self.tab_settings = SettingsTab()

        self._tabs.addTab(self.tab_overview, "📊 Overview")
        self._tabs.addTab(self.tab_topology, "🌐 Node Topology")
        self._tabs.addTab(self.tab_model, "🧠 Model & Offload")
        self._tabs.addTab(self.tab_playground, "💬 Playground")
        self._tabs.addTab(self.tab_deploy, "🚀 Deploy Wizard")
        self._tabs.addTab(self.tab_logs, "📝 Multi-Log Hub")
        self._tabs.addTab(self.tab_settings, "⚙️ Settings")

        root_layout.addWidget(self._tabs, stretch=1)

        # 3. Status Bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_bar_label = QLabel("Ready | Bridge: Listening on IPC/RPC | Branch: feature/gui-interface")
        status_bar.addWidget(self._status_bar_label)

        pm = get_tray_icon("idle").pixmap(32, 32)
        if pm and not pm.isNull():
            self.setWindowIcon(get_tray_icon("idle"))

    @LogHub.log_call("GUI")
    def _setup_connections(self):
        self._btn_tray.clicked.connect(self.hide)
        self._tray.show_window_requested.connect(self.show_window)
        self._tray.quit_requested.connect(self._on_quit)

    @LogHub.log_call("GUI")
    def show_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    @Slot()
    @LogHub.log_call("GUI")
    def _on_quit(self):
        QApplication.instance().quit()

    @LogHub.log_call("GUI")
    def update_status(self, status, worker_count=0):
        self._status_badge.setText(f"● {status.upper()}")
        if "kpi_nodes" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_nodes"].setText(f"{worker_count} Active")
        self._tray.update_status(status, worker_count)

    @LogHub.log_call("GUI")
    def update_worker_table(self, workers):
        if hasattr(self.tab_overview, "kpi_labels") and "kpi_nodes" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_nodes"].setText(f"{len(workers)} Active")

    @LogHub.log_call("GUI")
    def clear_workers(self):
        if hasattr(self.tab_overview, "kpi_labels") and "kpi_nodes" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_nodes"].setText("0 Active")

    @LogHub.log_call("GUI")
    def add_event(self, message):
        pass

    @LogHub.log_call("GUI")
    def set_service(self, name, status, detail=""):
        mapping = {
            "mDNS": "mdns",
            "REST API": "http",
            "RPC": "rpc",
            "LLaMA Server": "llama",
        }
        key = mapping.get(name)
        if key and key in self.tab_overview.service_badges:
            badge = self.tab_overview.service_badges[key]
            symbol = "✓" if status.lower() in ("running", "ready", "online", "active") else "○"
            badge.setText(f"{symbol} {name}: {status.title()}")
            color = "#4ade80" if status.lower() in ("running", "ready", "online", "active") else "#9ca3af"
            badge.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500;")

    @LogHub.log_call("GUI")
    def set_system_info(self, **kwargs):
        if "cpu_cores" in kwargs and "kpi_cpu" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_cpu"].setText(f"{kwargs['cpu_cores']} Cores")
        if "ram_total" in kwargs and "ram_available" in kwargs and "kpi_ram" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_ram"].setText(f"{kwargs['ram_available']} GB / {kwargs['ram_total']} GB")

    @LogHub.log_call("GUI")
    def set_uptime(self, uptime_str):
        pass

    @LogHub.log_call("GUI")
    def set_status_bar(self, text):
        self._status_bar_label.setText(text)

    @LogHub.log_call("GUI")
    def stop(self):
        self._tray.stop()

    @LogHub.log_call("GUI")
    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.hide()
        self._tray.show_message(
            "CLUSTER Control Plane",
            "Still running in system tray. Double-click to restore.",
            QSystemTrayIcon.MessageIcon.Information,
        )
