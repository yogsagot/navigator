"""Shift+F4 in the viewers is DN's ``cmXEditFile``, *Edit...*, as on every
status line of DN's; the view switches it had here moved to Shift+F3."""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.editor.edit_file_dialog import EditFileDialog


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "a.md").write_text("# Title\n\ntext\n")
    (tmp_path / "t.csv").write_text("a,b\n1,2\n")
    (tmp_path / "d.json").write_text('{"k": 1}\n')
    return tmp_path


def to(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def kinds(app):
    return [type(w).__name__ for w in app.shell.desktop.windows()]


def asked(app):
    return isinstance(app.modal, EditFileDialog)


@pytest.mark.parametrize("name, opens, view", [
    ("a.md", None, []),
    ("t.csv", "DBWindow", []),
    ("d.json", "StructWindow", [KeyEvent("f3", shift=True)]),
])
def test_shift_f4_in_a_viewer_asks_for_a_file_to_edit(place, name, opens, view):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}

    def name_it(a):
        a.modal.entry.value = "new.txt"

    run_app(app, [to(name), KeyEvent("f3"), Until(lambda a: len(a.shell.desktop.windows()) == 2), *view, IDLE,
                  lambda a: seen.update(kinds=kinds(a)),
                  KeyEvent("f4", shift=True), Until(asked), name_it, KeyEvent("enter"),
                  Until(lambda a: "EditWindow" in kinds(a)), lambda a: seen.update(after=kinds(a))])
    if opens:
        assert opens in seen["kinds"]
    assert "EditWindow" in seen["after"]


def test_shift_f3_and_shift_f4_in_the_quick_view(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 24))
    seen = {}

    def into_quick(a):
        a.manager.quick.viewer.focus()

    run_app(app, [to("a.md"), KeyEvent("q", ctrl=True),
                  Until(lambda a: a.manager.quick is not None and a.manager.quick.viewer.rendering),
                  into_quick, KeyEvent("f3", shift=True), IDLE,
                  lambda a: seen.update(rendering=a.manager.quick.viewer.rendering),
                  KeyEvent("f4", shift=True), Until(asked), KeyEvent("escape")])
    assert seen["rendering"] is False
