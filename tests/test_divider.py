"""The divider between the file manager's two sides: DOS Navigator's ``TSeparator``,
dragged with the mouse or moved by Alt+Left/Alt+Right, and kept as a proportion."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent, MouseClickEvent

from navigator import desktop_state
from navigator.__main__ import Navigator
from navigator.widgets.manager.manager import Manager


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "long").mkdir()
    (tmp_path / "short").mkdir()
    for n in range(60):
        (tmp_path / "long" / f"file{n:02}.txt").write_text("x")
    (tmp_path / "short" / "one.txt").write_text("x")
    return tmp_path


def navigator(left: Path, right: Path) -> Navigator:
    return Navigator(left, right, terminal=FakeTerminal(80, 24))


def border(column: str, row: int = 5):
    """Screen coordinates of a divider column: ``"right"`` the right side's left
    frame edge, ``"left"`` the left side's right one."""
    def where(app):
        manager = app.manager
        ox, oy = manager.offset()
        first, second = manager._sides()
        x = second.x if column == "right" else second.x - 1
        y = row if row >= 0 else manager.panels.height + row
        return ox + manager.x + x, oy + manager.y + y
    return where


def column(n: int, row: int = 5):
    def where(app):
        manager = app.manager
        ox, oy = manager.offset()
        return ox + manager.x + n, oy + manager.y + row
    return where


def mouse(where, action: str):
    def act(app):
        x, y = where(app)
        app.post_event(MouseClickEvent(x, y, button="left", action=action))
    return act


def drag(source, target) -> list:
    return [mouse(source, "press"), mouse(target, "move"), mouse(target, "release"), lambda a: None]


def widths(app) -> tuple[int, int]:
    first, second = app.manager._sides()
    return first.width, second.width


def test_the_right_sides_left_edge_drags_the_divider(place):
    app = navigator(place / "long", place / "short")
    seen = {}
    run_app(app, [lambda a: seen.update(before=widths(a)),
                  *drag(border("right"), column(30)), lambda a: seen.update(after=widths(a))])
    assert seen["before"] == (40, 40)
    assert seen["after"] == (30, 50)


def test_the_left_sides_right_edge_drags_where_there_is_no_scroll_bar(place):
    seen = {}
    run_app(navigator(place / "short", place / "long"),
            [*drag(border("left"), column(49)), lambda a: seen.update(after=widths(a))])
    # Taken one column left of where the right side starts, so the right side
    # starts one column right of the pointer.
    assert seen["after"] == (50, 30)


def test_over_the_scroll_bar_the_left_edge_scrolls_and_leaves_the_divider(place):
    seen = {}
    run_app(navigator(place / "long", place / "short"),
            [lambda a: seen.update(bar=a.manager.left.bar.visible),
             *drag(border("left", row=4), column(30, row=4)),
             lambda a: seen.update(after=widths(a), split=a.manager.split)])
    assert seen["bar"]
    assert seen["after"] == (40, 40) and seen["split"] is None


def test_below_the_scroll_bar_the_left_edge_drags(place):
    seen = {}
    run_app(navigator(place / "long", place / "short"),
            [*drag(border("left", row=-1), column(59, row=-1)), lambda a: seen.update(after=widths(a))])
    assert seen["after"] == (60, 20)


def test_the_divider_stops_short_of_either_edge(place):
    seen = {}
    run_app(navigator(place / "short", place / "short"),
            [*drag(border("right"), column(0)), lambda a: seen.update(low=widths(a)),
             *drag(border("right"), column(79)), lambda a: seen.update(high=widths(a))])
    assert seen["low"] == (Manager.MIN_SIDE, 80 - Manager.MIN_SIDE)
    assert seen["high"] == (80 - Manager.MIN_SIDE, Manager.MIN_SIDE)


def test_alt_arrows_move_it_a_column_even_in_list_mode(place):
    seen = {}

    def list_mode(a):
        a.manager.left.view_mode = "list"

    run_app(navigator(place / "long", place / "short"),
            [list_mode, lambda a: None, KeyEvent("left", alt=True), KeyEvent("left", alt=True),
             lambda a: seen.update(left=widths(a), cursor=a.manager.left.cursor),
             KeyEvent("right", alt=True), lambda a: seen.update(right=widths(a))])
    assert seen["left"] == (38, 42) and seen["cursor"] == 0
    assert seen["right"] == (39, 41)


def test_the_split_is_a_proportion_that_survives_a_resize(place):
    seen = {}

    def grow(a):
        a.shell.layout(120, 40)

    run_app(navigator(place / "short", place / "short"),
            [*drag(border("right"), column(30)), grow, lambda a: None,
             lambda a: seen.update(after=widths(a))])
    assert seen["after"] == (45, 75)


def test_the_split_stays_with_the_sides(place):
    seen = {}
    run_app(navigator(place / "short", place / "long"), [
        *drag(border("right"), column(30)),
        KeyEvent("f1", ctrl=True), lambda a: None,
        lambda a: seen.update(hidden=(a.manager.right.width, a.manager.width)),
        KeyEvent("f1", ctrl=True), lambda a: None,
        lambda a: seen.update(shown=widths(a)),
        KeyEvent("u", ctrl=True), lambda a: None,
        lambda a: seen.update(swapped=widths(a), left=a.manager.left.path.name),
        KeyEvent("t", ctrl=True), lambda a: None,
        lambda a: seen.update(tree=widths(a), first=type(a.manager._sides()[0]).__name__),
    ])
    assert seen["hidden"] == (50, 50)
    assert seen["shown"] == (30, 50)
    assert seen["swapped"] == (30, 50) and seen["left"] == "long"
    assert seen["tree"] == (30, 50)


def test_a_saved_desktop_keeps_the_split(place):
    seen = {}

    async def round_trip(a):
        data = desktop_state.snapshot(a.shell.desktop)
        for window in list(a.shell.desktop.windows()):
            window.close()
        await desktop_state.restore(a.shell.desktop, data)
        seen["split"] = next(w for w in a.shell.desktop.windows() if isinstance(w, Manager)).split

    run_app(navigator(place / "short", place / "short"),
            [*drag(border("right"), column(20)), lambda a: a.spawn(round_trip(a)),
             Until(lambda a: "split" in seen), lambda a: None,
             lambda a: seen.update(after=widths(a))])
    assert seen["split"] == 0.25
    assert seen["after"] == (20, 60)
