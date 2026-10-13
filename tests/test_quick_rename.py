"""File > Quick rename: one entry's new name, asked in a box."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.widgets.file_ops.rename_dialog import RenameDialog
from navigator.widgets.manager.commands import QuickRename


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


def rename(app) -> None:
    """What the menu item does: the command run as if its key were pressed."""
    app.spawn(app.run_command(QuickRename))


def asking(app) -> bool:
    return isinstance(app.modal, RenameDialog)


def test_the_box_holds_the_name_with_its_stem_selected_and_enter_renames(place):
    app = navigator(place)
    seen = {}

    def look(a):
        seen.update(value=a.modal.line.value, selected=a.modal.line.entry.selected_text)

    run_app(app, [to("b.txt"), rename, Until(asking), look, *typed("z"), KeyEvent("enter"),
                  Until(lambda a: (place / "z.txt").exists()), lambda a: None,
                  lambda a: seen.update(at=a.manager.left.selected.name)])
    assert seen["value"] == "b.txt" and seen["selected"] == "b"
    assert not (place / "b.txt").exists() and (place / "z.txt").read_text() == "b.txt"
    assert seen["at"] == "z.txt"


def test_the_one_tagged_file_is_renamed_not_the_cursors(place):
    app = navigator(place)

    def tag(a):
        a.manager.left.marked = frozenset({"c.txt"})

    run_app(app, [tag, to("a.txt"), rename, Until(asking), *typed("y"), KeyEvent("enter"),
                  Until(lambda a: (place / "y.txt").exists())])
    assert sorted(p.name for p in place.iterdir()) == ["a.txt", "b.txt", "y.txt"]


def test_enabled_only_for_one_entry(place):
    app = navigator(place)
    seen = []

    def check(a):
        seen.append(a.manager.enables(QuickRename()))

    def tag_two(a):
        a.manager.left.marked = frozenset({"a.txt", "b.txt"})

    run_app(app, [to(".."), check, to("a.txt"), check, tag_two, check])
    assert seen == [False, True, False]


def test_escape_and_a_taken_name_rename_nothing(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), rename, Until(asking), *typed("q"), KeyEvent("escape"), lambda a: None,
                  rename, Until(asking), *typed("c"), KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and not asking(a)),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter")])
    assert sorted(p.name for p in place.iterdir()) == ["a.txt", "b.txt", "c.txt"]
    assert seen["prompt"].startswith("Could not rename a.txt\nto c.txt")


def test_shift_f6_opens_it(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("f6", shift=True), Until(asking),
                  lambda a: seen.update(value=a.modal.line.value), KeyEvent("escape")])
    assert seen["value"] == "a.txt"


@pytest.mark.parametrize("name, is_dir, selected", [
    ("notes.txt", False, "notes"),
    ("a.tar.gz", False, "a.tar"),
    (".bashrc", False, ".bashrc"),
    ("README", False, "README"),
    ("conf.d", True, "conf.d"),
])
def test_the_stem_is_what_is_selected(name, is_dir, selected):
    box = RenameDialog(name=name, is_dir=is_dir)
    assert box.line.entry.selected_text == selected
    assert box.line.entry.cursor == len(selected)
