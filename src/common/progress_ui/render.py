"""render.py — _render() for ProgressUI."""
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
from .constants import STATUS_ICONS, _COLORS_SERVICES as COLORS_SERVICES


class RenderMixin:
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
                color = COLORS_SERVICES.get(sinfo["status"], "white")
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
            color = COLORS_SERVICES.get(status_str, "white") if status_str in COLORS_SERVICES else "yellow"
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
                color = COLORS_SERVICES.get(sinfo["status"], "white")
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
