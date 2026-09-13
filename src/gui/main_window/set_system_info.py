"""set_system_info.py — set_system_info() for MainWindow."""
from common.loghub import LogHub


class SetSystemInfoMixin:
    @LogHub.log_call("GUI")
    def set_system_info(self, **kwargs):
        if "cpu_cores" in kwargs and "kpi_cpu" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_cpu"].setText(f"{kwargs['cpu_cores']} Cores")
        if "ram_total" in kwargs and "ram_available" in kwargs and "kpi_ram" in self.tab_overview.kpi_labels:
            self.tab_overview.kpi_labels["kpi_ram"].setText(f"{kwargs['ram_available']} GB / {kwargs['ram_total']} GB")
