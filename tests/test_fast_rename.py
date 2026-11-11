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
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
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
                  KeyEvent("enter"), Until(lambda a: (place / "z.txt").exists()),
                  # The panel's re-read runs on a thread: its cursor is right once that is back.
                  Until(lambda a: a.manager.left.selected is not None and a.manager.left.selected.name == "z.txt"),
                  lambda a: seen.update(at=a.manager.left.selected.name, marked=set(a.manager.left.marked),
                                        right=[e.name for e in a.manager.right.items])])
    assert not (place / "b.txt").exists() and (place / "z.txt").read_text() == "b.txt"
    assert seen["at"] == "z.txt" and seen["marked"] == {"z.txt"}
    assert "z.txt" in seen["right"]


def test_the_other_panel_on_the_same_directory_lands_on_the_new_name_too(place):
    """Both panels show *place*: the passive one's cursor, on ``..``, goes to
    the renamed file, as F5/F6 put it on what they made."""
    app = navigator(place)
    seen = {}
    run_app(app, [to("b.txt"), KeyEvent("f6", alt=True), Until(editing), *typed("z.txt"),
                  KeyEvent("enter"),
                  # Each panel re-reads on its own thread: wait for both, not the first back.
                  Until(lambda a: all(side.selected is not None and side.selected.name == "z.txt"
                                      for side in (a.manager.left, a.manager.right))),
                  lambda a: seen.update(left=a.manager.left.selected.name, right=a.manager.right.selected.name)])
    assert seen == {"left": "z.txt", "right": "z.txt"}


def test_down_renames_and_then_moves_the_cursor(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("f6", alt=True), Until(editing), *typed("x.txt"),
                  KeyEvent("down"), Until(lambda a: (place / "x.txt").exists() and not editing(a)),
                  Until(lambda a: a.manager.left.selected is not None and a.manager.left.selected.name == "x.txt"),
                  lambda a: seen.update(at=a.manager.left.selected.name)])
    # x.txt sorts last; Down from it stays there, on the last row.
    names = sorted(p.name for p in place.iterdir())
    assert names == ["b.txt", "c.txt", "x.txt"] and seen["at"] == "x.txt"


def test_down_on_an_unchanged_name_renames_nothing_and_stays(place):
    # DN's ``cmCancel`` for the name as it was: the Down is not the panel's.
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("f6", alt=True), Until(editing), KeyEvent("down"),
                  Until(lambda a: not editing(a)), lambda a: None, lambda a: None,
                  lambda a: seen.update(at=a.manager.left.selected.name)])
    assert seen["at"] == "a.txt"
    assert sorted(p.name for p in place.iterdir()) == ["a.txt", "b.txt", "c.txt"]


def test_a_change_of_case_alone_renames(place):
    # A departure: DN compared the names upper-cased.
    app = navigator(place)
    run_app(app, [to("a.txt"), KeyEvent("f6", alt=True), Until(editing), *typed("A.txt"), KeyEvent("enter"),
                  Until(lambda a: not editing(a) and "A.txt" in {p.name for p in place.iterdir()})])
    names = {p.name for p in place.iterdir()}
    assert "A.txt" in names and "a.txt" not in names


def test_a_refused_rename_ended_by_down_still_moves_the_cursor(place):
    # DN posted the key after the rename was tried, whether or not it went.
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("f6", alt=True), Until(editing), *typed("c.txt"), KeyEvent("down"),
                  Until(lambda a: a.modal is not None and not editing(a)), KeyEvent("enter"),
                  Until(lambda a: a.modal is None), lambda a: None, lambda a: None,
                  lambda a: seen.update(at=a.manager.left.selected.name)])
    assert (place / "a.txt").read_text() == "a.txt"
    assert seen["at"] == "b.txt"


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
