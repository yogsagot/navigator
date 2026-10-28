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

**A key is set apart** where the text is :class:`Markup`: its ``~`` runs are
painted in the ``key`` part, as the key bar paints a key.  A plain ``str`` is
painted as it is, tildes and all -- so a file name or a path never has to be
escaped, and only a tooltip built to carry a key (:func:`with_keys`) is read
as markup.
"""

from __future__ import annotations

from collections.abc import Iterable

from navkit.commands import Command
from navkit.reactive import bind, computed, reactive
from navkit.screen import Surface, char_width
from navkit.text import caption_runs, escape_caption
from navkit.widget import Widget


class ShowTooltip(Command):
    """Show the tooltip of where the keyboard is, beside it, until the next
    key: the focused widget's :meth:`~navkit.widget.Widget.tooltip_at` at its
    :meth:`~navkit.widget.Widget.tooltip_anchor`.  For a terminal that never
    reports a resting pointer (no mode 1003), and for whoever does not reach
    for the mouse.  Bound in the application's own key table, which the
    application reads for this one command even while a modal is up -- a
    dialog's check box is what it is most wanted for."""


class Markup(str):
    """A tooltip whose ``~`` runs are keys (:func:`navkit.text.caption_runs`),
    ``~~`` a tilde.  Concatenating one gives a plain ``str`` again, so build
    the whole text with :func:`with_keys` or :func:`lines`, which escape what
    they are handed as plain."""


def _markup(text: str) -> str:
    """*text* as markup: itself if it is, its tildes doubled if it is not."""
    return str(text) if isinstance(text, Markup) else escape_caption(text)


def with_keys(text: str, keys: Iterable[str] | str) -> str:
    """*text* and the *keys* that do the same, already spelled for show
    (``Ctrl-F4``), in brackets after it: ``Close (Ctrl-F4)`` with the key set
    apart.  *text* alone, as it was, when there are no keys."""
    keys = [keys] if isinstance(keys, str) else list(keys)
    keys = [key for key in keys if key]
    if not keys:
        return text
    marked = ", ".join(f"~{escape_caption(key)}~" for key in keys)
    return Markup(f"{_markup(text)} ({marked})" if text else marked)


def plain(text: str) -> str:
    """*text* as read, its markup taken away: what a test compares, and what
    a line that cannot show a key's colour (the key bar's hint) shows."""
    if not isinstance(text, Markup):
        return text
    return "\n".join("".join(run for run, _ in caption_runs(line)) for line in text.split("\n"))


def lines(*texts: str) -> str:
    """The non-empty *texts*, a line each -- :class:`Markup` if any is."""
    found = [text for text in texts if text]
    if not any(isinstance(text, Markup) for text in found):
        return "\n".join(found)
    return Markup("\n".join(_markup(text) for text in found))


def _width(text: str) -> int:
    return sum(char_width(char) for char in text)


def _spans(line: str, room: int) -> list[tuple[int, int]]:
    """Where the pieces of *line* at most *room* cells wide start and end: at
    the last blank that fits, which is dropped, else wherever the width runs out."""
    spans: list[tuple[int, int]] = []
    start = 0
    while _width(line[start:]) > room:
        cut, used = start, 0
        for index in range(start, len(line)):
            used += char_width(line[index])
            if used > room:
                break
            cut = index + 1
        blank = line.rfind(" ", start, cut + 1)
        if blank > start:
            spans.append((start, blank))
            start = blank + 1
        else:
            end = max(start + 1, cut)
            spans.append((start, end))
            start = end
    spans.append((start, len(line)))
    return spans


def _wrap(line: str, room: int) -> list[str]:
    """*line* in pieces of at most *room* cells: at the last blank that fits,
    else wherever the width runs out."""
    return [line[start:end] for start, end in _spans(line, room)]


class Tooltip(Widget):
    """A tooltip's text in a box beside the pointer."""

    #: A key named in :class:`Markup`.
    parts = ("key",)

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
    def _pieces(self) -> tuple[tuple[str, tuple[bool, ...]], ...]:
        """Each line as shown and which of its characters are a key's, wrapped
        to what the parent leaves inside the padding."""
        parent = self.parent
        room = max(1, parent.width - 2) if parent is not None and parent.width > 2 else 0
        markup = isinstance(self.text, Markup)
        found: list[tuple[str, tuple[bool, ...]]] = []
        for line in self.text.split("\n"):
            runs = caption_runs(line) if markup else [(line, False)]
            plain = "".join(run for run, _ in runs)
            marks = tuple(marked for run, marked in runs for _ in run)
            spans = _spans(plain, room) if room else [(0, len(plain))]
            found.extend((plain[start:end], marks[start:end]) for start, end in spans)
        return tuple(found)

    @computed
    def lines(self) -> tuple[str, ...]:
        """The text's lines as shown, each wrapped to what the parent leaves
        inside the padding."""
        return tuple(text for text, _ in self._pieces)

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
        key = self.part_style("key")
        room = max(0, self.width - 2)
        surface.fill(0, 0, self.width, self.height, " ", style)
        for y, (line, marks) in enumerate(self._pieces):
            if not any(marks):
                surface.draw_text(1, y, line, style, room)
                continue
            x = 1
            for char, marked in zip(line, marks):
                if x - 1 >= room:
                    break
                surface.draw_text(x, y, char, key if marked else style, room - (x - 1))
                x += char_width(char)
