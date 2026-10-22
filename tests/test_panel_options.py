"""The option strip on each panel's bottom frame: Hidden files, the footer, the
view mode and the order, each panel's own, switched by a click."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent, MouseClickEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.manager.commands import SortBy, ToggleHidden, ToggleInfoLines, ToggleShowMode


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
    (tmp_path / "one" / "a.txt").write_text("a\n")
    return tmp_path


def navigator(place) -> Navigator:
    return Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))


def span(panel, command):
    return next(s for s in panel.options.spans if s[2].command is command)


def click(side, command):
    def action(app):
        panel = getattr(app.manager, side)
        strip = panel.options
        start = span(panel, command)[0]
        ox, oy = strip.offset()
        x, y = ox + strip.x + start, oy + strip.y
        app.post_event(MouseClickEvent(x=x, y=y, button="left", action="press"))
        app.post_event(MouseClickEvent(x=x, y=y, button="left", action="release"))
    return action


def test_both_panels_show_the_strip_on_the_bottom_frame_before_the_corner(place):
    seen = {}

    def look(a):
        for side in ("left", "right"):
            panel = getattr(a.manager, side)
            strip = panel.options
            seen[side] = (strip.visible, strip.y == panel.height - 1, strip.x + strip.width == panel.width - 3,
                          [s[2].command for s in strip.spans])

    run_app(navigator(place), [look])
    order = [ToggleHidden, ToggleInfoLines, ToggleShowMode, SortBy]
    assert seen["left"] == seen["right"] == (True, True, True, order)


def test_each_strip_lights_its_own_panels_switches(place):
    seen = {}

    def look(a):
        for side in ("left", "right"):
            panel = getattr(a.manager, side)
            seen[side] = tuple(panel.options._state(span(panel, c)[2])[0] for c in (ToggleHidden, ToggleInfoLines))

    run_app(navigator(place), [KeyEvent("ctrl+h"), look])
    assert seen == {"left": (False, True), "right": (True, True)}


def test_a_click_on_the_passive_panels_strip_switches_that_panel(place):
    seen = {}
    run_app(navigator(place), [click("right", ToggleHidden), lambda a: seen.update(
        active=a.manager.active_panel is a.manager.right,
        left=a.manager.left.show_hidden, right=a.manager.right.show_hidden)])
    assert seen == {"active": True, "left": True, "right": False}


def test_clicks_cycle_the_view_mode_and_open_the_sort_box(place):
    seen = {}
    run_app(navigator(place), [click("left", ToggleShowMode),
                               lambda a: seen.update(mode=a.manager.left.view_mode),
                               click("left", SortBy), lambda a: None,
                               lambda a: seen.update(modal=a.modal is not None), KeyEvent("escape")])
    assert seen["mode"] != SETTINGS.panel_defaults.view_mode and seen["modal"]


def test_the_labels_follow_the_mode_and_the_order(place):
    seen = {}

    def look(a):
        panel = a.manager.left
        panel.view_mode = "detailed"
        panel.sort_by("size", reverse=True)

    run_app(navigator(place), [look, lambda a: seen.update(
        labels=[s[3] for s in a.manager.left.options.spans][2:])])
    assert seen["labels"] == ["Detailed", "Size↑"]


def test_a_quick_search_keeps_the_strip_clear_of_its_label(place):
    seen = {}

    def look(a):
        panel = a.manager.left
        footer = panel.footer_text()
        strip = panel.options
        seen.update(searching=bool(footer),
                    clear=not strip.width or strip.x > panel.label_x(footer) + len(footer))

    run_app(navigator(place), [KeyEvent("s", ctrl=True), KeyEvent("a", "a"), look])
    assert seen == {"searching": True, "clear": True}


def test_the_strip_follows_its_setting(place):
    SETTINGS.file_manager.show_options = False
    seen = {}
    run_app(navigator(place), [lambda a: seen.update(shown=a.manager.left.options.visible)])
    assert not seen["shown"]
