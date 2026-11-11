"""Ctrl+E / Ctrl+X on the command line: DN's walk through the history, the typed draft kept aside."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent
from navml.history import HISTORY

from navigator.__main__ import Navigator


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for command in ("ls", "pwd", "make"):
        HISTORY.add("command", command)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))


def typed(text):
    return [KeyEvent(c, c) for c in text]


def walk(app, keys):
    """The line after each of *keys*: a list of ``(value, cursor)``."""
    seen = []
    actions = []
    for key in keys:
        actions += [key] if isinstance(key, KeyEvent) else key
        actions.append(lambda a: seen.append((a.shell.command_line.value, a.shell.command_line.cursor)))
    run_app(app, actions)
    return seen


E, X = KeyEvent("e", ctrl=True), KeyEvent("x", ctrl=True)


def test_past_the_newest_the_draft_comes_back(app):
    seen = walk(app, [typed("ech"), E, X])
    assert [v for v, _ in seen] == ["ech", "make", "ech"]
    assert seen[-1][1] == 3  # the caret at its end
    assert HISTORY.entries("command") == ["make", "pwd", "ls"]  # nothing unrun went in


def test_back_and_forth(app):
    seen = walk(app, [E, E, X, X])
    assert [v for v, _ in seen] == ["make", "pwd", "make", ""]


def test_an_edited_entry_becomes_the_draft_and_the_walk_starts_again(app):
    # DN's StrModified: AddCommand, and CurString back at the newest -- here kept aside.
    seen = walk(app, [E, E, typed(" all"), E, X])
    assert [v for v, _ in seen] == ["make", "pwd", "pwd all", "make", "pwd all"]
    assert "pwd all" not in HISTORY.entries("command")


def test_moving_the_caret_is_no_edit_and_the_walk_goes_on(app):
    seen = walk(app, [E, KeyEvent("left"), E])
    assert [v for v, _ in seen] == ["make", "make", "pwd"]


def test_escape_forgets_the_draft(app):
    seen = walk(app, [typed("ech"), E, KeyEvent("escape"), X])
    assert [v for v, _ in seen] == ["ech", "make", "", ""]


def test_shift_up_and_down_from_the_panels_keep_it_too(app):
    seen = walk(app, [typed("ech"), KeyEvent("up", shift=True), KeyEvent("down", shift=True)])
    assert [v for v, _ in seen] == ["ech", "make", "ech"]
