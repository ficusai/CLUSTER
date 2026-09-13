"""stop.py — stop() for ClusterWorker."""
from common.loghub import LogHub
from common.progress_ui import send_notification


class StopMixin:
    @LogHub.log_call("WORKER")
    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        if self.rpc_process:
            self._kill_process_tree(self.rpc_process)
        self.stop_advertising()
        send_notification("Cluster Worker", "Shutting down")
        if self.ui:
            self.ui.stop()
