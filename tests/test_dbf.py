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

FIELDS = (("NAME", "C", 10, 0), ("AGE", "N", 3, 0), ("BORN", "D", 8, 0), ("OK", "L", 1, 0),
          ("NOTES", "M", 10, 0))
ROWS = (("Ann", "34", "19900102", "T", "1"), ("Bob", "7", "20170311", "F", "0"), ("Cid", "61", "", "T", "0"))


def write_dbf(path: Path, rows=ROWS, fields=FIELDS) -> Path:
    """A dBase III file of *rows*, and a ``.dbt`` with one memo in block 1."""
    record_length = 1 + sum(f[2] for f in fields)
    header_length = 32 + 32 * len(fields) + 1
    data = bytearray(struct.pack("<BBBBIHH", 3, 126, 1, 1, len(rows), header_length, record_length) + bytes(20))
    for name, kind, length, decimals in fields:
        data += name.encode().ljust(11, b"\0") + kind.encode() + bytes(4) + bytes((length, decimals)) + bytes(14)
    data += b"\r"
    for index, row in enumerate(rows):
        data += b"*" if index == 1 else b" "
        for (name, kind, length, _), value in zip(fields, row):
            data += (value.rjust(length) if kind in "NM" else value.ljust(length)).encode()[:length]
    data += b"\x1a"
    path.write_bytes(bytes(data))
    path.with_suffix(".dbt").write_bytes(bytes(512) + b"Hello\r\nmemo\x1a".ljust(512, b"\0"))
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
                  Until(lambda a: isinstance(a.modal, DBListDialog)),
                  lambda a: seen.update(memo=list(a.modal.lines.items))])
    assert seen["cell"] == (1, 2) and seen["indicator"] == "2/3" and seen["last"] == 2
    assert seen["title"].startswith("dBase View - ")
    assert seen["what"] == "Structure of people.dbf"
    assert seen["fields"][1] == " \u200eAGE         \u200eNumeric      \u200e3          \u200e0"  # held left to right
    assert seen["memo"] == ["Hello", "memo"]


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
    assert seen["prompt"] == "fake.dbf: not a dBase file"


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
                  KeyEvent("m", "m"), Until(lambda a: isinstance(a.modal, DBListDialog)),
                  lambda a: seen.update(memo=list(a.modal.lines.items))])
    assert seen["cell"] == (4, 0)
    assert list(seen["enabled"]) == ["Fields...", "Memo view", "Edit field...", "Search...",
                                     "Search again", "Close"]
    assert seen["enabled"]["Memo view"]
    assert seen["memo"] == ["Hello", "memo"]
