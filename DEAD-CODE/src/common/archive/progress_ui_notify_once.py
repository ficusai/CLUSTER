"""Archived dead method previously defined in StateMixin (src/common/progress_ui/state.py).

notify_once had zero call sites across the codebase. Note it also depended on
an instance attribute `_notified_events` that is never set in InitProgressUIMixin.
"""


def notify_once(self, event_key, title, message, urgency="normal"):
    if event_key not in self._notified_events:
        self._notified_events.add(event_key)
        send_notification(title, message, urgency)