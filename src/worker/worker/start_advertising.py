"""start_advertising.py — start_advertising() for ClusterWorker."""
from common.loghub import LogHub
from common.discovery import MDNSAdvertiser


class StartAdvertisingMixin:
    @LogHub.log_call("WORKER")
    def start_advertising(self):
        self.mdns = MDNSAdvertiser(
            hostname=self.hostname,
            port=self.ctrl_port,
            platform=self.platform,
            cpu_cores=self.cpu_cores,
            ram_total=self.ram_total,
            ram_available=self.ram_available,
            rpc_port=self.rpc_port,
        )
        started = self.mdns.start()
        if started:
            self.log("Advertising via mDNS")
            if self.ui:
                self.ui.set_service("mDNS", "running")
        else:
            if self.ui:
                self.ui.set_service("mDNS", "idle", "zeroconf not available")
