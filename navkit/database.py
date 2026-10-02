"""The one database: SQLite, a model per table, and a schema checked only when it changed.

What Navigator remembers between runs and that is not a setting -- input-line
histories now, bookmarks and positions later -- lives in one SQLite file, opened
once by whoever owns the command line (:data:`DATABASE`, the way
:data:`navml.history.HISTORY` and ``navigator.settings.SETTINGS`` are the one
store of theirs).  Until something opens a file it is ``:memory:``, which is
what keeps a test, or an application constructed without ``main()``, off the
disk.

**A model is a class, usually generated.**  A ``.nml`` document whose root
extends :class:`Model` declares fields rather than children, and ``navml build``
writes the class with everything this module needs already computed: the
fields, the statements that create the table (:func:`ddl_for`) and their
fingerprint (:func:`fingerprint`).  A handler then talks to the table through
the class alone -- ``HistoryEntry.where(list_id="copy").order("-seq")`` -- with
no session, engine or connection in sight.

**The schema is examined only when it changed.**  Every fingerprint the file
has been migrated to is kept in one small table, ``_navml_schema``, read whole
when the file is opened.  The first time a model touches the database its own
fingerprint is compared with that one row; a match costs a dictionary lookup
and the model is never asked again in this process, so a file that is up to
date is opened with one ``SELECT`` and no ``PRAGMA table_info`` at all.  A
mismatch -- a first run, a new field, a newer or older Navigator having been
there -- migrates that one table under ``BEGIN IMMEDIATE`` and records the new
fingerprint.  A model never imported costs nothing.

**A migration diffs against the live table, not the old fingerprint**, so it
never needs to know which version wrote the file: a missing table is created,
a missing column added, the indexes recreated, and only a column whose
definition changed, or one a model names in ``__dropped__``, makes the table be
rebuilt.  A column the model does not mention is kept, which is what lets an
older Navigator open a newer file: every field has a default, so a row inserted
without the newer columns is still a valid row.

Writes are synchronous and committed one call at a time.  They are small and
bounded, in WAL mode, and run on the loop for the reason ``SETTINGS.save``
does; anything bulky belongs on a thread, the way file operations go.
"""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Generic, Iterator, Sequence, TypeVar

#: The table every fingerprint is kept in, one row per model table.
SCHEMA_TABLE = "_navml_schema"

#: The primary key every table has and no model declares.
KEY = "id"

#: How long a writer waits for another process's write to finish, in ms.
BUSY_TIMEOUT = 2000

M = TypeVar("M", bound="Model")


class DatabaseError(Exception):
    """A model or a query asked for something its table cannot answer."""


# -- what a column holds ------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Codec:
    """How one Python type is stored: its column type, its zero, both directions."""

    sql: str
    encode: Any = None
    decode: Any = None
    #: The value a field of this type defaults to when it names none, or
    #: ``_NO_ZERO`` for a type that has no natural empty value.
    zero: Any = None


_NO_ZERO = object()

#: Every type a field may hold.  A type absent here is refused by the build.
CODECS: dict[type, Codec] = {
    str: Codec("TEXT", zero=""),
    int: Codec("INTEGER", zero=0),
    float: Codec("REAL", zero=0.0),
    bool: Codec("INTEGER", encode=int, decode=bool, zero=False),
    bytes: Codec("BLOB", zero=b""),
    datetime: Codec(
        "TEXT", encode=datetime.isoformat, decode=datetime.fromisoformat,
        zero=_NO_ZERO,
    ),
    Path: Codec("TEXT", encode=str, decode=Path, zero=_NO_ZERO),
}


@dataclass(frozen=True, slots=True)
class Field:
    """One column: its name, the Python type it holds, and its default.

    ``null`` is whether ``None`` is a value it may hold; a field that is not
    nullable is ``NOT NULL`` with its default as the column's ``DEFAULT``, which
    is what keeps a row inserted by an older model -- one that never heard of
    this field -- a valid row.
    """

    name: str
    type: type
    default: Any = None
    null: bool = False

    @property
    def codec(self) -> Codec:
        return CODECS[self.type]

    def encode(self, value: Any) -> Any:
        if value is None:
            return None
        encode = self.codec.encode
        return value if encode is None else encode(value)

    def decode(self, value: Any) -> Any:
        if value is None:
            return None
        decode = self.codec.decode
        return value if decode is None else decode(value)

    def column(self) -> str:
        """The column definition, as ``CREATE TABLE`` and ``ADD COLUMN`` take it."""
        parts = [_quote(self.name), self.codec.sql]
        if not self.null:
            parts.append("NOT NULL")
        default = self.encode(self.default)
        if default is not None:
            parts.append(f"DEFAULT {_literal(default)}")
        return " ".join(parts)


