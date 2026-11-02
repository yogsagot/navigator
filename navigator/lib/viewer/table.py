"""CSV and TSV files for the spreadsheet window: what DOS Navigator's
``TCalcView`` (CALC.PAS) showed, read from a delimited text file instead of
DN's own ``.WKZ`` -- no widget in it.

**A file of any size opens at once.**  A thread walks it once and notes where
each record starts (:class:`TableSource` ``starts``), quote-aware, so a quoted
field may hold the delimiter and line breaks; a record is read when shown, by
``pread`` between two starts, and parsed by :mod:`csv` alone.  The loop sees
the walk's progress through plain fields -- ``complete``, ``position`` and a
stop flag -- as :class:`navigator.lib.viewer.SearchJob` does, never anything
reactive.

**View-only**: nothing here writes.  Sorting orders the rows shown
(:func:`sort_order`), never the file.

Cells are named as DN named them: columns ``A``..``Z``, ``AA``.., rows from 1.
"""

from __future__ import annotations

import csv
import io
import math
import os
import re
import threading
from array import array
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: How much a walk reads at once.
BLOCK = 1 << 20
#: How much the guess looks at.
SAMPLE = 64 * 1024
#: Rows the widths are measured over.
MEASURED = 200
#: The narrowest and widest a column opens at (DN's ``CellWidth`` started at 9).
MIN_WIDTH, MAX_WIDTH = 3, 40
#: Rows kept parsed.
CACHED_ROWS = 2048
#: The delimiters guessed among, and offered by *Format*.
DELIMITERS = (",", ";", "\t", "|")
#: What a file that is not UTF-8 is read in, unless *Format* says otherwise.
FALLBACK_ENCODING = "cp1252"


@dataclass(frozen=True)
class Dialect:
    """How a file is cut into cells: its delimiter and quote, whether its
    first record names the columns, and the encoding it is read in."""

    delimiter: str = ","
    quotechar: str = '"'
    header: bool = True
    encoding: str = "utf-8"


def guess(sample: bytes, name: str = "") -> Dialect:
    """The dialect *sample* -- a file's start -- looks written in.

    A ``.tsv``/``.tab`` name says tab; otherwise :class:`csv.Sniffer` picks
    among :data:`DELIMITERS`, and says whether the first row is a header;
    failing that, a comma and a header.  A UTF-8 byte order mark reads as
    ``utf-8-sig``; bytes that are not UTF-8 as :data:`FALLBACK_ENCODING`.
    """
    if sample.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    else:
        try:
            # A sample may end inside a character: drop up to three bytes.
            sample[: len(sample) - 3 if len(sample) >= SAMPLE else None].decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            encoding = FALLBACK_ENCODING
    text = sample.decode(encoding, errors="replace")
    # The sniffer wants whole lines: the last one may be cut.
    if len(sample) >= SAMPLE and "\n" in text:
        text = text[: text.rindex("\n") + 1]
    lowered = name.lower()
    sniffer = csv.Sniffer()
    if lowered.endswith((".tsv", ".tab")):
        delimiter = "\t"
    else:
        try:
            delimiter = sniffer.sniff(text, delimiters="".join(DELIMITERS)).delimiter
        except csv.Error:
            delimiter = ","
    try:
        header = sniffer.has_header(text) if text.strip() else True
    except csv.Error:
        header = True
    return Dialect(delimiter=delimiter, header=header, encoding=encoding)


def is_table(name: str) -> bool:
    """Whether F3 shows *name* as a spreadsheet: ``[viewer] table_masks``,
    with ``render_tables`` on."""
    import fnmatch

    from navigator.settings import SETTINGS

    settings = SETTINGS.viewer
    name = name.lower()
    return settings.render_tables and any(
        fnmatch.fnmatchcase(name, mask.strip().lower()) for mask in settings.table_masks.split(";") if mask.strip())


