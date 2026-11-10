"""Shift+Up/Down and Ctrl+Shift+Ins from the panels: the command line's, as DN's panel handed them on."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent
from navml.history import HISTORY

from navigator.__main__ import Navigator
from navigator.widgets.shell.command_line.command_line import HISTORY_ID


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a", "b", "c"):
        (tmp_path / name).write_text(name)
    return tmp_path


def test_shift_up_and_down_walk_the_history_and_the_cursor_stays(place):
    HISTORY.add(HISTORY_ID, "one")
    HISTORY.add(HISTORY_ID, "two")
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        seen.append((a.shell.command_line.value, a.manager.left.cursor))

    run_app(app, [lambda a: setattr(a.manager.left, "cursor", 1), look,
                  KeyEvent("up", shift=True), look, KeyEvent("up", shift=True), look,
                  KeyEvent("down", shift=True), look, KeyEvent("down", shift=True), look])
    assert seen == [("", 1), ("two", 1), ("one", 1), ("two", 1), ("", 1)]


def test_ctrl_shift_insert_copies_the_line(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("insert", ctrl=True, shift=True), lambda a: None,
                  *[KeyEvent(c, c) for c in "echo"], KeyEvent("insert", ctrl=True, shift=True), lambda a: None])
    texts = [text for text, _ in app.terminal.clipboard]
    assert texts == ["echo"]


def test_with_the_tree_holding_the_keyboard_the_line_is_untouched(place):
    HISTORY.add(HISTORY_ID, "one")
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, KeyEvent("tab"), lambda a: None,
                  KeyEvent("up", shift=True), lambda a: None])
    assert app.shell.command_line.value == ""
