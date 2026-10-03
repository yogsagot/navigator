"""Where a line's characters land on screen, and back.

The same rules the viewer paints by (``viewer.decode_cells``), over a string
instead of bytes: a tab runs to the next stop, a wide character takes two
columns, a combining mark takes none and is not drawn, and a control
character or a byte that was not UTF-8 is its CP437 glyph.

**The cursor lives in columns, not in string indices**, as it did in DN, where
the two were the same thing because ``ReadBlock`` had expanded every tab.  A
column may lie past a line's end -- Turbo Vision's editor let the cursor go
anywhere, and typing there pads with blanks -- and a column inside a tab or a
wide character belongs to that character.
"""

from __future__ import annotations

import unicodedata

from navkit.screen import char_width

from navigator.viewer import cp437

#: DN's hard-coded tab stop (``and cx,7`` in ``ReadBlock``).
TAB = 8


def is_escaped(char: str) -> bool:
    """Whether *char* stands for a byte that was not UTF-8 (``surrogateescape``)."""
    return "\udc80" <= char <= "\udcff"


def glyph(char: str) -> tuple[str, int]:
    """What *char* is drawn as, and how many columns it takes.

    A tab is not answered here: its width depends on where it starts.
    """
    code = ord(char)
    if is_escaped(char):
        return cp437(code - 0xDC00), 1
    if code < 0x20 or code == 0x7F:
        return cp437(code), 1
    if code < 0x7F:
        return char, 1
    if 0xD800 <= code <= 0xDFFF:
        return "?", 1
    width = char_width(char)
    if width == 0:
        if unicodedata.combining(char) or unicodedata.category(char) in ("Mn", "Me"):
            return "", 0
        return "·", 1
    return char, width


def advance(char: str, column: int, tab: int = TAB) -> int:
    """How many columns *char* takes when it starts at *column*."""
    if char == "\t":
        return tab - column % tab
    return glyph(char)[1]


def width(line: str, tab: int = TAB) -> int:
    """How many columns *line* takes."""
    column = 0
    for char in line:
        column += advance(char, column, tab)
    return column


def column_of(line: str, index: int, tab: int = TAB) -> int:
    """The column the character at *index* starts in; past the end, the end."""
    column = 0
    for char in line[:index]:
        column += advance(char, column, tab)
    return column


def index_at(line: str, column: int, tab: int = TAB) -> tuple[int, int]:
    """The string index a *column* falls on, and how far past the end it is.

    A column inside a tab or a wide character gives that character's index.
    Past the line's end the index is ``len(line)`` and the second value says
    how many blanks typing there would need first.
    """
    at = 0
    for index, char in enumerate(line):
        step = advance(char, at, tab)
        if step and column < at + step:
            return index, 0
        at += step
    return len(line), max(0, column - at)


def cells(line: str, tab: int = TAB, limit: int | None = None) -> list[tuple[str, int]]:
    """One ``(glyph, index)`` per column, as ``viewer.Line.cells`` has.

    The second column of a wide character is ``("", index)``, and a tab is
    as many blanks as it covers.  Stops once *limit* columns are known.
    """
    out: list[tuple[str, int]] = []
    for index, char in enumerate(line):
        if limit is not None and len(out) >= limit:
            break
        if char == "\t":
            out.extend((" ", index) for _ in range(tab - len(out) % tab))
            continue
        shown, cols = glyph(char)
        if cols == 0:
            continue
        out.append((shown, index))
        if cols == 2:
            out.append(("", index))
    return out


def span(line: str, left: int, right: int, tab: int = TAB) -> tuple[int, int]:
    """The string indices of the characters that start in columns *left* to *right*.

    What a column block holds of *line*: a tab or a wide character belongs to
    the column it starts in, so one straddling *left* stays outside.  Past the
    line's end both are ``len(line)``.
    """
    column, first = 0, None
    for index, char in enumerate(line):
        if first is None and column >= left:
            first = index
        if column >= right:
            return (index if first is None else first), index
        column += advance(char, column, tab)
    return (len(line) if first is None else first), len(line)
