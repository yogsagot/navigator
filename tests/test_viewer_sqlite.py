"""File > View > As DataBase on a SQLite file: the model in
``navigator/lib/viewer/sqlite.py`` and the dBase window showing it."""

from __future__ import annotations

import sqlite3

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.viewer import dbf, sqlite
from navigator.lib.viewer.sqlite import SQLiteError, SQLiteFile, is_sqlite


def build(path, rows: int = 600) -> None:
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE people(id INTEGER PRIMARY KEY, name TEXT NOT NULL, photo BLOB, score REAL);
        CREATE INDEX people_name ON people(name);
        CREATE TABLE kv(k TEXT PRIMARY KEY, v) WITHOUT ROWID;
        CREATE VIEW high AS SELECT name FROM people WHERE score > 100;
    """)
    connection.executemany("INSERT INTO people(name, photo, score) VALUES (?, ?, ?)",
                           [(f"p{i}\nx", b"\x00\x01" if i % 2 else None, i * 0.5) for i in range(rows)])
    connection.execute("DELETE FROM people WHERE id BETWEEN 10 AND 20")
    connection.execute("INSERT INTO kv VALUES ('a', 1)")
    connection.commit()
    connection.close()


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "x.sqlite"
    build(path)
    file = SQLiteFile(path)
    yield file
    file.close()


# -- the model ---------------------------------------------------------------------


def test_the_header_says_sqlite(tmp_path):
    build(tmp_path / "a.db")
    (tmp_path / "b.db").write_bytes(b"not a database")
    assert is_sqlite(tmp_path / "a.db") and not is_sqlite(tmp_path / "b.db")
    with pytest.raises(SQLiteError):
        SQLiteFile(tmp_path / "b.db")


def test_the_file_is_opened_read_only(db):
    with pytest.raises(sqlite3.Error):
        db.execute("INSERT INTO kv VALUES ('b', 2)")
    assert db.execute("PRAGMA query_only").fetchone() == (1,)


def test_tables_then_views_and_sqlites_own_left_out(db):
    db.execute("SELECT 1")  # nothing of sqlite_% to show even so
    assert db.objects() == [("kv", "table"), ("people", "table"), ("high", "view")]


def test_an_ordinary_table_pages_by_rowid_across_its_gaps(db, monkeypatch):
    monkeypatch.setattr(sqlite, "BLOCK", 8)
    table = db.table("people")
    assert table.count == 589
    assert [table.record(n)[0] for n in (0, 8, 9, 10, 588)] == [1, 9, 21, 22, 600]
    assert table.record(589) is None
    assert [(f.name, f.kind, f.primary, f.not_null) for f in table.fields] == [
        ("id", "N", True, False), ("name", "C", False, True), ("photo", "B", False, False), ("score", "F", False, False)]


def test_a_view_and_a_without_rowid_table_are_read_whole(db):
    assert db.table("kv").record(0) == ("a", 1)
    high = db.table("high")
    assert high.count == 399 and not high.truncated


def test_a_read_is_cut_at_the_limit(db, monkeypatch):
    monkeypatch.setattr(sqlite, "ROW_LIMIT", 50)
    view = db.table("high")
    assert view.count == 50 and view.truncated


def test_cells_null_blob_and_text(db):
    table = db.table("people")
    row = table.record(1)
    name, photo = table.fields[1], table.fields[2]
    assert table.shown(row, name) == "p1 x" and table.raw(row, name) == "p1\nx"
    assert table.shown(row, photo) == "‹blob 2 bytes›"
    assert table.memo(row, photo).startswith("00000000: 00 01")
    assert table.shown(table.record(0), photo) == "" and table.memo(table.record(0), photo) is None
    assert table.flag(row) == " " and not table.editable


def test_a_query_reads_and_nothing_else(db):
    result = db.query("SELECT name, count(*) FROM people;")
    assert [f.name for f in result.fields] == ["name", "count(*)"] and result.count == 1
    for sql in ("INSERT INTO kv VALUES ('b', 2)", "SELECT 1; SELECT 2", "ATTACH 'y.db' AS y",
                "PRAGMA query_only = 0", "DROP TABLE kv", "selec x", ""):
        with pytest.raises(SQLiteError):
            db.query(sql)
    assert db.table("kv").count == 1


def test_the_schema(db):
    schema = db.schema("people")
    assert schema["count"] == 589
    assert schema["indexes"] == [("people_name", False, ["name"])]
    assert schema["sql"].startswith("CREATE TABLE people")


def test_search_works_on_a_sqlite_table(db):
    table = db.table("people")
    assert dbf.find(table, "P21", case=False, all_fields=True, backward=False, record=-1, field=0) == (10, 1)


def test_a_wal_copied_beside_it_is_read(tmp_path):
    import shutil

    path = tmp_path / "w.db"
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode = wal")
    connection.execute("PRAGMA wal_autocheckpoint = 0")
    connection.execute("CREATE TABLE t(x)")
    connection.executemany("INSERT INTO t VALUES (?)", [(n,) for n in range(5)])
    connection.commit()
    copy = tmp_path / "copy"
    copy.mkdir()
    for name in ("w.db", "w.db-wal"):
        shutil.copy(tmp_path / name, copy / name)
    connection.close()
    file = SQLiteFile(copy / "w.db")
    assert file.table("t").count == 5
    file.close()


# -- the window ----------------------------------------------------------------------


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    build(tmp_path / "zz.sqlite")
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def db_window(app):
    from navigator.widgets.viewer.db_window import DBWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, DBWindow) else None


def keys(text: str) -> list[KeyEvent]:
    return [KeyEvent(c.lower(), c, shift=c.isupper()) for c in text]


def opened(*, choose: int = 1):
    """F3, *Tables*, the entry *choose* down chosen."""
    return [KeyEvent("end"), KeyEvent("f3"), Until(lambda a: a.modal is not None),
            *[KeyEvent("down")] * choose, KeyEvent("enter"), Until(lambda a: db_window(a) is not None)]


def test_f3_asks_which_table_and_shows_it(files):
    app = navigator(files)
    seen = {}
    run_app(app, [*opened(), lambda a: seen.update(window=db_window(a))])
    window = seen["window"]
    assert window.db.name == "people" and window.db.count == 589
    assert window.title == f"{files / 'zz.sqlite'} - people"
    assert window.list_name() == f"SQLite View - {files / 'zz.sqlite'}"
    assert window.indicator.text == "1/589"


def test_f5_switches_table_and_f4_is_refused(files):
    from navigator.widgets.viewer.commands import EditDbField

    app = navigator(files)
    seen = {}
    run_app(app, [
        *opened(),
        lambda a: seen.update(f4=db_window(a).refusal(EditDbField())),
        KeyEvent("f5"), Until(lambda a: a.modal is not None), KeyEvent("down"), KeyEvent("enter"),
        Until(lambda a: db_window(a) is not None and db_window(a).db.name == "high"),
        lambda a: seen.update(count=db_window(a).db.count),
    ])
    assert seen == {"f4": "The database is opened read-only", "count": 399}


def test_f6_runs_a_query_and_says_an_error(files):
    app = navigator(files)
    seen = {}
    run_app(app, [
        *opened(),
        KeyEvent("f6"), Until(lambda a: a.modal is not None), *keys("select k, v from kv"), KeyEvent("enter"),
        Until(lambda a: db_window(a) is not None and db_window(a).db.name == ""),
        lambda a: seen.update(row=db_window(a).db.record(0), title=db_window(a).title),
        KeyEvent("f6"), Until(lambda a: a.modal is not None), *keys("delete from kv"), KeyEvent("enter"),
        Until(lambda a: a.modal is not None and getattr(a.modal, "prompt", "")),
        lambda a: seen.update(error=a.modal.prompt),
    ])
    assert seen["row"] == ("a", 1) and seen["title"].endswith(" - Query")
    assert seen["error"] == "not authorized"


def test_f2_shows_the_schema(files):
    app = navigator(files)
    seen = {}
    run_app(app, [*opened(), KeyEvent("f2"), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(lines=list(a.modal.lines.items), title=a.modal.title)])
    text = "\n".join(seen["lines"])
    assert seen["title"] == "Structure of people"
    assert "PK" in text and "NOT NULL" in text and "589 rows" in text
    assert "people_name (name)" in text and "CREATE TABLE people" in text


def test_f7_searches_on_a_thread(files):
    app = navigator(files)
    seen = {}
    run_app(app, [
        *opened(),
        KeyEvent("f7"), Until(lambda a: a.modal is not None), *keys("p400"), KeyEvent("tab"), KeyEvent("tab"),
        KeyEvent("down"), KeyEvent("enter"),
        Until(lambda a: a.modal is None and db_window(a).viewer.record > 0),
        lambda a: seen.update(row=db_window(a).viewer.record),
    ], timeout=10)
    assert seen["row"] == 389


def test_a_db_that_is_not_sqlite_opens_as_text(files):
    from navigator.widgets.viewer.file_window import FileWindow

    (files / "zz.sqlite").unlink()
    (files / "zz.db").write_text("just text\n")
    app = navigator(files)
    run_app(app, [KeyEvent("end"), KeyEvent("f3"),
                  Until(lambda a: isinstance(a.shell.desktop.active_window, FileWindow))])


def test_a_table_with_no_rows_reads_0_of_0_and_f3_shows_nothing(tmp_path, monkeypatch):
    # A departure: DN refused an empty .dbf (it still is); a table or a query
    # with no rows is an answer, so the window opens on its field names.
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    connection = sqlite3.connect(tmp_path / "zz.sqlite")
    connection.execute("CREATE TABLE blank(a TEXT, b INTEGER)")
    connection.commit()
    connection.close()
    app = navigator(tmp_path)
    seen = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), Until(lambda a: db_window(a) is not None),
                  lambda a: seen.update(indicator=db_window(a).indicator.text),
                  KeyEvent("f3"), KeyEvent("down"), KeyEvent("end", ctrl=True), lambda a: None,
                  lambda a: seen.update(modal=a.modal, indicator_after=db_window(a).indicator.text)])
    assert seen == {"indicator": "0/0", "modal": None, "indicator_after": "0/0"}
