"""handle_connection.py — handle_connection() for ClusterWorker."""
import threading
import time
from common.loghub import LogHub


class HandleConnectionMixin:
    @LogHub.log_call("WORKER")
    def handle_connection(self):
        t = threading.Thread(target=self._read_loop, daemon=True)
        t.start()
        while self.running and self.registered:
            self._heartbeat()
            time.sleep(15)
