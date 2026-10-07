"""File > Execute OS command: DOS Navigator's ``ExecDOSCmd``."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.shell.commands import ExecuteOsCommand


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "my tool.sh").write_text("#!/bin/sh\n")
    (tmp_path / "my tool.sh").chmod(0o755)
    (tmp_path / "notes.txt").write_text("x")
    navigator = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    navigator.ran = []
    navigator.shell.run_command = lambda command, typed=True: navigator.ran.append(command)
    return navigator


def to(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def asking(a) -> bool:
    return a.modal is not None and a.modal.title == "Execute OS Command"


def test_an_executable_at_the_cursor_is_offered_and_ok_runs_the_line(app):
    seen = {}
    run_app(app, [to("my tool.sh"), lambda a: a.spawn(a.run_command(ExecuteOsCommand)), Until(asking),
                  lambda a: seen.update(line=a.modal.line.value, caption=a.modal.caption),
                  *[KeyEvent(c, c) for c in "--help"], KeyEvent("enter"), lambda a: None])
    assert seen["line"] == "my\\ tool.sh " and seen["caption"] == "~C~ommand"
    assert app.ran == ["my\\ tool.sh --help"]


def test_another_file_offers_nothing_and_cancel_runs_nothing(app):
    seen = {}
    run_app(app, [to("notes.txt"), lambda a: a.spawn(a.run_command(ExecuteOsCommand)), Until(asking),
                  lambda a: seen.update(line=a.modal.line.value), KeyEvent("escape"), lambda a: None])
    assert seen["line"] == "" and app.ran == []
