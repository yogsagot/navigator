"""Shift+Alt+Ins, ≡ > Screen grabber: DOS Navigator's ``ScreenGrabber`` (USERMENU.PAS).

A rectangle over the screen, its cells drawn inverted, moved and sized with
the keys; Enter puts the text in it on the clipboard, a line a row, and Esc
leaves.  The keys are ``TGrabber.HandleEvent``'s: the arrows move it, Ctrl
by eight across and four down; with Shift they move its bottom right
corner, sizing it; PgUp, PgDn, Home and End take it to the top, the bottom,
the left and the right.  It starts where it last was (``Top``, ``Bot``).

DN froze a copy of the screen under it; here the windows go on painting
under the rectangle, and what it takes is what was under it last.  Its
clipboard was DN's own, synced out with *Use system clipboard*; here it is
the application's (``copy_to_clipboard``), which that setting steers.
"""

from __future__ import annotations

import asyncio
from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import bind, reactive
from navkit.screen import Surface
from navkit.widget import Widget

#: Where the rectangle was last: ``(left, top, right, bottom)``, right and
#: bottom exclusive.  DN's ``Top`` (10, 5) and ``Bot`` (21, 6).
_last = [10, 5, 21, 6]


class ScreenGrabber(Widget):
    """The rectangle, over everything, taking every key."""

    #: The rectangle: left, top, right and bottom, the last two exclusive.
    area: Any = reactive((10, 5, 21, 6))

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.modal = True
        self.can_focus = True
        self.dims_behind = False
        self.x = bind(lambda o: 0)
        self.y = bind(lambda o: 0)
        self.width = bind(lambda o: o.parent.width if o.parent is not None else 0)
        self.height = bind(lambda o: o.parent.height if o.parent is not None else 0)
        self.area = tuple(_last)
        #: The text the rectangle covered when last painted, a string a row.
        self.text: list[str] = []
        self._done: asyncio.Future[Any] | None = None

    async def execute(self, app: Any) -> list[str] | None:
        """Show it; the rows taken with Enter, or None for Esc."""
        self._done = asyncio.get_running_loop().create_future()
        app.overlay(self)
        self.focus()
        try:
            return await self._done
        finally:
            if self.parent is not None:
                self.parent.remove(self)

    def _end(self, rows: list[str] | None) -> None:
        _last[:] = list(self.area)
        if self._done is not None and not self._done.done():
            self._done.set_result(rows)

    # -- the rectangle ------------------------------------------------------------------

    def _fit(self, left: int, top: int, right: int, bottom: int) -> None:
        """``TGrabber.Draw``'s clamping: at least a cell, never off the screen."""
        width, height = max(1, self.width), max(1, self.height)
        right, bottom = max(right, left + 1), max(bottom, top + 1)
        if right - left > width:
            right = left + width
        if bottom - top > height:
            bottom = top + height
        dx = -left if left < 0 else min(0, width - right)
        dy = -top if top < 0 else min(0, height - bottom)
        self.area = (left + dx, top + dy, right + dx, bottom + dy)

    def move(self, dx: int, dy: int) -> None:
        left, top, right, bottom = self.area
        self._fit(left + dx, top + dy, right + dx, bottom + dy)

    def resize(self, dx: int, dy: int) -> None:
        left, top, right, bottom = self.area
        self._fit(left, top, max(left + 1, right + dx), max(top + 1, bottom + dy))

    async def on_key(self, event: KeyEvent) -> bool:
        across = 8 if event.ctrl else 1
        down = 4 if event.ctrl else 1
        left, top, right, bottom = self.area
        key = event.key
        if event.matches("escape"):
            self._end(None)
        elif event.matches("enter"):
            self._end(list(self.text))
        elif key in ("pageup", "home", "end", "pagedown"):
            self.move(*{"pageup": (0, -top), "home": (-left, 0),
                        "end": (self.width - right, 0), "pagedown": (0, self.height - bottom)}[key])
        elif key in ("left", "right", "up", "down"):
            step = {"left": (-across, 0), "right": (across, 0), "up": (0, -down), "down": (0, down)}[key]
            (self.resize if event.shift else self.move)(*step)
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        return True

    # -- painting -----------------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        """What is under the rectangle, inverted (``Invert``), and kept as its text."""
        left, top, right, bottom = self.area
        rows: list[str] = []
        for y in range(top, min(bottom, surface.height)):
            text = []
            for x in range(left, min(right, surface.width)):
                char, style = surface.get(x, y)[:2]
                if char:
                    text.append(char)
                    surface.set_cell(x, y, char, style.derive(reverse=not style.reverse))
            rows.append("".join(text))
        self.text = rows
