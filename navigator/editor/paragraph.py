"""Paragraph formatting: DOS Navigator's ``FormatBlock`` (``EDITOR.PAS``).

The lines of a block are one paragraph: their words, gathered with every run
of blanks between them made one (``DelDoubles``), are laid out afresh between
the margins.  A line takes another word while ``length + word + blank`` stays
*under* the room it has -- ``right - left``, or ``right - indent`` for a
justified paragraph's first line -- and is then placed:

* ``left``: at the left margin;
* ``right``: so that it ends against the right margin (``RightSide - Length``),
  at the left margin if it does not fit;
* ``center``: midway in the room, from the left margin;
* ``justify``: widened to the full room by one blank at a time, gap by gap
  from the left and round again, then put at the left margin -- the first line
  at the paragraph indent -- except the last line, which is left as it is.

A blank line in the block is no break: DN reflowed the whole block, so a block
is one paragraph.  Words are what blanks separate; a tab is part of a word.
"""

from __future__ import annotations

MODES = ("justify", "right", "left", "center")


def words(lines: list[str]) -> list[str]:
    """Every word of *lines*, in order."""
    return [word for line in lines for word in line.split(" ") if word]


def _justify(line: str, room: int) -> str:
    """``WriteLeft``'s justify: blanks added gap by gap, from the left and round again."""
    parts = line.split(" ")
    if len(parts) < 2:
        return line
    gaps = [1] * (len(parts) - 1)
    width = len(line)
    at = 0
    while width < room:
        gaps[at] += 1
        width += 1
        at = (at + 1) % len(gaps)
    return "".join(part + " " * gap for part, gap in zip(parts, gaps + [0]))


def format_lines(
    lines: list[str], mode: str, *, left: int, right: int, indent: int,
) -> list[str]:
    """The paragraph in *lines*, laid out as *mode* says between the margins."""
    found = words(lines)
    if not found:
        return []
    out: list[str] = []
    room = (right - indent) if mode == "justify" else (right - left)
    current = ""
    pending: list[tuple[str, int]] = []
    for word in found:
        joiner = 1 if current else 0
        if len(current) + len(word) + joiner < room:
            current = f"{current} {word}" if current else word
            continue
        if current:
            pending.append((current, room))
        current = word
        room = right - left
    pending.append((current, room))
    for number, (line, room) in enumerate(pending):
        last = number == len(pending) - 1
        if mode == "right":
            gap = right - len(line)
            out.append(" " * (gap if gap > 0 else left) + line)
        elif mode == "left":
            out.append(" " * left + line)
        elif mode == "center":
            out.append(" " * (left + max(0, (room - len(line)) // 2)) + line)
        else:
            text = line if last else _justify(line, room)
            out.append(" " * (indent if number == 0 else left) + text)
    return out


def fix_margins(left: int, right: int, indent: int) -> tuple[int, int, int]:
    """``SetFormat``'s corrections: a left margin past the right, or below 0, is 0;
    a right margin under 2 is 2; an indent at or past the right margin, or below 0,
    is the left margin."""
    if left > right or left < 0:
        left = 0
    if right < 2:
        right = 2
    if indent >= right or indent < 0:
        indent = left
    return left, right, indent


#: What ``SplitString`` may break a line after, besides a blank.
WRAP_BREAKS = frozenset(" ,:.?!+;")


def wrap_line(
    text: str, cursor: int, *, left: int, right: int, justify: bool,
) -> tuple[str, str, tuple[int, int]] | None:
    """``SplitString``: *text* split where typing has pushed it past the right margin.

    Trailing blanks go first; a line no longer past the margin is not split
    (None).  Otherwise the line is cut after the last blank or ``,:.?!+;`` at
    or before the margin, the part after it -- its leading blanks dropped --
    put on a new line under the left margin; with *justify* the part that
    stays is widened to the margin as ``AutoJustify`` widened it.  Answers
    the two lines and where the cursor, a string index *cursor* in *text*,
    ends up: ``(0, index)`` on the first, ``(1, index)`` on the new one.

    A departure: a line with no break before the margin is cut at the margin,
    where DN's search for a break stopped at the first character and kept it.
    """
    stripped = text.rstrip(" ")
    if len(stripped) <= right:
        return None
    cut = right
    while cut > 0 and stripped[cut - 1] not in WRAP_BREAKS:
        cut -= 1
    if cut == 0 or not stripped[:cut].strip(" "):
        cut = right
    head = stripped[:cut].rstrip(" ")
    rest = stripped[cut:]
    tail = rest.lstrip(" ")
    tail_start = cut + (len(rest) - len(tail))
    if justify:
        head = _justify_to(head, right)
    new = " " * left + tail
    if cursor >= tail_start:
        return head, new, (1, left + min(cursor, len(stripped)) - tail_start)
    if cursor > len(head):
        return head, new, (1, left)
    return head, new, (0, cursor)


def _justify_to(line: str, width: int) -> str:
    """``AutoJustify``: blanks added after each word in turn, from the first, until
    *line* reaches *width*; a line of one word, or leading blanks only, stays."""
    indent = len(line) - len(line.lstrip(" "))
    body = line[indent:]
    if " " not in body:
        return line
    return " " * indent + _justify(body, width - indent)
