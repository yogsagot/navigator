"""Alt+F8: DOS Navigator's *Commands history* (``CmdHistory``, ``TTHistList``)."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navml.history import HISTORY


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for command in ("ls", "pwd", "make"):
        HISTORY.add("command", command)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))


def listing(a) -> bool:
    return a.modal is not None and a.modal.title == "Commands history"


def test_the_oldest_at_the_top_the_cursor_on_the_newest_and_drop_puts_it_on_the_line(app):
    seen = {}
    run_app(app, [KeyEvent("f8", alt=True), Until(listing),
                  lambda a: seen.update(items=list(a.modal.commands.items), at=a.modal.commands.selected),
                  KeyEvent("up"), KeyEvent("d", alt=True), lambda a: None,
                  lambda a: seen.update(line=a.shell.command_line.value, modal=a.modal)])
    assert seen["items"] == ["ls", "pwd", "make"] and seen["at"] == "make"
    assert seen["line"] == "pwd" and seen["modal"] is None


def test_run_runs_it(app):
    ran = []
    app.shell.run_command = lambda command, typed=True: ran.append(command)
    run_app(app, [KeyEvent("f8", alt=True), Until(listing), KeyEvent("enter"), lambda a: None])
    assert ran == ["make"]


def test_a_marked_command_is_kept_from_kill_and_del_kills_the_rest(app):
    seen = {}
    run_app(app, [KeyEvent("f8", alt=True), Until(listing),
                  KeyEvent("home"), KeyEvent("space"), KeyEvent("delete"),
                  KeyEvent("down"), KeyEvent("k", alt=True), lambda a: None,
                  lambda a: seen.update(items=list(a.modal.commands.items), kept=set(a.modal.commands.kept)),
                  KeyEvent("escape"), lambda a: None])
    assert seen["items"] == ["ls", "make"] and seen["kept"] == {"ls"}
    assert HISTORY.entries("command") == ["make", "ls"] and HISTORY.is_pinned("command", "ls")


def test_edit_changes_a_command_and_keeps_its_mark(app):
    seen = {}

    def retype(a):
        a.modal.line.value = "make all"

    run_app(app, [KeyEvent("f8", alt=True), Until(listing), KeyEvent("space"),
                  KeyEvent("e", alt=True), Until(lambda a: a.modal is not None and a.modal.title == "Edit History"),
                  lambda a: seen.update(was=a.modal.line.value), retype, KeyEvent("enter"), Until(listing),
                  lambda a: seen.update(items=list(a.modal.commands.items), at=a.modal.commands.selected),
                  KeyEvent("escape"), lambda a: None])
    assert seen["was"] == "make"
    assert seen["items"] == ["ls", "pwd", "make all"] and seen["at"] == "make all"
    assert HISTORY.is_pinned("command", "make all")
