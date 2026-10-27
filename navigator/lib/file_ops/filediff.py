"""Two files side by side, line against line: File > *Compare files*.

**A departure**: DOS Navigator compared files only to tell whether they were
the same (``CompareFiles`` in ``DISKTOOL.PAS``, behind *Compare directories*'
*Compare contents*) and never showed where they differed.  What is shown here
is Midnight Commander's ``mcdiff``, meld's and WinMerge's: the two files in
two columns, a line that is in one alone faced by an empty filler row in the
other, so that what is the same stays level across.

The model half, with no widget in it, run on a thread (:func:`compare`):

- **Lines are compared without their ``\\r``**, so a file saved on DOS and
  its copy saved here are the same text; one differing in its line endings
  alone says so (:attr:`TextDiff.endings_differ`) instead of every line
  being a difference.
- **A binary file is not split into lines**, nor one larger than
  :data:`TEXT_LIMIT`: either is answered with where the two first differ
  (:class:`DiffersAt`), the byte and the line it is on, as ``cmp`` would.
- **Every drive**: both files are read through their drives
  (:mod:`navigator.lib.drives`), a server's or an archive's as the disk's.
"""

from __future__ import annotations

from array import array
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from navigator.lib.system.job import Job, Stopped

#: Larger than this, on either side, is compared byte by byte, not line by
#: line: the alignment is no faster than quadratic at worst.
TEXT_LIMIT = 16 << 20
#: How much of each file is looked at for a NUL byte, which says binary
#: (git's own test).
HEAD = 8 << 10
#: How much is read at a time.
CHUNK = 1 << 16

#: What a row is: the same on both sides, a line changed into another, a
#: line the left has alone, a line the right has alone.
EQUAL, REPLACE, DELETE, INSERT = range(4)


class DiffJob(Job):
    """A comparison running: bytes read of both files, out of their sum (0
    while the lines are being aligned, which has no measure)."""

    def __init__(self) -> None:
        super().__init__()
        self.position = 0
        self.total = 0
        self.cancellable = True


@dataclass(frozen=True)
class Identical:
    """The two files hold the same bytes."""

    size: int


@dataclass(frozen=True)
class DiffersAt:
    """Where two files not compared by lines first differ: *offset* bytes in,
    on *line* (from 1).  *reason* is ``"binary"`` or ``"large"``."""

    offset: int
    line: int
    left_size: int
    right_size: int
    reason: str


@dataclass
class TextDiff:
    """Two texts aligned: one row for each line shown, on both sides.

    ``left_line[row]`` is the index in :attr:`left` of the line the row
    shows on the left, or -1 where the left has a filler row there; the same
    for the right.  ``kinds[row]`` is :data:`EQUAL`, :data:`REPLACE`,
    :data:`DELETE` or :data:`INSERT`.  Kept as arrays, so a file of a million
    lines is a few megabytes, not a million objects.
    """

    left: list[bytes]
    right: list[bytes]
    left_line: array = field(default_factory=lambda: array("l"))
    right_line: array = field(default_factory=lambda: array("l"))
    kinds: bytearray = field(default_factory=bytearray)
    #: The first row of each run of rows that are not :data:`EQUAL`.
    hunks: tuple[int, ...] = ()
    added: int = 0
    removed: int = 0
    changed: int = 0
    #: Every line is the same, but the bytes are not: ``\\r\\n`` against
    #: ``\\n``, or a last line ended on one side only.
    endings_differ: bool = False

    @property
    def rows(self) -> int:
        return len(self.kinds)

    def line(self, side: str, row: int) -> bytes | None:
        """What *side* (``"left"`` or ``"right"``) shows on *row*; None for a filler row."""
        lines, index = (self.left, self.left_line) if side == "left" else (self.right, self.right_line)
        number = index[row]
        return None if number < 0 else lines[number]

    def hunk_at(self, row: int) -> int:
        """The index of the last difference starting at or above *row*; -1 above the first."""
        return bisect_right(self.hunks, row) - 1

    def hunk_end(self, index: int) -> int:
        """The row after the last of difference *index*."""
        row = self.hunks[index]
        while row < self.rows and self.kinds[row] != EQUAL:
            row += 1
        return row

    def next_hunk(self, row: int) -> int | None:
        """The index of the first difference starting below *row*, or None."""
        index = bisect_right(self.hunks, row)
        return index if index < len(self.hunks) else None

    def previous_hunk(self, row: int) -> int | None:
        """The index of the last difference starting above *row*, or None."""
        index = bisect_right(self.hunks, row - 1) - 1
        return index if index >= 0 else None


def split_lines(data: bytes) -> list[bytes]:
    """*data*'s lines without their ends: ``\\n`` and one ``\\r`` before it."""
    lines = data.split(b"\n")
    if lines and not lines[-1]:
        lines.pop()  # the end of the last line, not a line after it
    return [line[:-1] if line.endswith(b"\r") else line for line in lines]


