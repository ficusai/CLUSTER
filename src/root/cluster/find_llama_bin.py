"""find_llama_bin.py — _find_llama_bin() for ClusterRoot."""
import os
from common.loghub import LogHub


class FindLlamaBinMixin:
    @LogHub.log_call("ROOT")
    def _find_llama_bin(self):
        bin_dir = self._find_bin_dir()
        if bin_dir:
            p = os.path.join(bin_dir, "llama-server")
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p
        return None
