"""stop.py — stop() for ClusterRoot."""
from common.loghub import LogHub
from common.progress_ui import send_notification


class StopMixin:
    @LogHub.log_call("ROOT")
    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        LogHub().info("ROOT", "Shutting down...")
        self.running = False

        if self.llama_process:
            self._kill_process_tree(self.llama_process)
        if self.local_rpc_process:
            self._kill_process_tree(self.local_rpc_process)

        if self.mdns:
            self.mdns.stop()
        if self.mdns_root:
            self.mdns_root.stop()
        self.udp_running = False
        if self.udp_listener:
            self.udp_listener.stop()

        if self.http_server:
            self.http_server.shutdown()

        if self.server_sock:
            self.server_sock.close()

        self.log("Goodbye.")
        send_notification("Cluster Root", "Shutting down")
        if self.ui:
            self.ui.stop()
        LogHub().stop()