def cell_name(column: int, row: int) -> str:
    """DN's ``GetCellName``: column 0, row 0 is ``A1``; column 26 is ``AA``."""
    return column_name(column) + str(row + 1)


def column_name(column: int) -> str:
    """``A``..``Z``, ``AA``..``AZ``, ``BA``..: spreadsheet letters for *column* from 0."""
    name = ""
    column += 1
    while column:
        column, rest = divmod(column - 1, 26)
        name = chr(ord("A") + rest) + name
    return name


_CELL = re.compile(r"\s*([A-Za-z]*)\s*(\d*)\s*$")


def parse_cell(text: str) -> tuple[int | None, int | None] | None:
    """What *Go to Cell Number* was given: ``B12`` is column 1, row 11;
    ``12`` a row alone, ``B`` a column alone (None for the other).  None for
    anything else."""
    match = _CELL.match(text)
    if match is None or not (match.group(1) or match.group(2)):
        return None
    letters, digits = match.group(1).upper(), match.group(2)
    column = None
    if letters:
        column = 0
        for letter in letters:
            column = column * 26 + ord(letter) - ord("A") + 1
        column -= 1
    row = int(digits) - 1 if digits else None
    if row is not None and row < 0:
        return None
    return column, row


def number(text: str) -> float | None:
    """*text* as a number, if it is one -- what *Search as Value* and a
    numeric sort compare: ``12``, ``-3.5``, ``1e3``, ``1,234,567.8``; a blank,
    ``nan`` or ``inf`` is not one."""
    text = text.strip()
    if not text:
        return None
    if _GROUPED.fullmatch(text):
        text = text.replace(",", "")
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


_GROUPED = re.compile(r"[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?")


