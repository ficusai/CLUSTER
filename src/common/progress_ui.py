import os
import platform
import subprocess
import threading
import time
from datetime import datetime

from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box
from rich.console import Group
from rich.columns import Columns
from .loghub import LogHub


_CROSS_PLATFORM_NOTIFY = None


def _detect_notifier():
    system = platform.system().lower()

    # Termux/Android
    if os.environ.get("TERMUX_VERSION"):
        try:
            subprocess.run(["termux-notification"], capture_output=True, timeout=2)
            return "termux"
        except Exception:
            pass

    # Linux (libnotify)
    if system == "linux":
        try:
            subprocess.run(["notify-send", "--version"], capture_output=True, timeout=2)
            return "notify-send"
        except Exception:
            pass
        try:
            import dbus
            return "dbus"
        except ImportError:
            pass

    # macOS
    if system == "darwin":
        try:
            subprocess.run(["osascript", "-e", "true"], capture_output=True, timeout=2)
            return "osascript"
        except Exception:
            pass

    # Windows
    if system == "windows":
        try:
            subprocess.run(
                ["powershell", "-Command", "Write-Output", "test"],
                capture_output=True, timeout=2,
            )
            return "powershell"
        except Exception:
            pass

    return None


def send_notification(title, message, urgency="normal"):
    global _CROSS_PLATFORM_NOTIFY
    if _CROSS_PLATFORM_NOTIFY is None:
        _CROSS_PLATFORM_NOTIFY = _detect_notifier()

    try:
        notifier = _CROSS_PLATFORM_NOTIFY
        if notifier == "termux":
            urgency_map = {"low": "low", "normal": "default", "critical": "high"}
            subprocess.run(
                ["termux-notification", "-t", title, "-c", message,
                 "--priority", urgency_map.get(urgency, "default")],
                timeout=3, capture_output=True,
            )
        elif notifier == "notify-send":
            subprocess.run(
                ["notify-send", "-u", urgency, title, message],
                timeout=3, capture_output=True,
            )
        elif notifier == "dbus":
            import dbus
            bus = dbus.SessionBus()
            notify_iface = bus.get_object(
                "org.freedesktop.Notifications",
                "/org/freedesktop/Notifications",
            )
            app_name = "AI Cluster"
            urgency_map = {"low": 0, "normal": 1, "critical": 2}
            notify_iface.Notify(
                app_name, 0, "", title, message, [],
                {"urgency": urgency_map.get(urgency, 1)},
                5000,
            )
        elif notifier == "osascript":
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{message}" with title "{title}"'],
                timeout=3, capture_output=True,
            )
        elif notifier == "powershell":
            ps_cmd = (
                f'[Windows.UI.Notifications.ToastNotificationManager,'
                f'Windows.UI.Notifications,ContentType=WindowsRuntime]::CreateToastNotifier()'
                f'.Show((New-Object '
                f'Windows.UI.Notifications.ToastNotification('
                f'[Windows.Data.Xml.Dom.XmlDocument]::new().LoadXml('
                f'"<toast><visual><binding template=\'ToastGeneric\'>'
                f'<text>{title}</text><text>{message}</text>'
                f'</binding></visual></toast>"))))'
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                timeout=3, capture_output=True,
            )
    except Exception:
        LogHub().exception("NOTIFY", f"send_notification failed: {title}: {message}")


STATUS_ICONS = {
    "starting": "\u23f3",
    "running": "\u2713",
    "stopped": "\u2717",
    "error": "\u26a0",
    "idle": "\u25cb",
    "discovering": "\u231b",
    "connecting": "\u23f3",
    "connected": "\u2713",
    "disconnected": "\u2717",
    "registered": "\u2713",
    "unregistered": "\u25cb",
}


_COLORS_SERVICES = {
    "running": "green",
    "starting": "yellow",
    "error": "red",
    "stopped": "red",
}


