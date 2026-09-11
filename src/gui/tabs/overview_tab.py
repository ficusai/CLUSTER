from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QFrame, QLabel, QHBoxLayout

class OverviewTab(QWidget):
    def __init__(self, bridge=None, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # KPI Metrics Row
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        cards = [
            ("CONNECTED NODES", "0 Active", "kpi_nodes"),
            ("TOTAL RAM POOL", "? GB / ? GB", "kpi_ram"),
            ("TOTAL CPU CORES", "? Cores", "kpi_cpu"),
            ("INFERENCE SPEED", "0 t/s", "kpi_speed")
        ]

        self.kpi_labels = {}
        for i, (title, val, key) in enumerate(cards):
            card = QFrame()
            card.setObjectName("KPICard")
            c_layout = QVBoxLayout(card)
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("color: #9ca3af; font-size: 11px; font-weight: 600;")
            lbl_val = QLabel(val)
            lbl_val.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 700; margin-top: 4px;")
            self.kpi_labels[key] = lbl_val
            c_layout.addWidget(lbl_title)
            c_layout.addWidget(lbl_val)
            kpi_grid.addWidget(card, 0, i)

        layout.addLayout(kpi_grid)

        # Service Indicators
        services_frame = QFrame()
        services_frame.setObjectName("KPICard")
        s_layout = QHBoxLayout(services_frame)
        self.service_badges = {}
        
        for svc_id, svc_name in [("mdns", "mDNS Discovery"), ("http", "Root HTTP API"), ("rpc", "RPC Engine"), ("llama", "LLaMA Server")]:
            badge = QLabel(f"○ {svc_name}: Idle")
            badge.setStyleSheet("color: #9ca3af; font-size: 12px; font-weight: 500;")
            self.service_badges[svc_id] = badge
            s_layout.addWidget(badge)
            
        layout.addWidget(services_frame)
        layout.addStretch()
