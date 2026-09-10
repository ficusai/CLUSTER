#!/usr/bin/env python3
"""External live dashboard for AI Cluster Auto-Connect.
Queries the root HTTP API and tails .run.log + logs/*.log in one Rich terminal UI.
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from common.loghub import LogHub

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich import box
except ImportError:
    print("Error: rich is required. Install with: pip install rich")
    sys.exit(1)


APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR / "logs"
RUN_LOG = LOG_DIR / "current.log"
if not RUN_LOG.exists():
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    RUN_LOG = logs[0] if logs else LOG_DIR / "launcher.log"
LOG_DIR = APP_DIR / "logs"
API_URL = "http://127.0.0.1:8080/api/status"

console = Console()


@LogHub.log_call("DASHBOARD")
def fetch_status():
    try:
        import urllib.request
        with urllib.request.urlopen(API_URL, timeout=2) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


@LogHub.log_call("DASHBOARD")
def tail_lines(path, max_lines=200):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]
    except Exception:
        return []


@LogHub.log_call("DASHBOARD")
def render_dashboard():
    status = fetch_status()
    now = datetime.now().strftime("%H:%M:%S")

    header = Text.assemble(
        ("AI Cluster Events", "bold cyan"),
        "  ",
        (f"{now}", "bold white"),
    )
    header_panel = Panel(header, box=box.HEAVY, border_style="cyan")

    if status:
        mode = "ROOT"
        hostname = status.get("hostname", "?")
        ai_mode = status.get("ai_mode", False)
        workers = status.get("workers", [])
        llama = status.get("llama_server", None)

        info_text = Text.assemble(
            (f"{hostname}\n", "bold yellow"),
            (f"Mode: {mode}   AI: {'yes' if ai_mode else 'no'}\n", "white"),
            (f"Workers: {len(workers)}   llama-server: ", "white"),
        )
        if llama:
            info_text.append(f"PID {llama.get('pid', '?')}", style="green")
        else:
            info_text.append("stopped", style="red")

        # Workers table
        w_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1), expand=True)
        w_table.add_column("hostname", style="bold")
        w_table.add_column("ip")
        w_table.add_column("platform")
        w_table.add_column("cores")
        w_table.add_column("ram GB")
        if workers:
            for w in workers:
                w_table.add_row(
                    w.get("hostname", "?"),
                    w.get("ip", "?"),
                    w.get("platform", "?"),
                    str(w.get("cpu_cores", "?")),
                    str(w.get("ram_available", "?")),
                )
        else:
            w_table.add_row("-", "-", "-", "-", "-")

        status_panel = Panel(
            info_text,
            title="Cluster Status",
            box=box.ROUNDED,
            border_style="blue",
        )
        workers_panel = Panel(
            w_table,
            title="Workers",
            box=box.ROUNDED,
            border_style="blue",
        )
    else:
        status_panel = Panel(
            Text("API unreachable", style="red"),
            title="Cluster Status",
            box=box.ROUNDED,
            border_style="red",
        )
        workers_panel = Panel(
            Text("No data", style="dim"),
            title="Workers",
            box=box.ROUNDED,
            border_style="blue",
        )

    # Recent log lines
    log_lines = tail_lines(RUN_LOG, 40)
    for p in sorted(LOG_DIR.glob("*.log")):
        log_lines.extend(tail_lines(p, 40))
    log_text = Text("\n".join(log_lines[-120:]) or "No log output yet.")
    log_panel = Panel(
        log_text,
        title="Recent Logs",
        box=box.ROUNDED,
        border_style="green",
    )

    layout = Layout()
    layout.split_column(
        Layout(header_panel, size=3),
        Layout(status_panel, size=5),
        Layout(workers_panel, size=8),
        Layout(log_panel),
    )
    return layout


@LogHub.log_call("DASHBOARD")
def main():
    console.clear()
    try:
        with Live(render_dashboard(), refresh_per_second=2, screen=False) as live:
            while True:
                time.sleep(2)
                live.update(render_dashboard())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
