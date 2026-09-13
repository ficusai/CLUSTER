"""handle_udp_message.py — _handle_udp_message(data, addr) for ClusterRoot."""
from common.loghub import LogHub
from common.protocol import parse_msg


class HandleUdpMessageMixin:
    @LogHub.log_call("ROOT")
    def _handle_udp_message(self, data, addr):
        try:
            msg = parse_msg(data)
            if msg.get("type") == "worker_discover":
                worker_ip = addr[0]
                if worker_ip not in self._discovered_via_udp:
                    if len(self._discovered_via_udp) >= self._discovered_via_udp_max:
                        self._discovered_via_udp.clear()
                    self._discovered_via_udp.add(worker_ip)
                    hostname = msg.get("hostname", worker_ip)
                    platform = msg.get("platform", "unknown")
                    self.log(f"UDP discovery: worker {hostname} at {worker_ip}")
                    self.notify("Worker looking for root", f"{hostname} ({platform}) at {worker_ip}", urgency="low")
        except Exception as exc:
            LogHub().warn("ROOT", f"UDP message parse failed from {addr[0]}: {exc}")
