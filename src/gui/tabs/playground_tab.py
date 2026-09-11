from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class PlaygroundTab(QWidget):
    def __init__(self, bridge=None, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("💬 Prompt Console & Real-time Telemetry (TTFT, t/s)")
        lbl.setStyleSheet("color: #6b7280; font-size: 14px; font-weight: 500;")
        layout.addWidget(lbl)
