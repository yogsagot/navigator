"""The menu bar's *ROOT*, before the clock, while root access is open.

Not DN's: DOS refused no one (``navigator.lib.system.elevate``).  While the
root helper runs, a step refused permission -- a panel's read, the quick
view's -- may go to root without asking again, so the screen says so, the
way a shell's ``#`` prompt does.  Utilities > *Close root access* ends it.
"""

from __future__ import annotations

from typing import Any

from navkit.i18n import tr
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget


def caption() -> str:
    return f" {tr('ROOT')} "


class RootMark(Widget):
    """`` ROOT `` while :attr:`open`, which the application sets from
    ``ELEVATION.running`` once a second (a thread starts and ends the helper)."""

    #: Whether root access is open.
    open: bool = reactive(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.height = 1

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        surface.draw_text(0, 0, caption(), self.style)
