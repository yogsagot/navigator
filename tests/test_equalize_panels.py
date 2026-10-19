"""Alt+=: the passive panel goes to the active panel's directory."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator


@pytest.fixture
def sides(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for side in ("west", "east"):
        (tmp_path / side).mkdir()
        (tmp_path / side / "a.txt").write_text(side)
    return tmp_path


def navigator(sides: Path) -> Navigator:
    return Navigator(sides / "west", sides / "east", terminal=FakeTerminal(80, 24))


def test_alt_equals_sends_the_passive_panel_to_the_active_one_and_keeps_the_keyboard(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("=", alt=True), lambda a: None])
    m = app.manager
    assert m.left.path == sides / "west" and m.right.path == sides / "west"
    assert app.focused is m.left


def test_alt_equals_from_the_right_panel_moves_the_left(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("tab"), lambda a: None, KeyEvent("=", alt=True), lambda a: None])
    m = app.manager
    assert m.left.path == sides / "east" and app.focused is m.right


def test_a_hidden_passive_side_is_shown(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("f2", ctrl=True), lambda a: None, KeyEvent("=", alt=True), lambda a: None])
    m = app.manager
    assert m.hidden_side is None and m.right.visible and m.right.path == sides / "west"


def test_a_tree_standing_in_for_the_passive_panel_gives_way(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, KeyEvent("=", alt=True), lambda a: None])
    m = app.manager
    assert m.replaced is None and m.right.path == sides / "west"
