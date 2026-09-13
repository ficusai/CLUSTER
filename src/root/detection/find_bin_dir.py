"""find_bin_dir.py — find_bin_dir() function."""
import os
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def find_bin_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    search_paths = [
        os.path.join(script_dir, "..", "..", "legacy", "bin"),
        "./legacy/bin",
        "./bin",
    ]
    for p in search_paths:
        ap = os.path.abspath(p)
        if os.path.isdir(ap):
            return ap
    return None
