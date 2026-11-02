"""F3 on a CSV: DOS Navigator's spreadsheet window (``TCalcWindow``), view-only --
the model in ``navigator/lib/viewer/table.py`` and the window around it."""

from __future__ import annotations

import time

import pytest

from conftest import FakeTerminal, Until, run_app, settle
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.viewer.table import (
    CellSearch,
    Dialect,
    TableSource,
    Work,
    cell_name,
    column_name,
    find,
    guess,
    number,
    parse_cell,
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


def test_widths_come_from_the_titles_and_rows(make):
    source = make(CITIES)
    source.measure()
    assert source.columns == 3 and source.widths == [3, 9, 7]


def test_cell_names_are_dns():
    assert [column_name(n) for n in (0, 25, 26, 27, 701, 702)] == ["A", "Z", "AA", "AB", "ZZ", "AAA"]
    assert cell_name(1, 2) == "B3"
    assert parse_cell("b12") == (1, 11) and parse_cell(" 7 ") == (None, 6) and parse_cell("C") == (2, None)
    assert parse_cell("12B") is None and parse_cell("") is None and parse_cell("A0") is None


def test_numbers():
    assert [number(t) for t in ("12", "-3.5", "1e3", "1,234.5", "nan", "", "1,2")] == [
        12.0, -3.5, 1000.0, 1234.5, None, None, None]


def test_a_column_of_numbers_sorts_as_numbers_blanks_last(make):
    source = make(b"n\n10\n9\n\n100\n")
    assert list(sort_order(source, 0, False)) == [1, 0, 3, 2]
    assert list(sort_order(source, 0, True)) == [3, 0, 1, 2]


def test_text_sorts_case_aside(make):
    source = make(b"name\nbob\nAnn\ncarl\n")
    assert list(sort_order(source, 0, False)) == [1, 0, 2]


def test_a_stopped_sort_says_nothing(make):
    work = Work()
    work.stop()
    assert sort_order(make(CITIES), 1, False, work) is None


def test_find_as_string_and_value(make):
    source = make(CITIES)
    assert find(source, CellSearch("LON"), order=None, row=-1, column=0) == (1, 1)
    assert find(source, CellSearch("LON", case=True), order=None, row=-1, column=0) is None
    assert find(source, CellSearch("5", as_value=True), order=None, row=-1, column=0) == (2, 2)
    assert find(source, CellSearch("say", whole=True), order=None, row=-1, column=0) == (2, 1)
    assert find(source, CellSearch("sa", whole=True), order=None, row=-1, column=0) is None


def test_find_goes_on_from_the_cell_and_back(make):
    source = make(b"a,b\nx,x\nx,y\n", dialect=Dialect())
    search = CellSearch("x")
    assert find(source, search, order=None, row=0, column=0) == (0, 1)
    assert find(source, search, order=None, row=0, column=1) == (1, 0)
    assert find(source, search, order=None, row=1, column=0, backward=True) == (0, 1)


def test_find_follows_the_order_shown(make):
    source = make(b"n\nb\na\n")
    order = sort_order(source, 0, False)
    assert find(source, CellSearch("b"), order=order, row=-1, column=0) == (1, 0)


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


def sheet_window(app):
    from navigator.widgets.viewer.sheet_window import SheetWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, SheetWindow) else None


def file_window(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, FileWindow) else None


def opened():
    return [KeyEvent("end"), KeyEvent("f3"), Until(lambda a: sheet_window(a) is not None)]


def keys(text: str) -> list[KeyEvent]:
    return [KeyEvent(c.lower(), c, shift=c.isupper()) for c in text]


def screen(app) -> list[str]:
    buffer = ScreenBuffer(80, 24)
    app.shell.layout(80, 24)
    settle()
    app.shell.render_tree(buffer)
    return ["".join(buffer.get(x, y)[0] or " " for x in range(80)) for y in range(24)]


def test_f3_on_a_csv_opens_the_spreadsheet(files):
    app = navigator(files)
    seen = {}
    run_app(app, [*opened(), KeyEvent("right"), KeyEvent("down"),
                  lambda a: seen.update(rows=screen(a), window=sheet_window(a))])
    window = seen["window"]
    assert window.zoomed and window.title == str(files / "zz.csv")
    assert window.list_name() == f"Spreadsheet - {files / 'zz.csv'}"
    text = "\n".join(seen["rows"])
    assert "B2" in text and "Lon don" in text and "Lon\r" not in text
    assert "city" in text and "Paris, FR" in text
    assert window.indicator.text.startswith("2/4")


