"""announce_loop.py — _announce_loop() for ClusterRoot."""
import time
import platform as plat
from common.loghub import LogHub
from common.protocol import make_msg


class AnnounceLoopMixin:
    @LogHub.log_call("ROOT")
    def _announce_loop(self):
        while self.udp_running:
            self.udp.broadcast(make_msg("root_announce",
                hostname=self.hostname, port=self.ctrl_port,
                platform=plat.system().lower(), http_port=self.http_port))
            time.sleep(5)
