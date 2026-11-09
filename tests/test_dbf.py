"""File > View > As DataBase, and F3 on a ``.dbf``: DOS Navigator's dBase
viewer (DBVIEW.PAS, DBWATCH.PAS)."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.lib.viewer import dbf
from navigator.__main__ import Navigator
from navigator.widgets.manager.commands import ViewAsDataBase
from navigator.widgets.viewer.db_list_dialog import DBListDialog
from navigator.widgets.viewer.db_window import DBWindow
from navigator.widgets.viewer.file_window import FileWindow
from navigator.widgets.viewer.memo_dialog import MemoDialog

FIELDS = (("NAME", "C", 10, 0), ("AGE", "N", 3, 0), ("BORN", "D", 8, 0), ("OK", "L", 1, 0),
          ("NOTES", "M", 10, 0))
ROWS = (("Ann", "34", "19900102", "T", "1"), ("Bob", "7", "20170311", "F", "0"), ("Cid", "61", "", "T", "0"))


def write_dbf(path: Path, rows=ROWS, fields=FIELDS, *, codec: str = "ascii", driver: int = 0,
              memo: bytes = b"Hello\r\nmemo") -> Path:
    """A dBase III file of *rows* in *codec*, its language-driver byte
    *driver*, and a ``.dbt`` with *memo* in block 1."""
    record_length = 1 + sum(f[2] for f in fields)
    header_length = 32 + 32 * len(fields) + 1
    data = bytearray(struct.pack("<BBBBIHH", 3, 126, 1, 1, len(rows), header_length, record_length) + bytes(20))
    data[29] = driver
    for name, kind, length, decimals in fields:
        data += name.encode(codec).ljust(11, b"\0") + kind.encode() + bytes(4) + bytes((length, decimals)) + bytes(14)
    data += b"\r"
    for index, row in enumerate(rows):
        data += b"*" if index == 1 else b" "
        for (name, kind, length, _), value in zip(fields, row):
            data += (value.rjust(length) if kind in "NM" else value.ljust(length)).encode(codec)[:length]
    data += b"\x1a"
    path.write_bytes(bytes(data))
    path.with_suffix(".dbt").write_bytes(bytes(512) + (memo + b"\x1a").ljust(512, b"\0"))
    return path


def test_the_header_fields_and_records_read_as_dn_read_them(tmp_path):
    db = dbf.DBFile(write_dbf(tmp_path / "people.dbf"))
    assert db.count == 3 and [f.name for f in db.fields] == ["NAME", "AGE", "BORN", "OK", "NOTES"]
    assert db.fields[1].offset == 11 and db.fields[2].width == dbf.DATE_WIDTH
    first, second = db.record(0), db.record(1)
    assert db.shown(first, db.fields[0]) == "Ann       " and db.shown(first, db.fields[2]) == "02-01-1990"
    assert db.shown(first, db.fields[4]) == "  Memo  " and db.shown(second, db.fields[4]) == "  memo  "
    assert second[:1] == b"*" and db.record(3) is None
    assert db.memo(first, db.fields[4]) == "Hello\r\nmemo"
    assert db.memo(second, db.fields[4]) is None


def test_a_file_that_does_not_add_up_is_refused(tmp_path):
    path = write_dbf(tmp_path / "bad.dbf")
    raw = bytearray(path.read_bytes())
    raw[10] = 99  # the record length
    path.write_bytes(bytes(raw))
    with pytest.raises(dbf.DBFError):
        dbf.DBFile(path)
    (tmp_path / "text.dbf").write_text("just text")
    with pytest.raises(dbf.DBFError):
        dbf.DBFile(tmp_path / "text.dbf")


def test_search_and_the_values_typed_back(tmp_path):
    db = dbf.DBFile(write_dbf(tmp_path / "people.dbf"))
    assert dbf.find(db, "bob", case=False, all_fields=False, backward=False, record=-1, field=0) == (1, 0)
    assert dbf.find(db, "bob", case=True, all_fields=False, backward=False, record=-1, field=0) is None
    assert dbf.find(db, "61", case=False, all_fields=True, backward=False, record=0, field=0) == (2, 1)
    assert dbf.find(db, "Ann", case=False, all_fields=False, backward=True, record=2, field=0) == (0, 0)
    assert dbf.date_stored("3-4-2024") == "20240403" and dbf.date_stored("x") is None
    assert dbf.number_stored("42", db.fields[1]) == " 42" and dbf.number_stored("12345", db.fields[1]) is None
    db.write_field(2, db.fields[0], "Dee")
    assert dbf.DBFile(db.path).shown(db.record(2), db.fields[0]) == "Dee       "


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    write_dbf(tmp_path / "people.dbf")
    (tmp_path / "fake.dbf").write_text("not a database\n")
    write_dbf(tmp_path / "empty.dbf", rows=())
    return tmp_path


def on(name: str):
    def action(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def memo_of(app) -> bytes:
    """The bytes *Memo view*'s viewer holds."""
    source = app.modal.viewer.source
    return source.read(0, source.size)


