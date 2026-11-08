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

*Regular expression* is the Find bar's (a departure: DN's search was for a
string alone): the text is a Python pattern, and the new text may name its
groups (``\\1``, ``\\g<name>``).  A match of nothing is never one.
:func:`all_matches` is what the bar counts, on a thread.

A pattern is matched within one line, as DN's string was, unless it says it
reaches across: a ``\\n`` or ``\\r`` in it, or the ``s`` flag (:func:`crosses`).
Then the text is searched whole, its lines joined by ``"\\n"`` whatever their
endings, with ``re.MULTILINE`` so ``^`` and ``$`` still mean a line's ends;
``\\s+`` or ``[^x]*`` alone never start crossing, so a search that found
something before finds the same.  In what a regular expression puts in, a
line break is the text's own ending (:func:`replacement`).
"""

from __future__ import annotations

import bisect
import functools
import re
from dataclasses import dataclass
from typing import Callable, Iterator

from navigator.lib.editor.document import Pos

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
    #: The Find bar's *Regular expression*: *text* is a pattern (a departure).
    regex: bool = False


#: The search the dialogs last set up, which F7 shows and Shift+F7 repeats.
SEARCH = SearchData()


def _whole(line: str, start: int, end: int) -> bool:
    return (start == 0 or line[start - 1] in BREAK_CHARS) and (
        end >= len(line) or line[end] in BREAK_CHARS
    )


#: What makes a pattern reach across lines: a ``\n`` or ``\r`` -- escaped, or a
#: real one pasted in -- or the inline ``s`` flag.
_CROSSING = re.compile(r"\\n|\n|\\r|\r|\(\?[a-zA-Z]*s[a-zA-Z]*[:)]")


def crosses(data: SearchData) -> bool:
    """Whether *data* is a regular expression that may match across lines."""
    return data.regex and bool(_CROSSING.search(data.text))


def _joined(lines: list[str]) -> tuple[str, list[int]]:
    """The lines as one text, each break a ``"\n"``, and where each line starts in it."""
    starts, at = [], 0
    for line in lines:
        starts.append(at)
        at += len(line) + 1
    return "\n".join(lines), starts


def _pos(starts: list[int], offset: int) -> Pos:
    line = bisect.bisect_right(starts, offset) - 1
    return Pos(line, offset - starts[line])


def _crossing_pattern(data: SearchData) -> re.Pattern[str]:
    flags = re.MULTILINE | (0 if data.case else re.IGNORECASE)
    return re.compile(data.text, flags)


@functools.lru_cache(maxsize=64)
def pattern_of(text: str, case: bool, regex: bool) -> re.Pattern[str]:
    """The compiled pattern *text* stands for; :class:`re.error` for a bad one."""
    return re.compile(text if regex else re.escape(text), 0 if case else re.IGNORECASE)


def valid(data: SearchData) -> bool:
    """Whether *data*'s text is something to search for: a pattern that compiles."""
    if not data.text:
        return False
    try:
        pattern_of(data.text, data.case, data.regex)
    except re.error:
        return False
    return True


def _matches(
    line: str, pattern: re.Pattern[str], start: int, stop: int, whole: bool,
) -> Iterator[tuple[int, int]]:
    """Every match within ``line[start:stop]``, a step past each one's start, as
    DN's search went on -- so they may overlap; empty ones left out."""
    at = start
    while at <= stop:
        match = pattern.search(line, at, stop)
        if match is None:
            return
        begin, end = match.span()
        if end > begin and (not whole or _whole(line, begin, end)):
            yield begin, end
        at = begin + 1


def find_in_line(
    line: str, text: str, start: int, stop: int, *, case: bool, whole: bool, backward: bool,
    regex: bool = False,
) -> tuple[int, int] | None:
    """The first match of *text* lying within ``line[start:stop]``, or the last if
    *backward*: its start and end, or None.  A bad pattern matches nothing."""
    if not text or (not regex and stop - start < len(text)):
        return None
    try:
        pattern = pattern_of(text, case, regex)
    except re.error:
        return None
    found = None
    for found in _matches(line, pattern, start, stop, whole):
        if not backward:
            return found
    return found


def replacement(lines: list[str], found: tuple[Pos, Pos], data: SearchData, newline: str = "\n") -> str:
    """What *found* is replaced by: *data*'s new text, its groups filled in under
    *Regular expression* from the match found there -- every line break in it,
    the new text's own ``\\n`` or one a group took, the text's *newline*."""
    new = data.new or ""
    if not data.regex:
        return new
    start, end = found
    try:
        if crosses(data):
            text, starts = _joined(lines)
            match = _crossing_pattern(data).match(text, starts[start.line] + start.index,
                                                  starts[end.line] + end.index)
        else:
            match = pattern_of(data.text, data.case, True).match(lines[start.line], start.index, end.index)
        out = match.expand(new) if match is not None else new
    except (re.error, IndexError):
        return new
    return out.replace("\r\n", "\n").replace("\n", newline) if newline != "\n" else out


