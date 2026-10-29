"""The painting behind ``static_text.nml``.

Nothing but the painting, which is the division a two-half component is for.
The one thing worth knowing is that the ``~A~`` run is drawn here and not by
whoever owns the text: a shortcut is a *rendering* of a caption, so it belongs
with whatever renders it, and that keeps one parser and two painters in the
whole library.
"""

from __future__ import annotations

import re

from navkit.bidi import display_width, painted_cells
from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget

from navml.widgets.dialog.control import caption_runs, parse_shortcut


def draw_caption(
    surface: Surface,
    x: int,
    y: int,
    text: str,
    style: Style,
    shortcut_style: Style,
    max_width: int | None = None,
) -> int:
    """Paint *text* with its ``~A~`` runs in *shortcut_style*.

    Returns the cells used, as :meth:`Surface.draw_text` does, so a caller
    laying out a row of these can keep counting.  One :meth:`Surface.draw_runs`
    call for the whole caption, so right-to-left text in it is ordered as one
    string and a marked letter keeps its colour wherever it lands.  Every
    marked run is highlighted, as Turbo Vision's ``MoveCStr`` highlighted
    them; the first is the shortcut.
    """
    return surface.draw_runs(
        x, y,
        [(run, shortcut_style if marked else style) for run, marked in caption_runs(text)],
        max_width,
    )


#: What :attr:`StaticText.links` treats as an address: a scheme and
#: everything up to the next space.
URL = re.compile(r"https?://\S+")


def link_urls(surface: Surface, x: int, y: int, line: str) -> None:
    """Mark every address in *line*, painted at *x*, *y*, as a link to itself.

    Done over the cells already drawn, so the ``~A~`` run and the colours stay
    as ``draw_caption`` left them.  An address a wrap has broken is linked a
    line at a time, each half to what it holds -- which is what the reader of
    a broken address sees too.

    The cells are found where they were painted (:func:`navkit.bidi.painted_cells`):
    in a Hebrew sentence, or on a mirrored screen, an address is not where
    counting characters from the left would put it.
    """
    matches = list(URL.finditer(line))
    if not matches:
        return
    for index, column, width in painted_cells(line, surface.rtl):
        match = next((m for m in matches if m.start() <= index < m.end()), None)
        if match is None:
            continue
        for cell in range(x + column, x + column + width):
            if 0 <= cell < surface.width:
                char, style = surface.get(cell, y)
                surface.set_cell(cell, y, char, style.derive(link=match.group()))


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
                x = max(0, self.width - display_width(plain))
            elif self.align == "center":
                x = max(0, (self.width - display_width(plain)) // 2)
            else:
                x = 0
            draw_caption(surface, x, row, line, style, shortcut, self.width - x)
            if self.links:
                link_urls(surface, x, row, plain)
