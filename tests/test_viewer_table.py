"""F3 on a CSV: the database window (the dBase and SQLite viewer's) on a
delimited text file, view-only -- the model in ``navigator/lib/viewer/table.py``
and the window showing it."""

from __future__ import annotations

import time

import pytest

from conftest import LISTED, FakeTerminal, Until, run_app, settle
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.viewer.table import (
    CSVTable,
    Dialect,
    SortedView,
    TableSource,
    Work,
    column_name,
    guess,
    number,
    sort_order,
)

CITIES = (
    b'id,city,pop\r\n'
    b'1,"Paris, FR",2148000\r\n'
    b'2,"Lon\r\ndon",8982000\r\n'
    b'3,"say ""hi""",5\r\n'
    b'4,x,'
)


@pytest.fixture
def make(tmp_path):
    def make(data: bytes, name: str = "t.csv", dialect: Dialect | None = None) -> TableSource:
        path = tmp_path / name
        path.write_bytes(data)
        source = TableSource(path, dialect)
        source.index()
        return source

    return make


# -- the model ---------------------------------------------------------------------


def test_records_end_outside_quotes_only(make):
    source = make(CITIES)
    assert source.complete and source.records == 5 and source.count == 4
    assert source.titles() == ["id", "city", "pop"]
    assert [source.row(n) for n in range(4)] == [
        ["1", "Paris, FR", "2148000"],
        ["2", "Lon\r\ndon", "8982000"],
        ["3", 'say "hi"', "5"],
        ["4", "x", ""],
    ]
    assert source.row(4) is None


@pytest.mark.parametrize("ending", [b"\n", b"\r\n", b"\r"])
def test_every_line_ending_ends_a_record(make, ending):
    source = make(ending.join([b"a,b", b"1,2", b"3,4"]) + ending)
    assert source.records == 3 and source.row(1) == ["3", "4"]


def test_a_crlf_split_across_blocks_is_one_ending(make, monkeypatch):
    from navigator.lib.viewer import table

    monkeypatch.setattr(table, "BLOCK", 4)
    source = make(b"a,b\r\n1,2\r\n3,4\r\n")
    assert list(source.starts) == [0, 5, 10]


def test_a_byte_order_mark_is_not_in_the_first_cell(make):
    source = make(b"\xef\xbb\xbfname,n\nx,1\n")
    assert source.dialect.encoding == "utf-8-sig"
    assert source.titles() == ["name", "n"]


def test_the_delimiter_and_header_are_guessed():
    assert guess(b"a;b;c\n1;2;3\n4;5;6\n").delimiter == ";"
    assert guess(b"a,b\n1,2\n", "x.tsv").delimiter == "\t"
    assert guess("name,n\n\xe9t\xe9,1\n".encode("cp1252")).encoding == "cp1252"
    assert guess(b"name,age\nann,31\nbob,42\n").header


def test_rows_read_again_after_leaving_the_cache(make, monkeypatch):
    from navigator.lib.viewer import table

    monkeypatch.setattr(table, "CACHED_ROWS", 2)
    source = make(b"".join(b"%d,x\n" % n for n in range(10)), dialect=Dialect(header=False))
    assert [source.row(n)[0] for n in (0, 5, 9, 0)] == ["0", "5", "9", "0"]


def test_column_letters_and_numbers():
    assert [column_name(n) for n in (0, 25, 26, 27, 701, 702)] == ["A", "Z", "AA", "AB", "ZZ", "AAA"]
    assert [number(t) for t in ("12", "-3.5", "1e3", "1,234.5", "nan", "", "1,2")] == [
        12.0, -3.5, 1000.0, 1234.5, None, None, None]


def test_a_csv_as_the_database_window_reads_it(make):
    table = CSVTable(make(CITIES))
    assert [(f.name, f.kind, f.width) for f in table.fields] == [("id", "N", 3), ("city", "C", 9), ("pop", "N", 7)]
    row = table.record(1)
    assert table.shown(row, table.fields[1]) == "Lon don" and table.memo(row, table.fields[1]) == "Lon\r\ndon"
    assert table.shown(table.record(2), table.fields[2]) == "      5"
    assert table.flag(row) == " " and not table.editable


def test_a_csv_without_a_header_names_its_columns_by_letter(make):
    table = CSVTable(make(b"1,2\n3,4\n", dialect=Dialect(header=False)))
    assert [f.name for f in table.fields] == ["A", "B"] and table.count == 2


def test_a_column_of_numbers_sorts_as_numbers_blanks_last(make):
    table = CSVTable(make(b"n\n10\n9\n\n100\n"))
    field = table.fields[0]
    assert list(sort_order(table, field, False)) == [1, 0, 3, 2]
    assert list(sort_order(table, field, True)) == [3, 0, 1, 2]


