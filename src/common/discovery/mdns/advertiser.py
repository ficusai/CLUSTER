"""advertiser.py — MDNSAdvertiser class."""
import socket
from common.loghub import LogHub
from ..get_local_ip import _get_local_ip
from common.protocol import MDNS_SERVICE_TYPE
from common.loghub import LogHub as _LH

HAVE_ZEROCONF = False
try:
    from zeroconf import ServiceInfo, ServiceBrowser, Zeroconf
    HAVE_ZEROCONF = True
except ImportError:
    pass


class MDNSAdvertiser:
    @LogHub.log_call("DISCOVERY")
    def __init__(self, hostname, port, platform, cpu_cores, ram_total, ram_available, rpc_port=50052):
        self.hostname = hostname
        self.port = port
        self.platform = platform
        self.cpu_cores = cpu_cores
        self.ram_total = ram_total
        self.ram_available = ram_available
        self.rpc_port = rpc_port
        self.info = None
        self.zeroconf = None

    @LogHub.log_call("DISCOVERY")
    def start(self):
        if not HAVE_ZEROCONF:
            return False
        self.zeroconf = Zeroconf()
        props = {
            "platform": self.platform,
            "cpu_cores": str(self.cpu_cores),
            "ram_total": str(self.ram_total),
            "ram_available": str(self.ram_available),
            "rpc_port": str(self.rpc_port),
        }
        local_ip = _get_local_ip()
        full_name = f"{self.hostname}.{MDNS_SERVICE_TYPE}"
        self.info = ServiceInfo(
            type_=MDNS_SERVICE_TYPE,
            name=full_name,
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties=props,
        )
        try:
            self.zeroconf.register_service(self.info)
        except Exception as exc:
            LogHub().exception("DISCOVERY", f"register_service failed: {exc}")
            return False
        return True

    @LogHub.log_call("DISCOVERY")
    def stop(self):
        if self.zeroconf:
            if self.info:
                try:
                    self.zeroconf.unregister_service(self.info)
                except Exception:
                    LogHub().exception("MDNS", "unregister_service failed")
            self.zeroconf.close()
            self.zeroconf = None
