"""clear_workers.py — clear_workers() for MainWindow."""
from common.loghub import LogHub


class ClearWorkersMixin:
    @LogHub.log_call("GUI")
    def clear_workers(self):
        if hasattr(self.tab_overview, "kpi_labels") and "kpi_nodes" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_nodes"].setText("0 Active")
