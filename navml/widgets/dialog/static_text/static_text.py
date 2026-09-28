"""The painting behind ``static_text.nml``.

Nothing but the painting, which is the division a two-half component is for.
The one thing worth knowing is that the ``~A~`` run is drawn here and not by
whoever owns the text: a shortcut is a *rendering* of a caption, so it belongs
with whatever renders it, and that keeps one parser and two painters in the
whole library.
"""

from __future__ import annotations

import re

from navkit.screen import Surface, char_width
from navkit.style import Style
from navkit.widget import Widget

from navml.widgets.dialog.control import parse_shortcut


def draw_caption(
    surface: Surface,
    x: int,
    y: int,
    text: str,
    style: Style,
    shortcut_style: Style,
    max_width: int | None = None,
) -> int:
    """Paint *text* with its ``~A~`` letter in *shortcut_style*.

    Returns the cells used, as :meth:`Surface.draw_text` does, so a caller
    laying out a row of these can keep counting.  Three calls rather than one
    because a style is per cell and the marked run is a different one; the
    widths come back from ``draw_text`` so a wide character inside the caption
    cannot put the third call in the wrong column.
    """
    caption, start, letter = parse_shortcut(text)
    if start < 0 or not letter:
        return surface.draw_text(x, y, caption, style, max_width)
    limit = surface.width - x if max_width is None else max_width
    used = surface.draw_text(x, y, caption[:start], style, limit)
    used += surface.draw_text(
        x + used, y, caption[start : start + len(letter)], shortcut_style, limit - used
    )
    used += surface.draw_text(
        x + used, y, caption[start + len(letter) :], style, limit - used
    )
    return used


#: What :attr:`StaticText.links` treats as an address: a scheme and
#: everything up to the next space.
URL = re.compile(r"https?://\S+")


def link_urls(surface: Surface, x: int, y: int, line: str) -> None:
    """Mark every address in *line*, painted at *x*, *y*, as a link to itself.

    Done over the cells already drawn, so the ``~A~`` run and the colours stay
    as ``draw_caption`` left them.  An address a wrap has broken is linked a
    line at a time, each half to what it holds -- which is what the reader of
    a broken address sees too.
    """
    for match in URL.finditer(line):
        column = x + sum(max(1, char_width(c)) for c in line[: match.start()])
        for offset in range(len(match.group())):
            if not 0 <= column + offset < surface.width:
                continue
            char, style = surface.get(column + offset, y)
            surface.set_cell(column + offset, y, char, style.derive(link=match.group()))


def wrapped(text: str, width: int) -> list[str]:
    """*text* broken to *width*, honouring the newlines it already has.

    Greedy on whitespace and never splits a word that fits, which is what a
    prompt wants; a word longer than the line is broken rather than allowed to
    clip, because a path or a filename is exactly the case that happens and
    losing its tail is worse than a hard break.
    """
    if width < 1:
        return []
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words, current = paragraph.split(" "), ""
        for word in words:
            while len(word) > width:
                if current:
                    lines.append(current)
                    current = ""
                lines.append(word[:width])
                word = word[width:]
            candidate = f"{current} {word}" if current else word
            if len(candidate) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


class StaticText(Widget):
    """A block of text that wraps, and never takes the keyboard."""

    #: The marked letter of a ``~A~`` run.  A part rather than a colour on the
    #: widget because it is a run *inside* one ``draw_text``, which is the
    #: case *Parts* exists for.
    parts = ("shortcut",)

    def render(self, surface: Surface) -> None:
        style, shortcut = self.style, self.part_style("shortcut")
        caption, _, _ = parse_shortcut(self.text)
        lines = (
            wrapped(self.text, self.width)
            if self.wrap
            else self.text.split("\n")
        )
        for row, line in enumerate(lines[: max(0, self.height)]):
            plain, _, _ = parse_shortcut(line)
            if self.align == "right":
                x = max(0, self.width - len(plain))
            elif self.align == "center":
                x = max(0, (self.width - len(plain)) // 2)
            else:
                x = 0
            draw_caption(surface, x, row, line, style, shortcut, self.width - x)
            if self.links:
                link_urls(surface, x, row, plain)