#: How many matches the Find bar counts before it says "more".
MATCH_LIMIT = 10_000


def _line_matches(line: str, pattern: re.Pattern[str], whole: bool) -> Iterator[tuple[int, int]]:
    """A line's matches, each searched for from the end of the one before."""
    at = 0
    while at <= len(line):
        hit = next(_matches(line, pattern, at, len(line), whole), None)
        if hit is None:
            return
        yield hit
        at = hit[1]


def all_matches(
    lines: list[str], data: SearchData, *, limit: int = MATCH_LIMIT,
) -> list[tuple[int, int, int, int]]:
    """Every match of *data* in the text, ``(line, start, end_line, end)`` in
    order -- *end_line* the line, but for one that reaches across; at most
    *limit*.  For a thread: it reads *lines* and nothing reactive."""
    if not valid(data):
        return []
    found: list[tuple[int, int, int, int]] = []
    if crosses(data):
        text, starts = _joined(lines)
        for begin, end in _line_matches(text, _crossing_pattern(data), data.whole):
            first, last = _pos(starts, begin), _pos(starts, end)
            found.append((first.line, first.index, last.line, last.index))
            if len(found) >= limit:
                return found
        return found
    pattern = pattern_of(data.text, data.case, data.regex)
    for number, line in enumerate(lines):
        for start, end in _line_matches(line, pattern, data.whole):
            found.append((number, start, number, end))
            if len(found) >= limit:
                return found
    return found


def line_matches(line: str, data: SearchData) -> list[tuple[int, int]]:
    """The matches :func:`all_matches` gives in one *line*: what the editor lights
    -- a pattern that does not :func:`cross` lines."""
    if not valid(data):
        return []
    return list(_line_matches(line, pattern_of(data.text, data.case, data.regex), data.whole))


#: The lines :func:`window_matches` reads past each end of the ones shown.
WINDOW_MARGIN = 64


def window_matches(
    lines: list[str], first: int, last: int, data: SearchData, margin: int = WINDOW_MARGIN,
) -> dict[int, list[tuple[int, int]]]:
    """For a pattern that :func:`crosses` lines: what to light on lines *first*
    to *last*, each line's part of every match, a match going on past a
    line's end lighting the break's cell (``len(line)`` to one past it).
    Searched in those lines and *margin* more each side, never the whole text;
    a match reaching outside them is not lit."""
    if not valid(data) or not lines:
        return {}
    low, high = max(0, first - margin), min(len(lines), last + margin + 1)
    text, starts = _joined(lines[low:high])
    lit: dict[int, list[tuple[int, int]]] = {}
    for begin, end in _line_matches(text, _crossing_pattern(data), data.whole):
        a, b = _pos(starts, begin), _pos(starts, end)
        for number in range(max(a.line + low, first), min(b.line + low, last) + 1):
            line = lines[number]
            start = a.index if number == a.line + low else 0
            stop = b.index if number == b.line + low else len(line) + 1
            if stop > start:
                lit.setdefault(number, []).append((start, stop))
        if b.line + low > last:
            break
    return lit


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
    if crosses(data):
        return _find_joined(lines, at, data, backward=backward, bounds=bounds)

    def part(number: int) -> tuple[int, int] | None:
        if bounds is None:
            return 0, len(lines[number])
        return bounds(number)

    options = dict(case=data.case, whole=data.whole, backward=backward, regex=data.regex)
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


def _find_joined(
    lines: list[str], at: Pos, data: SearchData, *, backward: bool,
    bounds: Callable[[int], tuple[int, int] | None] | None,
) -> tuple[Pos, Pos] | None:
    """:func:`find` for a pattern that :func:`crosses` lines: the text searched
    whole, forward from *at* or backward to it.  With *bounds*, the match lies
    wholly within the scope's first line's part to its last's."""
    try:
        pattern = _crossing_pattern(data)
    except re.error:
        return None
    text, starts = _joined(lines)
    low, high = 0, len(text)
    if bounds is not None:
        covered = [(number, bounds(number)) for number in range(len(lines))]
        covered = [(number, span) for number, span in covered if span is not None]
        if not covered:
            return None
        low = starts[covered[0][0]] + covered[0][1][0]
        high = starts[covered[-1][0]] + covered[-1][1][1]
    place = starts[min(at.line, len(starts) - 1)] + at.index
    found = None
    if not backward:
        found = next(_matches(text, pattern, max(low, place), high, data.whole), None)
    else:
        for found in _matches(text, pattern, low, min(high, place), data.whole):
            pass
    if found is None:
        return None
    return _pos(starts, found[0]), _pos(starts, found[1])

