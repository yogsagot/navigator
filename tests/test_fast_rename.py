"""Alt+F6: ``CM_RenameSingle``, the name at the cursor edited where it stands."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.manager.fast_rename import FastRenameLine


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_text(name)
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def to(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def typed(text: str) -> list[KeyEvent]:
    return [KeyEvent(c, c) for c in text]


def editing(app) -> bool:
    return isinstance(app.modal, FastRenameLine)


def test_the_line_lies_over_the_name_with_it_all_selected(place):
    app = navigator(place)
    seen = {}

    def look(a):
        line, panel = a.modal, a.manager.left
        x, y, width = panel.name_cell()
        ox, oy = panel.offset()
        seen.update(value=line.value, selected=line.selected_text,
                    at=(line.x + 1, line.y, line.width - 1), cell=(ox + panel.x + x, oy + panel.y + y, width))

    run_app(app, [to("b.txt"), KeyEvent("f6", alt=True), Until(editing), look, KeyEvent("escape")])
    assert seen["value"] == seen["selected"] == "b.txt"
    assert seen["at"] == seen["cell"]


def test_enter_renames_and_the_cursor_and_the_tag_go_with_the_file(place):
    app = navigator(place)
    seen = {}

    def tag(a):
        a.manager.left.marked = frozenset({"b.txt"})

    run_app(app, [tag, to("b.txt"), KeyEvent("f6", alt=True), Until(editing), *typed("z.txt"),
                  KeyEvent("enter"), Until(lambda a: (place / "z.txt").exists()), lambda a: None,
                  lambda a: seen.update(at=a.manager.left.selected.name, marked=set(a.manager.left.marked),
                                        right=[e.name for e in a.manager.right.items])])
    assert not (place / "b.txt").exists() and (place / "z.txt").read_text() == "b.txt"
    assert seen["at"] == "z.txt" and seen["marked"] == {"z.txt"}
    assert "z.txt" in seen["right"]


def test_down_renames_and_then_moves_the_cursor(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("f6", alt=True), Until(editing), *typed("x.txt"),
                  KeyEvent("down"), Until(lambda a: (place / "x.txt").exists() and not editing(a)),
                  lambda a: None, lambda a: None, lambda a: seen.update(at=a.manager.left.selected.name)])
    # x.txt sorts last; Down from it stays there, on the last row.
    names = sorted(p.name for p in place.iterdir())
    assert names == ["b.txt", "c.txt", "x.txt"] and seen["at"] == "x.txt"


def test_escape_renames_nothing_and_a_taken_name_is_refused(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("f6", alt=True), Until(editing), *typed("q"), KeyEvent("escape"),
                  lambda a: None,
                  to("a.txt"), KeyEvent("f6", alt=True), Until(editing), *typed("c.txt"), KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and not editing(a)),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter")])
    assert sorted(p.name for p in place.iterdir()) == ["a.txt", "b.txt", "c.txt"]
    assert seen["prompt"].startswith("Could not rename a.txt\nto c.txt")
    assert (place / "c.txt").read_text() == "c.txt"


def test_up_dir_is_never_renamed(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to(".."), KeyEvent("f6", alt=True), lambda a: None, lambda a: seen.update(modal=a.modal)])
    assert seen["modal"] is None


def test_a_slash_cannot_be_typed(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("f6", alt=True), Until(editing), KeyEvent("end"), *typed("/x"),
                  lambda a: seen.update(value=a.modal.value), KeyEvent("escape")])
    assert seen["value"] == "a.txtx"
