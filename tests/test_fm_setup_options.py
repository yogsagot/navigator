"""File Manager Setup's *Use arrows*, *Beep after copy* and *Auto change
directory* (DN's ``fmoUseArrows``, ``fmoBeep``, ``fmoAutoChangeDir``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.file_ops.copy_dialog import CopyDialog


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a", "b"):
        (tmp_path / name).mkdir()
    for index in range(5):
        (tmp_path / "a" / f"f{index}.txt").write_text(str(index))
    (tmp_path / "a" / "sub").mkdir()
    return tmp_path


def navigator(place: Path) -> Navigator:
    return Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 24))


def type_text(text: str) -> list[KeyEvent]:
    return [KeyEvent(char, char) for char in text]


def to_last(a):
    panel = a.manager.left
    panel.cursor = len(panel.items) - 1


def test_use_arrows_on_gives_home_and_left_to_a_line_with_text(place):
    seen = {}
    app = navigator(place)
    run_app(app, [to_last, *type_text("ls"), KeyEvent("home"), KeyEvent("right"),
                  lambda a: seen.update(caret=a.shell.command_line.cursor, cursor=a.manager.left.cursor)])
    assert seen["caret"] == 1 and seen["cursor"] == len(app.manager.left.items) - 1


def test_use_arrows_off_gives_them_to_the_panel_and_shift_to_the_line(place):
    SETTINGS.file_manager.use_arrows = False
    seen = {}
    app = navigator(place)
    run_app(app, [to_last, *type_text("ls"), KeyEvent("home"), KeyEvent("left"),
                  lambda a: seen.update(caret=a.shell.command_line.cursor, cursor=a.manager.left.cursor),
                  KeyEvent("home", shift=True),
                  lambda a: seen.update(shifted=a.shell.command_line.cursor)])
    assert seen["cursor"] == 0 and seen["caret"] == 2
    assert seen["shifted"] == 0


@pytest.mark.parametrize("beep", [True, False])
def test_beep_after_copy_rings_the_bell_once_the_copy_is_done(place, beep):
    SETTINGS.file_manager.beep_after_copy = beep
    app = navigator(place)
    seen = {}

    def on_file(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("f1.txt")

    run_app(app, [on_file, KeyEvent("f5"), Until(lambda a: isinstance(a.modal, CopyDialog)),
                  KeyEvent("enter"), Until(lambda a: (place / "b" / "f1.txt").exists() and a.modal is None),
                  lambda a: None, lambda a: seen.update(bells=a.terminal.bells)])
    assert seen["bells"] == (1 if beep else 0)


@pytest.mark.parametrize("follow", [True, False])
def test_auto_change_directory_says_whether_the_panel_follows_the_tree(place, monkeypatch, follow):
    from navigator.widgets.manager.manager import Manager

    monkeypatch.setattr(Manager, "LOCATE_DELAY", 0.01)
    SETTINGS.file_manager.auto_change_dir = follow
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("t", ctrl=True), KeyEvent("tab"), KeyEvent("down"), lambda a: None,
                  lambda a: seen.update(tree=a.manager.tree.selected_path, panel=a.manager.left.path)],
            settle=0.1)
    assert seen["tree"] != place / "a"
    assert (seen["panel"] == seen["tree"]) is follow
