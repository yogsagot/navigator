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


def dropped(name_up_steps):
    """Alt+F8, Up *name_up_steps* times from the newest, Alt+D (*Drop*)."""
    from conftest import Until

    return [KeyEvent("f8", alt=True), Until(lambda a: a.modal is not None and a.modal.title == "Commands history"),
            *[KeyEvent("up")] * name_up_steps, KeyEvent("d", alt=True), Until(lambda a: a.modal is None)]


def test_after_drop_ctrl_e_goes_on_from_the_command_chosen(app):
    # DN's ``CurString := DT.I``: ``pwd`` dropped, Ctrl+E is the one older.
    seen = walk(app, [dropped(1), E])
    assert [v for v, _ in seen] == ["pwd", "ls"]


def test_after_drop_ctrl_x_goes_on_to_the_newer_and_then_the_draft(app):
    seen = walk(app, [dropped(1), X, X])
    assert [v for v, _ in seen] == ["pwd", "make", ""]


def test_a_draft_typed_before_drop_comes_back(app):
    seen = walk(app, [typed("ech"), dropped(1), X, X])
    assert [v for v, _ in seen] == ["ech", "pwd", "make", "ech"]


def test_shift_up_recalls_onto_an_auto_hidden_empty_line_and_shows_it(app):
    from navigator.settings import SETTINGS

    SETTINGS.interface.auto_hide_command_line = True
    seen = {}
    run_app(app, [lambda a: seen.update(before=a.shell.command_line.visible), KeyEvent("up", shift=True),
                  lambda a: seen.update(value=a.shell.command_line.value, after=a.shell.command_line.visible)])
    assert seen == {"before": False, "value": "make", "after": True}


def test_shift_up_puts_nothing_on_a_hidden_line(app):
    from navigator.settings import SETTINGS

    SETTINGS.interface.hide_command_line = True
    seen = {}
    run_app(app, [KeyEvent("up", shift=True), lambda a: seen.update(value=a.shell.command_line.value)])
    assert seen["value"] == ""
