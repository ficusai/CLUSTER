"""find_bin_dir.py — _find_bin_dir() for ClusterRoot."""
import os
from common.loghub import LogHub


class FindBinDirMixin:
    @LogHub.log_call("ROOT")
    def _find_bin_dir(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths = [
            os.path.join(script_dir, "..", "..", "bin"),
            "./bin",
        ]
        for p in search_paths:
            ap = os.path.abspath(p)
            if os.path.isdir(ap):
                return ap
        return None
