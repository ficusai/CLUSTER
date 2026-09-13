"""run.py — run() for ClusterRoot."""
import platform as plat
import threading
import time
from common.loghub import LogHub
from ..detection import detect_cpu_cores, detect_ram


class RunMixin:
    @LogHub.log_call("ROOT")
    def run(self):
        self.log(f"Cluster Root starting on {self.hostname}")
        local_ip = self._get_local_ip()
        self.log(f"IP: {local_ip}")

        if self.ui:
            self.ui.set_system_info(
                hostname=self.hostname,
                local_ip=local_ip,
                ai_mode=self.ai_mode,
                platform=plat.system().lower(),
                cpu_cores=detect_cpu_cores(),
                ram_total=detect_ram()[0],
                ram_available=detect_ram()[1],
                http_port=self.http_port,
            )
            self.ui.set_service("TCP server", "starting", f"port {self.ctrl_port}")
            self.ui.set_service("mDNS", "starting", "")
            self.ui.set_service("HTTP API", "starting", f"port {self.http_port}")
            if self.ai_mode:
                self.ui.set_service("AI server", "starting", "")

        if self.ai_mode:
            self.start_local_rpc()

        self.start_mdns_discovery()
        self.start_root_advertising()
        self.start_tcp_server()
        self.start_http_api()

        if self.ai_mode:
            threading.Thread(target=self.check_llama_workers, daemon=True).start()

        self.log(f"Ready. Workers can connect to {local_ip}:{self.ctrl_port}")
        self.log(f"API: http://{local_ip}:{self.http_port}/api/status")
        self.notify("Root ready", f"Workers can connect to {local_ip}:{self.ctrl_port}")

        if self.ai_mode:
            time.sleep(5)
            self.start_llama_server()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.stop()