def window_of(app):
    return app.shell.desktop.active_window


def test_f3_on_a_dbf_opens_the_dbase_viewer_and_its_keys_move_the_cell(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  KeyEvent("down"), KeyEvent("right"), KeyEvent("enter"),
                  lambda a: seen.update(cell=(window_of(a).viewer.record, window_of(a).viewer.field),
                                        indicator=window_of(a).indicator.text,
                                        title=window_of(a).list_name()),
                  KeyEvent("pagedown", ctrl=True), lambda a: seen.update(last=window_of(a).viewer.record),
                  KeyEvent("f2"), Until(lambda a: isinstance(a.modal, DBListDialog)),
                  lambda a: seen.update(fields=list(a.modal.lines.items), what=a.modal.title),
                  KeyEvent("enter"), Until(lambda a: a.modal is None),
                  KeyEvent("pageup", ctrl=True), KeyEvent("end"), KeyEvent("f3"),
                  Until(lambda a: isinstance(a.modal, MemoDialog)),
                  lambda a: seen.update(memo=memo_of(a))])
    assert seen["cell"] == (1, 2) and seen["indicator"] == "2/3" and seen["last"] == 2
    assert seen["title"].startswith("dBase View - ")
    assert seen["what"] == "Structure of people.dbf"
    assert seen["fields"][1] == " \u200eAGE         \u200eNumeric      \u200e3          \u200e0"  # held left to right
    assert seen["memo"] == b"Hello\r\nmemo"


def test_f4_edits_a_character_field_in_the_file(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))

    def type_it(a):
        a.modal.line.value = "Zed"

    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  KeyEvent("f4"), Until(lambda a: getattr(a.modal, "title", "") == "Edit field"), type_it,
                  KeyEvent("enter"), Until(lambda a: a.modal is None)])
    db = dbf.DBFile(place / "people.dbf")
    assert db.shown(db.record(0), db.fields[0]) == "Zed       "


def test_a_dbf_that_is_not_one_is_viewed_as_text_and_as_database_says_so(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [on("fake.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), FileWindow)),
                  KeyEvent("escape"), lambda a: None, lambda a: a.spawn(a.run_command(ViewAsDataBase)),
                  Until(lambda a: getattr(a.modal, "title", "") == "Cannot view file"),
                  lambda a: seen.update(prompt=a.modal.prompt)])
    assert seen["prompt"] == "fake.dbf: not a dBase or SQLite file"


def test_an_empty_database_shows_its_structure_and_opens_no_window(place):
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [on("empty.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(a.modal, DBListDialog)),
                  lambda a: seen.update(title=a.modal.title), KeyEvent("enter"), Until(lambda a: a.modal is None),
                  lambda a: seen.update(window=type(window_of(a)).__name__)])
    assert seen["title"] == "Empty database empty.dbf" and seen["window"] == "Manager"


def test_the_view_menu_joins_the_bar_shows_the_keys_and_greys_memo_off_a_memo(place):
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def look(name):
        def action(a):
            window = window_of(a)
            menu = window.view_menu
            seen[name] = {caption: (key_caption(menu.entry(caption), a, a.focused),
                                    a.command_enabled(menu.entry(caption).command, a.focused))
                          for caption in ("Fields...", "Memo view", "Edit field...", "Search...")}
            seen["bar"] = [str(e.text).replace("~", "") for e in a.shell.menu.entries()]
        return action

    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  look("name"), KeyEvent("end"), look("memo"),
                  KeyEvent("v", "v", alt=True), KeyEvent("f", "f"), Until(lambda a: isinstance(a.modal, DBListDialog)),
                  lambda a: seen.update(fields=a.modal.title)])
    assert "View" in seen["bar"]
    assert seen["name"] == {"Fields...": ("F2", True), "Memo view": ("F3", False),
                            "Edit field...": ("F4", True), "Search...": ("F7", True)}
    assert seen["memo"]["Memo view"] == ("F3", True)
    assert seen["fields"] == "Structure of people.dbf"


