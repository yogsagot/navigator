"""dBase files for File > View > As DataBase: DOS Navigator's ``TDBFile``
(DBWATCH.PAS) and the parts of ``TDBViewer`` (DBVIEW.PAS) that are not drawing.

A ``.dbf`` is a 32-byte header -- the record count at 4, the header's length
at 8 and a record's at 10 -- then a 32-byte descriptor a field, each a name
of up to eleven characters, a type letter, a length and a count of decimals.
A record is a flag byte (``*`` deleted) and its fields side by side.  A file
whose field lengths do not add up to its record length is refused, as
``TDBFile.Init`` refused it.  Records are read when wanted, by ``pread``, so
a file of any size opens at once.

Memo fields name a block in a ``.dbt`` (dBase III: 512-byte blocks, the text
ending at ``^Z``) or an ``.fpt`` (FoxPro: the block size big-endian in its
header, each block a type and a big-endian length), as ``ViewMemo`` looked
for them.  Text is read in code page 437, DN's.
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from navkit.i18n import tr

#: The code page names and values are read in.
CODEC = "cp437"
#: ``TFieldListBox.GetText``'s type names.
TYPES = {"N": "Numeric", "C": "Character", "M": "Memo", "L": "Logical", "D": "Date", "F": "Float",
         "P": "Picture"}
#: Columns a date takes: ``DD-MM-YYYY``, the panels' order.
DATE_WIDTH = 10


class DBFError(ValueError):
    """Not a dBase file ``TDBFile.Init`` would open."""


@dataclass(frozen=True)
class Field:
    """``FieldRec``: a column -- its name, type letter, length, decimals, its
    offset in a record, and how wide it is shown (``Ln``)."""

    name: str
    kind: str
    length: int
    decimals: int
    offset: int

    @property
    def width(self) -> int:
        # A memo is as wide as its block number, 10 (DBWATCH.PAS: max(name, Len)).
        shown = DATE_WIDTH if self.kind == "D" else self.length
        return max(len(self.name), shown)


class DBFile:
    """``TDBFile``: the header and fields of *path*, and its records on demand."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        fd = os.open(self.path, os.O_RDONLY)
        try:
            header = os.pread(fd, 32, 0)
            if len(header) < 32:
                raise DBFError("not a dBase file")
            self.count, self.header_length, self.record_length = struct.unpack_from("<IHH", header, 4)
            fields: list[Field] = []
            offset = 1
            for index in range(self.header_length // 32 - 1):
                raw = os.pread(fd, 32, 32 * (index + 1))
                if len(raw) < 32 or raw[0] == 0x0D:
                    break
                name = raw[:11].split(b"\0", 1)[0].decode(CODEC, "replace").strip()
                if not name:
                    raise DBFError("a field without a name")
                kind, length, decimals = chr(raw[11]), raw[16], raw[17]
                fields.append(Field(name, kind, length, decimals, offset))
                offset += length
            if not fields or offset != self.record_length:
                raise DBFError("not a dBase file")
        finally:
            os.close(fd)
        self.fields = fields
        self._fd: int | None = None
        self._cache: tuple[int, bytes] = (0, b"")

    #: Records read at a time around the one wanted, as DN's ``Buf`` held them.
    CACHE = 256
    #: The kinds *Memo view* (F3) opens on: memo fields alone.  A SQLite
    #: table (``navigator.lib.viewer.sqlite``) answers the same questions.
    memo_kinds = frozenset({"M"})
    #: F4 changes a field in the file.
    editable = True

    def record(self, index: int) -> bytes | None:
        """Record *index*, from 0, or None past either end (``GetRecord``)."""
        if not 0 <= index < self.count:
            return None
        start, block = self._cache
        if not start <= index < start + len(block) // max(1, self.record_length):
            start = max(0, index - self.CACHE // 2)
            if self._fd is None:
                self._fd = os.open(self.path, os.O_RDONLY)
            block = os.pread(self._fd, self.CACHE * self.record_length,
                             self.header_length + start * self.record_length)
            self._cache = (start, block)
        at = (index - start) * self.record_length
        data = block[at:at + self.record_length]
        return data if len(data) == self.record_length else None

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    @staticmethod
    def flag(record: bytes) -> str:
        """The first column: ``*`` for a deleted record."""
        return record[:1].decode(CODEC, "replace")

    @staticmethod
    def raw(record: bytes, field: Field) -> str:
        return record[field.offset:field.offset + field.length].decode(CODEC, "replace")

    def shown(self, record: bytes, field: Field) -> str:
        """What a cell shows (``TDBViewer.Draw``): a memo as ``Memo`` or, empty,
        ``memo``; a date day first; the rest as it is stored."""
        text = self.raw(record, field)
        if field.kind == "M":
            return "  Memo  " if text.strip().isdigit() and int(text) > 0 else "  memo  "
        if field.kind == "D":
            return date_shown(text)
        return text

    def memo(self, record: bytes, field: Field) -> str | None:
        """:meth:`memo_data` read as text, in the table's code page."""
        data = self.memo_data(record, field)
        return None if data is None else data.decode(CODEC, "replace")

    def memo_data(self, record: bytes, field: Field) -> bytes | None:
        """``ViewMemo``: the bytes of the memo *field* of *record* points at,
        from the first of :func:`memo_files` there is; None for none.

        Read as DN read them: a ``.dbt`` the dBase III way, from ``block *
        512`` up to ``0x1A``; any other (``.fpt``, ``.sct``, ``.frt``) the
        FoxPro way -- the block size big-endian at offset 4, and at ``block *
        size`` a type and a big-endian length before the text.  Raises
        ``FileNotFoundError`` (*Could not find MEMO file*) with neither."""
        text = self.raw(record, field).strip()
        if field.kind != "M" or not text.isdigit() or int(text) == 0:
            return None
        block = int(text)
        for memo in memo_files(self.path):
            if not memo.is_file():
                continue
            with open(memo, "rb") as file:
                if memo.suffix.lower() != ".dbt":
                    file.seek(4)
                    size = struct.unpack(">I", file.read(4))[0] or 512
                    file.seek(block * size + 4)
                    length = struct.unpack(">I", file.read(4))[0]
                    return file.read(length)
                file.seek(block * 512)
                data = bytearray()
                while chunk := file.read(512):
                    end = chunk.find(b"\x1a")
                    if end >= 0:
                        data += chunk[:end]
                        break
                    data += chunk
                return bytes(data)
        raise FileNotFoundError(tr("Could not find MEMO file"))

    def write_field(self, index: int, field: Field, text: str) -> None:
        """``StoreField``: *text*, padded to the field, written into record *index*."""
        data = text.encode(CODEC, "replace")[:field.length].ljust(field.length)
        with open(self.path, "r+b") as file:
            file.seek(self.header_length + index * self.record_length + field.offset)
            file.write(data)
        self._cache = (0, b"")


def memo_files(path: Path) -> list[Path]:
    """Where *path*'s memos may be, in the order ``ViewMemo`` tried them.

    ``if (XT[0] = #4) and (XT <> '.DBF') then XT[4] := 'T' else XT :=
    '.FPT'``, then ``.dbt``: a four-character extension other than ``.dbf``
    with its last letter ``T`` (``.scx`` -> ``.sct``, ``.frx`` -> ``.frt``),
    else ``.fpt``.  DN upper-cased the name, which a POSIX name cannot be:
    each is tried in the table's own case first, then the other.
    """
    suffix = path.suffix
    first = suffix[:3] + "t" if len(suffix) == 4 and suffix.lower() != ".dbf" else ".fpt"
    upper = suffix.isupper()
    found: list[Path] = []
    for name in (first, ".dbt"):
        for spelled in ((name.upper(), name.lower()) if upper else (name.lower(), name.upper())):
            candidate = path.with_suffix(spelled)
            if candidate not in found:
                found.append(candidate)
    return found


def date_shown(text: str) -> str:
    """``YYYYMMDD`` as ``DD-MM-YYYY`` (``DateToHuman``); blank stays blank."""
    if len(text) < 8 or not text[:8].isdigit():
        return text.ljust(DATE_WIDTH)[:DATE_WIDTH]
    return f"{text[6:8]}-{text[4:6]}-{text[0:4]}"


def date_stored(text: str) -> str | None:
    """A ``DD-MM-YYYY`` typed back as ``YYYYMMDD``; a two-digit year is this
    century's, as DN read one.  None for something that is not a date."""
    import re
    import time

    numbers = [int(part) for part in re.findall(r"\d+", text)]
    if len(numbers) != 3:
        return None
    day, month, year = numbers
    if year < 100:
        year += time.localtime().tm_year // 100 * 100
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year % 10000:04d}{month:02d}{day:02d}"


def is_number(text: str) -> bool:
    """Whether *text* reads as a number (an empty one is 0, as ``Val`` read it)."""
    try:
        float(text.strip() or "0")
    except ValueError:
        return False
    return True


def number_stored(text: str, field: Field) -> str | None:
    """A number typed into a numeric field, right-aligned to its length with
    its decimals (``Str(R:Len:Dec)``); None for one that is not a number."""
    try:
        value = float(text.strip() or "0")
    except ValueError:
        return None
    shown = f"{value:.{field.decimals}f}"
    return shown.rjust(field.length) if len(shown) <= field.length else None


def find(db: DBFile, text: str, *, case: bool, all_fields: bool, backward: bool,
         record: int, field: int, work: Any = None) -> tuple[int, int] | None:
    """``ContSearch``: the first cell after record *record* holding *text* --
    or before it, *backward* -- in the cursor's field (*field*) or in all of
    them; ``(record, field)``, or None.

    DN started a record's fields from the wrong end, so that only one of
    them was looked at; here every one in the scope is, in order.  Any
    source with ``fields``, ``count``, ``record`` and ``raw`` will do -- a
    SQLite table too.  *work*, given, is told where it is and may stop it.
    """
    wanted = text if case else text.upper()
    fields = range(len(db.fields)) if all_fields else [field]
    step = -1 if backward else 1
    number = record + step
    while 0 <= number < db.count:
        if work is not None and number % 1024 == 0:
            # On a thread (``DBWindow._find``): how far, and whether to stop.
            work.position = number if not backward else db.count - number
            if work.stopped:
                return None
        data = db.record(number)
        if data is not None:
            for index in (reversed(fields) if backward else fields):
                cell = db.raw(data, db.fields[index])
                if wanted in (cell if case else cell.upper()):
                    return number, index
        number += step
    return None
