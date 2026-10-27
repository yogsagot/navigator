"""The panels' Ctrl+C/Ctrl+X and Ctrl+V: paths on the clipboard, entries kept
to paste (``navigator/lib/file_ops/clip.py``), and F5's or F6's dialog on them."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.file_ops.clip import CLIP
from navigator.widgets.file_ops.copy_dialog import CopyDialog


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a", "b", "c"):
        (tmp_path / name).mkdir()
    for name in ("f1.txt", "f2.txt"):
        (tmp_path / "a" / name).write_text(name)
    (tmp_path / "a" / "sub").mkdir()
    CLIP.clear()
    yield tmp_path.resolve()
    CLIP.clear()


def navigator(place: Path) -> Navigator:
    return Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 24))


def key(name: str) -> KeyEvent:
    return KeyEvent(name, char=name if len(name) == 1 else None)


def to(name: str):
    """Put the active panel's cursor on *name*."""
    def act(app):
        panel = app.manager.active_panel
        panel.cursor = [entry.name for entry in panel.items].index(name)
    return act


def tag(*names: str):
    def act(app):
        panel = app.manager.active_panel
        panel.marked = frozenset(entry.key for entry in panel.items if entry.name in names)
    return act


def dialog_up(app) -> bool:
    return isinstance(app.modal, CopyDialog)


def test_ctrl_ins_puts_the_tagged_paths_on_the_clipboard_one_a_line(place):
    app = navigator(place)
    run_app(app, [tag("f1.txt", "f2.txt"), key("ctrl+insert")])
    assert app.terminal.clipboard[-1] == (f"{place / 'a' / 'f1.txt'}\n{place / 'a' / 'f2.txt'}", False)
    assert [entry.name for entry in CLIP.entries] == ["f1.txt", "f2.txt"]
    assert not CLIP.move


def test_a_clipped_row_is_marked_and_every_panel_says_so(place):
    app = navigator(place)
    seen = {}

    def look(a):
        panel = a.manager.left
        index = [entry.name for entry in panel.items].index("f2.txt")
        panel.cursor = 0  # the cursor bar keeps its own colours
        seen["style"] = panel.row_style(index, panel.items[index])
        seen["left"] = [(text or "").replace("~", "") for text, _ in a.manager.left.info_lines]
        seen["right"] = [(text or "").replace("~", "") for text, _ in a.manager.right.info_lines]

    run_app(app, [to("f2.txt"), key("ctrl+x"), look])
    assert CLIP.move
    assert "Clipboard: 1 file to move" in seen["left"]
    assert "Clipboard: 1 file to move" in seen["right"]
    assert seen["style"].dim


def test_cut_and_paste_in_the_other_panel_moves_and_forgets(place):
    app = navigator(place)
    run_app(app, [to("f1.txt"), key("ctrl+delete"), key("tab"), key("ctrl+v"), Until(dialog_up),
                  key("enter"), Until(lambda a: (place / "b" / "f1.txt").exists())])
    assert not (place / "a" / "f1.txt").exists()
    assert not CLIP


def test_a_copy_pasted_stays_to_paste_again(place):
    app = navigator(place)

    def go_c(a):
        a.manager.right.path = place / "c"

    run_app(app, [to("f1.txt"), key("ctrl+c"), key("tab"), key("shift+insert"), Until(dialog_up),
                  key("enter"), Until(lambda a: (place / "b" / "f1.txt").exists()),
                  go_c, key("ctrl+v"), Until(dialog_up), key("enter"),
                  Until(lambda a: (place / "c" / "f1.txt").exists())])
    assert (place / "a" / "f1.txt").exists()
    assert CLIP


def test_the_paste_copies_from_where_it_was_clipped(place):
    app = navigator(place)

    def wander(a):
        a.manager.left.path = place / "c"

    run_app(app, [to("f2.txt"), key("ctrl+c"), wander, key("tab"), key("ctrl+v"), Until(dialog_up),
                  key("enter"), Until(lambda a: (place / "b" / "f2.txt").exists())])


def test_with_text_on_the_line_the_keys_are_the_lines(place):
    app = navigator(place)

    def type_(a):
        a.shell.command_line.insert("echo hi")

    run_app(app, [to("f1.txt"), type_, key("ctrl+c"), key("ctrl+x")])
    assert not CLIP


def test_esc_forgets_the_clip(place):
    app = navigator(place)
    run_app(app, [to("f1.txt"), key("ctrl+c"), key("escape")])
    assert not CLIP


def test_any_other_copy_forgets_the_clip(place):
    app = navigator(place)
    run_app(app, [to("f1.txt"), key("ctrl+c"), lambda a: a.copy_to_clipboard("something else")])
    assert not CLIP


def test_a_directory_is_not_pasted_into_itself(place):
    app = navigator(place)

    def into(a):
        a.manager.right.path = place / "a" / "sub"

    run_app(app, [to("sub"), key("ctrl+x"), into, key("tab"), key("ctrl+v"), lambda a: None])
    assert app.modal is None or not isinstance(app.modal, CopyDialog)
    assert (place / "a" / "sub").is_dir()


def test_a_clip_alone_asks_for_a_frame_with_the_sign_in_the_gutter(place):
    app = navigator(place)
    run_app(app, [to("f1.txt"), lambda a: a.terminal.frames.clear(), key("ctrl+x"), lambda a: None])
    sign = app.manager.left.clip_mark(True)
    assert any(sign in frame for frame in app.terminal.frames)