def test_a_right_click_on_a_memo_cell_moves_there_and_offers_memo_view(place):
    from navkit.events import MouseClickEvent
    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.menu.popup_menu import PopupMenu

    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def popup(a):
        return next((c for c in a.root.children if isinstance(c, PopupMenu)), None)

    def click_memo(a):
        viewer = window_of(a).viewer
        x = 1 + sum(viewer.db.fields[i].width + 1 for i in range(4))
        ox, oy = viewer.offset()
        a.post_event(MouseClickEvent(x=ox + viewer.x + x, y=oy + viewer.y + 1, button="right", action="press"))

    def look(a):
        box = popup(a).box
        seen["enabled"] = {parse_shortcut(e.text)[0]: box.enabled(e)
                           for e in box.entries() if hasattr(e, "command")}
        seen["cell"] = (window_of(a).viewer.field, window_of(a).viewer.record)

    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  click_memo, Until(lambda a: popup(a) is not None), look,
                  KeyEvent("m", "m"), Until(lambda a: isinstance(a.modal, MemoDialog)),
                  lambda a: seen.update(memo=memo_of(a))])
    assert seen["cell"] == (4, 0)
    assert list(seen["enabled"]) == ["Fields...", "Memo view", "Edit field...", "Sort by column",
                                     "Search...", "Search again", "Close"]
    assert seen["enabled"]["Memo view"]
    assert seen["memo"] == b"Hello\r\nmemo"


# -- F4 on each kind of field ---------------------------------------------------------------------


def edit_cell(place, field, typed=None, *, wait_box=True):
    """F4 on record 0's *field*-th cell, *typed* into the box when one comes up."""
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))

    def to_field(a):
        window_of(a).viewer.field = field

    def type_it(a):
        a.modal.line.value = typed

    steps = [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)), to_field,
             KeyEvent("f4")]
    if wait_box:
        steps += [Until(lambda a: getattr(a.modal, "title", "") == "Edit field"), type_it, KeyEvent("enter"),
                  Until(lambda a: a.modal is None)]
    else:
        steps += [lambda a: None]
    run_app(app, steps)
    db = dbf.DBFile(place / "people.dbf")
    return db.raw(db.record(0), db.fields[field])


def test_f4_on_a_logical_field_flips_it_unasked(place):
    assert edit_cell(place, 3, wait_box=False) == "F"   # was T


def test_f4_on_a_date_takes_it_day_first_and_stores_it_year_first(place):
    assert edit_cell(place, 2, "25-12-2001") == "20011225"


def test_f4_on_a_number_stores_it_right_aligned(place):
    assert edit_cell(place, 1, "5") == "  5"


def test_f4_leaves_a_memo_as_it_is(place):
    assert edit_cell(place, 4, wait_box=False) == "         1"


def test_f4_on_a_read_only_file_says_it_is_write_protected(place, monkeypatch):
    import os

    from navigator.settings import SETTINGS

    if os.geteuid() == 0:
        pytest.skip("root is refused nothing")
    monkeypatch.setattr(SETTINGS.system, "elevate", "off")
    os.chmod(place / "people.dbf", 0o444)
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}
    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  KeyEvent("f4"), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(said=a.modal.prompt), KeyEvent("enter")])
    os.chmod(place / "people.dbf", 0o644)
    assert seen["said"] == "Could not edit field - file is write-protected"


# -- the indicator, F4's limits and refusals, a memo's width ---------------------------------