class TableSource:
    """A delimited file, its records found by a thread and read when shown.

    ``records`` counts every record found so far, the header among them;
    ``count`` the rows shown under it.  :meth:`index` walks the file -- on a
    thread, which :meth:`start` gives it -- and is done when ``complete``.
    """

    def __init__(self, path: Path | str, dialect: Dialect | None = None) -> None:
        self.path = Path(path)
        fd = os.open(self.path, os.O_RDONLY)
        try:
            self.size = os.fstat(fd).st_size
            sample = os.pread(fd, SAMPLE, 0)
        finally:
            os.close(fd)
        self.dialect = dialect or guess(sample, self.path.name)
        #: Where each record starts; the end of one is the next one's start.
        self.starts = array("Q", [3 if sample.startswith(b"\xef\xbb\xbf") else 0])
        #: The offset the walk has got to, and whether it has reached the end.
        self.position = 0
        self.complete = self.size == 0
        if self.complete:
            self.starts = array("Q")
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._fd: int | None = None
        self._rows: OrderedDict[int, list[str]] = OrderedDict()
        self._lock = threading.Lock()
        #: How many columns the widest row measured has, and their widths.
        self.columns = 0
        self.widths: list[int] = []

    # -- the walk ------------------------------------------------------------------

    def start(self) -> None:
        """Walk the file on a thread of its own."""
        if self._thread is None and not self.complete:
            self._thread = threading.Thread(target=self.index, name="nav-table-index", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def index(self) -> None:
        """Find every record's start: a quote opens and closes a field, and a
        line break outside one ends the record -- ``\\r\\n``, ``\\n`` or ``\\r``.
        A doubled quote inside a field turns it off and on again, which is
        all a record's bounds need to know of it."""
        quote = self.dialect.quotechar.encode("latin-1", "replace")[:1] or b'"'
        hits = re.compile(re.escape(quote) + rb"|\r\n?|\n")
        quoted = False
        offset = self.starts[0] if len(self.starts) else 0
        carry = b""
        try:
            with open(self.path, "rb") as file:
                file.seek(offset)
                while not self._stop.is_set():
                    block = file.read(BLOCK)
                    if not block:
                        break
                    data = carry + block
                    base = offset - len(carry)
                    # A \r at the very end may be the first half of \r\n.
                    end = len(data) - 1 if data.endswith(b"\r") else len(data)
                    for match in hits.finditer(data, 0, end):
                        if match.group() == quote:
                            quoted = not quoted
                        elif not quoted:
                            nxt = base + match.end()
                            if nxt < self.size:
                                self.starts.append(nxt)
                    carry = data[end:]
                    offset += len(block)
                    self.position = offset
        except OSError:
            pass
        finally:
            if not self._stop.is_set():
                self.position = self.size
                self.complete = True

    def wait(self) -> None:
        """Until the walk is over: for a thread that needs every record."""
        if self._thread is not None:
            self._thread.join()
        elif not self.complete:
            self.index()

    # -- counting --------------------------------------------------------------------

    @property
    def records(self) -> int:
        """Records whose end is known: all of them once the walk is over."""
        found = len(self.starts)
        return found if self.complete else max(0, found - 1)

    @property
    def count(self) -> int:
        """Rows under the titles."""
        return max(0, self.records - (1 if self.dialect.header else 0))

    @property
    def percent(self) -> int:
        return 100 if self.complete or not self.size else min(99, self.position * 100 // self.size)

    # -- reading -----------------------------------------------------------------------

    def _span(self, record: int) -> tuple[int, int] | None:
        starts = self.starts
        if not 0 <= record < self.records:
            return None
        end = starts[record + 1] if record + 1 < len(starts) else self.size
        return starts[record], end

    def record(self, index: int) -> list[str] | None:
        """Record *index*, from 0, as its cells; None if not found (yet)."""
        with self._lock:
            row = self._rows.get(index)
            if row is not None:
                self._rows.move_to_end(index)
                return row
        span = self._span(index)
        if span is None:
            return None
        start, end = span
        if self._fd is None:
            self._fd = os.open(self.path, os.O_RDONLY)
        data = os.pread(self._fd, end - start, start)
        row = self.parse(data)
        with self._lock:
            self._rows[index] = row
            if len(self._rows) > CACHED_ROWS:
                self._rows.popitem(last=False)
        return row

    def parse(self, data: bytes) -> list[str]:
        """One record's bytes as its cells."""
        dialect = self.dialect
        text = data.decode(dialect.encoding.replace("-sig", ""), errors="replace")
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=dialect.delimiter,
                            quotechar=dialect.quotechar, strict=False)
        try:
            return next(reader)
        except StopIteration:
            return []
        except csv.Error:
            return [text.rstrip("\r\n")]

    def titles(self) -> list[str] | None:
        """The header's cells, if the first record is one."""
        return self.record(0) if self.dialect.header else None

    def row(self, index: int) -> list[str] | None:
        """Row *index* under the titles, as its cells."""
        return self.record(index + (1 if self.dialect.header else 0))

    def row_offset(self, index: int) -> int:
        """Where row *index* starts in the file: what the text view opens at."""
        record = index + (1 if self.dialect.header else 0)
        return self.starts[record] if 0 <= record < len(self.starts) else 0

    def row_at(self, offset: int) -> int:
        """The row holding byte *offset*: what the table opens at from the text."""
        import bisect

        record = max(0, bisect.bisect_right(self.starts, offset) - 1)
        return max(0, record - (1 if self.dialect.header else 0))

    def measure(self) -> None:
        """``columns`` and ``widths`` from the titles and the first rows found."""
        rows = [self.record(index) for index in range(min(self.records, MEASURED + 1))]
        rows = [row for row in rows if row is not None]
        from navkit.bidi import display_width

        columns = max((len(row) for row in rows), default=0)
        widths = [MIN_WIDTH] * columns
        for row in rows:
            for column, cell in enumerate(row):
                widths[column] = max(widths[column], min(MAX_WIDTH, display_width(cell)))
        self.columns, self.widths = columns, widths

    def with_dialect(self, dialect: Dialect) -> TableSource:
        """The same file read another way (*Format*): a new source, walked anew."""
        self.close()
        return TableSource(self.path, dialect)

    def close(self) -> None:
        self._stop.set()
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None


# -- thread work ----------------------------------------------------------------------


class Work:
    """A sort or a search running on a thread: ``position`` of ``total``
    the thread writes, ``stopped`` the loop sets -- as ``SearchJob``."""

    #: What a progress box offers: a sort or a search stops at any row.
    cancellable = True

    def __init__(self, total: int = 0) -> None:
        self.position = 0
        self.total = total
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()


def sort_order(source: TableSource, column: int, descending: bool, work: Work | None = None) -> array | None:
    """The rows in the order of *column*'s cells -- as numbers when every
    one that is not blank is one, else as text, case aside -- a stable sort,
    blanks last either way.  None if stopped."""
    source.wait()
    work = work or Work()
    count = source.count
    work.total = count
    cells: list[str] = []
    for index in range(count):
        if index % 4096 == 0:
            work.position = index
            if work.stopped:
                return None
        row = source.row(index)
        cells.append(row[column] if row is not None and column < len(row) else "")
    values = [number(cell) for cell in cells]
    numeric = all(value is not None for value, cell in zip(values, cells) if cell.strip()) \
        and any(value is not None for value in values)
    blank = [not cell.strip() for cell in cells]
    if numeric:
        keys: list[Any] = [value if value is not None else 0.0 for value in values]
    else:
        keys = [cell.casefold() for cell in cells]
    order = sorted(range(count), key=keys.__getitem__, reverse=descending)
    # Blanks last, in file order, whichever way.
    order = [index for index in order if not blank[index]] + [index for index in range(count) if blank[index]]
    return array("Q", order)


@dataclass(frozen=True)
class CellSearch:
    """DN's ``SearchData`` (``dlgFindCell``): the pattern, *Search as*
    string or value, *Case sensitive* and *Whole words only*."""

    text: str
    as_value: bool = False
    case: bool = False
    whole: bool = False

    def matches(self, cell: str) -> bool:
        if self.as_value:
            wanted, value = number(self.text), number(cell)
            return wanted is not None and value is not None and wanted == value
        text, cell = (self.text, cell) if self.case else (self.text.casefold(), cell.casefold())
        if not self.whole:
            return text in cell
        return re.search(r"(?<!\w)" + re.escape(text) + r"(?!\w)", cell) is not None


def find(source: TableSource, search: CellSearch, *, order: array | None, row: int, column: int,
         backward: bool = False, work: Work | None = None) -> tuple[int, int] | None:
    """``SearchCell``: the next cell after (*row*, *column*) -- or before it,
    *backward* -- that *search* matches, row by row in the order shown;
    ``(row, column)`` in that order, or None.  *row* -1 starts at the top."""
    work = work or Work()
    step = -1 if backward else 1
    shown = row
    first = True
    while True:
        if shown < 0 and not first:
            return None
        if shown >= 0:
            if shown >= source.count:
                if source.complete:
                    return None
                source.wait()
                if shown >= source.count:
                    return None
            if shown % 1024 == 0:
                work.position = shown
                if work.stopped:
                    return None
            index = order[shown] if order is not None and shown < len(order) else shown
            cells = source.row(index) or []
            columns = range(len(cells))
            if first:
                columns = range(column + 1, len(cells)) if not backward else range(min(column, len(cells)) - 1, -1, -1)
            elif backward:
                columns = range(len(cells) - 1, -1, -1)
            for at in columns:
                if search.matches(cells[at]):
                    return shown, at
        first = False
        shown += step


__all__ = [
    "CellSearch",
    "Dialect",
    "TableSource",
    "Work",
    "cell_name",
    "column_name",
    "find",
    "guess",
    "is_table",
    "number",
    "parse_cell",
    "sort_order",
]