def test_text_sorts_case_aside_and_the_view_reads_through_the_order(make):
    table = CSVTable(make(b"name\nbob\nAnn\ncarl\n"))
    order = sort_order(table, table.fields[0], False)
    view = SortedView(table, order, 0, False)
    assert [view.record(n)[0] for n in range(view.count)] == ["Ann", "bob", "carl"]
    assert view.source_index(0) == 1 and view.fields is table.fields


def test_a_stopped_sort_says_nothing(make):
    work = Work()
    work.stop()
    table = CSVTable(make(CITIES))
    assert sort_order(table, table.fields[1], False, work) is None


def test_a_big_file_has_rows_before_its_walk_ends(tmp_path):
    path = tmp_path / "big.csv"
    path.write_bytes(b"n,square\n" + b"".join(b"%d,%d\n" % (n, n * n) for n in range(200_000)))
    source = TableSource(path)
    source.start()
    deadline = time.monotonic() + 5
    while source.records < 2 and time.monotonic() < deadline:
        time.sleep(0.001)
    assert source.row(0) == ["0", "0"]
    source.wait()
    assert source.complete and source.count == 200_000 and source.row(199_999) == ["199999", str(199_999 ** 2)]
    assert source.row_at(source.row_offset(1234)) == 1234
    source.close()


# -- the window -----------------------------------------------------------------------


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "zz.csv").write_bytes(CITIES)
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def db_window(app):
    from navigator.widgets.viewer.db_window import DBWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, DBWindow) else None


def file_window(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, FileWindow) else None


def opened():
    # A panel on another drive lists on a thread from the start: End once it is in.
    return [LISTED, KeyEvent("end"), KeyEvent("f3"), Until(lambda a: db_window(a) is not None)]


def screen(app) -> list[str]:
    buffer = ScreenBuffer(80, 24)
    app.shell.layout(80, 24)
    settle()
    app.shell.render_tree(buffer)
    return ["".join(buffer.get(x, y)[0] or " " for x in range(80)) for y in range(24)]


def test_f3_on_a_csv_opens_the_database_window(files):
    app = navigator(files)
    seen = {}
    run_app(app, [*opened(), KeyEvent("down"),
                  lambda a: seen.update(rows=screen(a), window=db_window(a))])
    window = seen["window"]
    assert window.zoomed and window.title == str(files / "zz.csv") and window.csv is not None
    assert window.list_name() == f"Spreadsheet - {files / 'zz.csv'}"
    rows = seen["rows"]
    assert rows[2].split() == ["║", "id", "city", "pop", "║"]
    assert "Lon don" in rows[4] and "Paris, FR" in rows[3]
    assert window.indicator.text.startswith("2/4")


def test_f2_f3_and_f4_on_a_csv(files):
    from navigator.widgets.viewer.commands import EditDbField

    app = navigator(files)
    seen = {}
    run_app(app, [
        *opened(), KeyEvent("down"), KeyEvent("right"),
        lambda a: seen.update(f4=db_window(a).refusal(EditDbField())),
        KeyEvent("f3"), Until(lambda a: a.modal is not None),
        lambda a: seen.update(memo=a.modal.viewer.source.read(0, a.modal.viewer.size),
                              encoding=a.modal.viewer.encoding),
        KeyEvent("escape"), Until(lambda a: a.modal is None),
        KeyEvent("f2"), Until(lambda a: a.modal is not None),
        lambda a: seen.update(fields="\n".join(a.modal.lines.items)),
    ])
    assert seen["f4"] == "The database is opened read-only"
    assert seen["memo"] == b"Lon\r\ndon" and seen["encoding"] == "utf-8"
    assert "city" in seen["fields"] and "Comma" in seen["fields"] and "4 rows" in seen["fields"]


def test_f8_sorts_the_view_and_round_again(files):
    app = navigator(files)
    seen = []

    def firsts(a):
        db = db_window(a).db
        seen.append([db.record(n)[0] for n in range(db.count)])

    run_app(app, [
        *opened(), KeyEvent("right"), KeyEvent("right"),
        KeyEvent("f8"), Until(lambda a: getattr(db_window(a).db, "sort", None) == (2, False)), firsts,
        KeyEvent("f8"), Until(lambda a: getattr(db_window(a).db, "sort", None) == (2, True)), firsts,
        KeyEvent("f8"), Until(lambda a: getattr(db_window(a).db, "sort", None) is None), firsts,
    ])
    assert seen == [["3", "1", "2", "4"], ["2", "1", "3", "4"], ["1", "2", "3", "4"]]
    assert (files / "zz.csv").read_bytes() == CITIES