def test_the_indicator_prints_both_numbers_plain(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    rows = tuple((f"n{i}", str(i % 999), "", "T", "0") for i in range(1234))
    write_dbf(tmp_path / "many.dbf", rows=rows)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))

    def to_1000(a):
        window_of(a).viewer.go(record=999)

    seen = {}
    run_app(app, [on("many.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  to_1000, lambda a: None, lambda a: seen.update(text=window_of(a).indicator.text)])
    assert seen["text"] == "1000/1234"


def refused(place, field, typed):
    """F4 on record 0's *field*-th cell with *typed*: what the box after says,
    and the cell as it is in the file afterwards."""
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def to_field(a):
        window_of(a).viewer.field = field

    def type_it(a):
        seen["limit"] = a.modal.line.entry.max_length
        a.modal.line.value = typed

    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  to_field, KeyEvent("f4"), Until(lambda a: getattr(a.modal, "title", "") == "Edit field"),
                  type_it, KeyEvent("enter"), Until(lambda a: getattr(a.modal, "title", "") == "Error"),
                  lambda a: seen.update(said=a.modal.prompt), KeyEvent("enter"), Until(lambda a: a.modal is None)])
    db = dbf.DBFile(place / "people.dbf")
    return seen, db.raw(db.record(0), db.fields[field])


def test_f4_says_a_number_is_not_one_and_leaves_the_cell(place):
    seen, cell = refused(place, 1, "abc")
    assert seen == {"limit": 3, "said": "Not a number"} and cell == " 34"


def test_f4_says_a_number_does_not_fit(place):
    # Three characters, a number, and a billion in a field three wide.
    seen, cell = refused(place, 1, "1e9")
    assert seen == {"limit": 3, "said": "The number does not fit the field"} and cell == " 34"


def test_f4_says_a_date_is_not_one(place):
    seen, cell = refused(place, 2, "32-13-2020")
    assert seen == {"limit": 10, "said": "Not a date"} and cell == "19900102"


def test_f4_caps_a_character_field_at_its_length(place):
    from navigator.widgets.shell.edit_line_dialog import EditLineDialog

    box = EditLineDialog("abcdefghijkl", max_length=10)
    assert box.line.value == "abcdefghij" and box.line.entry.max_length == 10


def test_a_memo_column_is_as_wide_as_its_field():
    assert dbf.Field("NOTES", "M", 10, 0, 0).width == 10
    assert dbf.Field("N", "M", 4, 0, 0).width == 4


def test_the_indicator_is_the_passive_frames_colour_while_another_window_is_active(place):
    from navigator.lib.appearance import scheme

    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def look(name):
        def step(a):
            window = next(w for w in a.shell.desktop.windows() if isinstance(w, DBWindow))
            seen[name] = (window.indicator.style, window.style)
        return step

    def other(a):
        window = next(w for w in a.shell.desktop.windows() if not isinstance(w, DBWindow))
        a.shell.desktop.activate(window)

    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  look("active"), other, lambda a: None, look("passive")])
    assert seen["active"][0] == seen["active"][1]
    assert seen["passive"][0] == seen["passive"][1]
    assert seen["active"][0] != seen["passive"][0]


def test_holding_the_right_quarter_moves_on_field_by_field(place, monkeypatch):
    """DBVIEW.PAS's ``evMouseDown`` loop on ``evMouseMove+evMouseAuto``: held,
    the quarter steps again on every tick, until the release."""
    from navkit.events import MouseClickEvent

    monkeypatch.setattr("navkit.application.REPEAT_DELAY", 0.02)
    monkeypatch.setattr("navkit.application.REPEAT_EVERY", 0.005)
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def hold(a):
        viewer = seen["viewer"] = window_of(a).viewer
        ox, oy = viewer.offset()
        a.post_event(MouseClickEvent(x=ox + viewer.x + viewer.width - 2, y=oy + viewer.y + 2,
                                     button="left", action="press"))

    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  hold, Until(lambda a: seen["viewer"].field == len(seen["viewer"].db.fields) - 1),
                  MouseClickEvent(x=0, y=0, button="none", action="release"),
                  lambda a: seen.update(capture=a.mouse_capture)])
    assert seen["capture"] is None


# -- Memo view: DN's memo file names, and the memo in a viewer ---------------------------------