class _Matcher(SequenceMatcher):
    """``SequenceMatcher`` that a stopped job stops: the search for each
    matching block looks at it first, so *Cancel* is not a wait for a
    quadratic alignment to end."""

    def __init__(self, a: list[bytes], b: list[bytes], job: Any) -> None:
        self.job = job
        super().__init__(None, a, b, autojunk=False)

    def find_longest_match(self, alo: int = 0, ahi: int | None = None, blo: int = 0,
                           bhi: int | None = None) -> Any:
        if self.job is not None and self.job.stopped:
            raise Stopped
        return super().find_longest_match(alo, ahi, blo, bhi)


def align(left_data: bytes, right_data: bytes, job: Any = None) -> TextDiff:
    """The rows two texts are shown in, the same lines level across."""
    left, right = split_lines(left_data), split_lines(right_data)
    diff = TextDiff(left, right)
    opcodes = _opcodes(left, right, job)
    hunks: list[int] = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            _rows(diff, EQUAL, range(i1, i2), range(j1, j2))
            continue
        hunks.append(diff.rows)
        paired = min(i2 - i1, j2 - j1)
        _rows(diff, REPLACE, range(i1, i1 + paired), range(j1, j1 + paired))
        _rows(diff, DELETE, range(i1 + paired, i2), None)
        _rows(diff, INSERT, None, range(j1 + paired, j2))
        diff.changed += paired
        diff.removed += i2 - i1 - paired
        diff.added += j2 - j1 - paired
    diff.hunks = tuple(hunks)
    diff.endings_differ = not hunks and left_data != right_data
    return diff


#: The largest range -- lines on the left times lines on the right -- handed
#: to ``SequenceMatcher`` whole; a larger one is cut at anchors first, and one
#: with no line unique to both sides is shown as one change.  The matcher is quadratic at worst
#: (each of thousands of small blocks found by a scan of the whole range), and
#: a gap of repeated lines alone is where that worst is met.
MATCHER_LIMIT = 1 << 20


def _opcodes(left: list[bytes], right: list[bytes], job: Any) -> list[tuple[str, int, int, int, int]]:
    """``get_opcodes()`` for two lists of lines.

    A range small enough (:data:`MATCHER_LIMIT`) goes to ``SequenceMatcher``,
    whose alignment is the better one.  A larger one is cut by **patience
    diff** first: the lines that occur once on each side are paired, the
    longest run of pairs in order on both sides kept as anchors, and only
    what lies between two anchors handed on, the equal lines around each
    taken with it.  git's ``--patience``: near linear where the matcher
    alone, on a large file with a third of its lines changed, takes minutes.
    A large range with no unique line is one change."""
    blocks: list[tuple[int, int, int]] = []
    pending = [(0, len(left), 0, len(right))]
    while pending:
        if job is not None and job.stopped:
            raise Stopped
        alo, ahi, blo, bhi = pending.pop()
        # The same at the start and the end of the range: taken as it is.
        start = alo
        while alo < ahi and blo < bhi and left[alo] == right[blo]:
            alo += 1
            blo += 1
        if alo > start:
            blocks.append((start, blo - (alo - start), alo - start))
        end = ahi
        while alo < ahi and blo < bhi and left[ahi - 1] == right[bhi - 1]:
            ahi -= 1
            bhi -= 1
        if end > ahi:
            blocks.append((ahi, bhi, end - ahi))
        if alo == ahi or blo == bhi:
            continue
        if (ahi - alo) * (bhi - blo) <= MATCHER_LIMIT:
            matcher = _Matcher(left[alo:ahi], right[blo:bhi], job)
            blocks.extend((a + alo, b + blo, size) for a, b, size in matcher.get_matching_blocks() if size)
            continue
        i, j = alo, blo
        for a, b in _anchors(left, right, alo, ahi, blo, bhi):
            blocks.append((a, b, 1))
            pending.append((i, a, j, b))
            i, j = a + 1, b + 1
        if i > alo:
            pending.append((i, ahi, j, bhi))
    blocks.sort()
    opcodes: list[tuple[str, int, int, int, int]] = []
    i = j = 0
    for a, b, size in [*_merged(blocks), (len(left), len(right), 0)]:
        if i < a and j < b:
            opcodes.append(("replace", i, a, j, b))
        elif i < a:
            opcodes.append(("delete", i, a, j, j))
        elif j < b:
            opcodes.append(("insert", i, i, j, b))
        if size:
            opcodes.append(("equal", a, a + size, b, b + size))
        i, j = a + size, b + size
    return opcodes


