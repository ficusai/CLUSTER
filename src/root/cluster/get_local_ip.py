"""get_local_ip.py — _get_local_ip() for ClusterRoot."""
from common.loghub import LogHub
from common.discovery import _get_local_ip as _common_get_local_ip


class GetLocalIpMixin:
    @LogHub.log_call("ROOT")
    def _get_local_ip(self):
        return _common_get_local_ip()
