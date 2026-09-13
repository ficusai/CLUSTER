"""set_service.py — set_service() for MainWindow."""
from common.loghub import LogHub


class SetServiceMixin:
    @LogHub.log_call("GUI")
    def set_service(self, name, status, detail=""):
        mapping = {
            "mDNS": "mdns",
            "REST API": "http",
            "RPC": "rpc",
            "LLaMA Server": "llama",
        }
        key = mapping.get(name)
        if key and key in self.tab_overview.service_badges:
            badge = self.tab_overview.service_badges[key]
            symbol = "✓" if status.lower() in ("running", "ready", "online", "active") else "○"
            badge.setText(f"{symbol} {name}: {status.title()}")
            color = "#4ade80" if status.lower() in ("running", "ready", "online", "active") else "#9ca3af"
            badge.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 500;")
