"""run.py — run() for ClusterWorker."""
from common.loghub import LogHub
from common.protocol import MSG_TASK


class RunMixin:
    @LogHub.log_call("WORKER")
    def run(self):
        self.log(f"Starting on {self.platform} ({self.hostname})")
        self.log(f"CPU: {self.cpu_cores} cores | RAM: {self.ram_available}/{self.ram_total} GB")
        self.log(f"[AI_MODE] self.ai_mode={self.ai_mode!r}")

        if self.ui:
            self.ui.set_system_info(
                hostname=self.hostname,
                platform=self.platform,
                cpu_cores=self.cpu_cores,
                ram_total=self.ram_total,
                ram_available=self.ram_available,
                ai_mode=self.ai_mode,
            )
            self.ui.set_service("discovery", "idle", "")
            self.ui.set_service("connection", "idle", "")
            self.ui.set_connection("idle")

        self.start_advertising()

        if not self.root_ip:
            self.root_ip = self.discover_root(timeout=5)

        if not self.root_ip:
            self.log("No root found on network. Retrying in background...")
            self.notify("No root found", "Retrying discovery in background...")
            if self.ui:
                self.ui.set_connection("discovering", registered=False)
                self.ui.set_service("discovery", "discovering", "retrying...")
            if not self._reconnect():
                self.log("Could not discover any root device.")
                self.notify("No root found", "No root device on network. Start root with --root first.")
                self.log("Make sure a root device is running on the network.")
                self.log("Run this app with --root on the coordinator device first.")
                if self.ui:
                    self.ui.set_connection("error")
                    self.ui.set_service("discovery", "error", "no root found")
                try:
                    while self.running:
                        time.sleep(10)
                        if not self.registered:
                            self._reconnect()
                except KeyboardInterrupt:
                    pass
                self.stop()
                return

        if self.register_with_root(self.root_ip):
            self.notify("Connected to root", f"Root IP: {self.root_ip}")
            self.log(f"[AI_MODE] after register: ai_mode={self.ai_mode!r}")
            if self.ai_mode:
                try:
                    start_result = self._handle_start_rpc({"rpc_port": self.rpc_port})
                    self.log(f"Auto-started rpc-server: {start_result}")
                except Exception:
                    LogHub().exception("WORKER", "Failed to auto_start_rpc after register")
            self.handle_connection()

        # Connection lost — try to reconnect
        if self.running and not self.registered:
            self.log("Connection lost. Attempting reconnect...", notify=True)
            self.notify("Connection lost", f"Lost connection to root at {self.root_ip}", urgency="critical")
            if self.ui:
                self.ui.set_connection("disconnected")
                self.ui.set_service("connection", "error", "lost connection")
            self.conn = None
            if self._reconnect():
                self.notify("Reconnected", f"Root IP: {self.root_ip}")
                if self.ai_mode:
                    try:
                        self.conn.send(MSG_TASK, id="auto_start_rpc", action="start_rpc",
                                      payload={"rpc_port": self.rpc_port})
                    except Exception:
                        LogHub().exception("WORKER", "Failed to send auto_start_rpc after reconnect")
                self.handle_connection()

        self.stop()
