"""find_rpc_bin.py — _find_rpc_bin() for ClusterRoot."""
import os
from common.loghub import LogHub


class FindRpcBinMixin:
    @LogHub.log_call("ROOT")
    def _find_rpc_bin(self):
        bin_dir = self._find_bin_dir()
        if bin_dir:
            p = os.path.join(bin_dir, "rpc-server")
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p
        return None
