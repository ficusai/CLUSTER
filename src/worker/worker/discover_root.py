"""discover_root.py — discover_root(timeout, force) for ClusterWorker."""
import time
from common.loghub import LogHub
from common.discovery import UDPBroadcastDiscovery
from common.protocol import make_msg, parse_msg


class DiscoverRootMixin:
    @LogHub.log_call("WORKER")
    def discover_root(self, timeout=5, force=False):
        """Discover root via mDNS + UDP broadcast. Returns root IP or None."""
        if self.root_ip and not force:
            return self.root_ip

        self.log(f"Scanning for root devices (timeout: {timeout}s)...")
        self.notify("Looking for root", "Scanning network for root device...", urgency="low")
        if self.ui:
            self.ui.set_connection("discovering")
            self.ui.set_service("discovery", "discovering", f"timeout: {timeout}s")

        from common.discovery import discover_roots_on_network
        roots = discover_roots_on_network(timeout=timeout)

        if roots:
            root = roots[0]
            source = root.get('source', 'discovery')
            self.log(f"Found root via {source}: {root['hostname']} at {root['ip']}")
            self.notify("Root found", f"{root['hostname']} at {root['ip']} via {source}")
            if self.ui:
                self.ui.set_connection("discovering", root_ip=root["ip"])
                self.ui.set_service("discovery", "running")
            return root["ip"]

        # Last resort: direct UDP broadcast one-shot
        self.log("No root found via mDNS+UDP, trying direct broadcast...")
        if self.ui:
            self.ui.set_service("discovery", "discovering", "direct UDP broadcast")
        udp = UDPBroadcastDiscovery()
        found = [None]

        def on_udp_response(data, addr):
            try:
                msg = parse_msg(data)
                if msg.get("type") == "root_announce":
                    found[0] = addr[0]
            except Exception:
                LogHub().exception("WORKER", "UDP response parse failed")

        udp.start_listener(on_udp_response)
        # Send multiple discovery requests to cover root announce interval (5s)
        for _ in range(3):
            udp.broadcast(make_msg("worker_discover",
                hostname=self.hostname, platform=self.platform))
            time.sleep(2)
        udp.stop()

        if found[0]:
            self.log(f"Found root via UDP broadcast: {found[0]}")
            self.notify("Root found", f"Root at {found[0]} via UDP broadcast")
        return found[0]
