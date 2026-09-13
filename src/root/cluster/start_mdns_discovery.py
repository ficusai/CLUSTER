"""start_mdns_discovery.py — start_mdns_discovery() for ClusterRoot."""
from common.loghub import LogHub
from common.discovery import MDNSDiscovery


class StartMdnsDiscoveryMixin:
    @LogHub.log_call("ROOT")
    def start_mdns_discovery(self):
        self.mdns = MDNSDiscovery(on_worker_found=self._on_mdns_worker_found)
        if self.mdns.start():
            self.log("mDNS discovery started for workers")
        else:
            self.log("mDNS not available (zeroconf not installed)")
