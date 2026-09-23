"""The painting behind ``static_text.nml``.

Nothing but the painting, which is the division a two-half component is for.
The one thing worth knowing is that the ``~A~`` run is drawn here and not by
whoever owns the text: a shortcut is a *rendering* of a caption, so it belongs
with whatever renders it, and that keeps one parser and two painters in the
whole library.
"""

from __future__ import annotations

from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget

from navml.widgets.control import parse_shortcut


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