def zero_of(kind: type) -> Any:
    """The default a field of *kind* has when it names none, or raise."""
    codec = CODECS.get(kind)
    if codec is None or codec.zero is _NO_ZERO:
        raise DatabaseError(f"{getattr(kind, '__name__', kind)} has no empty value")
    return codec.zero


@dataclass(frozen=True, slots=True)
class Index:
    """``CREATE [UNIQUE] INDEX``: a name of its own, and the columns it covers."""

    name: str
    columns: tuple[str, ...]
    unique: bool = False


# -- the statements a model is made of ----------------------------------------


def create_table(table: str, fields: Sequence[Field]) -> str:
    """The ``CREATE TABLE`` statement for *fields*, with the implicit key first."""
    columns = [f"{_quote(KEY)} INTEGER PRIMARY KEY"]
    columns.extend(field.column() for field in fields)
    return f"CREATE TABLE {_quote(table)} ({', '.join(columns)})"


def create_index(table: str, index: Index) -> str:
    unique = "UNIQUE " if index.unique else ""
    columns = ", ".join(_quote(column) for column in index.columns)
    return (
        f"CREATE {unique}INDEX {_quote(index_name(table, index))} "
        f"ON {_quote(table)} ({columns})"
    )


def index_name(table: str, index: Index) -> str:
    """Index names are per database, so each is prefixed with its table's."""
    return f"{table}_{index.name}"


def ddl_for(
    table: str, fields: Sequence[Field], indexes: Sequence[Index] = ()
) -> tuple[str, ...]:
    """Every statement that makes *table* from nothing, in order.

    The build calls this to write ``__ddl__`` and a migration calls it again to
    rebuild, so the two can never disagree about what a model's table is.
    """
    return (create_table(table, fields),) + tuple(
        create_index(table, index) for index in indexes
    )


def fingerprint(ddl: Sequence[str], dropped: Sequence[str] = ()) -> str:
    """What ``_navml_schema`` records for a model: a hash of its statements.

    ``__dropped__`` is in it because it changes what a migration does without
    changing a single statement.
    """
    text = "\n".join(ddl)
    if dropped:
        text += "\n-- dropped: " + ", ".join(dropped)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _literal(value: Any) -> str:
    """*value* as an SQL literal, for a ``DEFAULT`` clause, which takes no parameter."""
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, bytes):
        return f"X'{value.hex()}'"
    return "'" + str(value).replace("'", "''") + "'"


# -- the file ------------------------------------------------------------------