def write_fpt(path: Path, memo: bytes, block_size: int = 64, block: int = 1) -> Path:
    """A FoxPro memo file with *memo* in *block*: the block size big-endian at
    offset 4, and a type and a big-endian length before the text."""
    header = struct.pack(">IHH", block + 1, 0, block_size).ljust(block * block_size, b"\0")
    path.write_bytes(header + struct.pack(">II", 1, len(memo)) + memo)
    return path


@pytest.mark.parametrize("table, names", [
    ("a.dbf", ["a.fpt", "a.FPT", "a.dbt", "a.DBT"]),
    ("a.scx", ["a.sct", "a.SCT", "a.dbt", "a.DBT"]),
    ("a.FRX", ["a.FRT", "a.frt", "a.DBT", "a.dbt"]),
    ("a.db", ["a.fpt", "a.FPT", "a.dbt", "a.DBT"]),
])
def test_the_memo_file_is_looked_for_where_dn_looked(table, names):
    assert [p.name for p in dbf.memo_files(Path(table))] == names


def test_a_foxpro_memo_is_read_from_its_own_file_before_the_dbt(tmp_path):
    db = dbf.DBFile(write_dbf(tmp_path / "people.dbf"))
    first = db.record(0)
    assert db.memo_data(first, db.fields[4]) == b"Hello\r\nmemo"           # the .dbt, dBase III's way
    write_fpt(tmp_path / "people.fpt", b"From the \xfapt")
    assert db.memo_data(first, db.fields[4]) == b"From the \xfapt"         # the .fpt wins
    assert db.memo(first, db.fields[4]) == "From the ·pt"                   # decoded in CP437


def test_a_screen_files_memo_is_in_its_sct(tmp_path):
    table = write_dbf(tmp_path / "form.dbf")
    screen = table.rename(tmp_path / "form.scx")
    (tmp_path / "form.dbt").unlink()
    write_fpt(tmp_path / "form.sct", b"on the screen")
    db = dbf.DBFile(screen)
    assert db.memo_data(db.record(0), db.fields[4]) == b"on the screen"
    (tmp_path / "form.sct").unlink()
    with pytest.raises(FileNotFoundError):
        db.memo_data(db.record(0), db.fields[4])


def test_a_memory_source_reads_and_finds_as_a_file_does():
    import re

    from navigator.lib.viewer import MemorySource

    source = MemorySource(b"first line\nsecond line\n", "x.memo")
    assert source.size == 23 and source.read(6, 4) == b"line" and source.peek(0) == ord("f")
    assert not source.editable
    assert source.find(re.compile(rb"second"), 0, backward=False, span=6) == (11, 6)


def test_memo_view_is_the_memo_in_a_viewer_with_the_viewers_keys(place, monkeypatch):
    import navigator.lib.viewer as viewer_model
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

    monkeypatch.setattr(viewer_model, "last_search", None)
    long = b"word " * 30 + b"needle at the end"
    write_fpt(place / "people.fpt", long + b"\r\nsecond line")
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        box = a.modal
        viewer = box.viewer
        seen.update(size=(box.width, box.height), title=box.title, wrap=viewer.wrap, focused=a.focused is viewer,
                    data=memo_of(a))

    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  KeyEvent("end"), KeyEvent("f3"), Until(lambda a: isinstance(a.modal, MemoDialog)), look,
                  KeyEvent("f2"), lambda a: seen.update(wrapped=a.modal.viewer.wrap),
                  KeyEvent("f7"), Until(lambda a: isinstance(a.modal, ViewerFindDialog)),
                  *[KeyEvent(c, c) for c in "needle"], KeyEvent("enter"),
                  Until(lambda a: isinstance(a.modal, MemoDialog) and a.modal.viewer.hit is not None),
                  lambda a: seen.update(hit=a.modal.viewer.hit),
                  KeyEvent("escape"), Until(lambda a: a.modal is None),
                  lambda a: seen.update(back=a.focused is window_of(a).viewer)])
    assert seen["size"] == (69, 19) and seen["title"] == "Memo view"
    assert seen["focused"] and seen["data"] == long + b"\r\nsecond line"
    assert seen["wrapped"] is not seen["wrap"]
    assert seen["hit"] == (long.index(b"needle"), 6)
    assert seen["back"]


# -- The table's code page (the language-driver byte, a .cpg, Shift+F6) ---------------------------

