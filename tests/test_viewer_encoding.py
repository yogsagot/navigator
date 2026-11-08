"""The viewer's File > Encoding (Shift+F6, DN's ``cmLoadXlatTable`` and its
``XLT`` tables) and File > Save as (Shift+F5, ``cmSaveAll``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.lib import viewer as model
from navigator.__main__ import Navigator
from navigator.lib.viewer import ViewSource, byte_table, compile_search, hex_row
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
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
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
        seen["title"] = box.box.title
        # UTF-8, then a submenu a group: the fifth is Cyrillic, where CP866
        # is sixth (Windows-1251, KOI8-R, KOI8-U, KOI8-T, ISO-8859-5, CP866).
        for _ in range(5):
            a.post_event(KeyEvent("down"))
        a.post_event(KeyEvent("enter"))
        for _ in range(5):
            a.post_event(KeyEvent("down"))
        a.post_event(KeyEvent("enter"))

    run_app(app, [on_file, KeyEvent("f3"), Until(lambda a: viewer_of(a) is not None),
                  KeyEvent("f6", shift=True), Until(lambda a: any(isinstance(w, PopupMenu) for w in a.root.children)),
                  choose_cp866, lambda a: None, lambda a: None,
                  lambda a: seen.update(encoding=viewer_of(a).encoding, info=viewer_of(a).info_text,
                                        row="".join(c for c, _ in viewer_of(a).source.line(0).cells))])
    assert seen["current"] == 0 and seen["title"] == "Encoding"
    assert seen["encoding"] == "cp866" and seen["info"].endswith("{CP866}")
    assert seen["row"] == RUSSIAN.rstrip("\n")


def test_shift_f5_saves_the_file_recoded(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))

    def on_file(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("ru.txt")

    def name_it(a):
        a.modal.target.value = str(place / "utf8.txt")

    seen = {}
    run_app(app, [on_file, KeyEvent("f3"), Until(lambda a: viewer_of(a) is not None),
                  lambda a: viewer_of(a).set_encoding("cp866"), KeyEvent("f5", shift=True),
                  Until(lambda a: a.modal is not None),
                  lambda a: seen.update(title=a.modal.title, prompt=a.modal.prompt), KeyEvent("enter"),
                  Until(lambda a: isinstance(a.modal, FileDialog)), name_it, KeyEvent("enter"),
                  Until(lambda a: (place / "utf8.txt").exists())])
    assert seen["title"] == "Confirmation" and "from CP866 to UTF-8?" in seen["prompt"]
    assert (place / "utf8.txt").read_text(encoding="utf-8") == RUSSIAN


def save_steps(place, target, *answers, encoding="cp866"):
    """Shift+F5 on ``ru.txt`` read in *encoding*, each of *answers* (a key
    name) given to the box it opens, *target* typed into the file dialog
    where it comes."""
    def on_file(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("ru.txt")

    def name_it(a):
        a.modal.target.value = str(target)

    steps = [on_file, KeyEvent("f3"), Until(lambda a: viewer_of(a) is not None),
             lambda a: viewer_of(a).set_encoding(encoding), KeyEvent("f5", shift=True)]
    for answer in answers:
        if answer == "name":
            steps += [Until(lambda a: isinstance(a.modal, FileDialog)), name_it, KeyEvent("enter")]
        else:
            steps += [Until(lambda a: a.modal is not None and not isinstance(a.modal, FileDialog)),
                      KeyEvent(answer) if answer == "escape" else KeyEvent(answer, alt=True)]
    return steps


def test_no_to_the_translation_saves_the_bytes_as_they_are(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    target = place / "raw.txt"
    run_app(app, save_steps(place, target, "n", "name") + [Until(lambda a: target.exists())])
    assert target.read_bytes() == (place / "ru.txt").read_bytes()


def test_escape_on_the_translation_saves_nothing(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, save_steps(place, place / "x.txt", "escape")
            + [lambda a: seen.update(modal=a.modal)])
    assert seen["modal"] is None and not (place / "x.txt").exists()


def test_a_utf8_file_is_not_asked_about_translating(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    target = place / "plain.txt"
    run_app(app, save_steps(place, target, "name", encoding="utf-8") + [Until(lambda a: target.exists())])
    assert target.read_bytes() == (place / "ru.txt").read_bytes()


@pytest.mark.parametrize("key, expected", [("p", "old\n" + RUSSIAN), ("y", RUSSIAN), ("escape", "old\n")])
def test_an_existing_file_is_replaced_appended_to_or_left(place, key, expected):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    target = place / "there.txt"
    target.write_text("old\n", encoding="utf-8")
    seen = {}

    def buttons(a):
        seen.update(buttons=[b.text.replace("~", "") for b in a.modal.buttons_row])

    steps = save_steps(place, target, "y", "name")
    steps += [Until(lambda a: a.modal is not None and not isinstance(a.modal, FileDialog)), buttons,
              KeyEvent(key) if key == "escape" else KeyEvent(key, alt=True),
              Until(lambda a: a.modal is None and not a.busy)]
    if key != "escape":
        steps.append(Until(lambda a: target.read_text(encoding="utf-8") == expected))
    run_app(app, steps)
    assert seen["buttons"][:3] == ["Yes", "Append", "Cancel"]
    assert target.read_text(encoding="utf-8") == expected


def test_save_as_appends_and_stops_at_the_limit(tmp_path):
    source = tmp_path / "ru.txt"
    source.write_bytes(RUSSIAN.encode("cp866"))
    out = tmp_path / "out.txt"
    out.write_bytes(b"old\n")
    model.save_as(source, out, "cp866", append=True)
    assert out.read_text(encoding="utf-8") == "old\n" + RUSSIAN
    model.save_as(source, tmp_path / "short.txt", limit=6)
    assert (tmp_path / "short.txt").read_bytes() == RUSSIAN.encode("cp866")[:6]
    # Appended to itself, it doubles once.
    size = source.stat().st_size
    model.save_as(source, source, append=True, limit=size)
    assert source.read_bytes() == RUSSIAN.encode("cp866") * 2


def test_the_recoding_does_not_split_a_character_between_blocks(tmp_path):
    source = tmp_path / "big.txt"
    text = "я" * (1 << 16)
    source.write_bytes(text.encode("utf-16-le"))
    model.save_as(source, tmp_path / "out.txt", "utf-16-le", limit=(1 << 16) + 1)
    # The limit cut the last character in half: one replacement, nothing else broken.
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "я" * (1 << 15) + "\ufffd"


def test_shift_f6_opens_on_the_group_of_the_encoding_in_use(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}

    def on_file(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("ru.txt")

    def popup(a):
        return next((w for w in a.root.children if isinstance(w, PopupMenu)), None)

    run_app(app, [on_file, KeyEvent("f3"), Until(lambda a: viewer_of(a) is not None),
                  lambda a: viewer_of(a).set_encoding("cp866"),
                  KeyEvent("f6", shift=True), Until(lambda a: popup(a) is not None and len(popup(a).boxes) == 2),
                  lambda a: seen.update(group=popup(a).boxes[0].current,
                                        item=popup(a).boxes[1].menu.entries()[popup(a).boxes[1].current].text),
                  KeyEvent("escape"), KeyEvent("escape")])
    assert seen["item"].replace("~", "") == "CP866 DOS Cyrillic"
