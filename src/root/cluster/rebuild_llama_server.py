"""rebuild_llama_server.py — rebuild_llama_server() for ClusterRoot."""
import subprocess
from common.loghub import LogHub


class RebuildLlamaServerMixin:
    @LogHub.log_call("ROOT")
    def rebuild_llama_server(self):
        if not self.ai_mode:
            self.log("AI mode disabled, skipping rebuild")
            return
        if self.llama_process and self.llama_process.poll() is None:
            self.llama_process.terminate()
            try:
                self.llama_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.llama_process.kill()
        self.start_llama_server()