def test_f7_searches_a_csv(files):
    app = navigator(files)
    seen = {}
    run_app(app, [
        *opened(),
        KeyEvent("f7"), Until(lambda a: a.modal is not None), *[KeyEvent(c, c) for c in "say"],
        KeyEvent("tab"), KeyEvent("tab"), KeyEvent("down"), KeyEvent("enter"),
        Until(lambda a: a.modal is None and db_window(a).viewer.record == 2),
        lambda a: seen.update(field=db_window(a).viewer.field),
    ])
    assert seen["field"] == 1


def test_the_column_width_mode_and_ctrl_arrows(files):
    from navigator.widgets.viewer.commands import ChangeWidth

    app = navigator(files)
    seen = []
    run_app(app, [
        *opened(), KeyEvent("right", ctrl=True),
        lambda a: seen.append(db_window(a).viewer.width_of(0)),
        lambda a: a.spawn(a.run_command(ChangeWidth)), Until(lambda a: db_window(a).viewer.resizing),
        KeyEvent("left"), KeyEvent("left"), KeyEvent("enter"),
        lambda a: seen.append((db_window(a).viewer.width_of(0), db_window(a).viewer.resizing)),
    ])
    assert seen == [4, (2, False)]


def test_format_reads_the_file_again(files):
    (files / "zz.csv").write_bytes(b"a;b\n1;2\n")
    app = navigator(files)
    seen = []
    run_app(app, [
        *opened(),
        lambda a: seen.append(db_window(a).csv.dialect.delimiter),
        KeyEvent("f6", shift=True), Until(lambda a: a.modal is not None),
        lambda a: a.modal.delimiter.__setattr__("value", 0),
        KeyEvent("enter"), Until(lambda a: db_window(a).csv.dialect.delimiter == ","),
        lambda a: seen.append(db_window(a).db.record(0)),
    ])
    assert seen == [";", ["1;2"]]


def test_shift_f3_goes_to_the_text_and_back(files):
    data = b"n,square\n" + b"".join(b"%d,%d\n" % (n, n * n) for n in range(100))
    (files / "zz.csv").write_bytes(data)
    app = navigator(files)
    seen = {}
    run_app(app, [
        *opened(), *[KeyEvent("down")] * 10,
        KeyEvent("f3", shift=True), Until(lambda a: file_window(a) is not None),
        lambda a: seen.update(top=file_window(a).viewer.top),
        KeyEvent("f3", shift=True),
        # Moved to its row, then the text window closed.
        Until(lambda a: db_window(a) is not None and len(a.shell.desktop.windows()) == 2),
        lambda a: seen.update(row=db_window(a).viewer.record),
    ])
    assert seen["top"] == data.index(b"\n10,") + 1
    assert seen["row"] == 10
    assert len(app.shell.desktop.windows()) == 2  # the manager and the table


def test_f8_sorts_a_sqlite_table_too(tmp_path, monkeypatch):
    import sqlite3

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    connection = sqlite3.connect(tmp_path / "zz.sqlite")
    connection.execute("CREATE TABLE t(n INTEGER)")
    connection.executemany("INSERT INTO t VALUES (?)", [(3,), (1,), (2,)])
    connection.commit()
    connection.close()
    app = navigator(tmp_path)
    seen = []
    run_app(app, [*opened(), KeyEvent("f8"), Until(lambda a: getattr(db_window(a).db, "sort", None) == (0, False)),
                  lambda a: seen.extend(db_window(a).db.record(n)[0] for n in range(3))])
    assert seen == [1, 2, 3]


def test_as_spreadsheet_on_any_file(files):
    from navigator.widgets.manager.commands import ViewAsSpreadsheet

    (files / "zz.csv").unlink()
    (files / "zz.txt").write_bytes(b"one\ttwo\n")
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), lambda a: a.spawn(a.run_command(ViewAsSpreadsheet)),
                  Until(lambda a: db_window(a) is not None),
                  lambda a: seen.update(fields=[f.name for f in db_window(a).db.fields])])
    assert len(seen["fields"]) == 2


def test_a_csv_on_another_drive(files):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = mount(MemoryDrive("sheet"))
    try:
        drive.make("/zz.csv", CITIES)
        app = Navigator(drive.location("/"), files, terminal=FakeTerminal(80, 24))
        seen = {}
        run_app(app, [*opened(), lambda a: seen.update(title=db_window(a).title,
                                                       use=db_window(a).use_set is not None)])
        assert seen == {"title": str(drive.location("/zz.csv")), "use": True}
    finally:
        unmount(drive.site)
