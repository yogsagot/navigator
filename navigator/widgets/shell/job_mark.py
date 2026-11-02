"""The menu bar's mark of operations in the background, just before the window strip's chips.

Not DN's, whose copies held the screen (``navigator.lib.system.background``).
While a copy or an erase is in the background the bar says how far it is:
`` 42% ``, and one segment each for more -- `` 10%|20% ``, oldest first --
each its own tooltip and its own click, which brings that one's box back.
A segment whose work has a question waiting reads ``?20%`` in the error
box's colours (``JobMark::job:asking``).  Window > *Background operation*
brings a box back too: one with a question first, else the newest.
"""

from __future__ import annotations

from typing import Any

from navkit import commands, tooltip
from navkit.bidi import display_width
from navkit.events import MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import computed
from navkit.screen import Surface
from navkit.tooltip import with_keys
from navkit.widget import Widget

from navigator.lib.system.background import BACKGROUND, Running
from navigator.widgets.shell.commands import ShowBackground

#: Between two segments.
SEPARATOR = "|"


def segment(entry: Running) -> str:
    """``42%``, or ``?42%`` while *entry* has a question waiting."""
    return f"{'?' if entry.asking else ''}{entry.percent}%"


def segments() -> list[tuple[int, str, Running]]:
    """``(start, text, entry)`` for each operation, oldest first, after the leading space."""
    found: list[tuple[int, str, Running]] = []
    x = 1
    for entry in BACKGROUND.jobs:
        text = segment(entry)
        found.append((x, text, entry))
        x += display_width(text) + display_width(SEPARATOR)
    return found


def caption() -> str:
    """What the mark says now; ``""`` with nothing in the background."""
    if not BACKGROUND.jobs:
        return ""
    return f" {SEPARATOR.join(text for _, text, _ in segments())} "


class JobMark(Widget):
    """:func:`caption` over the bar's row, while anything is in the background."""

    parts = ("job",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.height = 1

    @computed
    def busy(self) -> bool:
        """Anything in the background: when the mark shows at all."""
        return bool(BACKGROUND.jobs)

    @computed
    def natural_width(self) -> int:
        """As wide as :func:`caption` is now."""
        return display_width(caption())

    def entry_at(self, column: int) -> Running | None:
        """The operation whose segment is under *column*: the space before
        the first goes with it, and the one after the last with that."""
        found = segments()
        if not found:
            return None
        for start, text, entry in found:
            # A separator goes with the segment after it.
            if column < start + display_width(text):
                return entry
        return found[-1][2]

    def tooltip_at(self, x: int, y: int) -> str:
        """The operation under *x*: what it was started on and how far it is,
        or that it waits; the file it is on; and how to bring it back."""
        entry = self.entry_at(x)
        if entry is None:
            return super().tooltip_at(x, y)
        if entry.asking:
            line = tr("{operation}: waiting for an answer").format(operation=entry.subject)
        else:
            line = tr("{operation}: {percent}% done").format(operation=entry.subject, percent=entry.percent)
        app = self.application
        key = commands.key_for(app, ShowBackground) if app is not None else None
        # The file in hand indented under it, as the box's row would name it.
        return tooltip.lines(line, f"  {entry.current}" if entry.current else "",
                             with_keys(tr("Click to bring the box back"), commands.key_label(key) if key else ""))

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.button != "left" or event.action != "press":
            return False
        entry = self.entry_at(event.x)
        if entry is None:
            return False
        BACKGROUND.recall(entry)
        return True

    def render(self, surface: Surface) -> None:
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        runs: list[tuple[str, Any]] = [(" ", style)]
        for index, (_, text, entry) in enumerate(segments()):
            if index:
                runs.append((SEPARATOR, style))
            runs.append((text, self.part_style("job", asking=entry.asking)))
        runs.append((" ", style))
        if BACKGROUND.jobs:
            surface.draw_runs(0, 0, runs, self.width)
