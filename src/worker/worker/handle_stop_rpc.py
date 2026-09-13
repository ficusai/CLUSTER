"""handle_stop_rpc.py — _handle_stop_rpc(payload) for ClusterWorker."""
from common.loghub import LogHub


class HandleStopRpcMixin:
    @LogHub.log_call("WORKER")
    def _handle_stop_rpc(self, payload):
        if self.rpc_process and self.rpc_process.poll() is None:
            self._kill_process_tree(self.rpc_process)
            return {"status": "stopped"}
        return {"status": "not_running"}
