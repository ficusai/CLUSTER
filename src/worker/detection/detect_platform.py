"""detect_platform.py — detect_platform() function."""
import os
import platform as plat
from common.loghub import LogHub


@LogHub.log_call("WORKER")
def detect_platform():
    p = plat.system().lower()
    if p == "linux" and os.path.exists("/data/data/com.termux/files/usr"):
        return "android"
    if p == "darwin":
        machine = plat.machine().lower()
        platform_str = plat.platform().lower()
        if "iphone" in platform_str or "ipad" in platform_str:
            return "ios"
        if machine in ("arm64", "aarch64"):
            if os.path.exists("/usr/lib/libcryptex.dylib") or os.path.exists("/var/containers"):
                return "ios"
            if os.path.exists("/System/Library/CoreServices/SystemVersion.plist"):
                return "macos"
            return "ios"
        return "macos"
    if p == "windows":
        return "windows"
    return p
