"""Read a screenshot's ``.ans`` file into cells.

A Help page names a picture as ``![alt](shots/NAME.svg)``, which is what
GitHub and a website show.  Nothing here can draw an SVG, so
``tools/screenshot.py`` writes the same screen beside it as ``NAME.ans`` --
text with SGR colours -- and Help shows that.

The reader is strict, because the writer's grammar is small
(``tools/screenshot.py``, ``as_ansi``): one line a screen row, each run of
cells preceded by one ``ESC[0;...m`` that says the whole of its look, each
line ended ``ESC[0m``.  The parameters are the reset, then any of bold (1),
italic (3), underline (4) and strike (9), then both colours as
``38;2;r;g;b`` and ``48;2;r;g;b``.  Anything else -- another escape, a cursor
movement, a palette index, text before a line's first run -- is a
:class:`ValueError`: this is not a terminal emulator (``navkit/console.py``
is), and a file that asks for one was not written by the tool.

Nothing here knows of widgets or of files: text in, cells out.
"""

from __future__ import annotations

import re

from navkit.screen import Cell, char_width, is_flag
from navkit.style import Style

_SGR = re.compile(r"\x1b\[([0-9;]*)m")
_ATTRIBUTES = {1: "bold", 3: "italic", 4: "underline", 9: "strike"}


def _style(parameters: str) -> Style | None:
    """The look ``ESC[<parameters>m`` selects; None for the bare reset that ends a line."""
    try:
        numbers = [int(part) for part in parameters.split(";")]
    except ValueError:
        raise ValueError(f"not an SGR this reads: {parameters!r}") from None
    if numbers[0] != 0:
        raise ValueError(f"a run's SGR starts with a reset, not {parameters!r}")
    if len(numbers) == 1:
        return None
    look: dict[str, object] = {}
    at = 1
    while at < len(numbers):
        number = numbers[at]
        if number in _ATTRIBUTES:
            look[_ATTRIBUTES[number]] = True
            at += 1
        elif number in (38, 48) and numbers[at + 1 : at + 2] == [2] and len(numbers) >= at + 5:
            colour = tuple(numbers[at + 2 : at + 5])
            if not all(0 <= part <= 255 for part in colour):
                raise ValueError(f"not a colour: {parameters!r}")
            look["fg" if number == 38 else "bg"] = colour
            at += 5
        else:
            raise ValueError(f"not an SGR this reads: {parameters!r}")
    if "fg" not in look or "bg" not in look:
        raise ValueError(f"a run says both its colours: {parameters!r}")
    return Style(**look)  # type: ignore[arg-type]


def read(text: str) -> list[list[Cell]]:
    """The rows of cells *text* paints, every row as wide as the first.

    A wide character gets its second cell back (``""``, as a
    :class:`~navkit.screen.ScreenBuffer` keeps it), and a mark or the second
    half of a flag joins the cell before it, as it does there.  Raises
    :class:`ValueError` for anything outside the grammar above.
    """
    rows: list[list[Cell]] = []
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for number, line in enumerate(lines, 1):
        row: list[Cell] = []
        style: Style | None = None
        at = 0
        for match in _SGR.finditer(line):
            chars = line[at : match.start()]
            if chars and style is None:
                raise ValueError(f"line {number}: text outside a run")
            try:
                row.extend(_cells(chars, style))  # type: ignore[arg-type]
            except ValueError as error:
                raise ValueError(f"line {number}: {error}") from None
            style = _style(match.group(1))
            at = match.end()
        if at == 0 or line[at:] or style is not None:
            raise ValueError(f"line {number}: does not end with a reset")
        if rows and len(row) != len(rows[0]):
            raise ValueError(f"line {number}: {len(row)} cells wide, the first is {len(rows[0])}")
        rows.append(row)
    return rows


def _cells(chars: str, style: Style) -> list[Cell]:
    """*chars* as the cells of one run."""
    cells: list[Cell] = []
    held = ""  # a cell's text: a base, then whatever joins it
    for char in chars:
        if ord(char) < 0x20 or 0x7F <= ord(char) < 0xA0:
            raise ValueError(f"{char!r} is not a cell")
        joins = char_width(char) == 0 or (len(held) == 1 and is_flag(held + char))
        if held and not joins:
            cells.append((held, style))
            cells.extend([("", style)] * (char_width(held) - 1))
            held = ""
        if joins and not held:
            raise ValueError(f"{char!r} has no cell to join")
        held += char
    if held:
        cells.append((held, style))
        cells.extend([("", style)] * (char_width(held) - 1))
    return cells
