"""The mouse on the info lines: DN's ``TInfoView.HandleEvent`` -- the divider
scrolls while held, *Current file*/*Selected*/*Totals* start a drag."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent, MouseClickEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navkit.application.REPEAT_EVERY", 0.005)
    monkeypatch.setattr(SETTINGS.file_manager, "info_divider", True)
    monkeypatch.setattr(SETTINGS.file_manager, "drag_drop_columns", True)
    (tmp_path / "west").mkdir()
    (tmp_path / "east").mkdir()
    for n in range(30):
        (tmp_path / "west" / f"f{n:02}.txt").write_text("x")
    return tmp_path


def app_in(place):
    return Navigator(place / "west", place / "east", terminal=FakeTerminal(100, 30))


def at(panel, part):
    """Screen x, y of the first cell of *part* in *panel*'s info lines."""
    x = panel.inset + 1
    for y in range(panel.height):
        if panel.info_part_at(x, y) == part:
            ox, oy = panel.offset()
            return ox + panel.x + x, oy + panel.y + y
    raise AssertionError(f"no {part} line")


def press(panel_of, part, button="left"):
    def act(a):
        x, y = at(panel_of(a), part)
        a.post_event(MouseClickEvent(x, y, button, "press"))
    return act


def release_at(panel_of, part):
    def act(a):
        x, y = at(panel_of(a), part)
        a.post_event(MouseClickEvent(x, y, "left", "release"))
    return act


def left(a):
    return a.manager.left


def right(a):
    return a.manager.right


def test_the_divider_held_scrolls_down(place):
    app = app_in(place)
    seen = {}
    run_app(app, [press(left, "divider"), Until(lambda a: left(a).cursor >= 3),
                  lambda a: a.post_event(MouseClickEvent(*at(left(a), "divider"), "left", "release")),
                  lambda a: seen.update(stop=left(a).cursor), Until(lambda a: True),
                  lambda a: seen.update(later=left(a).cursor)])
    assert seen["stop"] >= 3 and seen["later"] == seen["stop"]


def test_the_divider_with_the_middle_button_tags_what_it_passes(place):
    app = app_in(place)
    seen = {}
    run_app(app, [lambda a: setattr(left(a), "cursor", 1), press(left, "divider", "middle"),
                  Until(lambda a: left(a).cursor >= 3),
                  lambda a: a.post_event(MouseClickEvent(*at(left(a), "divider"), "middle", "release")),
                  lambda a: seen.update(tagged=sorted(e.name for e in left(a).items if e.key in left(a).marked))])
    assert seen["tagged"][:2] == ["f00.txt", "f01.txt"]


def test_the_divider_of_the_inactive_panel_only_selects_it(place):
    for n in range(5):
        (place / "east" / f"e{n}.txt").write_text("x")
    app = app_in(place)
    seen = {}
    run_app(app, [press(right, "divider"), lambda a: None,
                  lambda a: seen.update(active=a.manager.active_panel is right(a), cursor=right(a).cursor)])
    assert seen == {"active": True, "cursor": 0}


def dropped(app, monkeypatch):
    from navigator.widgets.manager.manager.manager import Manager

    seen = []

    async def record(self, event):
        seen.append(sorted(entry.name for entry in event.entries))
        return True

    monkeypatch.setattr(Manager, "on_dropped", record)
    return seen


def drag_from(part):
    def go(a):
        x, y = at(left(a), part)
        # Over the other panel's rows: its directory takes the drop.
        tx, ty = right(a).offset()[0] + right(a).x + 5, right(a).offset()[1] + right(a).y + 4
        for event in (MouseClickEvent(x, y, "left", "press"), MouseClickEvent(tx, ty, "left", "move"),
                      MouseClickEvent(tx, ty, "left", "release")):
            a.post_event(event)
    return go


def test_the_current_file_line_drags_the_cursors_file(place, monkeypatch):
    app = app_in(place)
    seen = dropped(app, monkeypatch)
    run_app(app, [lambda a: setattr(left(a), "cursor", 3), drag_from("current-file"), Until(lambda a: seen)])
    assert seen == [[left(app).items[3].name]]


def test_the_selected_line_drags_the_tagged_files(place, monkeypatch):
    app = app_in(place)
    seen = dropped(app, monkeypatch)

    def tag(a):
        p = left(a)
        p.marked = frozenset(e.key for e in p.items if e.name in ("f01.txt", "f02.txt"))

    run_app(app, [tag, lambda a: None, drag_from("selected-files"), Until(lambda a: seen)])
    assert seen == [["f01.txt", "f02.txt"]]


def test_the_totals_line_drags_every_file(place, monkeypatch):
    app = app_in(place)
    seen = dropped(app, monkeypatch)
    monkeypatch.setattr(SETTINGS.panel_defaults, "totals", True)
    run_app(app, [drag_from("totals"), Until(lambda a: seen)])
    assert len(seen[0]) == 30


def test_without_drag_and_drop_the_lines_start_nothing(place, monkeypatch):
    monkeypatch.setattr(SETTINGS.file_manager, "drag_drop_columns", False)
    app = app_in(place)
    seen = {}
    run_app(app, [press(left, "current-file"), lambda a: None, lambda a: seen.update(drag=left(a)._drag)])
    assert seen["drag"] is None
