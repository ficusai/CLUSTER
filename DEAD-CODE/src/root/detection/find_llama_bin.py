"""find_llama_bin.py — find_llama_bin() function."""
import os
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def find_llama_bin():
    bin_dir = find_bin_dir()
    if bin_dir:
        p = os.path.join(bin_dir, "llama-server")
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None
