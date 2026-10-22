"""Ctrl+H's hidden files and Alt+I's footer, kept per side across runs (``panel_state``)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app

from navigator.__main__ import Navigator
from navigator.lib.config import panel_state
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager import Manager


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    SETTINGS.startup.autosave_desktop = False
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
    return tmp_path


def navigator(place) -> Navigator:
    return Navigator(place / "one", place / "two", terminal=FakeTerminal(100, 30))


def sides(a) -> dict:
    left, right = a.manager.left, a.manager.right
    return {"left": (left.show_hidden, left.show_info), "right": (right.show_hidden, right.show_info)}


def test_what_each_side_was_left_showing_comes_back_at_the_next_start(place):
    from navkit.events import KeyEvent

    run_app(navigator(place), [KeyEvent("ctrl+h"), KeyEvent("tab"), KeyEvent("alt+i")])
    seen = {}
    run_app(navigator(place), [lambda a: seen.update(sides(a))])
    assert seen == {"left": (False, True), "right": (True, False)}


def test_a_new_manager_takes_each_sides_kept_state(place):
    manager = Manager(place / "one", place / "two")
    manager.left.show_info = False
    manager.right.show_hidden = False
    panel_state.remember(manager, "left")
    panel_state.remember(manager, "right")
    fresh = Manager(place / "two", place / "one")
    assert (fresh.left.show_hidden, fresh.left.show_info) == (True, False)
    assert (fresh.right.show_hidden, fresh.right.show_info) == (False, True)


def test_with_nothing_kept_the_system_setting_decides(place):
    SETTINGS.system.show_hidden = False
    manager = Manager(place / "one", place / "two")
    assert not manager.left.show_hidden and manager.left.show_info
