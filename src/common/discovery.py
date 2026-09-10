import socket
import threading
import time
import json
import functools

HAVE_ZEROCONF = False
try:
    from zeroconf import ServiceInfo, ServiceBrowser, Zeroconf
    HAVE_ZEROCONF = True
except ImportError:
    pass

from .protocol import (
    UDP_DISCOVERY_PORT, MDNS_SERVICE_TYPE, MDNS_ROOT_SERVICE_TYPE,
    CTRL_PORT_DEFAULT, make_msg, parse_msg
)
from .loghub import LogHub


@LogHub.log_call("DISCOVERY")
def _get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 53))
        ip = s.getsockname()[0]
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    finally:
        s.close()

    try:
        hostname = socket.gethostname()
        for addr in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
            ip = addr[4][0]
            if ip and not ip.startswith("127."):
                return ip
    except Exception:
        pass

    try:
        _, _, ips = socket.gethostbyname_ex(socket.gethostname())
        for ip in ips:
            if ip and not ip.startswith("127."):
                return ip
    except Exception:
        pass

    try:
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    ip = addr_info.get("addr")
                    if ip and not ip.startswith("127."):
                        return ip
    except Exception:
        pass

    return "127.0.0.1"


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
        # IPv4-only mDNS advertisement (socket.inet_aton). IPv6 support would require
        # zeroconf's ServiceInfo with ipv6_addresses.
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


class UDPBroadcastDiscovery:
    @LogHub.log_call("DISCOVERY")
    def __init__(self, port=UDP_DISCOVERY_PORT):
        self.port = port
        self.sock = None
        self.running = False

    @LogHub.log_call("DISCOVERY")
    def start_listener(self, on_message):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass
        self.sock.settimeout(1)
        try:
            self.sock.bind(("0.0.0.0", self.port))
        except OSError as e:
            self.sock.close()
            self.sock = None
            LogHub().exception("DISCOVERY", f"Failed to bind UDP listener on port {self.port}: {e}")
            return f"Failed to bind UDP listener on port {self.port}: {e}"
        self.running = True
        t = threading.Thread(target=self._listen_loop, args=(on_message,), daemon=True)
        t.start()

    @LogHub.log_call("DISCOVERY")
    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RD)
            except OSError:
                pass
            self.sock.close()
            self.sock = None

    @LogHub.log_call("DISCOVERY")
    def _listen_loop(self, on_message):
        while self.running and self.sock:
            try:
                data, addr = self.sock.recvfrom(4096)
                on_message(data, addr)
            except socket.timeout:
                continue
            except OSError as e:
                if e.errno == 9:
                    # Socket closed during shutdown; exit cleanly.
                    break
                LogHub().exception("DISCOVERY", f"UDP listen loop failed: {e}")
                break

    @LogHub.log_call("DISCOVERY")
    def broadcast(self, message, broadcast_ip="255.255.255.255"):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        data = message if isinstance(message, bytes) else json.dumps(message).encode()
        try:
            s.sendto(data, (broadcast_ip, self.port))
        except Exception:
            LogHub().exception("DISCOVERY", f"UDP broadcast to {broadcast_ip}:{self.port} failed")
        finally:
            s.close()


class MDNSRootAdvertiser:
    @LogHub.log_call("DISCOVERY")
    def __init__(self, hostname, port, platform, cpu_cores, ram_total, ram_available, http_port=8080):
        self.hostname = hostname
        self.port = port
        self.platform = platform
        self.cpu_cores = cpu_cores
        self.ram_total = ram_total
        self.ram_available = ram_available
        self.http_port = http_port
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
            "http_port": str(self.http_port),
        }
        local_ip = _get_local_ip()
        full_name = f"{self.hostname}.{MDNS_ROOT_SERVICE_TYPE}"
        self.info = ServiceInfo(
            type_=MDNS_ROOT_SERVICE_TYPE,
            name=full_name,
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties=props,
        )
        try:
            self.zeroconf.register_service(self.info)
        except Exception as exc:
            LogHub().exception("DISCOVERY", f"root register_service failed: {exc}")
            return False
        return True

    @LogHub.log_call("DISCOVERY")
    def stop(self):
        if self.zeroconf:
            if self.info:
                try:
                    self.zeroconf.unregister_service(self.info)
                except Exception:
                    LogHub().exception("MDNS", "root advertiser unregister_service failed")
            self.zeroconf.close()
            self.zeroconf = None


@LogHub.log_call("DISCOVERY")
def discover_roots_on_network(timeout=5):
    """Discover root devices on the local network via mDNS + UDP.
    Returns a list of dicts with ip, hostname, port, platform, http_port."""
    roots = {}
    lock = threading.Lock()

    # mDNS discovery
    zc = None
    browser = None
    if HAVE_ZEROCONF:
        class RootListener:
            @LogHub.log_call("DISCOVERY")
            def add_service(self, zc, service_type, name):
                info = zc.get_service_info(service_type, name)
                if info:
                    try:
                        ip = socket.inet_ntoa(info.addresses[0])
                        props = {}
                        for k, v in info.properties.items():
                            k = k.decode() if isinstance(k, bytes) else k
                            v = v.decode() if isinstance(v, bytes) else v
                            props[k] = v
                        with lock:
                            if ip not in roots:
                                roots[ip] = {
                                    "ip": ip,
                                    "hostname": name.split(".")[0],
                                    "port": info.port,
                                    "platform": props.get("platform", "unknown"),
                                    "http_port": int(props.get("http_port", 8080)),
                                    "source": "mDNS",
                                }
                    except Exception:
                        LogHub().exception("DISCOVERY", "RootListener.add_service failed")

            @LogHub.log_call("DISCOVERY")
            def update_service(self, zc, service_type, name):
                pass

            @LogHub.log_call("DISCOVERY")
            def remove_service(self, zc, service_type, name):
                pass

        zc = Zeroconf()
        browser = ServiceBrowser(zc, MDNS_ROOT_SERVICE_TYPE, RootListener())

    # UDP broadcast listener
    udp_sock = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except OSError:
        s = None
    if s is not None:
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(0.5)
            s.bind(("0.0.0.0", UDP_DISCOVERY_PORT))
            udp_sock = s
        except OSError:
            s.close()

    deadline = time.time() + timeout
    while time.time() < deadline:
        if udp_sock:
            try:
                data, addr = udp_sock.recvfrom(4096)
                msg = parse_msg(data)
                if msg.get("type") == "root_announce":
                    ip = addr[0]
                    with lock:
                        if ip not in roots:
                            roots[ip] = {
                                "ip": ip,
                                "hostname": msg.get("hostname", ip),
                                "port": msg.get("port", CTRL_PORT_DEFAULT),
                                "platform": msg.get("platform", "unknown"),
                                "http_port": msg.get("http_port", 8080),
                                "source": "UDP",
                            }
            except socket.timeout:
                continue
            except Exception:
                LogHub().exception("DISCOVERY", "UDP recvfrom failed during root discovery")
                break
        else:
            time.sleep(0.5)

    if browser:
        try:
            browser.cancel()
        except Exception:
            LogHub().exception("DISCOVERY", "browser.cancel failed on cleanup")
    if zc:
        try:
            zc.close()
        except Exception:
            LogHub().exception("DISCOVERY", "zeroconf.close failed on cleanup")
    if udp_sock:
        udp_sock.close()

    return list(roots.values())