def _anchors(left: list[bytes], right: list[bytes], alo: int, ahi: int, blo: int,
             bhi: int) -> list[tuple[int, int]]:
    """The lines unique to both ranges, paired, the longest run of them in
    order on both sides (patience sorting)."""
    counts: dict[bytes, int] = {}
    for line in left[alo:ahi]:
        counts[line] = counts.get(line, 0) + 1
    where: dict[bytes, int] = {}
    seen: dict[bytes, int] = {}
    for j in range(blo, bhi):
        line = right[j]
        if counts.get(line) == 1:
            seen[line] = seen.get(line, 0) + 1
            where[line] = j
    pairs = [(i, where[line]) for i in range(alo, ahi)
             if (line := left[i]) in where and seen[line] == 1]
    tails: list[int] = []
    ends: list[int] = []
    before = [-1] * len(pairs)
    for k, (_, j) in enumerate(pairs):
        at = bisect_left(tails, j)
        if at:
            before[k] = ends[at - 1]
        if at == len(tails):
            tails.append(j)
            ends.append(k)
        else:
            tails[at] = j
            ends[at] = k
    run: list[tuple[int, int]] = []
    k = ends[-1] if ends else -1
    while k >= 0:
        run.append(pairs[k])
        k = before[k]
    run.reverse()
    return run


def _merged(blocks: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Matching blocks, sorted, with each that runs on into the next joined to it."""
    out: list[tuple[int, int, int]] = []
    for a, b, size in blocks:
        if out and out[-1][0] + out[-1][2] == a and out[-1][1] + out[-1][2] == b:
            out[-1] = (out[-1][0], out[-1][1], out[-1][2] + size)
        else:
            out.append((a, b, size))
    return out


def _rows(diff: TextDiff, kind: int, lefts: range | None, rights: range | None) -> None:
    count = len(lefts if lefts is not None else rights)  # type: ignore[arg-type]
    diff.left_line.extend(lefts if lefts is not None else [-1] * count)
    diff.right_line.extend(rights if rights is not None else [-1] * count)
    diff.kinds.extend(bytes([kind]) * count)


def first_difference(a: Any, b: Any, job: Any = None, head_a: bytes = b"",
                     head_b: bytes = b"") -> tuple[int, int] | None:
    """Where the readers *a* and *b* first differ: ``(offset, line)``, the
    line counted from 1; None when they hold the same bytes.  *head_a* and
    *head_b* are what was read of each already.  One that ends first differs
    where it ends."""
    offset, line = 0, 1
    one, two = head_a, head_b
    while True:
        if job is not None:
            job.wait_while_paused()
            if job.stopped:
                raise Stopped
        if not one:
            one = a.read(CHUNK)
        if not two:
            two = b.read(CHUNK)
        count = min(len(one), len(two))
        if not count:
            return (offset, line) if one or two else None
        x, y = one[:count], two[:count]
        if x != y:
            at = _mismatch(x, y)
            return offset + at, line + x.count(b"\n", 0, at)
        offset += count
        line += x.count(b"\n")
        if job is not None:
            job.position = 2 * offset
        one, two = one[count:], two[count:]


def _mismatch(x: bytes, y: bytes) -> int:
    """The first index where the equally long *x* and *y* differ, halving
    the slices compared rather than looking at each byte in Python."""
    low, high = 0, len(x)
    while high - low > 64:
        middle = (low + high) // 2
        if x[low:middle] != y[low:middle]:
            high = middle
        else:
            low = middle
    return next(i for i in range(low, high) if x[i] != y[i])


def compare(left: Path | Any, right: Path | Any, job: Any = None) -> Identical | DiffersAt | TextDiff:
    """Compare the files at *left* and *right*, on any drives.  Raises
    ``OSError`` for one that cannot be read, :class:`Stopped` when *job* is
    stopped."""
    from navigator.lib.drives import Location, drive_of

    left, right = Location.of(left), Location.of(right)
    left_drive, right_drive = drive_of(left), drive_of(right)
    left_size, right_size = left_drive.stat(left).st_size, right_drive.stat(right).st_size
    if job is not None:
        job.total = left_size + right_size
    with left_drive.open_read(left) as a, right_drive.open_read(right) as b:
        head_a, head_b = _read(a, HEAD), _read(b, HEAD)
        reason = ""
        if b"\0" in head_a or b"\0" in head_b:
            reason = "binary"
        elif max(left_size, right_size) > TEXT_LIMIT:
            reason = "large"
        if reason:
            found = first_difference(a, b, job, head_a, head_b)
            if found is None:
                return Identical(left_size)
            return DiffersAt(found[0], found[1], left_size, right_size, reason)
        left_data = head_a + _read_all(a, job)
        right_data = head_b + _read_all(b, job)
    if left_data == right_data:
        return Identical(len(left_data))
    if job is not None:
        job.total = 0
    return align(left_data, right_data, job)


def _read(reader: Any, count: int) -> bytes:
    """Up to *count* bytes, however few a drive hands over at a time."""
    parts = []
    while count > 0:
        data = reader.read(count)
        if not data:
            break
        parts.append(data)
        count -= len(data)
    return b"".join(parts)


def _read_all(reader: Any, job: Any) -> bytes:
    parts = []
    while True:
        if job is not None:
            job.wait_while_paused()
            if job.stopped:
                raise Stopped
        data = reader.read(CHUNK)
        if not data:
            return b"".join(parts)
        parts.append(data)
        if job is not None:
            job.position += len(data)
