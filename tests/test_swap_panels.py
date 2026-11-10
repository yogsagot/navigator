"""Ctrl+U: ``cmSwapPanels``, the two sides change places."""

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


def rect(window):
    return (window.x, window.y, window.width, window.height, window.zoomed)


@pytest.mark.parametrize("hide, stays", [("f2", "left"), ("f1", "right")])
def test_with_a_side_hidden_the_visible_panel_goes_across_and_one_side_stays_hidden(sides, hide, stays):
    # DN read LVisible/RVisible once at the top of HandleEvent: the cmHide* after
    # the swap, chosen by those flags, found both showing and hid the other side.
    app = navigator(sides)
    seen = {}

    def before(a):
        m = a.manager
        seen["shown"] = m.left if hide == "f2" else m.right
        seen["rect"] = rect(m)

    run_app(app, [KeyEvent(hide, ctrl=True), lambda a: None, before, KeyEvent("u", ctrl=True), lambda a: None])
    m = app.manager
    shown = seen["shown"]
    assert m.hidden_side == stays
    other = "right" if stays == "left" else "left"
    assert getattr(m, other) is shown and shown.visible and app.focused is shown
    # The window moved to the half the panel now stands on.
    x, _, width, _, _ = seen["rect"]
    assert (m.x > x) if stays == "left" else (m.x < x)


def test_ctrl_u_twice_with_a_side_hidden_puts_everything_back(sides):
    app = navigator(sides)
    seen = {}

    def look(name):
        def act(a):
            m = a.manager
            seen[name] = (rect(m), m.hidden_side, m.left.path, a.focused is m.left)
        return act

    run_app(app, [KeyEvent("f2", ctrl=True), lambda a: None, look("before"),
                  KeyEvent("u", ctrl=True), lambda a: None, KeyEvent("u", ctrl=True), lambda a: None,
                  look("after")])
    assert seen["after"] == seen["before"]


def test_a_quick_view_on_the_hidden_side_moves_with_it(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("q", ctrl=True), lambda a: None, KeyEvent("f2", ctrl=True), lambda a: None,
                  KeyEvent("u", ctrl=True), lambda a: None])
    m = app.manager
    # The view stood in for the right side, hidden: now the left one, still hidden.
    assert m.hidden_side == "left" and m.replacement is m.quick and not m.quick.visible
    assert m.right.path == sides / "west" and m.right.visible


def test_hide_left_hides_whatever_is_on_the_left_now(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("u", ctrl=True), lambda a: None, KeyEvent("f1", ctrl=True), lambda a: None])
    m = app.manager
    assert m.hidden_side == "left" and m.left.path == sides / "east" and not m.left.visible


# -- Ctrl+T/Q/L with a side hidden: ``SwitchView``'s order ---------------------------------------


@pytest.mark.parametrize("key, view", [("t", "tree"), ("q", "quick"), ("l", "info")])
def test_a_view_on_the_hidden_side_comes_back_with_it(sides, key, view):
    app = navigator(sides)
    seen = {}
    run_app(app, [KeyEvent(key, ctrl=True), lambda a: None, KeyEvent("f2", ctrl=True), lambda a: None,
                  KeyEvent(key, ctrl=True), lambda a: None,
                  lambda a: seen.update(state=(a.manager.hidden_side, a.manager.replacement,
                                               a.focused is a.manager.left))])
    m = app.manager
    assert seen["state"] == (None, getattr(m, view), True)
    assert getattr(m, view).visible


def test_a_view_put_away_leaves_the_other_hidden_side_hidden(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, KeyEvent("tab"), lambda a: None,
                  KeyEvent("f1", ctrl=True), lambda a: None, KeyEvent("t", ctrl=True), lambda a: None])
    m = app.manager
    assert m.replacement is None and m.hidden_side == "left"
    assert m.right.visible and app.focused is m.right


def test_a_view_into_a_hidden_passive_side_shows_it(sides):
    app = navigator(sides)
    run_app(app, [KeyEvent("f2", ctrl=True), lambda a: None, KeyEvent("t", ctrl=True), lambda a: None])
    m = app.manager
    assert m.hidden_side is None and m.replacement is m.tree and m.tree.visible
    assert app.focused is m.left
