"""Utilities > Edit environment: DOS Navigator's ``EditDOSEvironment``."""

from __future__ import annotations

import os

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.environ import apply, changes, valid_name
from navigator.subshell import Subshell
from navkit.console import ConsoleScreen


def test_changes_and_apply():
    assert changes({"A": "1", "B": "2", "C": "3"}, {"A": "1", "B": "x", "D": "4"}) == \
        {"C": None, "B": "x", "D": "4"}
    environ = {"A": "1", "C": "3"}
    apply({"C": None, "D": "4"}, environ)
    assert environ == {"A": "1", "D": "4"}
    assert valid_name("PATH") and not valid_name("") and not valid_name("A=B")


@pytest.mark.parametrize("shell, line", [
    ("/bin/bash", " export GREETING='hi there'; unset GONE"),
    ("/usr/bin/fish", " set -gx GREETING 'hi there'; set -e GONE"),
])
def test_the_running_shell_is_told_unseen(shell, line, monkeypatch):
    subshell = Subshell(ConsoleScreen(80, 24), shell=shell)
    monkeypatch.setattr(Subshell, "is_running", property(lambda self: True))
    subshell.can_complete = True
    subshell._send_next = lambda: None
    assert subshell.set_environment({"GREETING": "hi there", "GONE": None})
    assert subshell._queue == [(line, "silent")]


def test_a_shell_without_the_hook_is_not_told(monkeypatch):
    subshell = Subshell(ConsoleScreen(80, 24), shell="/bin/tcsh")
    monkeypatch.setattr(Subshell, "is_running", property(lambda self: True))
    subshell.can_complete = False
    assert not subshell.set_environment({"A": "1"}) and subshell._queue == []


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    saved = dict(os.environ)
    os.environ["NAV_TEST_KEEP"] = "old"
    os.environ["NAV_TEST_GONE"] = "bye"
    told = []
    monkeypatch.setattr(Subshell, "set_environment", lambda self, found: told.append(dict(found)))
    navigator = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))
    navigator.told = told
    yield navigator
    os.environ.clear()
    os.environ.update(saved)


def editing(a) -> bool:
    return a.modal is not None and a.modal.title == "Environment Variables Editor"


def titled(start: str):
    return lambda a: a.modal is not None and str(a.modal.title).startswith(start)


def test_edit_append_rename_delete_and_ok(app):
    from navigator.widgets.shell.commands import EnvEdit

    seen = {}

    def to(name):
        def action(a):
            a.modal.names.cursor = a.modal.names.items.index(name)
        return action

    def retype(text):
        def action(a):
            a.modal.line.value = text
        return action

    def change_value(a):
        a.modal.value.value = "new"

    run_app(app, [
        lambda a: a.spawn(a.run_command(EnvEdit)), Until(editing),
        to("NAV_TEST_KEEP"), lambda a: None,
        lambda a: seen.update(shown=a.modal.value.value), change_value, KeyEvent("down"), lambda a: None,
        KeyEvent("a", alt=True), Until(titled("Add Environment Variable")),
        retype("NAV_TEST_ADDED=yes=really"), KeyEvent("enter"), Until(editing), lambda a: None,
        to("NAV_TEST_ADDED"), KeyEvent("r", alt=True), Until(titled('Rename variable "NAV_TEST_ADDED"')),
        retype("NAV_TEST_RENAMED"), KeyEvent("enter"), Until(editing), lambda a: None,
        to("NAV_TEST_GONE"), KeyEvent("d", alt=True), Until(titled("Confirm")),
        lambda a: seen.update(ask=a.modal.prompt), KeyEvent("y", alt=True), Until(editing), lambda a: None,
        KeyEvent("k", alt=True), lambda a: None,
    ])
    assert seen["shown"] == "old"
    assert seen["ask"] == 'OK to delete the Environment\nvariable "NAV_TEST_GONE"'
    assert os.environ["NAV_TEST_KEEP"] == "new"
    assert os.environ["NAV_TEST_RENAMED"] == "yes=really"
    assert "NAV_TEST_GONE" not in os.environ and "NAV_TEST_ADDED" not in os.environ
    assert app.told == [{"NAV_TEST_GONE": None, "NAV_TEST_KEEP": "new", "NAV_TEST_RENAMED": "yes=really"}]


def test_cancel_changes_nothing(app):
    from navigator.widgets.shell.commands import EnvEdit

    def change_value(a):
        a.modal.value.value = "changed"

    run_app(app, [lambda a: a.spawn(a.run_command(EnvEdit)), Until(editing), change_value,
                  KeyEvent("escape"), lambda a: None])
    assert os.environ["NAV_TEST_KEEP"] == "old" and app.told == []
