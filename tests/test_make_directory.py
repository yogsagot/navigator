"""F7 as DN's ``MakeDirectory``: a ``;`` list, parents made, one there already accepted, DN's cursor and words."""

from __future__ import annotations

import asyncio

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navml.widgets.dialog.dialog import Dialog

from navigator.__main__ import Navigator
from navigator.lib.drives import Location
from navigator.lib.file_ops.undo import UNDO
from navigator.widgets.file_ops.make_directory import make_directories, parts_of
from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "here").mkdir()
    (tmp_path / "here" / "zzz.txt").write_text("z")
    (tmp_path / "here" / "there").mkdir()
    UNDO.clear()
    return tmp_path


def f7(text):
    """F7, *text* typed into the box, Enter."""
    def typed(a):
        a.modal.entry.value = text
    return [KeyEvent("f7"), Until(lambda a: isinstance(a.modal, MkdirDialog)), typed, KeyEvent("enter")]


def cursor_name(a):
    panel = a.manager.left
    return panel.items[panel.cursor].name


def on(name):
    def act(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return act


def test_the_parts_of_a_list():
    assert parts_of(" a ;; b/c ;") == ["a", "b/c"]


def test_a_path_makes_every_directory_on_its_way_and_leaves_the_cursor(place):
    here = place / "here"
    app = Navigator(here, place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [Until(lambda a: len(a.manager.left.items) > 2), on("zzz.txt"), *f7("a/b"),
                  Until(lambda a: (here / "a" / "b").is_dir() and a.modal is None),
                  Until(lambda a: "a" in [e.name for e in a.manager.left.items]),
                  lambda a: seen.update(cursor=cursor_name(a))])
    assert (here / "a" / "b").is_dir()
    assert seen["cursor"] == "zzz.txt"  # ``if Dr <> P^.DirectoryName then Exit``


def test_a_list_makes_each_and_the_cursor_goes_to_the_first(place):
    here = place / "here"
    app = Navigator(here, place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [Until(lambda a: len(a.manager.left.items) > 2), *f7("x; y"),
                  Until(lambda a: (here / "y").is_dir() and a.modal is None),
                  Until(lambda a: cursor_name(a) == "x"), lambda a: seen.update(cursor=cursor_name(a))])
    assert (here / "x").is_dir() and (here / "y").is_dir() and not (here / "x; y").exists()
    assert seen["cursor"] == "x"


def test_one_there_already_is_accepted_and_the_cursor_goes_to_it(place):
    here = place / "here"
    app = Navigator(here, place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [Until(lambda a: len(a.manager.left.items) > 2), on("zzz.txt"), *f7("there"),
                  Until(lambda a: a.modal is None and cursor_name(a) == "there"),
                  lambda a: seen.update(cursor=cursor_name(a), modal=a.modal)])
    assert seen == {"cursor": "there", "modal": None}


def test_a_file_in_the_way_is_dn_s_could_not_create_the_directory(place):
    here = place / "here"
    app = Navigator(here, place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [Until(lambda a: len(a.manager.left.items) > 2), *f7("zzz.txt"),
                  Until(lambda a: isinstance(a.modal, Dialog) and not isinstance(a.modal, MkdirDialog)),
                  lambda a: seen.update(title=a.modal.title, prompt=a.modal.prompt), KeyEvent("enter"),
                  Until(lambda a: a.modal is None)])
    assert seen["title"] == "Error"
    assert seen["prompt"].splitlines()[0] == f"Could not create the directory {here / 'zzz.txt'}"


def test_the_box_says_directory_name():
    box = MkdirDialog()
    assert box.entry.label_text.replace("~", "") == "Directory name"


def test_another_panel_showing_the_base_reads_it_again(place):
    here = place / "here"
    app = Navigator(here, here, terminal=FakeTerminal(80, 24))
    run_app(app, [Until(lambda a: len(a.manager.right.items) > 2), *f7("fresh"),
                  Until(lambda a: "fresh" in [e.name for e in a.manager.right.items])])
    assert "fresh" in [e.name for e in app.manager.right.items]


def test_undo_takes_back_the_new_directories_above_too(place):
    here = place / "here"
    app = Navigator(here, place, terminal=FakeTerminal(80, 24))

    def undo(a):
        entry = UNDO.peek()
        a.manager.spawn(a.manager._undo_mkdir(a.manager.left, entry))

    run_app(app, [Until(lambda a: len(a.manager.left.items) > 2), *f7("a/b"),
                  Until(lambda a: (here / "a" / "b").is_dir() and a.modal is None), undo,
                  Until(lambda a: not (here / "a").exists())])
    assert not (here / "a").exists()


def test_undo_leaves_a_directory_that_was_there(place):
    here = place / "here"
    app = Navigator(here, place, terminal=FakeTerminal(80, 24))

    def undo(a):
        entry = UNDO.peek()
        a.manager.spawn(a.manager._undo_mkdir(a.manager.left, entry))

    run_app(app, [Until(lambda a: len(a.manager.left.items) > 2), *f7("there/b"),
                  Until(lambda a: (here / "there" / "b").is_dir() and a.modal is None), undo,
                  Until(lambda a: not (here / "there" / "b").exists())])
    assert (here / "there").is_dir()


def test_alt_t_s_making_takes_a_list_and_parents_too(place):
    here = place / "here"
    results, failure = asyncio.run(make_directories(None, here, "p/q;r"))
    assert failure is None and (here / "p" / "q").is_dir() and (here / "r").is_dir()
    assert [m.place for m in results] == [Location.of(here / "p" / "q"), Location.of(here / "r")]
    assert [m.top for m in results] == [Location.of(here / "p"), Location.of(here / "r")]
