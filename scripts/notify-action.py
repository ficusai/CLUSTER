#!/usr/bin/env python3
"""Clickable auto-dismiss notification helper with optional action callback."""

import sys
import subprocess
import shlex

try:
    import gi
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify, GLib
except Exception:
    gi = None


def _popen_cmd(cmd):
    argv = shlex.split(cmd)
    return subprocess.Popen(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def main():
    if len(sys.argv) < 3:
        sys.stderr.write(
            "Usage: notify-action.py <title> <message> [action-command]\n"
        )
        sys.exit(1)

    title = sys.argv[1]
    message = sys.argv[2]
    action_cmd = sys.argv[3] if len(sys.argv) > 3 else None

    if gi and Notify.init("notify-action"):
        n = Notify.Notification.new(title, message, "dialog-information")
        n.set_timeout(5000)

        clicked = [False]
        loop = GLib.MainLoop()

        def _on_action(notification, action_name):
            if action_name == "open" and action_cmd and not clicked[0]:
                clicked[0] = True
                try:
                    _popen_cmd(action_cmd)
                except Exception as exc:
                    sys.stderr.write(f"Action command failed: {exc}\n")
            notification.close()
            loop.quit()

        def _on_closed(*_args):
            loop.quit()

        # Guarantee we exit even if the notification server never emits 'closed'.
        GLib.timeout_add_seconds(6, lambda *_args: loop.quit())

        if action_cmd:
            n.add_action("open", "Open Terminal", _on_action)

        n.connect("closed", _on_closed)

        if n.show():
            loop.run()
            Notify.uninit()
            return

    # Fallback: at least send the notification with timeout, no action
    cmd = ["notify-send", title, message, "--expire-time=5000"]
    try:
        subprocess.run(cmd)
    except Exception:
        pass


if __name__ == "__main__":
    main()
