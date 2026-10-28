"""The box a tooltip is shown in -- :attr:`Widget.tooltip` made visible.

Not Turbo Vision's or DOS Navigator's: neither had tooltips.  The application
puts one on top (:meth:`Application.overlay`) when the mouse pointer has rested
on a widget with a tooltip for :attr:`Application.tooltip_delay` milliseconds, and
takes it away at the next input.  See *Tooltips: hover that waits* in
``navkit/DESIGN.md``.

**Its geometry is bound, not assigned**: the root's ``layout`` hands every
child its own size on a resize, and steps around a size that carries a
binding.  Each line of :attr:`Tooltip.text` is padded a blank either side,
wrapped where it would pass the parent's width -- a long path, cut at any
character since it has no blanks to break at --
and the box sits a cell below and right of :attr:`Tooltip.anchor` -- left of
it or above it instead where it would pass the parent's edge.
"""

from __future__ import annotations

from navkit.reactive import bind, computed, reactive
from navkit.screen import Surface, char_width
from navkit.widget import Widget


def _width(text: str) -> int:
    return sum(char_width(char) for char in text)


def _wrap(line: str, room: int) -> list[str]:
    """*line* in pieces of at most *room* cells: at the last blank that fits,
    else wherever the width runs out."""
    pieces: list[str] = []
    while _width(line) > room:
        cut, used = 0, 0
        for index, char in enumerate(line):
            used += char_width(char)
            if used > room:
                break
            cut = index + 1
        blank = line.rfind(" ", 0, cut + 1)
        if blank > 0:
            pieces.append(line[:blank])
            line = line[blank + 1:]
        else:
            pieces.append(line[: max(1, cut)])
            line = line[max(1, cut):]
    pieces.append(line)
    return pieces


class Tooltip(Widget):
    """A tooltip's text in a box beside the pointer."""

    #: What it says; a line per ``\\n``.
    text: str = reactive("")
    #: The pointer's cell, in the parent's coordinates.
    anchor: tuple[int, int] = reactive((0, 0))

    def __init__(self, text: str = "", anchor: tuple[int, int] = (0, 0), **kwargs) -> None:
        super().__init__(**kwargs)
        self.text = text
        self.anchor = anchor
        self.width = bind(lambda s: s._size[0])
        self.height = bind(lambda s: s._size[1])
        self.x = bind(lambda s: s._place(s.anchor[0], s.width, s.parent.width if s.parent else 0))
        self.y = bind(lambda s: s._place(s.anchor[1], s.height, s.parent.height if s.parent else 0))

    @computed
    def lines(self) -> tuple[str, ...]:
        """The text's lines, each wrapped to what the parent leaves inside the padding."""
        parent = self.parent
        room = max(1, parent.width - 2) if parent is not None and parent.width > 2 else 0
        found: list[str] = []
        for line in self.text.split("\n"):
            found.extend(_wrap(line, room) if room else [line])
        return tuple(found)

    @computed
    def _size(self) -> tuple[int, int]:
        """The text's width with its padding, and its lines, each no more than
        the parent has."""
        parent = self.parent
        width = max(_width(line) for line in self.lines) + 2
        height = len(self.lines)
        if parent is not None:
            width, height = min(width, parent.width), min(height, parent.height)
        return width, height

    @staticmethod
    def _place(at: int, size: int, room: int) -> int:
        """Where a box *size* long starts beside *at*: after it, else before
        it, else as far along as it fits."""
        if at + 1 + size <= room:
            return at + 1
        if at - size >= 0:
            return at - size
        return max(0, room - size)

    def render(self, surface: Surface) -> None:
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        for y, line in enumerate(self.lines):
            surface.draw_text(1, y, line, style, max(0, self.width - 2))