class ProgressUI:
    def __init__(self, mode="root"):
        self.mode = mode
        self._state = {
            "services": {},
            "events": [],
            "workers": {},
            "connection_status": "idle",
            "root_ip": None,
            "registered": False,
            "platform": "",
            "hostname": "",
            "cpu_cores": 0,
            "ram_total": 0,
            "ram_available": 0,
            "http_port": None,
            "local_ip": None,
            "ai_mode": False,
            "version": "",
        }
        self._lock = threading.Lock()
        self._running = False
        self._live = None
        self._refresh_thread = None
        self._start_time = time.time()
        self._notified_events = set()

    def start(self):
        self._running = True
        self._live = Live(self._render(), refresh_per_second=4, screen=True)
        self._live.start()
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()
        send_notification(
            "AI Cluster Auto-Connect",
            f"Starting in {self.mode.upper()} mode...",
        )

    def stop(self):
        self._running = False
        if self._live:
            try:
                self._live.stop()
            except Exception:
                LogHub().exception("UI", "Failed to stop live display")

    def _refresh_loop(self):
        while self._running:
            time.sleep(0.5)
            self._update_display()

    def _update_display(self):
        if self._live and self._running:
            try:
                self._live.update(self._render())
            except Exception:
                LogHub().exception("UI", "Failed to update live display")

    def set_service(self, name, status, detail=""):
        with self._lock:
            self._state["services"][name] = {"status": status, "detail": detail}

    def add_event(self, message, notify=False):
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self._state["events"].append((ts, message))
            if len(self._state["events"]) > 100:
                self._state["events"].pop(0)
        if notify:
            send_notification("Cluster", message)

    def update_worker(self, wid, info):
        with self._lock:
            self._state["workers"][wid] = info

    def remove_worker(self, wid):
        with self._lock:
            self._state["workers"].pop(wid, None)

    def set_connection(self, status, root_ip=None, registered=False):
        with self._lock:
            self._state["connection_status"] = status
            if root_ip is not None:
                self._state["root_ip"] = root_ip
            self._state["registered"] = registered

    _ALLOWED_SYSTEM_KEYS = {
        "platform", "hostname", "cpu_cores", "ram_total", "ram_available",
        "http_port", "local_ip", "ai_mode", "version",
    }

    def set_system_info(self, **kwargs):
        with self._lock:
            for k, v in kwargs.items():
                if k in self._ALLOWED_SYSTEM_KEYS:
                    self._state[k] = v

    def notify_once(self, event_key, title, message, urgency="normal"):
        if event_key not in self._notified_events:
            self._notified_events.add(event_key)
            send_notification(title, message, urgency)

    def _render(self):
        with self._lock:
            state = dict(self._state)

        mode_label = "ROOT" if self.mode == "root" else "WORKER"
        hostname = state.get("hostname", "?")
        local_ip = state.get("local_ip", "?")
        version = state.get("version", "")

        header = Text.assemble(
            ("AI Cluster Auto-Connect", "bold cyan"),
            (f" v{version}  ", "dim white" if version else ""),
            ("\u2014 ", "dim"),
            (f"{mode_label} mode", "bold yellow" if self.mode == "worker" else "bold green"),
            "\n",
            (f"{hostname} ({local_ip})", "dim"),
        )
        header_panel = Panel(header, box=box.HEAVY, border_style="cyan")

        left_parts = []

        if self.mode == "root":
            svc_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            svc_table.add_column("icon", style="bold", width=2)
            svc_table.add_column("service")
            svc_table.add_column("status", width=14)

            for sname, sinfo in sorted(state["services"].items()):
                icon = STATUS_ICONS.get(sinfo["status"], "\u25cb")
                color = _COLORS_SERVICES.get(sinfo["status"], "white")
                detail = sinfo.get("detail", "")
                status_text = Text(f"{icon} {sinfo['status'].upper()}", style=color)
                label = f"{sname:20s}"
                svc_table.add_row("", label, status_text)

            svc_panel = Panel(
                Group(
                    Text("Services", style="bold underline"),
                    svc_table,
                ),
                box=box.ROUNDED,
                border_style="blue",
            )
            left_parts.append(svc_panel)

            workers = state.get("workers", {})
            w_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            w_table.add_column("icon", width=2)
            w_table.add_column("worker", style="bold")
            w_table.add_column("info", style="dim")
            for wid, info in sorted(workers.items())[:15]:
                icon = STATUS_ICONS.get("connected", "\u2713")
                host = info.get("hostname", wid)
                plat = info.get("platform", "?")
                cores = info.get("cpu_cores", "?")
                ram = info.get("ram_available", 0)
                w_table.add_row(
                    icon,
                    f"{host}",
                    f"{plat}  {cores}c  {ram}g",
                )
            if not workers:
                w_table.add_row("", Text("(waiting for workers...)", style="dim"), "")

            w_panel = Panel(
                Group(
                    Text(f"Workers ({len(workers)} active)", style="bold underline"),
                    w_table,
                ),
                box=box.ROUNDED,
                border_style="green",
            )
            left_parts.append(w_panel)

        else:
            conn_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            conn_table.add_column("", width=14)
            conn_table.add_column("value")

            status_str = state.get("connection_status", "idle")
            icon = STATUS_ICONS.get(status_str, "\u25cb")
            color = _COLORS_SERVICES.get(status_str, "white") if status_str in _COLORS_SERVICES else "yellow"
            conn_table.add_row(
                Text("Status:", style="bold"),
                Text(f"{icon}  {status_str.upper()}", style=color),
            )
            root_ip = state.get("root_ip")
            conn_table.add_row(
                Text("Root IP:", style="bold"),
                Text(root_ip or "---", style="cyan" if root_ip else "dim"),
            )
            registered = state.get("registered", False)
            reg_icon = STATUS_ICONS.get("registered" if registered else "unregistered")
            conn_table.add_row(
                Text("Registered:", style="bold"),
                Text(f"{reg_icon}  {'Yes' if registered else 'No'}", style="green" if registered else "red"),
            )

            conn_panel = Panel(
                Group(
                    Text("Connection", style="bold underline"),
                    conn_table,
                ),
                box=box.ROUNDED,
                border_style="blue",
            )
            left_parts.append(conn_panel)

            sys_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            sys_table.add_column("", width=14)
            sys_table.add_column("value")
            sys_table.add_row(
                Text("Platform:", style="bold"),
                Text(state.get("platform", "?")),
            )
            sys_table.add_row(
                Text("CPU cores:", style="bold"),
                Text(str(state.get("cpu_cores", "?"))),
            )
            sys_table.add_row(
                Text("RAM:", style="bold"),
                Text(f"{state.get('ram_available', '?')} / {state.get('ram_total', '?')} GB"),
            )
            sys_panel = Panel(
                Group(
                    Text("System", style="bold underline"),
                    sys_table,
                ),
                box=box.ROUNDED,
                border_style="yellow",
            )
            left_parts.append(sys_panel)

            svc_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            svc_table.add_column("icon", style="bold", width=2)
            svc_table.add_column("service")
            svc_table.add_column("status", width=14)
            for sname, sinfo in sorted(state["services"].items()):
                icon = STATUS_ICONS.get(sinfo["status"], "\u25cb")
                color = _COLORS_SERVICES.get(sinfo["status"], "white")
                detail = sinfo.get("detail", "")
                status_text = Text(f"{icon} {sinfo['status'].upper()}", style=color)
                svc_table.add_row("", f"{sname:20s}", status_text)
            svc_panel = Panel(
                Group(
                    Text("Services", style="bold underline"),
                    svc_table,
                ),
                box=box.ROUNDED,
                border_style="blue",
            )
            left_parts.append(svc_panel)

        events = state.get("events", [])
        event_lines = []
        for ts, msg in events[-20:]:
            event_lines.append(Text(f"  [{ts}] {msg}"))
        if not event_lines:
            event_lines.append(Text("  (no events yet)", style="dim"))

        events_panel = Panel(
            Group(
                Text("Events", style="bold underline"),
                Group(*event_lines),
            ),
            box=box.ROUNDED,
            border_style="magenta",
            height=22,
        )

        uptime = int(time.time() - self._start_time)
        uptime_str = f"{uptime // 60}m {uptime % 60}s"
        if self.mode == "root":
            footer_text = Text.assemble(
                (" Status: ", "bold"),
                ("Running", "green"),
                ("  |  Workers: ", "bold"),
                (str(len(state["workers"])), "cyan"),
                ("  |  Uptime: ", "bold"),
                (uptime_str, "yellow"),
                ("  |  Press Ctrl+C to stop", "dim"),
            )
        else:
            status_str = state.get("connection_status", "idle")
            color = "green" if state.get("registered") else "yellow"
            footer_text = Text.assemble(
                (" Status: ", "bold"),
                (status_str.upper(), color),
                ("  |  Registered: ", "bold"),
                ("Yes" if state.get("registered") else "No", "green" if state.get("registered") else "red"),
                ("  |  Uptime: ", "bold"),
                (uptime_str, "yellow"),
                ("  |  Press Ctrl+C to stop", "dim"),
            )
        footer_panel = Panel(footer_text, box=box.HEAVY, border_style="cyan")

        body = Columns([Group(*left_parts), events_panel], equal=False, expand=True)

        layout = Group(header_panel, body, footer_panel)
        return layout
