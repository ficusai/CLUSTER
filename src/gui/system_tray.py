import os
import threading
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont, QCursor
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from .resources import APP_ICON_SVG, STATUS_ICONS, ICON_COLORS
from common.loghub import LogHub

COLOR_BG = QColor("#2C5F8A")
COLOR_OK = QColor("#2ECC71")
COLOR_WARN = QColor("#F1C40F")
COLOR_ERR = QColor("#E74C3C")
COLOR_IDLE = QColor("#95A5A6")


@LogHub.log_call("GUI")
def _make_tray_pixmap(status="idle", badge=None):
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    bg = COLOR_BG
    painter.setBrush(bg)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, size, size, 12, 12)

    dot_color = {
        "running": COLOR_OK,
        "starting": COLOR_WARN,
        "error": COLOR_ERR,
        "stopped": COLOR_ERR,
        "idle": COLOR_IDLE,
        "discovering": COLOR_WARN,
        "connected": COLOR_OK,
        "disconnected": COLOR_ERR,
    }.get(status, COLOR_IDLE)

    painter.setBrush(dot_color)
    painter.drawEllipse(22, 4, 20, 20)

    painter.setBrush(QColor(255, 255, 255, 180))
    painter.drawEllipse(6, 36, 14, 14)
    painter.drawEllipse(44, 36, 14, 14)

    painter.setPen(QColor(255, 255, 255, 120))
    painter.drawLine(32, 24, 13, 40)
    painter.drawLine(32, 24, 51, 40)

    if badge:
        painter.setBrush(QColor("#E74C3C"))
        painter.setPen(Qt.PenStyle.NoPen)
        font = QFont("sans-serif", 20, QFont.Weight.Bold)
        painter.setFont(font)
        text = str(badge) if badge < 100 else "99+"
        metrics = painter.fontMetrics()
        tw = metrics.horizontalAdvance(text) + 12
        th = metrics.height() + 4
        painter.drawRoundedRect(size - tw - 2, 0, tw, th, 8, 8)
        painter.setPen(QColor("white"))
        painter.drawText(size - tw - 2, 0, tw, th, Qt.AlignmentFlag.AlignCenter, text)

    painter.end()
    return pixmap


_tray_icon_cache = {}


@LogHub.log_call("GUI")
def get_tray_icon(status="idle", badge=None):
    key = (status, badge)
    if key not in _tray_icon_cache:
        pm = _make_tray_pixmap(status, badge)
        icon = QIcon(pm)
        _tray_icon_cache[key] = icon
        if len(_tray_icon_cache) > 20:
            _tray_icon_cache.clear()
    return _tray_icon_cache[key]


class SystemTray(QObject):
    show_window_requested = Signal()
    quit_requested = Signal()

    @LogHub.log_call("GUI")
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = "idle"
        self._worker_count = 0
        self._tray = None
        self._menu = None
        self._setup()

    @LogHub.log_call("GUI")
    def _setup(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = get_tray_icon("idle")
        self._tray = QSystemTrayIcon(icon)
        self._tray.setToolTip("AI Cluster Auto-Connect")

        self._menu = QMenu()

        self._show_action = QAction("Show Window", self._menu)
        self._show_action.triggered.connect(self.show_window_requested.emit)
        self._menu.addAction(self._show_action)

        self._status_action = QAction("Status: Idle")
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)

        self._menu.addSeparator()

        self._quit_action = QAction("Quit", self._menu)
        self._quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(self._quit_action)

        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    @LogHub.log_call("GUI")
    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()

    @LogHub.log_call("GUI")
    def update_status(self, status, worker_count=0):
        self._status = status
        self._worker_count = worker_count
        if not self._tray:
            return
        icon = get_tray_icon(status, worker_count if worker_count > 0 else None)
        self._tray.setIcon(icon)
        tooltip = f"AI Cluster Auto-Connect\nStatus: {status.upper()}"
        if worker_count > 0:
            tooltip += f"\nWorkers: {worker_count}"
        self._tray.setToolTip(tooltip)
        if self._status_action:
            self._status_action.setText(f"Status: {status.upper()} | Workers: {worker_count}")

    @LogHub.log_call("GUI")
    def show_message(self, title, message, icon=QSystemTrayIcon.MessageIcon.Information, duration=5000):
        if self._tray:
            self._tray.showMessage(title, message, icon, duration)

    @LogHub.log_call("GUI")
    def stop(self):
        if self._tray:
            self._tray.hide()
            self._tray = None