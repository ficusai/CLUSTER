"""discovery.py — MDNSDiscovery class."""
import socket
from common.loghub import LogHub
from common.protocol import MDNS_SERVICE_TYPE

HAVE_ZEROCONF = False
try:
    from zeroconf import ServiceBrowser, Zeroconf
    HAVE_ZEROCONF = True
except ImportError:
    pass


class MDNSDiscovery:
    @LogHub.log_call("DISCOVERY")
    def __init__(self, on_worker_found=None):
        self.zeroconf = None
        self.browser = None
        self.on_worker_found = on_worker_found
        self.workers = {}

    @LogHub.log_call("DISCOVERY")
    def start(self):
        if not HAVE_ZEROCONF:
            return False
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(
            self.zeroconf, MDNS_SERVICE_TYPE, self._make_listener()
        )
        return True

    @LogHub.log_call("DISCOVERY")
    def stop(self):
        if self.browser:
            try:
                self.browser.cancel()
            except Exception:
                LogHub().exception("MDNS", "browser.cancel failed")
        if self.zeroconf:
            self.zeroconf.close()
            self.zeroconf = None

    @LogHub.log_call("DISCOVERY")
    def _make_listener(self):
        class Listener:
            @LogHub.log_call("DISCOVERY")
            def __init__(self, outer):
                self.outer = outer

            @LogHub.log_call("DISCOVERY")
            def add_service(self, zeroconf, service_type, name):
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    worker = self._parse_info(info)
                    if worker and worker["ip"] not in self.outer.workers:
                        self.outer.workers[worker["ip"]] = worker
                        if self.outer.on_worker_found:
                            self.outer.on_worker_found(worker)

            @LogHub.log_call("DISCOVERY")
            def update_service(self, zeroconf, service_type, name):
                pass

            @LogHub.log_call("DISCOVERY")
            def remove_service(self, zeroconf, service_type, name):
                pass

            @staticmethod
            @LogHub.log_call("DISCOVERY")
            def _parse_info(info):
                try:
                    ip = socket.inet_ntoa(info.addresses[0])
                    props = {}
                    for k, v in info.properties.items():
                        k = k.decode() if isinstance(k, bytes) else k
                        v = v.decode() if isinstance(v, bytes) else v
                        props[k] = v
                    return {
                        "ip": ip,
                        "hostname": info.name.split(".")[0],
                        "port": info.port,
                        "platform": props.get("platform", "unknown"),
                        "cpu_cores": int(props.get("cpu_cores", 0)),
                        "ram_total": float(props.get("ram_total", 0)),
                        "ram_available": float(props.get("ram_available", 0)),
                        "rpc_port": int(props.get("rpc_port", 50052)),
                    }
                except Exception:
                    LogHub().exception("MDNS", "parse_info failed")
                    return None

        return Listener(self)
