"""get_local_ip.py — get_local_ip() function (wrapper around common.discovery._get_local_ip)."""
from common.loghub import LogHub
from common.discovery import _get_local_ip as _common_get_local_ip


@LogHub.log_call("ROOT")
def get_local_ip():
    return _common_get_local_ip()
