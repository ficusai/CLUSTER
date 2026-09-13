"""read_loop.py — _read_loop() for ClusterWorker."""
from common.loghub import LogHub


class ReadLoopMixin:
    @LogHub.log_call("WORKER")
    def _read_loop(self):
        while self.running and self.registered:
            try:
                msg = self.conn.recv()
                if msg is None:
                    self.log("Connection closed by root")
                    self.registered = False
                    break
                self._handle_message(msg)
            except Exception as e:
                self.log(f"Connection error: {e}")
                self.registered = False
                break
