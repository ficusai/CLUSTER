"""setup_ui.py — _setup_ui() for MainWindow."""
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
from common.loghub import LogHub
from ..resources import APP_ICON_SVG, ICON_COLORS
from ..system_tray import SystemTray, get_tray_icon
from ..tabs.overview_tab import OverviewTab
from ..tabs.topology_tab import TopologyTab
from ..tabs.model_tab import ModelTab
from ..tabs.playground_tab import PlaygroundTab
from ..tabs.deploy_tab import DeployTab
from ..tabs.logs_tab import LogsTab
from ..tabs.settings_tab import SettingsTab


class SetupUiMixin:
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