RUSSIAN_FIELDS = (("ИМЯ", "C", 10, 0), ("NOTES", "M", 10, 0))
RUSSIAN_ROWS = (("Анна", "1"), ("Борис", "0"))


def write_russian(path: Path, codec: str = "cp866", driver: int = 0x65) -> Path:
    return write_dbf(path, RUSSIAN_ROWS, RUSSIAN_FIELDS, codec=codec, driver=driver,
                     memo="Привет".encode(codec))


@pytest.mark.parametrize("codec, driver", [("cp866", 0x65), ("cp866", 0x26), ("cp1251", 0xC9)])
def test_the_language_driver_byte_names_the_code_page(tmp_path, codec, driver):
    db = dbf.DBFile(write_russian(tmp_path / "ru.dbf", codec, driver))
    assert db.codec == codec
    assert db.fields[0].name == "ИМЯ"
    assert db.raw(db.record(0), db.fields[0]).strip() == "Анна"
    assert db.memo(db.record(0), db.fields[1]) == "Привет"


def test_no_driver_byte_reads_as_dns_cp437(tmp_path):
    db = dbf.DBFile(write_dbf(tmp_path / "people.dbf"))
    assert db.codec == "cp437" == dbf.CODEC


@pytest.mark.parametrize("text, codec", [("UTF-8\n", "utf-8"), ("1251", "cp1251"), ("ANSI 1251", "cp1251"),
                                         ("nonsense", "cp866"), ("", "cp866")])
def test_a_cpg_beside_the_table_wins_over_the_byte(tmp_path, text, codec):
    path = write_russian(tmp_path / "ru.dbf")
    (tmp_path / "ru.cpg").write_text(text)
    assert dbf.DBFile(path).codec == codec


def test_a_cpg_in_capitals_beside_a_table_in_capitals(tmp_path):
    path = write_russian(tmp_path / "RU.DBF", "cp1251", 0)
    (tmp_path / "RU.CPG").write_text("1251")
    db = dbf.DBFile(path)
    assert db.codec == "cp1251" and db.fields[0].name == "ИМЯ"


def test_every_language_driver_is_a_page_shift_f6_offers():
    from navigator.lib import codepages

    offered = {page.key for page in codepages.ONE_BYTE}
    assert set(dbf.LANGUAGE_DRIVERS.values()) <= offered


def test_the_companions_are_the_memo_files_and_the_cpg():
    names = [p.name for p in dbf.companions(Path("a.dbf"))]
    assert names == ["a.fpt", "a.FPT", "a.dbt", "a.DBT", "a.cpg", "a.CPG"]


def test_set_codec_reads_the_cells_and_names_again_and_f4_writes_in_it(tmp_path):
    db = dbf.DBFile(write_russian(tmp_path / "ru.dbf", "cp866", 0))
    assert db.codec == "cp437" and db.fields[0].name != "ИМЯ"
    db.record(0)
    db.set_codec("cp866")
    assert db.fields[0].name == "ИМЯ" and db.fields[0].raw_name == "ИМЯ".encode("cp866")
    assert db.raw(db.record(0), db.fields[0]).strip() == "Анна"
    assert dbf.find(db, "борис", case=False, all_fields=False, backward=False, record=-1, field=0) == (1, 0)
    db.write_field(0, db.fields[0], "Вера")
    raw = (tmp_path / "ru.dbf").read_bytes()
    assert "Вера".encode("cp866").ljust(10) in raw


def test_f4_in_utf_8_never_cuts_a_character_in_half(tmp_path):
    path = write_russian(tmp_path / "ru.dbf", "utf-8", 0)
    (tmp_path / "ru.cpg").write_text("UTF-8")
    db = dbf.DBFile(path)
    db.write_field(0, db.fields[0], "Ярослава")  # 16 bytes into 10
    cell = dbf.DBFile(path).record(0)[1:11]
    assert cell == "Яросл".encode().ljust(10)


def russian_place(place):
    write_russian(place / "ru.dbf", "cp866", 0)
    return place