def test_home_end_and_goto(files):
    app = navigator(files)
    seen = []
    run_app(app, [
        *opened(),
        KeyEvent("end"), lambda a: seen.append((sheet_window(a).sheet.col, sheet_window(a).sheet.row)),
        KeyEvent("home"), lambda a: seen.append((sheet_window(a).sheet.col, sheet_window(a).sheet.row)),
        KeyEvent("f6"), Until(lambda a: a.modal is not None), *keys("B3"), KeyEvent("enter"),
        Until(lambda a: a.modal is None),
        lambda a: seen.append((sheet_window(a).sheet.col, sheet_window(a).sheet.row)),
    ])
    assert seen == [(2, 3), (0, 0), (1, 2)]


def test_find_and_search_again(files):
    app = navigator(files)
    seen = []
    run_app(app, [
        *opened(),
        KeyEvent("f7"), Until(lambda a: a.modal is not None), *keys("0"), KeyEvent("enter"),
        Until(lambda a: a.modal is None and sheet_window(a).sheet.row == 0 and sheet_window(a).sheet.col == 2),
        lambda a: seen.append((sheet_window(a).sheet.col, sheet_window(a).sheet.row)),
        KeyEvent("f7", shift=True), Until(lambda a: sheet_window(a).sheet.row == 1),
        lambda a: seen.append((sheet_window(a).sheet.col, sheet_window(a).sheet.row)),
    ])
    assert seen == [(2, 0), (2, 1)]


def test_f5_sorts_the_view_and_round_again(files):
    app = navigator(files)
    seen = []

    def firsts(a):
        sheet = sheet_window(a).sheet
        seen.append([sheet.cells(n)[0] for n in range(sheet.count)])

    run_app(app, [
        *opened(), KeyEvent("right"), KeyEvent("right"),
        KeyEvent("f5"), Until(lambda a: sheet_window(a).sheet.sort == (2, False)), firsts,
        KeyEvent("f5"), Until(lambda a: sheet_window(a).sheet.sort == (2, True)), firsts,
        KeyEvent("f5"), Until(lambda a: sheet_window(a).sheet.sort is None), firsts,
    ])
    assert seen == [["3", "1", "2", "4"], ["2", "1", "3", "4"], ["1", "2", "3", "4"]]
    assert (files / "zz.csv").read_bytes() == CITIES


def test_format_reads_the_file_again(files):
    (files / "zz.csv").write_bytes(b"a;b\n1;2\n")
    app = navigator(files)
    seen = []
    run_app(app, [
        *opened(),
        lambda a: seen.append(sheet_window(a).source.dialect.delimiter),
        KeyEvent("f6", shift=True), Until(lambda a: a.modal is not None),
        lambda a: a.modal.delimiter.__setattr__("value", 0),
        KeyEvent("enter"), Until(lambda a: sheet_window(a).source.dialect.delimiter == ","),
        lambda a: seen.append(sheet_window(a).sheet.cells(0)),
    ])
    assert seen == [";", ["1;2"]]


def test_shift_f4_goes_to_the_text_and_back(files):
    data = b"n,square\n" + b"".join(b"%d,%d\n" % (n, n * n) for n in range(100))
    (files / "zz.csv").write_bytes(data)
    app = navigator(files)
    seen = {}
    run_app(app, [
        *opened(), *[KeyEvent("down")] * 10,
        KeyEvent("f4", shift=True), Until(lambda a: file_window(a) is not None),
        lambda a: seen.update(top=file_window(a).viewer.top),
        KeyEvent("f4", shift=True), Until(lambda a: sheet_window(a) is not None),
        lambda a: seen.update(row=sheet_window(a).sheet.row),
    ])
    assert seen["top"] == data.index(b"\n10,") + 1
    assert seen["row"] == 10
    assert len(app.shell.desktop.windows()) == 2  # the manager and the sheet


def test_as_spreadsheet_on_any_file(files):
    from navigator.widgets.manager.commands import ViewAsSpreadsheet

    (files / "zz.csv").unlink()
    (files / "zz.txt").write_bytes(b"one\ttwo\n")
    app = navigator(files)
    seen = {}
    run_app(app, [KeyEvent("end"), lambda a: a.spawn(a.run_command(ViewAsSpreadsheet)), Until(lambda a: sheet_window(a) is not None),
                  lambda a: seen.update(cells=sheet_window(a).sheet.cells(0) or sheet_window(a).source.titles())])
    assert seen["cells"] == ["one", "two"]


def test_a_csv_on_another_drive(files, monkeypatch):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = mount(MemoryDrive("sheet"))
    try:
        drive.make("/zz.csv", CITIES)
        app = Navigator(drive.location("/"), files, terminal=FakeTerminal(80, 24))
        seen = {}
        run_app(app, [*opened(), lambda a: seen.update(title=sheet_window(a).title,
                                                       use=sheet_window(a).use_set is not None)])
        assert seen == {"title": str(drive.location("/zz.csv")), "use": True}
    finally:
        unmount(drive.site)