class Database:
    """One SQLite connection and the fingerprints its tables are migrated to."""

    def __init__(self) -> None:
        self._connection: sqlite3.Connection | None = None
        self._schemas: dict[str, str] = {}
        self._ensured: set[str] = set()
        #: The file open now, or ``None`` before anything was, or for ``:memory:``.
        self.path: Path | None = None

    def open(self, path: str | Path = ":memory:") -> None:
        """Connect to *path*, creating it if needed, closing whatever was open.

        Raises :class:`sqlite3.Error` (or :class:`OSError` for the directory)
        when the file cannot be used; the caller decides whether to carry on
        in memory.
        """
        self.close()
        memory = str(path) == ":memory:"
        if not memory:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            str(path), isolation_level=None, check_same_thread=False
        )
        try:
            connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT}")
            if not memory:
                connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                f"CREATE TABLE IF NOT EXISTS {_quote(SCHEMA_TABLE)} "
                f"(name TEXT PRIMARY KEY, schema TEXT NOT NULL, "
                f"migrated TEXT NOT NULL)"
            )
            self._schemas = dict(
                connection.execute(f"SELECT name, schema FROM {_quote(SCHEMA_TABLE)}")
            )
        except BaseException:
            connection.close()
            raise
        self._connection = connection
        self._ensured = set()
        self.path = None if memory else Path(path)

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
        self._connection = None
        self._schemas = {}
        self._ensured = set()
        self.path = None

    @property
    def connection(self) -> sqlite3.Connection:
        """The open connection, opening ``:memory:`` if nothing has been."""
        if self._connection is None:
            self.open()
        assert self._connection is not None
        return self._connection

    def execute(self, sql: str, parameters: Sequence[Any] = ()) -> sqlite3.Cursor:
        """Run one statement: the way out when a query is beyond :class:`Query`."""
        return self.connection.execute(sql, parameters)

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Everything inside commits together, or not at all.

        ``BEGIN IMMEDIATE`` takes the write lock up front, so two processes
        each reading before writing cannot both decide to.  A transaction
        opened inside another is a savepoint of it.
        """
        connection = self.connection
        if connection.in_transaction:
            name = f"sp{id(object())}"
            connection.execute(f"SAVEPOINT {name}")
            try:
                yield
            except BaseException:
                connection.execute(f"ROLLBACK TO {name}")
                connection.execute(f"RELEASE {name}")
                raise
            connection.execute(f"RELEASE {name}")
            return
        connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            connection.execute("ROLLBACK")
            self._forget_schemas()
            raise
        connection.execute("COMMIT")

    # -- the schema -------------------------------------------------------------

    def _forget_schemas(self) -> None:
        """Read the fingerprints again, after a rollback may have undone one."""
        assert self._connection is not None
        self._schemas = dict(
            self._connection.execute(f"SELECT name, schema FROM {_quote(SCHEMA_TABLE)}")
        )
        self._ensured = set()

    def schema_of(self, table: str) -> str | None:
        """The fingerprint *table* was last migrated to, as read at open."""
        return self._schemas.get(table)

    def ensure(self, model: type[Model]) -> None:
        """Make *model*'s table match it, if it does not already.

        The fast path is the whole point: one set lookup once a model has been
        seen, one dictionary lookup the first time when nothing changed.
        """
        table = model.__table__
        if table in self._ensured:
            return
        self.connection  # opens :memory: if need be, which resets what was ensured
        if self._schemas.get(table) != model.__schema__:
            self._migrate(model)
        self._ensured.add(table)

    def _migrate(self, model: type[Model]) -> None:
        """Migrate under the write lock, unless another process just did.

        Inside a caller's transaction this is only a savepoint of it, and a
        rollback takes the table with it: :meth:`transaction` forgets the
        caches when that happens, so they are never left claiming a table
        that is not there.
        """
        table = model.__table__
        with self.transaction():
            # Asked again under the lock: another process may have got here first.
            row = self.execute(
                f"SELECT schema FROM {_quote(SCHEMA_TABLE)} WHERE name = ?", (table,)
            ).fetchone()
            if row is None or row[0] != model.__schema__:
                migrate(self, model)
                self.execute(
                    f"INSERT INTO {_quote(SCHEMA_TABLE)} (name, schema, migrated) "
                    f"VALUES (?, ?, ?) ON CONFLICT(name) DO UPDATE SET "
                    f"schema = excluded.schema, migrated = excluded.migrated",
                    (table, model.__schema__, datetime.now().isoformat(timespec="seconds")),
                )
        self._schemas[table] = model.__schema__


def migrate(database: Database, model: type[Model]) -> None:
    """Bring *model*'s table in line with it, judged against the live table.

    Called inside a transaction.  Public so a test can watch what it does.
    """
    table = model.__table__
    live = {
        row[1]: row
        for row in database.execute(f"PRAGMA table_info({_quote(table)})")
    }
    if not live:
        for statement in model.__ddl__:
            database.execute(statement)
        return
    dropped = [name for name in model.__dropped__ if name in live]
    changed = [
        field.name for field in model.__fields__
        if field.name in live and not _same_column(live[field.name], field)
    ]
    if dropped or changed:
        _rebuild(database, model, live)
        return
    for field in model.__fields__:
        if field.name not in live:
            database.execute(
                f"ALTER TABLE {_quote(table)} ADD COLUMN {field.column()}"
            )
    _recreate_indexes(database, model)


def _same_column(row: Sequence[Any], field: Field) -> bool:
    """Does a ``PRAGMA table_info`` row say what *field* would create?"""
    _, _, kind, notnull, default, _ = row
    wanted = field.encode(field.default)
    return (
        kind.upper() == field.codec.sql
        and bool(notnull) == (not field.null)
        and default == (None if wanted is None else _literal(wanted))
    )


def _recreate_indexes(database: Database, model: type[Model]) -> None:
    table = model.__table__
    for row in database.execute(f"PRAGMA index_list({_quote(table)})").fetchall():
        name, origin = row[1], row[3]
        if origin == "c":  # made by CREATE INDEX, so ours to drop
            database.execute(f"DROP INDEX {_quote(name)}")
    for index in model.__indexes__:
        database.execute(create_index(table, index))


def _rebuild(
    database: Database, model: type[Model], live: dict[str, Sequence[Any]]
) -> None:
    """SQLite's own recipe for a change ``ALTER TABLE`` cannot make.

    Create the new table beside the old one, copy every column the two share,
    drop the old one and rename the new one into its place.  A live column the
    model does not mention and does not drop is carried over as it was, so a
    newer Navigator's columns survive an older one rebuilding the table.
    """
    table = model.__table__
    staging = f"{table}__navml_new"
    known = {field.name for field in model.__fields__}
    kept = [
        row for name, row in live.items()
        if name != KEY and name not in known and name not in model.__dropped__
    ]
    statement = create_table(staging, model.__fields__)
    if kept:
        extra = ", ".join(_column_from(row) for row in kept)
        statement = statement[:-1] + f", {extra})"
    database.execute(statement)
    common = [KEY] + [
        name for name in [f.name for f in model.__fields__] + [row[1] for row in kept]
        if name in live
    ]
    columns = ", ".join(_quote(name) for name in common)
    database.execute(
        f"INSERT INTO {_quote(staging)} ({columns}) "
        f"SELECT {columns} FROM {_quote(table)}"
    )
    database.execute(f"DROP TABLE {_quote(table)}")
    database.execute(f"ALTER TABLE {_quote(staging)} RENAME TO {_quote(table)}")
    for index in model.__indexes__:
        database.execute(create_index(table, index))


def _column_from(row: Sequence[Any]) -> str:
    """A column definition recovered from a ``PRAGMA table_info`` row."""
    _, name, kind, notnull, default, _ = row
    text = f"{_quote(name)} {kind}"
    if notnull:
        text += " NOT NULL"
    if default is not None:
        text += f" DEFAULT {default}"
    return text


#: The one database every model uses.
DATABASE = Database()


# -- models and queries ---------------------------------------------------------

_OPERATORS = {
    "eq": "=", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">=",
    "like": "LIKE",
}


class Query(Generic[M]):
    """A ``SELECT`` being described: immutable, run when iterated.

    ``where`` takes ``field=value`` for equality and ``field__op=value`` for the
    rest (``lt le gt ge ne like in``); ``None`` compares with ``IS``.  Names are
    checked against the model and every value is a parameter, so nothing a
    caller passes is ever spliced into the SQL.
    """

    __slots__ = ("model", "_where", "_parameters", "_order", "_limit", "_offset")

    def __init__(
        self,
        model: type[M],
        where: tuple[str, ...] = (),
        parameters: tuple[Any, ...] = (),
        order: tuple[str, ...] = (),
        limit: int | None = None,
        offset: int | None = None,
    ) -> None:
        self.model = model
        self._where = where
        self._parameters = parameters
        self._order = order
        self._limit = limit
        self._offset = offset

    def _copy(self, **changes: Any) -> Query[M]:
        values = {
            "where": self._where, "parameters": self._parameters,
            "order": self._order, "limit": self._limit, "offset": self._offset,
        }
        values.update(changes)
        return Query(self.model, **values)

    def where(self, **conditions: Any) -> Query[M]:
        clauses = list(self._where)
        parameters = list(self._parameters)
        for key, value in conditions.items():
            name, _, operator = key.partition("__")
            field = self.model._field(name)
            column = _quote(name)
            if operator == "in":
                values = [field.encode(v) for v in value]
                if not values:
                    clauses.append("0")
                    continue
                clauses.append(f"{column} IN ({', '.join('?' * len(values))})")
                parameters.extend(values)
                continue
            if operator not in ("", *_OPERATORS):
                raise DatabaseError(f"no operator {operator!r} in {key!r}")
            sql = _OPERATORS[operator or "eq"]
            if value is None and sql in ("=", "!="):
                clauses.append(f"{column} IS {'NOT ' if sql == '!=' else ''}NULL")
                continue
            clauses.append(f"{column} {sql} ?")
            parameters.append(field.encode(value))
        return self._copy(where=tuple(clauses), parameters=tuple(parameters))

    def order(self, *names: str) -> Query[M]:
        """Sort by *names*; a leading ``-`` sorts that one descending."""
        terms = []
        for name in names:
            descending = name.startswith("-")
            name = name.lstrip("-")
            self.model._field(name)
            terms.append(f"{_quote(name)}{' DESC' if descending else ''}")
        return self._copy(order=self._order + tuple(terms))

    def limit(self, count: int) -> Query[M]:
        return self._copy(limit=int(count))

    def offset(self, count: int) -> Query[M]:
        return self._copy(offset=int(count))

    def _sql(self, what: str) -> tuple[str, tuple[Any, ...]]:
        sql = f"SELECT {what} FROM {_quote(self.model.__table__)}"
        if self._where:
            sql += " WHERE " + " AND ".join(self._where)
        if self._order:
            sql += " ORDER BY " + ", ".join(self._order)
        if self._limit is not None or self._offset is not None:
            sql += f" LIMIT {self._limit if self._limit is not None else -1}"
            if self._offset is not None:
                sql += f" OFFSET {self._offset}"
        return sql, self._parameters

    def _run(self, what: str) -> sqlite3.Cursor:
        database = self.model._database()
        return database.execute(*self._sql(what))

    def __iter__(self) -> Iterator[M]:
        model = self.model
        columns = model._columns()
        cursor = self._run(", ".join(_quote(c) for c in columns))
        for row in cursor:
            yield model._from_row(columns, row)

    def all(self) -> list[M]:
        return list(self)

    def first(self) -> M | None:
        return next(iter(self.limit(1)), None)

    def count(self) -> int:
        if self._limit is None and self._offset is None:
            return self._run("COUNT(*)").fetchone()[0]
        return sum(1 for _ in self._run(_quote(KEY)))

    def exists(self) -> bool:
        return self.first() is not None

    def values(self, name: str) -> list[Any]:
        """One column of every row, decoded."""
        field = self.model._field(name)
        return [field.decode(row[0]) for row in self._run(_quote(name))]

    def _keys(self) -> list[int]:
        return [row[0] for row in self._run(_quote(KEY))]

    def delete(self) -> int:
        """Delete every row this query selects; how many there were."""
        database = self.model._database()
        table = _quote(self.model.__table__)
        if self._limit is None and self._offset is None and not self._order:
            sql = f"DELETE FROM {table}"
            if self._where:
                sql += " WHERE " + " AND ".join(self._where)
            return database.execute(sql, self._parameters).rowcount
        keys = self._keys()
        if not keys:
            return 0
        return database.execute(
            f"DELETE FROM {table} WHERE {_quote(KEY)} IN ({', '.join('?' * len(keys))})",
            keys,
        ).rowcount

    def update(self, **values: Any) -> int:
        """Set *values* on every row this query selects; how many there were."""
        if not values:
            return 0
        model = self.model
        assignments = ", ".join(f"{_quote(name)} = ?" for name in values)
        encoded = [model._field(name).encode(v) for name, v in values.items()]
        keys = self._keys()
        if not keys:
            return 0
        return model._database().execute(
            f"UPDATE {_quote(model.__table__)} SET {assignments} "
            f"WHERE {_quote(KEY)} IN ({', '.join('?' * len(keys))})",
            [*encoded, *keys],
        ).rowcount

    def __repr__(self) -> str:
        sql, parameters = self._sql("*")
        return f"<Query {sql} {parameters!r}>"


class Model:
    """A row of a table, and through its class the table itself.

    Generated from markup, normally: the build fills the class attributes
    below.  The instance is plain -- an attribute per field and ``id`` -- so a
    hand-written half may add methods and properties freely.
    """

    #: The table the rows live in.
    __table__: ClassVar[str] = ""
    #: Every declared field, in the order the document gives them.
    __fields__: ClassVar[tuple[Field, ...]] = ()
    #: ``index`` and ``unique`` lines.
    __indexes__: ClassVar[tuple[Index, ...]] = ()
    #: Columns a migration removes, by name.
    __dropped__: ClassVar[tuple[str, ...]] = ()
    #: What :func:`ddl_for` made of the three above.
    __ddl__: ClassVar[tuple[str, ...]] = ()
    #: :func:`fingerprint` of :attr:`__ddl__`, compared with ``_navml_schema``.
    __schema__: ClassVar[str] = ""

    id: int | None

    def __init__(self, **values: Any) -> None:
        self.id = values.pop(KEY, None)
        for field in type(self).__fields__:
            setattr(self, field.name, values.pop(field.name, field.default))
        if values:
            raise TypeError(
                f"{type(self).__name__} has no field {', '.join(map(repr, values))}"
            )

    # -- the table ---------------------------------------------------------------

    @classmethod
    def _database(cls) -> Database:
        DATABASE.ensure(cls)
        return DATABASE

    @classmethod
    def _field(cls, name: str) -> Field:
        if name == KEY:
            return _KEY_FIELD
        for field in cls.__fields__:
            if field.name == name:
                return field
        raise DatabaseError(f"{cls.__name__} has no field {name!r}")

    @classmethod
    def _columns(cls) -> tuple[str, ...]:
        return (KEY,) + tuple(field.name for field in cls.__fields__)

    @classmethod
    def _from_row(cls: type[M], columns: Sequence[str], row: Sequence[Any]) -> M:
        instance = cls.__new__(cls)
        for name, value in zip(columns, row):
            setattr(instance, name, cls._field(name).decode(value))
        return instance

    @classmethod
    def query(cls: type[M]) -> Query[M]:
        return Query(cls)

    @classmethod
    def where(cls: type[M], **conditions: Any) -> Query[M]:
        return Query(cls).where(**conditions)

    @classmethod
    def all(cls: type[M]) -> list[M]:
        return Query(cls).all()

    @classmethod
    def get(cls: type[M], **conditions: Any) -> M | None:
        """The one row matching *conditions*, or ``None``."""
        return Query(cls).where(**conditions).first()

    @classmethod
    def count(cls, **conditions: Any) -> int:
        return Query(cls).where(**conditions).count()

    @classmethod
    def delete_where(cls, **conditions: Any) -> int:
        return Query(cls).where(**conditions).delete()

    @classmethod
    def create(cls: type[M], **values: Any) -> M:
        """Insert a row and return it, its ``id`` filled in."""
        instance = cls(**values)
        instance.save()
        return instance

    @classmethod
    def upsert(cls: type[M], **values: Any) -> M:
        """Insert a row, or update the one a unique index says it already is.

        The index is the first ``unique`` one whose columns *values* covers.
        Only the fields given are written over an existing row; the rest keep
        what they held, which is how a history entry added again keeps its pin.
        """
        target = next(
            (index for index in cls.__indexes__
             if index.unique and set(index.columns) <= set(values)),
            None,
        )
        if target is None:
            raise DatabaseError(
                f"{cls.__name__}.upsert needs every column of a unique index, "
                f"and {sorted(values)} covers none"
            )
        names = list(values)
        encoded = [cls._field(name).encode(values[name]) for name in names]
        updates = [n for n in names if n not in target.columns]
        conflict = ", ".join(_quote(c) for c in target.columns)
        action = (
            "DO UPDATE SET " + ", ".join(f"{_quote(n)} = excluded.{_quote(n)}" for n in updates)
            if updates else "DO NOTHING"
        )
        cls._database().execute(
            f"INSERT INTO {_quote(cls.__table__)} "
            f"({', '.join(_quote(n) for n in names)}) "
            f"VALUES ({', '.join('?' * len(names))}) "
            f"ON CONFLICT({conflict}) {action}",
            encoded,
        )
        found = cls.get(**{column: values[column] for column in target.columns})
        assert found is not None
        return found

    # -- one row -------------------------------------------------------------------

    def save(self) -> None:
        """Insert this row, or write it over the one with its ``id``."""
        cls = type(self)
        database = cls._database()
        names = [field.name for field in cls.__fields__]
        values = [field.encode(getattr(self, field.name)) for field in cls.__fields__]
        table = _quote(cls.__table__)
        if self.id is None:
            cursor = database.execute(
                f"INSERT INTO {table} ({', '.join(_quote(n) for n in names)}) "
                f"VALUES ({', '.join('?' * len(names))})",
                values,
            )
            self.id = cursor.lastrowid
            return
        assignments = ", ".join(f"{_quote(n)} = ?" for n in names)
        database.execute(
            f"UPDATE {table} SET {assignments} WHERE {_quote(KEY)} = ?",
            [*values, self.id],
        )

    def delete(self) -> None:
        if self.id is None:
            return
        cls = type(self)
        cls._database().execute(
            f"DELETE FROM {_quote(cls.__table__)} WHERE {_quote(KEY)} = ?", (self.id,)
        )
        self.id = None

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return all(
            getattr(self, name, None) == getattr(other, name, None)
            for name in type(self)._columns()
        )

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        fields = ", ".join(
            f"{name}={getattr(self, name, None)!r}" for name in type(self)._columns()
        )
        return f"{type(self).__name__}({fields})"


_KEY_FIELD = Field(KEY, int, None, null=True)


__all__ = [
    "CODECS",
    "DATABASE",
    "Database",
    "DatabaseError",
    "Field",
    "Index",
    "Model",
    "Query",
    "ddl_for",
    "fingerprint",
    "migrate",
    "zero_of",
]
