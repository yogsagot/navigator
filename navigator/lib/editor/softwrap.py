"""Soft wrap: a line's cells cut into the rows they are shown on.

Not DOS Navigator's, whose *Auto wrap* (``SplitString`` at ``RightSide``)
put real breaks in the text, and whose viewer's *Wrap* was the viewer's own.
Here the text never changes: a line is shown on as many rows as its cells
need, and every place in the text -- the cursor, a block, a marker -- stays
a line and a column of it.  What maps between the two lives here, pure, so
the rules are tested without a widget:

- A row ends at the last blank that fits, the blank staying on the row it
  ends; a word longer than a row is cut where the row ends.
- A wide character is never split: a row that would end on its first half
  ends a cell short.
- A line whose last row is full gets one more, empty: the caret at its end
  needs a cell, as the unwrapped editor's has one past the text.
- An empty line is one row.

The cells are :func:`navigator.lib.editor.columns.cells`' -- one per column,
a tab already the blanks it covers from the line's start, a wide character's
second cell ``("", index)`` -- so a row is a range of columns of the line.
"""

from __future__ import annotations

from typing import Sequence

#: A row: the line's columns from *start* to *stop*, stop exclusive.
Row = tuple[int, int]


def rows(cells: Sequence[tuple[str, int]], width: int) -> list[Row]:
    """The rows *cells* -- one line's -- are shown on, *width* columns each."""
    width = max(1, width)
    count = len(cells)
    if count == 0:
        return [(0, 0)]
    found: list[Row] = []
    start = 0
    while count - start > width:
        stop = start + width
        # A wide character's second half would begin the next row: end before its first.
        if cells[stop][0] == "" and stop - 1 > start:
            stop -= 1
        # The last blank that fits ends the row, the blank on it.
        cut = stop
        while cut > start and cells[cut - 1][0] != " ":
            cut -= 1
        if cut > start:
            stop = cut
        found.append((start, stop))
        start = stop
    found.append((start, count))
    if count - start == width:
        # A full last row: the caret at the line's end goes on a row of its own.
        found.append((count, count))
    return found


def locate(line_rows: Sequence[Row], column: int) -> tuple[int, int]:
    """Which row *column* of the line is shown on, and how far along it.

    A column where one row ends and the next begins is the next one's first; a
    column at or past the line's end is on its last row.
    """
    for number, (start, stop) in enumerate(line_rows):
        if column < stop or number == len(line_rows) - 1:
            return number, max(0, column - start)
    return 0, column


def column_at(line_rows: Sequence[Row], row: int, x: int, line_end: bool = True) -> int:
    """The line's column shown at *x* on *row*: held to the row's last cell, or
    -- on the line's last row, with *line_end* -- to the line's end past it."""
    row = max(0, min(row, len(line_rows) - 1))
    start, stop = line_rows[row]
    last = row == len(line_rows) - 1
    if last and line_end:
        return start + max(0, x)
    if stop == start:
        return start
    return start + max(0, min(x, stop - start - 1))
