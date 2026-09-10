import socket
import threading
import time

from common.discovery import UDPBroadcastDiscovery, discover_roots_on_network


def test_udp_broadcast_loopback():
    udp = UDPBroadcastDiscovery(port=52052)
    received = []

    def on_msg(data, addr):
        received.append((data, addr))

    udp.start_listener(on_msg)
    msg = b"hello"
    udp.broadcast(msg)
    time.sleep(0.5)
    udp.stop()
    assert any(r[0] == msg for r in received)


def test_discover_roots_udp_fallback():
    # Without mDNS, discover_roots_on_network should still return empty on quiet network
    roots = discover_roots_on_network(timeout=1)
    assert isinstance(roots, list)
