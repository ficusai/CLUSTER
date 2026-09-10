import time
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Slot
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


COLOR_BG_DARK = QColor("#1a1a2e")
COLOR_BG_CARD = QColor("#16213e")
COLOR_BG_INNER = QColor("#0f3460")
COLOR_ACCENT = QColor("#e94560")
COLOR_TEXT = QColor("#e0e0e0")
COLOR_TEXT_DIM = QColor("#8899aa")
COLOR_GREEN = QColor("#2ECC71")
COLOR_YELLOW = QColor("#F1C40F")
COLOR_RED = QColor("#E74C3C")
COLOR_CYAN = QColor("#00d2ff")


class StatusIndicator(QFrame):
    @LogHub.log_call("GUI")
    def __init__(self, label, color=COLOR_TEXT_DIM, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.setStyleSheet(f"""
            StatusIndicator {{
                background-color: {color.name()};
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
        """)
        self._color = color

    @LogHub.log_call("GUI")
    def set_color(self, color):
        self._color = color
        self.setStyleSheet(f"""
            StatusIndicator {{
                background-color: {color.name()};
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
        """)


class InfoCard(QFrame):
    @LogHub.log_call("GUI")
    def __init__(self, title, value="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            InfoCard {{
                background-color: {COLOR_BG_CARD.name()};
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(f"color: {COLOR_TEXT_DIM.name()}; font-size: 11px;")
        title_font = QFont("sans-serif", 9)
        title_font.setWeight(QFont.Weight.Light)
        self._title_label.setFont(title_font)
        layout.addWidget(self._title_label)

        self._value_label = QLabel(value)
        self._value_label.setStyleSheet(f"color: {COLOR_CYAN.name()}; font-size: 18px; font-weight: bold;")
        layout.addWidget(self._value_label)

    @LogHub.log_call("GUI")
    def set_value(self, value):
        self._value_label.setText(str(value))


class WorkerTable(QTableWidget):
    @LogHub.log_call("GUI")
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Hostname", "Platform", "CPU Cores", "RAM (GB)", "IP"])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)

        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLOR_BG_CARD.name()};
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                color: {COLOR_TEXT.name()};
                font-size: 12px;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #1e1e3a;
            }}
            QTableWidget::item:selected {{
                background-color: {COLOR_BG_INNER.name()};
                color: {COLOR_CYAN.name()};
            }}
            QHeaderView::section {{
                background-color: {COLOR_BG_DARK.name()};
                color: {COLOR_TEXT_DIM.name()};
                padding: 6px 10px;
                border: none;
                border-bottom: 1px solid #2a2a4a;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        self._name_to_ip = {}

    @LogHub.log_call("GUI")
    def update_workers(self, workers):
        self._name_to_ip = {}
        ip_to_host = {}
        host_order = []
        for wid, info in workers.items():
            host = info.get("hostname", wid)
            ip = info.get("ip", wid.split(":")[0] if ":" in wid else wid)
            ip_to_host[ip] = host
            if host not in host_order:
                host_order.append(host)
            self._name_to_ip[host] = ip

        self.setRowCount(len(host_order))
        for row, host in enumerate(host_order):
            ip = self._name_to_ip[host]
            wid = next((k for k in workers if workers[k].get("hostname") == host or k == host or workers[k].get("ip") == host), None)
            info = workers.get(wid, {})

            self._set_item(row, 0, host)
            self._set_item(row, 1, info.get("platform", "?"))
            self._set_item(row, 2, str(info.get("cpu_cores", "?")))
            ram = info.get("ram_available", 0)
            self._set_item(row, 3, f"{ram}" if ram else "?")
            self._set_item(row, 4, ip)

    @LogHub.log_call("GUI")
    def _set_item(self, row, col, text):
        item = QTableWidgetItem(str(text))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, col, item)

    @LogHub.log_call("GUI")
    def clear_workers(self):
        self.setRowCount(0)


class EventLog(QTextEdit):
    MAX_EVENTS = 500

    @LogHub.log_call("GUI")
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BG_DARK.name()};
                color: {COLOR_TEXT.name()};
                border: 1px solid #2a2a4a;
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        self._count = 0

    @LogHub.log_call("GUI")
    def append_event(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        color = COLOR_TEXT_DIM.name()
        if "error" in message.lower() or "fail" in message.lower():
            color = COLOR_RED.name()
        elif "connect" in message.lower() or "register" in message.lower():
            color = COLOR_GREEN.name()
        elif "disconnect" in message.lower() or "lost" in message.lower():
            color = COLOR_YELLOW.name()

        html = f'<span style="color: {COLOR_TEXT_DIM.name()}">[{ts}]</span> <span style="color: {color}">{self._escape(message)}</span><br/>'
        self.insertHtml(html)
        self._count += 1

        if self._count > self.MAX_EVENTS:
            doc = self.document()
            block = doc.begin()
            while self._count > self.MAX_EVENTS:
                block = block.next()
                self._count -= 1
            cursor = self.textCursor()
            cursor.moveStart(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, self._count - self.MAX_EVENTS)
            cursor.removeSelectedText()

        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @staticmethod
    @LogHub.log_call("GUI")
    def _escape(text):
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class ServicesGroup(QFrame):
    @LogHub.log_call("GUI")
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            ServicesGroup {{
                background-color: {COLOR_BG_CARD.name()};
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        title = QLabel("Services")
        title.setStyleSheet(f"color: {COLOR_TEXT.name()}; font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        self._service_widgets = {}

    @LogHub.log_call("GUI")
    def update_service(self, name, status, detail=""):
        if name not in self._service_widgets:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            indicator = StatusIndicator(name)
            row_layout.addWidget(indicator)

            name_label = QLabel(name)
            name_label.setStyleSheet(f"color: {COLOR_TEXT.name()}; font-size: 12px;")
            name_label.setFixedWidth(140)
            row_layout.addWidget(name_label)

            status_label = QLabel(status.upper())
            status_label.setStyleSheet(f"color: {COLOR_TEXT_DIM.name()}; font-size: 11px;")
            row_layout.addWidget(status_label)

            detail_label = QLabel(detail)
            detail_label.setStyleSheet(f"color: {COLOR_TEXT_DIM.name()}; font-size: 10px;")
            row_layout.addWidget(detail_label, 1)

            self._service_widgets[name] = (indicator, status_label, detail_label)
            self.layout().addWidget(row)
        else:
            indicator, status_label, detail_label = self._service_widgets[name]

        color_str = ICON_COLORS.get(status, "#95A5A6")
        color = QColor(color_str)
        indicator.set_color(color)
        status_label.setText(status.upper())
        status_label.setStyleSheet(f"color: {color_str}; font-size: 11px; font-weight: bold;")
        detail_label.setText(detail)


class SystemInfoPanel(QFrame):
    @LogHub.log_call("GUI")
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            SystemInfoPanel {{
                background-color: {COLOR_BG_CARD.name()};
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        title = QLabel("System Info")
        title.setStyleSheet(f"color: {COLOR_TEXT.name()}; font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        self._labels = {}

    @LogHub.log_call("GUI")
    def set_info(self, key, value):
        if key not in self._labels:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            k = QLabel(f"{key}:")
            k.setStyleSheet(f"color: {COLOR_TEXT_DIM.name()}; font-size: 11px;")
            k.setFixedWidth(100)
            row_layout.addWidget(k)

            v = QLabel(str(value))
            v.setStyleSheet(f"color: {COLOR_CYAN.name()}; font-size: 11px; font-weight: bold;")
            row_layout.addWidget(v, 1)

            self._labels[key] = v
            self.layout().addWidget(row_widget)
        else:
            self._labels[key].setText(str(value))


class MainWindow(QMainWindow):
    @LogHub.log_call("GUI")
    def __init__(self, mode="root"):
        super().__init__()
        self._mode = mode
        self._tray = SystemTray(self)
        self._setup_ui()
        self._setup_connections()

    @LogHub.log_call("GUI")
    def _setup_ui(self):
        self.setWindowTitle("AI Cluster Auto-Connect")
        self.setMinimumSize(900, 620)
        self.resize(1100, 720)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_BG_DARK.name()};
            }}
            QLabel {{
                color: {COLOR_TEXT.name()};
            }}
            QPushButton {{
                background-color: {COLOR_ACCENT.name()};
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
            QPushButton:pressed {{
                background-color: #a93226;
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
            QTabWidget::pane {{
                background-color: {COLOR_BG_DARK.name()};
                border: none;
            }}
            QTabBar::tab {{
                background-color: {COLOR_BG_CARD.name()};
                color: {COLOR_TEXT_DIM.name()};
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLOR_BG_INNER.name()};
                color: {COLOR_CYAN.name()};
                border-bottom: 2px solid {COLOR_ACCENT.name()};
            }}
            QTabBar::tab:hover {{
                background-color: {COLOR_BG_INNER.name()};
                color: {COLOR_TEXT.name()};
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("AI Cluster Auto-Connect")
        title.setStyleSheet(f"color: {COLOR_CYAN.name()}; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        self._status_indicator = StatusIndicator("idle", QColor("#95A5A6"))
        header_layout.addWidget(self._status_indicator)

        self._status_label = QLabel("IDLE")
        self._status_label.setStyleSheet(f"color: {COLOR_TEXT_DIM.name()}; font-size: 13px;")
        header_layout.addWidget(self._status_label)

        header_layout.addStretch()

        mode_label = QLabel(self._mode.upper())
        mode_label.setStyleSheet(f"""
            color: {'#2ECC71' if self._mode == 'root' else '#F1C40F'};
            background-color: rgba(255,255,255,0.05);
            padding: 4px 14px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(mode_label)

        self._minimize_btn = QPushButton("Minimize to Tray")
        self._minimize_btn.setFixedWidth(140)
        self._minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXT_DIM.name()};
                border: 1px solid #2a2a4a;
                padding: 6px 14px;
                border-radius: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.05);
                color: {COLOR_TEXT.name()};
            }}
        """)
        header_layout.addWidget(self._minimize_btn)

        main_layout.addWidget(header)

        summary = QWidget()
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(8)

        self._card_workers = InfoCard("Workers", "0")
        summary_layout.addWidget(self._card_workers)

        self._card_uptime = InfoCard("Uptime", "0m 0s")
        summary_layout.addWidget(self._card_uptime)

        self._card_cpu = InfoCard("CPU Cores", "?")
        summary_layout.addWidget(self._card_cpu)

        self._card_ram = InfoCard("RAM", "? / ? GB")
        summary_layout.addWidget(self._card_ram)

        main_layout.addWidget(summary)

        self._tabs = QTabWidget()
        main_layout.addWidget(self._tabs, 1)

        workers_tab = QWidget()
        workers_layout = QVBoxLayout(workers_tab)
        workers_layout.setContentsMargins(0, 4, 0, 0)
        self._worker_table = WorkerTable()
        workers_layout.addWidget(self._worker_table)
        self._tabs.addTab(workers_tab, "Workers")

        services_tab = QWidget()
        services_layout = QVBoxLayout(services_tab)
        services_layout.setContentsMargins(0, 4, 0, 0)

        left_right = QWidget()
        lr_layout = QHBoxLayout(left_right)
        lr_layout.setContentsMargins(0, 0, 0, 0)
        lr_layout.setSpacing(8)

        self._services_group = ServicesGroup()
        lr_layout.addWidget(self._services_group, 1)

        self._system_info = SystemInfoPanel()
        lr_layout.addWidget(self._system_info, 1)

        services_layout.addWidget(left_right)
        self._tabs.addTab(services_tab, "Services")

        events_tab = QWidget()
        events_layout = QVBoxLayout(events_tab)
        events_layout.setContentsMargins(0, 4, 0, 0)
        self._event_log = EventLog()
        events_layout.addWidget(self._event_log)
        self._tabs.addTab(events_tab, "Events")

        status_bar = QStatusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLOR_BG_CARD.name()};
                color: {COLOR_TEXT_DIM.name()};
                border-top: 1px solid #2a2a4a;
                font-size: 11px;
            }}
        """)
        self._status_bar_label = QLabel("Ready")
        status_bar.addWidget(self._status_bar_label)
        self.setStatusBar(status_bar)

        pm = get_tray_icon("idle").pixmap(32, 32)
        if pm and not pm.isNull():
            self.setWindowIcon(get_tray_icon("idle"))

    @LogHub.log_call("GUI")
    def _setup_connections(self):
        self._minimize_btn.clicked.connect(self.hide)
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
        color_map = {
            "running": COLOR_GREEN,
            "starting": COLOR_YELLOW,
            "error": COLOR_RED,
            "stopped": COLOR_RED,
            "idle": COLOR_TEXT_DIM,
            "discovering": COLOR_YELLOW,
            "connected": COLOR_GREEN,
            "disconnected": COLOR_RED,
        }
        color = color_map.get(status, COLOR_TEXT_DIM)
        self._status_indicator.set_color(color)
        self._status_label.setText(status.upper())
        self._status_label.setStyleSheet(f"color: {color.name()}; font-size: 13px; font-weight: bold;")

        self._card_workers.set_value(str(worker_count))
        self._tray.update_status(status, worker_count)

    @LogHub.log_call("GUI")
    def update_worker_table(self, workers):
        self._worker_table.update_workers(workers)

    @LogHub.log_call("GUI")
    def clear_workers(self):
        self._worker_table.clear_workers()

    @LogHub.log_call("GUI")
    def add_event(self, message):
        self._event_log.append_event(message)

    @LogHub.log_call("GUI")
    def set_service(self, name, status, detail=""):
        self._services_group.update_service(name, status, detail)

    @LogHub.log_call("GUI")
    def set_system_info(self, **kwargs):
        for k, v in kwargs.items():
            label_map = {
                "hostname": "Hostname",
                "local_ip": "IP Address",
                "platform": "Platform",
                "cpu_cores": "CPU Cores",
                "ram_total": "RAM Total",
                "ram_available": "RAM Available",
                "ai_mode": "AI Mode",
                "http_port": "HTTP Port",
                "version": "Version",
            }
            display_key = label_map.get(k, k.replace("_", " ").title())
            self._system_info.set_info(display_key, v)

        if "cpu_cores" in kwargs:
            self._card_cpu.set_value(str(kwargs["cpu_cores"]))
        if "ram_total" in kwargs and "ram_available" in kwargs:
            self._card_ram.set_value(f"{kwargs['ram_available']} / {kwargs['ram_total']} GB")

    @LogHub.log_call("GUI")
    def set_uptime(self, uptime_str):
        self._card_uptime.set_value(uptime_str)

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
            "AI Cluster Auto-Connect",
            "Still running in system tray. Double-click to restore.",
            QSystemTrayIcon.MessageIcon.Information,
        )