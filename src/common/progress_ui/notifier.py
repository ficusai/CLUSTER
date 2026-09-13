"""notifier.py — Cross-platform notification functions."""
import os
import platform
import subprocess
from ..loghub import LogHub


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
