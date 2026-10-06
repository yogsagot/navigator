"""Ctrl+U: ``cmSwapPanels``, the two sides change places."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator


@pytest.fixture
def sides(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for side in ("west", "east"):
        (tmp_path / side).mkdir()
        for name in ("a.txt", "b.txt", "c.txt"):
            (tmp_path / side / name).write_text(side)
    return tmp_path


def navigator(sides: Path) -> Navigator:
    return Navigator(sides / "west", sides / "east", terminal=FakeTerminal(80, 24))


def test_ctrl_u_swaps_the_panels_whole_and_the_keyboard_goes_with_its_panel(sides):
    app = navigator(sides)
    seen = {}

    def before(a):
        m = a.manager
        seen["west"], seen["east"] = m.left, m.right
        seen["places"] = (m.left.x, m.right.x)
        m.left.cursor = 2
        m.left.marked = frozenset({"a.txt"})

    run_app(app, [before, KeyEvent("u", ctrl=True), lambda a: None])
    m = app.manager
    assert m.right is seen["west"] and m.left is seen["east"]
    assert m.right.path == sides / "west" and m.left.path == sides / "east"
    assert (m.left.x, m.right.x) == seen["places"]
    assert m.right.cursor == 2 and m.right.marked == {"a.txt"}
    assert app.focused is m.right and m.active_panel is m.right


def test_ctrl_u_twice_puts_everything_back(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("u", ctrl=True), lambda a: None, KeyEvent("u", ctrl=True), lambda a: None])
    m = app.manager
    assert m.left.path == sides / "west" and m.right.path == sides / "east"
    assert m.left.x < m.right.x and app.focused is m.left


def test_a_tree_standing_in_for_a_panel_goes_with_it(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, KeyEvent("u", ctrl=True), lambda a: None])
    m = app.manager
    # The tree stood in for the passive east panel on the right: now on the left.
    assert m.replacement is m.tree and m.replaced is m.left
    assert m.left.path == sides / "east" and m.tree.x < m.right.x
    assert app.focused is m.right and m.right.path == sides / "west"


def test_a_hidden_side_is_shown_and_the_panels_swap(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("f2", ctrl=True), lambda a: None, KeyEvent("u", ctrl=True), lambda a: None])
    m = app.manager
    assert m.hidden_side is None and m.left.visible and m.right.visible
    assert m.left.path == sides / "east" and m.right.path == sides / "west"
    assert m.zoomed


def test_hide_left_hides_whatever_is_on_the_left_now(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("u", ctrl=True), lambda a: None, KeyEvent("f1", ctrl=True), lambda a: None])
    m = app.manager
    assert m.hidden_side == "left" and m.left.path == sides / "east" and not m.left.visible
