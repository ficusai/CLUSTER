"""env_with_libpath.py — env_with_libpath(bin_dir) module-level function."""
import os
from common.loghub import LogHub


@LogHub.log_call("ROOT")
def env_with_libpath(bin_dir=None):
    env = os.environ.copy()
    if bin_dir:
        lp = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = f"{bin_dir}:{lp}" if lp else bin_dir
    return env
