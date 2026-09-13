"""discover_roots_on_network.py — discover_roots_on_network(timeout) module-level function."""
import socket
import threading
import time
from common.loghub import LogHub
from common.protocol import UDP_DISCOVERY_PORT, MDNS_ROOT_SERVICE_TYPE, CTRL_PORT_DEFAULT, make_msg, parse_msg

HAVE_ZEROCONF = False
try:
    from zeroconf import ServiceInfo, ServiceBrowser, Zeroconf
    HAVE_ZEROCONF = True
except ImportError:
    pass


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
