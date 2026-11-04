"""Shift+left click in a panel tags every row from the cursor to the one clicked."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import MouseClickEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """The left panel's rows 2 to 6: ``..``, ``alpha``, ``beta``, ``one.txt``, ``two.txt``."""
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(SETTINGS.file_manager, "drag_drop_columns", True)
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()
    (tmp_path / "one.txt").write_text("one")
    (tmp_path / "two.txt").write_text("two")
    return tmp_path


def click(y: int, *, shift: bool = False) -> list:
    return [MouseClickEvent(x=5, y=y, button="left", action="press", shift=shift),
            MouseClickEvent(x=5, y=y, button="left", action="release", shift=shift)]


def tagged(app) -> list[str]:
    return [e.name for e in app.manager.left.marked_entries]


def test_shift_click_tags_from_the_cursor_to_the_row_clicked(tree):
    app = Navigator(tree, tree, terminal=FakeTerminal(80, 24))
    run_app(app, [*click(3), *click(6, shift=True)])
    assert tagged(app) == ["alpha", "beta", "one.txt", "two.txt"]
    assert app.manager.left.selected.name == "two.txt"


def test_shift_click_upwards_adds_to_the_tags_and_never_tags_dot_dot(tree):
    app = Navigator(tree, tree, terminal=FakeTerminal(80, 24))

    def tag_two(a):
        panel = a.manager.left
        panel.marked = frozenset({next(e.key for e in panel.items if e.name == "two.txt")})

    run_app(app, [tag_two, *click(4), *click(2, shift=True)])
    assert tagged(app) == ["alpha", "beta", "two.txt"]
    assert app.manager.left.selected.name == ".."


def test_a_plain_click_tags_nothing(tree):
    app = Navigator(tree, tree, terminal=FakeTerminal(80, 24))
    run_app(app, [*click(3), *click(6)])
    assert tagged(app) == []


def ctrl_click(y: int) -> list:
    return [MouseClickEvent(x=5, y=y, button="left", action="press", ctrl=True),
            MouseClickEvent(x=5, y=y, button="left", action="release", ctrl=True)]


def test_ctrl_click_tags_a_range_too(tree):
    """VTE (xfce4-terminal) never reports Shift+click; Ctrl+click does the same."""
    app = Navigator(tree, tree, terminal=FakeTerminal(80, 24))
    run_app(app, [*click(6), lambda a: None, *ctrl_click(4)])
    assert tagged(app) == ["beta", "one.txt", "two.txt"]
    assert app.manager.left.selected.name == "beta"


def test_ctrl_double_click_inserts_the_name_and_tags_nothing(tree):
    app = Navigator(tree, tree, terminal=FakeTerminal(80, 24))
    run_app(app, [*click(3), lambda a: None, *ctrl_click(5), *ctrl_click(5)])
    assert tagged(app) == []
    assert app.shell.command_line.value.strip() == "one.txt"
