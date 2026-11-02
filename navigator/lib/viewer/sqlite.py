"""SQLite files for File > View > As DataBase: the dBase viewer's window
(``TDBWindow``/``TDBViewer``, DBVIEW.PAS) on today's single-file database -- a
departure, DN read dBase alone.  No widget in it.

**Read-only, always.**  The file is opened ``mode=ro`` (``immutable=1`` where
even that cannot be done) with ``PRAGMA query_only``; a query typed in the
window runs under an authorizer that allows reading and nothing else, so
neither it nor an ``ATTACH`` can write anywhere.

**A table opens at once whatever its size**: an ordinary table's rowids are
listed on a thread, and a screenful is fetched by an indexed seek on one of
them (``WHERE rowid >= ?``) -- as cheap on the loop as the dBase viewer's
``pread``.  A view, a ``WITHOUT ROWID`` table and a query's result have no
such key; they are read whole on the thread, up to :data:`ROW_LIMIT` rows.

A table (:class:`SQLTable`) answers what the dBase window asks of a
``dbf.DBFile``: ``fields``, ``count``, ``record``, ``shown``, ``raw``,
``memo``, ``flag``, ``memo_kinds``, ``editable``, ``path``, ``close``.
"""

from __future__ import annotations

import sqlite3
import threading
from array import array
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: What a SQLite file starts with.
MAGIC = b"SQLite format 3\x00"
#: Rows fetched at a time from an ordinary table.
BLOCK = 256
#: Blocks kept.
CACHED_BLOCKS = 64
#: Rows read from a view, a ``WITHOUT ROWID`` table or a query, at most.
ROW_LIMIT = 100_000
#: Rows the widths are measured over, and the widths' bounds.
MEASURED = 200
MIN_WIDTH, MAX_WIDTH = 3, 40
#: How much of a blob *Memo view* shows.
BLOB_SHOWN = 64 * 1024


class SQLiteError(ValueError):
    """Not a SQLite file this viewer can open, or a query that failed."""


def is_sqlite(path: Path | str) -> bool:
    """Whether *path* starts with SQLite's header: one read of a file just named."""
    try:
        with open(path, "rb") as file:
            return file.read(len(MAGIC)) == MAGIC
    except OSError:
        return False


def is_database(name: str) -> bool:
    """Whether F3 looks in *name* for a SQLite file: ``[viewer] database_masks``."""
    import fnmatch

    from navigator.settings import SETTINGS

    name = name.lower()
    return any(fnmatch.fnmatchcase(name, mask.strip().lower())
               for mask in SETTINGS.viewer.database_masks.split(";") if mask.strip())


def quoted(name: str) -> str:
    """*name* as an SQL identifier."""
    return '"' + name.replace('"', '""') + '"'


def affinity(declared: str) -> str:
    """A column's kind by SQLite's affinity rules, as the window's letters:
    ``N`` integer, ``F`` real, ``C`` text, ``B`` blob (or none declared)."""
    upper = declared.upper()
    if "INT" in upper:
        return "N"
    if any(word in upper for word in ("CHAR", "CLOB", "TEXT")):
        return "C"
    if not upper or "BLOB" in upper:
        return "B"
    if any(word in upper for word in ("REAL", "FLOA", "DOUB")):
        return "F"
    return "N"


def kind_of(value: Any) -> str:
    """A query column's kind, by its first value that is not NULL."""
    if isinstance(value, bool | int):
        return "N"
    if isinstance(value, float):
        return "F"
    if isinstance(value, bytes):
        return "B"
    return "C"


@dataclass
class SQLField:
    """A column: what the dBase window reads of a ``dbf.Field`` -- name,
    kind, length, decimals, its index (``offset``), how wide it is shown --
    and what *Structure of* says of it."""

    name: str
    kind: str
    offset: int
    declared: str = ""
    primary: bool = False
    not_null: bool = False
    width: int = MIN_WIDTH
    length: int = 0
    decimals: int = 0


