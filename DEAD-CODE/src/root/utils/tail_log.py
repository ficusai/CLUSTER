"""tail_log.py — tail_log(log_path, max_lines) module-level function."""
import os
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def tail_log(log_path, max_lines=40):
    try:
        if not os.path.isfile(log_path):
            return
        with open(log_path, "r", errors="replace") as f:
            lines = f.readlines()
        tail = lines[-max_lines:]
        if tail:
            print(f"--- begin tail of {os.path.basename(log_path)} ---")
            for line in tail:
                print(line.rstrip("\n"))
            print(f"--- end tail of {os.path.basename(log_path)} ---")
    except Exception as e:
        print(f"Could not read log {log_path}: {e}")