def test_shift_f6_on_a_dbase_table_opens_the_encoding_box(place):
    from navml.widgets.menu.popup_menu import PopupMenu

    russian_place(place)
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def popup(a):
        return next((c for c in a.root.children if isinstance(c, PopupMenu)), None)

    run_app(app, [on("ru.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  KeyEvent("f6", shift=True), Until(lambda a: popup(a) is not None),
                  lambda a: seen.update(title=popup(a).title),
                  # CP437 is in a submenu, opened: Esc out of it, then the box.
                  KeyEvent("escape"), KeyEvent("escape"), Until(lambda a: popup(a) is None),
                  lambda a: seen.update(codec=window_of(a).db.codec, focused=a.focused is window_of(a).viewer)])
    assert seen == {"title": "Encoding", "codec": "cp437", "focused": True}


def test_the_page_chosen_redraws_the_table_and_the_memo_opens_in_it(place, monkeypatch):
    from navigator.widgets.viewer import viewer_host

    russian_place(place)
    asked = []

    async def pick(host, current):
        asked.append(current)
        return "cp866"

    monkeypatch.setattr(viewer_host, "pick_encoding", pick)
    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        window = window_of(a)
        db = window.db
        seen.update(name=db.fields[0].name, cell=db.shown(db.record(window.viewer.record), db.fields[0]).strip(),
                    row=window.viewer.record, screen="\n".join(a.terminal.text_lines()) if hasattr(
                        a.terminal, "text_lines") else "")

    run_app(app, [on("ru.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)),
                  KeyEvent("down"), KeyEvent("f6", shift=True), Until(lambda a: window_of(a).db.codec == "cp866"),
                  look, KeyEvent("up"), KeyEvent("end"), KeyEvent("f3"),
                  Until(lambda a: isinstance(a.modal, MemoDialog)),
                  lambda a: seen.update(memo=(memo_of(a), a.modal.viewer.encoding))])
    assert asked == ["cp437"]
    assert seen["name"] == "ИМЯ" and seen["cell"] == "Борис" and seen["row"] == 1
    assert seen["memo"] == ("Привет".encode("cp866"), "cp866")


def format_entry(window):
    from navigator.widgets.viewer.commands import TableFormat

    return next(e for e in window.view_menu.entries() if getattr(e, "command", None) is TableFormat)


def test_the_view_menu_names_shift_f6_for_the_table(place):
    from navml.widgets.menu.menu_box.menu_box import key_caption

    app = Navigator(place, place, terminal=FakeTerminal(100, 30))
    seen = {}

    def look(a):
        entry = format_entry(window_of(a))
        seen.update(entry=(str(entry.text), key_caption(entry, a, a.focused),
                           a.command_enabled(entry.command, a.focused)))

    run_app(app, [on("people.dbf"), KeyEvent("f3"), Until(lambda a: isinstance(window_of(a), DBWindow)), look])
    assert seen["entry"] == ("E~n~coding...", "Shift-F6", True)
    # Not a dBase table (a CSV's): still *Format*.
    assert str(format_entry(DBWindow(None)).text) == "Fo~r~mat..."


def test_shift_f6_is_refused_in_a_sqlite_table(tmp_path):
    from navigator.widgets.viewer.commands import TableFormat

    window = DBWindow(None, sqlite=object())
    assert window.code_page is False
    assert window.refusal(TableFormat()) == "Only in a CSV or dBase file"
    db = dbf.DBFile(write_dbf(tmp_path / "people.dbf"))
    assert DBWindow(db).refusal(TableFormat()) == ""


def test_a_table_from_another_drive_brings_its_memo_and_cpg(tmp_path, monkeypatch):
    import asyncio

    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive
    from navigator.widgets.drives import use_file

    drive = mount(MemoryDrive("tables"))
    try:
        for name in ("ru.dbf", "ru.fpt", "ru.cpg"):
            drive.make(f"/t/{name}", "x")
        asked = []

        async def materialize(app, origins):
            asked.extend(str(o.path) for o in origins)
            return None

        monkeypatch.setattr(use_file, "materialize", materialize)
        desktop = type("Desktop", (), {"application": None})()
        assert asyncio.run(use_file.database_elsewhere(desktop, drive.location("/t/ru.dbf"))) is None
        assert asked == ["/t/ru.dbf", "/t/ru.fpt", "/t/ru.cpg"]
    finally:
        unmount(drive.site)
