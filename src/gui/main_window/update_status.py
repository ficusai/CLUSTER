"""update_status.py — update_status() for MainWindow."""
from common.loghub import LogHub


class UpdateStatusMixin:
    @LogHub.log_call("GUI")
    def update_status(self, status, worker_count=0):
        self._status_badge.setText(f"● {status.upper()}")
        if "kpi_nodes" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_nodes"].setText(f"{worker_count} Active")
        self._tray.update_status(status, worker_count)
