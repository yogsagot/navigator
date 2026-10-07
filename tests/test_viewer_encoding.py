"""The viewer's File > Encoding (Shift+F6, DN's ``cmLoadXlatTable`` and its
``XLT`` tables) and File > Save as (Shift+F5, ``cmSaveAll``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator import viewer as model
from navigator.__main__ import Navigator
from navigator.viewer import ViewSource, byte_table, compile_search, hex_row
from navml.widgets.dialog.file_dialog import FileDialog
from navml.widgets.menu.popup_menu import PopupMenu

RUSSIAN = "Привет, мир\n"


def test_a_code_page_table_reads_each_byte_as_its_letter(tmp_path):
    path = tmp_path / "ru.txt"
    path.write_bytes(RUSSIAN.encode("cp866"))
    source = ViewSource(path)
    source.table = byte_table("cp866")
    row = source.line(0)
    assert "".join(char for char, _ in row.cells) == RUSSIAN.rstrip("\n")
    assert byte_table("utf-8") is None
    assert byte_table("cp1251")[0x01] == "☺"  # the controls stay the VGA's


def test_hex_rows_and_the_search_go_through_the_code_page():
    table = byte_table("koi8-r")
    data = "Мир".encode("koi8-r")
    assert hex_row(data, 0, 3, 0, table).endswith("│ Мир")
    pattern, _ = compile_search("мир", encoding="koi8-r")
    assert pattern.search(b"xx" + data)
    never, _ = compile_search("€", encoding="koi8-r")
    assert never.search("€".encode("utf-8")) is None


def test_save_as_writes_the_file_in_utf8(tmp_path):
    source = tmp_path / "ru.txt"
    source.write_bytes(RUSSIAN.encode("cp1251"))
    model.save_as(source, tmp_path / "out.txt", "cp1251")
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == RUSSIAN
    model.save_as(source, tmp_path / "same.bin")
    assert (tmp_path / "same.bin").read_bytes() == source.read_bytes()


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "ru.txt").write_bytes(RUSSIAN.encode("cp866"))
    return tmp_path


def viewer_of(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window.viewer if isinstance(window, FileWindow) else None


def test_shift_f6_chooses_the_encoding_from_a_box(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}

    def on_file(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("ru.txt")

    def choose_cp866(a):
        box = next(w for w in a.root.children if isinstance(w, PopupMenu))
        seen["current"] = box.box.current
        for _ in range(4):
            a.post_event(KeyEvent("down"))
        a.post_event(KeyEvent("enter"))

    run_app(app, [on_file, KeyEvent("f3"), Until(lambda a: viewer_of(a) is not None),
                  KeyEvent("f6", shift=True), Until(lambda a: any(isinstance(w, PopupMenu) for w in a.root.children)),
                  choose_cp866, lambda a: None, lambda a: None,
                  lambda a: seen.update(encoding=viewer_of(a).encoding, info=viewer_of(a).info_text,
                                        row="".join(c for c, _ in viewer_of(a).source.line(0).cells))])
    assert seen["current"] == 0
    assert seen["encoding"] == "cp866" and seen["info"].endswith("{CP866}")
    assert seen["row"] == RUSSIAN.rstrip("\n")


def test_shift_f5_saves_the_file_recoded(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))

    def on_file(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("ru.txt")

    def name_it(a):
        a.modal.target.value = str(place / "utf8.txt")

    run_app(app, [on_file, KeyEvent("f3"), Until(lambda a: viewer_of(a) is not None),
                  lambda a: viewer_of(a).set_encoding("cp866"), KeyEvent("f5", shift=True),
                  Until(lambda a: isinstance(a.modal, FileDialog)), name_it, KeyEvent("enter"),
                  Until(lambda a: (place / "utf8.txt").exists())])
    assert (place / "utf8.txt").read_text(encoding="utf-8") == RUSSIAN
