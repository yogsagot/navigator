"""The editor's search: DOS Navigator's ``SearchData`` and ``TFileEditor.Search`` (``MICROED.PAS``).

Line by line, as DN searched: a match never spans a line break.  Forward, a
line is searched from a place onwards and the match may start there; backward,
the match has to end at or before the place, which is what lets the cursor
left at a match's start find the one before it.  *Case sensitive* off
compares without case (``UpCaseStr``), and *Whole words only* wants a
``BREAK_CHARS`` character or the line's edge on either side.  The scope
limits each line to the columns of it a block covers; a line outside it is
passed over.

:data:`SEARCH` is the dialog's record, kept from one search to the next as
DN's typed constant was -- ``Options: 4`` (prompt on replace), forward,
global, from the start.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from navigator.editor.document import Pos

#: DN's ``BreakChars`` (``ADVANCE.PAS``): what ends a word for Ctrl+Left,
#: Ctrl+Right, the word deletes and *Whole words only* -- less DOS's
#: end-of-file mark ``^Z``.
BREAK_CHARS = frozenset(", []{}():;.^&*!#$/\\'\"%><-+=|?\r\n\t\x0c")


@dataclass
class SearchData:
    """``TSearchData``: what the Find and Replace dialogs fill in."""

    #: ``Line``: the text to find.
    text: str = ""
    #: ``What``: the text to put in its place, or None for a plain search (``#0``).
    new: str | None = None
    #: ``Options`` bits 1, 2 and 4.
    case: bool = False
    whole: bool = False
    prompt: bool = True
    #: ``Dir``: 0 forward, 1 backward.
    backward: bool = False
    #: ``Scope``: 0 global, 1 selected text.
    selected: bool = False
    #: ``Origin``: 0 entire scope, 1 from cursor.
    from_cursor: bool = False


#: The search the dialogs last set up, which F7 shows and Shift+F7 repeats.
SEARCH = SearchData()


def _whole(line: str, start: int, end: int) -> bool:
    return (start == 0 or line[start - 1] in BREAK_CHARS) and (
        end >= len(line) or line[end] in BREAK_CHARS
    )


def find_in_line(
    line: str, text: str, start: int, stop: int, *, case: bool, whole: bool, backward: bool,
) -> tuple[int, int] | None:
    """The first match of *text* lying within ``line[start:stop]``, or the last if
    *backward*: its start and end, or None."""
    if not text or stop - start < len(text):
        return None
    pattern = re.compile(re.escape(text), 0 if case else re.IGNORECASE)
    found = None
    at = start
    while True:
        match = pattern.search(line, at, stop)
        if match is None:
            return found
        if not whole or _whole(line, match.start(), match.end()):
            if not backward:
                return match.start(), match.end()
            found = match.start(), match.end()
        at = match.start() + 1


def find(
    lines: list[str],
    at: Pos,
    data: SearchData,
    *,
    backward: bool,
    bounds: Callable[[int], tuple[int, int] | None] | None = None,
) -> tuple[Pos, Pos] | None:
    """The next match of *data* from *at*, forward or *backward*: where it starts and ends.

    *bounds* gives the part of a line the scope covers, as string indices,
    or None for a line outside it; without it every line is searched whole.
    """
    count = len(lines)

    def part(number: int) -> tuple[int, int] | None:
        if bounds is None:
            return 0, len(lines[number])
        return bounds(number)

    options = dict(case=data.case, whole=data.whole, backward=backward)
    if not backward:
        line, start = at.line, at.index
        while 0 <= line < count:
            span = part(line)
            if span is not None:
                lo, hi = max(start, span[0]), span[1]
                found = find_in_line(lines[line], data.text, lo, hi, **options)
                if found is not None:
                    return Pos(line, found[0]), Pos(line, found[1])
            line, start = line + 1, 0
        return None
    line, stop = at.line, at.index
    while 0 <= line < count:
        span = part(line)
        if span is not None:
            lo, hi = span[0], min(stop, span[1])
            found = find_in_line(lines[line], data.text, lo, hi, **options)
            if found is not None:
                return Pos(line, found[0]), Pos(line, found[1])
        line -= 1
        if line >= 0:
            stop = len(lines[line])
    return None
