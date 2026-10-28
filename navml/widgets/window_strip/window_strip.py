"""The windows of a desktop on one line, by number -- a component in Python alone.

Not Turbo Vision's or DOS Navigator's: a window behind a zoomed one is out of
sight and soon out of mind, and DN OSP's answer, the window's number in its
close icon, says nothing about the others.  This lists them all, in number
order, the top one marked, and a click on one brings it forward -- the same
numbers Win+1 .. Win+9 go by.  The wheel anywhere over it steps the top
window along them, down to the next number and up to the one before, round
from the last to the first.

Two forms: the numbers alone, a chip of three cells each, or each number with
the window's :meth:`~navml.widgets.window.Window.short_name`.  Titles too long
for the width are cut evenly, down to the numbers alone, and what still does
not fit is counted at the end as ``+3``.  Nothing is painted while there are
fewer than two windows, because one is never out of sight.

**Painted from** :attr:`Desktop.open_windows` **and** ``active_window``, the
two reactive things a desktop has; the names are read at every paint, and a
window's name changing repaints its own frame, so the strip goes with it.

**A chip's tooltip is its window's whole name** (:meth:`~navml.widgets.window.Window.list_name`,
a chip's being cut or left out) and the key that brings it forward; the ``+k``
lists the windows it counts, one a line.
"""

from __future__ import annotations

from typing import Any

from navkit import commands
from navkit.events import MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget

from navml.commands import SelectWindow


class WindowStrip(Widget):
    """A desktop's numbered windows, as chips; the top one ``:selected``."""

    #: The desktop whose windows are listed.
    desktop: Any = reactive(None)

    #: Whether a chip carries the window's name after its number.
    labels: bool = reactive(False)

    #: Which end of its width the chips keep to: ``"left"`` or ``"right"``.
    align: str = reactive("left")

    #: A window's chip, ``:selected`` for the top one, and the number on it.
    parts = ("chip", "number")

    def windows(self) -> list[Any]:
        """The numbered windows, in number order."""
        desktop = self.desktop
        if desktop is None:
            return []
        return sorted((w for w in desktop.open_windows if w.number), key=lambda w: w.number)

    def chips(self) -> list[tuple[int, str, Any]]:
        """``(start, text, window)`` for each chip shown, left to right.

        A window left out for want of room has no chip; :meth:`hidden` counts
        them.
        """
        return self._layout()[0]

    def hidden(self) -> int:
        """How many windows have no chip for want of room."""
        return self._layout()[1]

    def window_at(self, column: int) -> Any:
        """The window whose chip is under *column*, or None."""
        for start, text, window in self.chips():
            if start <= column < start + len(text):
                return window
        return None

    def tooltip_at(self, x: int, y: int) -> str:
        chips, hidden, end = self._layout()
        window = self.window_at(x)
        if window is not None:
            return self._describe(window)
        if hidden and end <= x < end + len(f"+{hidden}"):
            return "\n".join(f"{w.number} {w.list_name()}" for w in self.windows()[len(chips):])
        return super().tooltip_at(x, y)

    def _describe(self, window: Any) -> str:
        """*window*'s name, and the key that brings it forward."""
        app = self.application
        key = None
        if app is not None and self.desktop is not None:
            key = commands.key_for(app, SelectWindow(number=window.number), self.desktop)
        name = window.list_name() or window.short_name()
        return f"{name} ({commands.key_label(key)})" if key else name

    def _fit(self, names: list[str]) -> list[str]:
        """*names* cut evenly until every chip fits, or to nothing."""
        def width(cut: int) -> int:
            return sum(3 + (min(len(n), cut) + 1 if n and cut else 0) for n in names)

        cut = max((len(n) for n in names), default=0)
        while cut > 0 and width(cut) > self.width:
            cut -= 1
        ellipsis = "\u2026" if self.glyphs > 1 else "~"
        return [n if len(n) <= cut else n[: cut - 1] + ellipsis if cut > 1 else n[:cut] for n in names]

    def _layout(self) -> tuple[list[tuple[int, str, Any]], int, int]:
        """The chips shown, how many windows were left out, and where the
        ``+k`` that counts them starts."""
        windows = self.windows()
        if len(windows) < 2:
            return [], 0, 0
        names = self._fit([w.short_name() if self.labels else "" for w in windows])
        chips: list[tuple[int, str, Any]] = []
        x, hidden = 0, 0
        for index, (window, name) in enumerate(zip(windows, names)):
            text = f" {window.number} {name} " if name else f" {window.number} "
            rest = len(windows) - index - 1
            if x + len(text) > self.width - (len(f"+{rest}") if rest else 0):
                hidden = len(windows) - index
                break
            chips.append((x, text, window))
            x += len(text)
        used = x + (len(f"+{hidden}") if hidden else 0)
        shift = max(0, self.width - used) if self.align == "right" else 0
        return [(start + shift, text, w) for start, text, w in chips], hidden, x + shift

    def render(self, surface: Surface) -> None:
        desktop = self.desktop
        top = desktop.active_window if desktop is not None else None
        chips, hidden, end = self._layout()
        for start, text, window in chips:
            selected = window is top
            surface.draw_text(start, 0, text, self.part_style("chip", selected=selected))
            surface.draw_text(start + 1, 0, str(window.number), self.part_style("number", selected=selected))
        if hidden:
            surface.draw_text(end, 0, f"+{hidden}", self.part_style("chip"))

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.is_wheel:
            return self._step(-1 if event.button in ("wheel_up", "wheel_left") else 1)
        if event.button != "left" or event.action != "press":
            return False
        window = self.window_at(event.x)
        if window is None or self.desktop is None:
            return False
        self.desktop.activate(window)
        return True

    def _step(self, delta: int) -> bool:
        """Bring forward the window *delta* numbers on from the top one."""
        windows = self.windows()
        if len(windows) < 2:
            return False
        top = self.desktop.active_window
        index = windows.index(top) if top in windows else (-1 if delta > 0 else 0)
        self.desktop.activate(windows[(index + delta) % len(windows)])
        return True
