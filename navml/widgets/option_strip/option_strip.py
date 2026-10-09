"""A row of a window's options, each lit while it is on -- a component written in Python alone.

Not DOS Navigator's: its windows showed their options only as the ``On``/``Off``
of a menu's key column, and a mode switched on once -- a column block kept for
one file -- was easy to forget.  The strip shows the options of the window it
sits in, one short label each, and a click on one runs the command that switches
it, as the menu entry would.  **Actions are not its business**: a strip holds
switches and values, and everything that *does* something stays on the menus
and the keys.

**Everything it shows comes from the commands.**  An item is a command and a
label; whether it is lit is the command's ``checks`` answer (unless the item
says otherwise) and whether it is greyed its ``enables`` -- asked from
:attr:`OptionStrip.target`, the widget whose options they are -- so the strip
and the menus cannot disagree.  Both are read while painting, as ``KeyBar``
reads them: any reactive write repaints the frame, so an option switched from a
key or a menu lights here without anything telling the strip.

**Each item is bracketed, ``[§]``, as a frame's icons are, and the items stand
a cell apart.**  The strip paints nothing between them, so on a window's
border the frame's own line shows through in the frame's colours --
``═[⌶]═[⇥]═[§]═``.

**It is as wide as its items.**  :attr:`OptionStrip.used_width` is what they
take, and the items that would pass :attr:`OptionStrip.room` are left out from
the last -- so whoever places the strip binds its width to the one and gives it
the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from navkit import commands
from navkit.commands import Binding
from navkit.events import MouseClickEvent
from navkit.reactive import computed, reactive
from navkit.screen import Surface, char_width
from navkit.widget import Widget


@dataclass(frozen=True)
class OptionItem:
    """One option: the command a click asks for, and the label it is shown by.

    *label* is called while painting and while laying out, so whatever
    reactive it reads -- the mode it names, the language -- is followed.  *lit*
    overrides the command's ``checks``: a value such as the file type is never
    lit, and Insert/Overwrite is lit in overwrite.
    """

    command: Binding
    label: Callable[[], str]
    lit: Callable[[], bool] | None = None


def text_width(text: str) -> int:
    """The columns *text* takes on screen."""
    return sum(char_width(char) for char in text)


class OptionStrip(Widget):
    """A window's options in a row, each lit while on, each switched by a click."""

    #: An option's label.  ``:checked`` while it is on, ``:disabled`` while
    #: its command cannot run.
    parts = ("item",)

    #: The options, left to right.  Replaced, never changed in place.
    items: tuple = reactive(())

    #: Whose options they are: the widget a click's command starts from, and
    #: whose ``checks``/``enables`` answer for lit and greyed -- so the answer
    #: is about this window even while a menu holds the keyboard.
    target: Any = reactive(None)

    #: The columns there are for the strip; items that would pass them are
    #: left out, the last first.
    room: int = reactive(0)

    @computed
    def spans(self) -> tuple[tuple[int, int, OptionItem, str], ...]:
        """``(start, end, item, label)`` for each item shown: ``[label]`` from
        *start* to *end*, end exclusive, a cell after the one before."""
        found, column = [], 0
        for item in self.items:
            label = item.label()
            end = column + text_width(label) + 2
            if end > self.room:
                break
            found.append((column, end, item, label))
            column = end + 1
        return tuple(found)

    @computed
    def used_width(self) -> int:
        """What the shown items take, from the first ``[`` to the last ``]``."""
        spans = self.spans
        return spans[-1][1] if spans else 0

    def _state(self, item: OptionItem) -> tuple[bool, bool]:
        """Whether *item* is lit, and whether its command can run now."""
        app = self.application
        if app is None:
            return False, False
        enabled = commands.enabled(app, item.command, self.target)
        if item.lit is not None:
            lit = item.lit()
        else:
            lit = commands.checked(app, item.command, self.target) is True
        return lit and enabled, enabled

    def render(self, surface: Surface) -> None:
        # No fill: what is between the items is whatever lies beneath.
        for start, _end, item, label in self.spans:
            lit, enabled = self._state(item)
            look = self.part_style("item", checked=lit, disabled=not enabled)
            surface.draw_text(start, 0, f"[{label}]", look, max(0, self.width - start))

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A left press on an item runs its command, if it can run.  Every press
        is the strip's, so none reaches the frame beneath it."""
        if event.action != "press" or event.button != "left":
            return True
        app = self.application
        for start, end, item, _label in self.spans:
            if start <= event.x < end and app is not None:
                if commands.enabled(app, item.command, self.target):
                    await commands.run(app, item.command, self.target)
                break
        return True
