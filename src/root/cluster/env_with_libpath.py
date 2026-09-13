"""env_with_libpath.py — _env_with_libpath() for ClusterRoot."""
import os
from common.loghub import LogHub


class EnvWithLibpathMixin:
    @LogHub.log_call("ROOT")
    def _env_with_libpath(self):
        env = os.environ.copy()
        bin_dir = self._find_bin_dir()
        if bin_dir:
            lp = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = f"{bin_dir}:{lp}" if lp else bin_dir
        return env
