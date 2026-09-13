"""update_worker_table.py — update_worker_table() for MainWindow."""
from common.loghub import LogHub


class UpdateWorkerTableMixin:
    @LogHub.log_call("GUI")
    def update_worker_table(self, workers):
        if hasattr(self.tab_overview, "kpi_labels") and "kpi_nodes" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_nodes"].setText(f"{len(workers)} Active")
