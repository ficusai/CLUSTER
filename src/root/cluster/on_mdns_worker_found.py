"""on_mdns_worker_found.py — _on_mdns_worker_found(worker) for ClusterRoot."""
from common.loghub import LogHub


class OnMdnsWorkerFoundMixin:
    @LogHub.log_call("ROOT")
    def _on_mdns_worker_found(self, worker):
        self.log(f"mDNS found worker: {worker['hostname']} at {worker['ip']}")
        self.notify("Worker discovered", f"{worker['hostname']} ({worker['platform']}) at {worker['ip']}", urgency="low")
