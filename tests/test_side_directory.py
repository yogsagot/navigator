"""Ctrl+[ and Ctrl+]: DN's ``$1A1B``/``$1B1D``, a side's directory onto the command line."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("west", "east", "my dir", "east/sub"):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    return tmp_path


def tree_lands_on(target_of):
    """An ``Until`` predicate: the tree's cursor on ``target_of(app)``.

    ``show`` walks on a thread, and a later walk (Ctrl+T's own, to the
    panel's directory) may land after it and take the cursor back: asked
    again then -- but not more than every 0.3 s, as each ``show`` drops the
    walk before it."""
    import time

    asked = [0.0]

    def there(a):
        tree = a.manager.tree
        target = target_of(a)
        if tree.selected_path == target:
            return True
        if time.monotonic() - asked[0] > 0.3:
            asked[0] = time.monotonic()
            tree.show(target)
        return False
    return there


def line(app) -> str:
    return app.shell.command_line.value


def test_ctrl_bracket_right_is_the_right_sides_directory_whatever_is_active(place):
    app = Navigator(place / "west", place / "east", terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("]", ctrl=True), lambda a: None])
    assert line(app) == f"{place / 'east'}/"


def test_ctrl_bracket_left_is_the_left_sides(place):
    app = Navigator(place / "west", place / "east", terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("tab"), KeyEvent("[", ctrl=True), lambda a: None])
    assert line(app) == f"{place / 'west'}/"


def test_a_blank_in_the_name_is_escaped_as_ctrl_enter_escapes_it(place):
    app = Navigator(place / "west", place / "my dir", terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("]", ctrl=True), lambda a: None])
    assert line(app) == str(place).replace(" ", "\\ ") + "/my\\ dir/"


def test_the_root_is_one_slash(place):
    app = Navigator(place / "west", Path("/"), terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("]", ctrl=True), lambda a: None])
    assert line(app) == "/"


def test_the_tree_on_the_side_answers_its_cursors_directory(place):
    app = Navigator(place / "east", place / "west", terminal=FakeTerminal(80, 24))

    sub = place / "east" / "sub"
    run_app(app, [KeyEvent("t", ctrl=True), Until(lambda a: a.manager.tree.selected_path is not None),
                  Until(tree_lands_on(lambda a: sub), timeout=5), KeyEvent("]", ctrl=True), lambda a: None])
    assert line(app) == f"{place / 'east' / 'sub'}/"


def test_a_hidden_side_still_answers(place):
    app = Navigator(place / "west", place / "east", terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("f2", ctrl=True), lambda a: None, KeyEvent("]", ctrl=True), lambda a: None])
    assert line(app) == f"{place / 'east'}/"


def test_after_text_on_the_line_it_goes_in_at_the_caret(place):
    app = Navigator(place / "west", place / "east", terminal=FakeTerminal(80, 24))
    run_app(app, [*[KeyEvent(c, c) for c in "ls"], KeyEvent("]", ctrl=True), lambda a: None])
    assert line(app) == f"ls {place / 'east'}/"
