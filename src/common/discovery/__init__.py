"""discovery package — public API. Backward-compat re-exports."""
from .get_local_ip import _get_local_ip
from .discover_roots_on_network import discover_roots_on_network
from .mdns import MDNSAdvertiser, MDNSDiscovery, MDNSRootAdvertiser
from .udp import UDPBroadcastDiscovery
