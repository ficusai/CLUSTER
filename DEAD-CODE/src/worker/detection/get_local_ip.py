"""get_local_ip.py — _get_local_ip() function."""
import socket
from common.loghub import LogHub


@LogHub.log_call("WORKER")
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
