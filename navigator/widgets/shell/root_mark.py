"""The menu bar's *ROOT*, before the clock, while root access is open.

Not DN's: DOS refused no one (``navigator.lib.system.elevate``).  While the
root helper runs, a step refused permission -- a panel's read, the quick
view's -- may go to root without asking again, so the screen says so, the
way a shell's ``#`` prompt does.  Utilities > *Close root access* ends it.

**Its tooltip says what the mark means and how it ends** -- after System
Setup's idle minutes, or at once from the menu -- since a bare ``ROOT`` says
neither.
"""

from __future__ import annotations

from typing import Any

from navkit import commands
from navkit.i18n import tr, tr_n
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navigator.settings import SETTINGS
from navigator.widgets.shell.commands import CloseRootAccess


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

    def tooltip_at(self, x: int, y: int) -> str:
        """What *ROOT* means, when it closes by itself, and how to close it now."""
        lines = [tr("Root access is open"),
                 tr("A step refused permission is done again as root without asking")]
        minutes = SETTINGS.system.root_timeout
        if minutes > 0:
            lines.append(tr_n("It closes after {n} idle minute", "It closes after {n} idle minutes", minutes))
        # The menu's own captions, so the path reads as the menu does in any language.
        path = " > ".join(caption.replace("~", "") for caption in (tr("~U~tilities"), tr("Close ~r~oot access")))
        close = tr("{menu} closes it now").format(menu=path)
        app = self.application
        key = commands.key_for(app, CloseRootAccess) if app is not None else None
        lines.append(f"{close} ({commands.key_label(key)})" if key else close)
        return "\n".join(lines)

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        surface.draw_text(0, 0, caption(), self.style)
