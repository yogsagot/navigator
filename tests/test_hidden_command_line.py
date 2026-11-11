"""*Hide command line* (DN's ``ouiHideCmdline``): the hidden line takes nothing, and never takes the panel's keys."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent, PasteEvent
from navml.history import HISTORY

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a.txt", "b.txt"):
        (tmp_path / name).write_text(name)
    return tmp_path


def on(name):
    def act(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return act


def hide(a):
    SETTINGS.interface.hide_command_line = True


def test_a_paste_puts_nothing_on_a_hidden_line_and_space_still_tags(place):
    # DN's hidden ``TCommandLine`` took no keys, Shift+Ins's paste among them.
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [hide, on("a.txt"), PasteEvent("echo hi"), lambda a: None,
                  lambda a: seen.update(line=a.shell.command_line.value),
                  KeyEvent("space"), lambda a: None, lambda a: seen.update(marked=set(a.manager.left.marked))])
    assert seen["line"] == ""
    assert "a.txt" in seen["marked"]


def test_text_left_on_a_hidden_line_never_takes_the_panel_s_keys(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}

    def leave_text(a):
        a.shell.command_line.set_text("left over")
        SETTINGS.interface.hide_command_line = True

    run_app(app, [leave_text, on("a.txt"), KeyEvent("space"), lambda a: None,
                  lambda a: seen.update(marked=set(a.manager.left.marked), line=a.shell.command_line.value)])
    assert "a.txt" in seen["marked"]
    assert seen["line"] == "left over"  # kept for when the line is shown again


def test_drop_in_commands_history_puts_nothing_on_a_hidden_line(place):
    HISTORY.add("command", "make")
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [hide, KeyEvent("f8", alt=True),
                  Until(lambda a: a.modal is not None and a.modal.title == "Commands history"),
                  KeyEvent("d", alt=True), Until(lambda a: a.modal is None),
                  lambda a: seen.update(line=a.shell.command_line.value)])
    assert seen["line"] == ""


def test_a_paste_still_lands_on_a_shown_line(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [PasteEvent("echo hi"), lambda a: None, lambda a: seen.update(line=a.shell.command_line.value)])
    assert seen["line"] == "echo hi"
