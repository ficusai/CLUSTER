"""progress_ui.py — ProgressUI class composed from per-method mixins."""
from .init_progress_ui import InitProgressUIMixin
from .lifecycle import LifecycleMixin
from .state import StateMixin
from .render import RenderMixin


class ProgressUI(InitProgressUIMixin, LifecycleMixin, StateMixin, RenderMixin):
    pass
