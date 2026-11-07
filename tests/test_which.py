"""``navigator/lib/system/which.py``: ``shutil.which`` remembered a moment --
and a menu held open costs no ``$PATH`` walk per frame."""

from __future__ import annotations

import shutil

import pytest

from navigator.lib.system import which as which_module
from navigator.lib.system.which import which


@pytest.fixture
def counted(monkeypatch):
    """``shutil.which`` replaced by one that counts what it is asked."""
    asked = []

    def fake(name, path=None):
        asked.append(name)
        return f"/usr/bin/{name}"

    monkeypatch.setattr(shutil, "which", fake)
    return asked


def test_an_answer_is_kept(counted):
    assert which("gpg") == which("gpg") == "/usr/bin/gpg"
    assert counted == ["gpg"]


def test_a_changed_path_is_looked_through_at_once(counted, monkeypatch):
    which("gpg")
    monkeypatch.setenv("PATH", "/opt/elsewhere")
    which("gpg")
    assert counted == ["gpg", "gpg"]


def test_a_which_put_in_place_is_asked_at_once(counted, monkeypatch):
    which("gpg")
    monkeypatch.setattr(shutil, "which", lambda name, path=None: None)
    assert which("gpg") is None


def test_after_the_ttl_it_looks_again(counted, monkeypatch):
    monkeypatch.setattr(which_module, "TTL", 0.0)
    which("gpg")
    which("gpg")
    assert counted == ["gpg", "gpg"]


def test_forget_looks_again(counted):
    which("gpg")
    which_module.forget()
    which("gpg")
    assert counted == ["gpg", "gpg"]


def test_menus_asked_again_and_again_walk_path_once_a_program(tmp_path, counted, monkeypatch):
    from conftest import FakeTerminal, run_app
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))
    seen = {}

    def ask(a):
        from navml.widgets.menu.menu_item import MenuItem

        entries = []

        def walk(items):
            for item in items or ():
                if isinstance(item, MenuItem) and getattr(item, "command", None) is not None:
                    entries.append(item.command)
                walk(getattr(item, "items", None) or getattr(item, "children", None))

        walk(a.shell.menu.children)
        counted.clear()
        for _ in range(10):
            for command in entries:
                a.command_enabled(command, a.manager.left)
        seen["entries"] = len(entries)
        seen["asked"] = list(counted)

    run_app(app, [ask])
    assert seen["entries"] > 50
    assert len(seen["asked"]) == len(set(seen["asked"])), seen["asked"]
