"""tail_log.py — _tail_log(log_path, max_lines) for ClusterRoot."""
import os
from common.loghub import LogHub


class TailLogMixin:
    @LogHub.log_call("ROOT")
    def _tail_log(self, log_path, max_lines=40):
        try:
            if not os.path.isfile(log_path):
                return
            with open(log_path, "r", errors="replace") as f:
                lines = f.readlines()
            tail = lines[-max_lines:]
            if tail:
                self.log(f"--- begin tail of {os.path.basename(log_path)} ---")
                for line in tail:
                    self.log(line.rstrip("\n"))
                self.log(f"--- end tail of {os.path.basename(log_path)} ---")
        except Exception as e:
            self.log(f"Could not read log {log_path}: {e}")
