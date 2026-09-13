"""worker_comm_loop.py — _worker_comm_loop(conn, worker_id) for ClusterRoot."""
from common.loghub import LogHub


class WorkerCommLoopMixin:
    @LogHub.log_call("ROOT")
    def _worker_comm_loop(self, conn, worker_id):
        while self.running:
            try:
                msg = conn.recv()
                if msg is None:
                    break
                self._handle_worker_message(msg, worker_id)
            except Exception:
                LogHub().exception("ROOT", f"Worker comm error for {worker_id}")
                break