def shown(value: Any) -> str:
    """What a cell paints: NULL as nothing, a blob by its size, a line break
    or a tab as a blank."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return f"‹blob {len(value):,} bytes›"
    text = str(value)
    if any(char in text for char in "\r\n\t"):
        text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("\t", " ")
    return text


class SQLiteFile:
    """A SQLite file, opened read-only: its tables and views, a table or a
    query's result as an :class:`SQLTable`.  One connection, one lock: the
    loop's fetches and a thread's reads take turns."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if not is_sqlite(self.path):
            raise SQLiteError("not a SQLite file")
        self.lock = threading.RLock()
        self.connection = self._connect()

    def _connect(self) -> sqlite3.Connection:
        uri = self.path.resolve().as_uri()
        last: Exception | None = None
        for flags in ("mode=ro", "mode=ro&immutable=1"):
            try:
                connection = sqlite3.connect(f"{uri}?{flags}", uri=True, check_same_thread=False)
                connection.execute("PRAGMA query_only = 1")
                connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
                return connection
            except sqlite3.Error as error:
                last = error
        raise SQLiteError(str(last))

    def close(self) -> None:
        with self.lock:
            self.connection.close()

    def execute(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        with self.lock:
            return self.connection.execute(sql, parameters)

    def objects(self) -> list[tuple[str, str]]:
        """``(name, type)`` of every table and view, SQLite's own left out."""
        with self.lock:
            rows = self.connection.execute(
                "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') "
                "AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\' ORDER BY type, name").fetchall()
        return [(name, kind) for name, kind in rows]

    def columns(self, name: str) -> list[SQLField]:
        """*name*'s columns as declared (``PRAGMA table_xinfo``), hidden ones left out."""
        with self.lock:
            rows = self.connection.execute(f"PRAGMA table_xinfo({quoted(name)})").fetchall()
        return [SQLField(column, affinity(declared or ""), index, declared or "", bool(pk), bool(not_null))
                for index, (_, column, declared, not_null, _, pk, hidden) in enumerate(
                    row for row in rows if row[6] in (0, 2, 3))]

    def table(self, name: str, work: Any = None) -> SQLTable:
        """*name*'s rows: by rowid for an ordinary table, else read whole.
        A thread calls it; *work*'s stop ends the listing (``SQLiteError``)."""
        kind = dict(self.objects()).get(name)
        if kind is None:
            raise SQLiteError(f"no table {name}")
        declared = {field.name: field for field in self.columns(name)}
        source = f"SELECT * FROM {quoted(name)}"
        rowids: array | None = None
        if kind == "table":
            try:
                with self.lock:
                    cursor = self.connection.execute(f"SELECT rowid FROM {quoted(name)} ORDER BY rowid")
                    rowids = array("q")
                    while batch := cursor.fetchmany(65536):
                        if work is not None and work.stopped:
                            raise SQLiteError("stopped")
                        rowids.extend(rowid for (rowid,) in batch)
            except sqlite3.OperationalError:
                rowids = None  # WITHOUT ROWID
        if rowids is not None:
            with self.lock:
                cursor = self.connection.execute(f"{source} LIMIT 0")
            names = [column[0] for column in cursor.description]
            table = SQLTable(self, name, _fields(names, declared), rowids=rowids, select=source)
        else:
            names, rows, cut = self._read(source, work)
            table = SQLTable(self, name, _fields(names, declared, rows), rows=rows, truncated=cut)
        table.measure()
        return table

    def query(self, sql: str, work: Any = None) -> SQLTable:
        """A query typed in the window, its result read whole on the thread.
        One statement, reading only -- anything else is refused by SQLite or
        by the authorizer, and said as :class:`SQLiteError`."""
        text = sql.strip().rstrip(";").strip()
        if not text:
            raise SQLiteError("an empty query")
        with self.lock:
            self.connection.set_authorizer(_reading_only)
            try:
                names, rows, cut = self._read(text, work)
            except (sqlite3.Error, sqlite3.Warning) as error:
                raise SQLiteError(str(error)) from error
            finally:
                self.connection.set_authorizer(None)
        table = SQLTable(self, "", _fields(names, {}, rows), rows=rows, truncated=cut)
        table.measure()
        return table

    def _read(self, sql: str, work: Any) -> tuple[list[str], list[tuple], bool]:
        with self.lock:
            cursor = self.connection.execute(sql)
            if cursor.description is None:
                raise SQLiteError("the statement returns no rows")
            names = [column[0] for column in cursor.description]
            rows: list[tuple] = []
            while len(rows) <= ROW_LIMIT and (batch := cursor.fetchmany(4096)):
                if work is not None and work.stopped:
                    raise SQLiteError("stopped")
                rows.extend(batch)
        cut = len(rows) > ROW_LIMIT
        return names, rows[:ROW_LIMIT], cut

    def schema(self, name: str) -> dict[str, Any]:
        """*Structure of*'s extras for *name*: its ``CREATE``, its indexes as
        ``(name, unique, columns)``, and its row count.  A thread calls it."""
        with self.lock:
            sql = self.connection.execute(
                "SELECT sql FROM sqlite_master WHERE name = ?", (name,)).fetchone()
            indexes = []
            for row in self.connection.execute(f"PRAGMA index_list({quoted(name)})").fetchall():
                index_name, unique = row[1], bool(row[2])
                columns = [info[2] or "" for info in
                           self.connection.execute(f"PRAGMA index_info({quoted(index_name)})").fetchall()]
                indexes.append((index_name, unique, columns))
            count = self.connection.execute(f"SELECT count(*) FROM {quoted(name)}").fetchone()[0]
        return {"sql": (sql[0] if sql else "") or "", "indexes": indexes, "count": count}


#: What a typed query may do: read, call functions, and recurse.
_ALLOWED = frozenset({sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                      getattr(sqlite3, "SQLITE_RECURSIVE", 33)})


def _reading_only(action: int, *args: Any) -> int:
    return sqlite3.SQLITE_OK if action in _ALLOWED else sqlite3.SQLITE_DENY


def _fields(names: list[str], declared: dict[str, SQLField], rows: list[tuple] | None = None) -> list[SQLField]:
    fields = []
    for index, name in enumerate(names):
        known = declared.get(name)
        if known is not None:
            fields.append(SQLField(name, known.kind, index, known.declared, known.primary, known.not_null))
            continue
        kind = "C"
        for row in rows or ():
            if row[index] is not None:
                kind = kind_of(row[index])
                break
        fields.append(SQLField(name, kind, index))
    return fields


class SQLTable:
    """A table's rows, or a query's: what the dBase window shows."""

    #: The kinds *Memo view* (F3) opens on: text and blobs.
    memo_kinds = frozenset({"C", "B"})
    #: View-only: F4 is refused (``DBWindow.refusal``).
    editable = False

    def __init__(self, file: SQLiteFile, name: str, fields: list[SQLField], *, rowids: array | None = None,
                 select: str = "", rows: list[tuple] | None = None, truncated: bool = False) -> None:
        self.file = file
        self.path = file.path
        #: The table's name; "" for a query's result.
        self.name = name
        self.fields = fields
        self.truncated = truncated
        self._rowids = rowids
        self._select = select
        self._rows = rows
        self._blocks: OrderedDict[int, list[tuple]] = OrderedDict()

    @property
    def count(self) -> int:
        return len(self._rowids) if self._rowids is not None else len(self._rows or ())

    def record(self, index: int) -> tuple | None:
        """Row *index*, from 0, or None past either end."""
        if not 0 <= index < self.count:
            return None
        if self._rows is not None:
            return self._rows[index]
        block, at = divmod(index, BLOCK)
        # The loop paints and a search's thread reads: one at a time.
        with self.file.lock:
            rows = self._blocks.get(block)
            if rows is None:
                start = self._rowids[block * BLOCK]
                rows = self.file.connection.execute(
                    f"{self._select} WHERE rowid >= ? ORDER BY rowid LIMIT {BLOCK}", (start,)).fetchall()
                self._blocks[block] = rows
                if len(self._blocks) > CACHED_BLOCKS:
                    self._blocks.popitem(last=False)
            else:
                self._blocks.move_to_end(block)
        return rows[at] if at < len(rows) else None

    @staticmethod
    def flag(record: tuple) -> str:
        """No delete flag: SQLite has none."""
        return " "

    @staticmethod
    def shown(record: tuple, field: SQLField) -> str:
        return shown(record[field.offset])

    @staticmethod
    def raw(record: tuple, field: SQLField) -> str:
        """What a search looks at: the value as text, a blob as shown."""
        value = record[field.offset]
        if value is None:
            return ""
        return shown(value) if isinstance(value, bytes) else str(value)

    @staticmethod
    def memo(record: tuple, field: SQLField) -> str | None:
        """*Memo view*: the whole text, or a blob as hex rows."""
        value = record[field.offset]
        if value is None:
            return None
        if isinstance(value, bytes):
            from navigator.lib.viewer import hex_row

            data = value[:BLOB_SHOWN]
            lines = [hex_row(data[at:at + 16], at, 16, 0) for at in range(0, len(data), 16)]
            if len(value) > BLOB_SHOWN:
                lines.append(f"... {len(value) - BLOB_SHOWN:,} more bytes")
            return "\n".join(lines)
        return str(value)

    def measure(self) -> None:
        """Each field's width: its name or its widest value among the first rows."""
        from navkit.bidi import display_width

        rows = [row for row in (self.record(index) for index in range(min(self.count, MEASURED))) if row]
        for field in self.fields:
            widest = max((display_width(shown(row[field.offset])) for row in rows), default=0)
            field.width = max(MIN_WIDTH, min(MAX_WIDTH, max(display_width(field.name), widest)))

    def close(self) -> None:
        """The file is the window's to close (``SQLiteFile.close``)."""


__all__ = ["SQLField", "SQLTable", "SQLiteError", "SQLiteFile", "is_database", "is_sqlite"]
