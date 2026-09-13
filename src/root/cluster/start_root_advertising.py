"""start_root_advertising.py — start_root_advertising() for ClusterRoot."""
import threading
import platform as plat
from common.loghub import LogHub
from common.protocol import UDP_DISCOVERY_PORT, MDNS_ROOT_SERVICE_TYPE
from common.discovery import MDNSRootAdvertiser, UDPBroadcastDiscovery
from ..detection import detect_cpu_cores, detect_ram


class StartRootAdvertisingMixin:
    @LogHub.log_call("ROOT")
    def start_root_advertising(self):
        self.mdns_root = MDNSRootAdvertiser(
            hostname=self.hostname,
            port=self.ctrl_port,
            platform=plat.system().lower(),
            cpu_cores=detect_cpu_cores(),
            ram_total=detect_ram()[0],
            ram_available=detect_ram()[1],
            http_port=self.http_port,
        )
        if self.mdns_root.start():
            self.log(f"mDNS advertising as root on {MDNS_ROOT_SERVICE_TYPE}")
            if self.ui:
                self.ui.set_service("mDNS", "running", MDNS_ROOT_SERVICE_TYPE)
        else:
            if self.ui:
                self.ui.set_service("mDNS", "stopped", "zeroconf not installed")

        self.udp = UDPBroadcastDiscovery()
        self.udp_running = True
        t = threading.Thread(target=self._announce_loop, daemon=True)
        t.start()
        if self.ui:
            self.ui.set_service("UDP broadcast", "running", f"port {UDP_DISCOVERY_PORT}")

        self.udp_listener = UDPBroadcastDiscovery()
        err = self.udp_listener.start_listener(self._handle_udp_message)
        if err:
            self.log(err)

        local_ip = self._get_local_ip()
        self.notify("Root on network", f"Announcing as root on {local_ip}:{self.ctrl_port}")
