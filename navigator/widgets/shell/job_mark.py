"""The menu bar's mark of operations in the background, just before the window strip's chips.

Not DN's, whose copies held the screen (``navigator.lib.system.background``).
While a copy or an erase is in the background the bar says how far it is --
`` 42% ``, or `` 2:37% `` for two, each counted by its own fraction -- and
`` ?42% `` in the error box's colours (``JobMark:asking``) while one has a
question waiting.  A click, or Window > *Background operation*, brings a box
back: one with a question first, else the newest.
"""

from __future__ import annotations

from typing import Any

from navkit import commands, tooltip
from navkit.events import MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import computed
from navkit.screen import Surface
from navkit.tooltip import with_keys
from navkit.widget import Widget

from navigator.lib.system.background import BACKGROUND
from navigator.widgets.shell.commands import ShowBackground


def caption() -> str:
    """What the mark says now; ``""`` with nothing in the background."""
    jobs = BACKGROUND.jobs
    if not jobs:
        return ""
    mark = "?" if BACKGROUND.asking else ""
    count = f"{len(jobs)}:" if len(jobs) > 1 else ""
    return f" {mark}{count}{BACKGROUND.percent()}% "


class JobMark(Widget):
    """:func:`caption` over the bar's row, while anything is in the background."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.height = 1

    @computed
    def asking(self) -> bool:
        """A question waits: the ``asking`` state its colours follow."""
        return BACKGROUND.asking

    def tooltip_at(self, x: int, y: int) -> str:
        """Each operation, how far it is, whether it waits; and how to bring one back."""
        lines = []
        for entry in BACKGROUND.jobs:
            if entry.asking:
                lines.append(tr("{operation}: waiting for an answer").format(operation=entry.title))
            else:
                lines.append(tr("{operation}: {percent}% done").format(operation=entry.title, percent=entry.percent))
        app = self.application
        key = commands.key_for(app, ShowBackground) if app is not None else None
        lines.append(with_keys(tr("Click to bring the box back"), commands.key_label(key) if key else ""))
        return tooltip.lines(*lines)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.button != "left" or event.action != "press":
            return False
        BACKGROUND.recall()
        return True

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        surface.draw_text(0, 0, caption(), self.style)
