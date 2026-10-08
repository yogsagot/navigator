"""The line that catches a key: every key it is given is one to bind.

A :class:`~navml.widgets.dialog.control.Control` that takes the keyboard and
every key with it, ahead of the dialog's own table -- Tab, Alt+letter and
F10 are keys to bind here, not the dialog's.  Enter accepts what it caught
and Esc cancels, so those two can be bound only in ``keybindings.ini``.  Two
keys in a row are a chord, ``Ctrl-K B``; a third starts again.
"""

from __future__ import annotations

from typing import Any

from navkit.commands import key_label, parse_key
from navkit.events import KeyEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navml.widgets.dialog.control import Control


class KeyCatcher(Control):
    """The keys caught so far, shown as a menu shows them."""

    #: Each key caught, in its canonical spelling; at most two, a chord's.
    caught: tuple[str, ...] = reactive(())

    #: How many keys a chord may have.
    CHORD = 2

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Called with the spec on Enter, or None on Esc: the dialog's close.
        self.done: Any = None

    @property
    def spec(self) -> str:
        """What was caught as a key table spells it; empty for nothing yet."""
        return " ".join(self.caught)

    def render(self, surface: Surface) -> None:
        text = " ".join(key_label(key) for key in self.caught)
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        surface.draw_text(max(0, (self.width - len(text)) // 2), 0, text, self.style, self.width)

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("enter"):
            if self.caught and self.done is not None:
                self.done(self.spec)
            return True
        if event.matches("escape"):
            if self.done is not None:
                self.done(None)
            return True
        try:
            key = parse_key(event.name)
        except ValueError:
            return True
        start = self.caught if len(self.caught) < self.CHORD else ()
        self.caught = (*start, key)
        return True
