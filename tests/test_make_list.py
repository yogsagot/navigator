"""Alt+L: ``MakeListFile``, the tagged files written to a list file."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.file_ops.makelist import AUTO_PATHS, STORE_PATHS, make_lines, templates
from navml.history import HISTORY

FILES = [Path("/w/a b.txt"), Path("/w/README")]


def test_a_plain_list_is_the_names_as_they_are_or_the_paths():
    assert make_lines(FILES, "", Path("/w"), 0) == ["a b.txt", "README"]
    assert make_lines(FILES, "", Path("/w"), STORE_PATHS) == ["/w/a b.txt", "/w/README"]
    assert make_lines(FILES, "", Path("/w"), AUTO_PATHS) == ["a b.txt", "README"]
    assert make_lines(FILES, "", Path("/x"), AUTO_PATHS) == ["/w/a b.txt", "/w/README"]


def test_an_action_without_macros_is_followed_by_the_quoted_file():
    assert make_lines(FILES, "cp ", Path("/w"), 0) == ["cp 'a b.txt'", "cp README"]


def test_each_template_is_a_line_and_autodetermine_puts_the_directory_in():
    assert templates("a;b;;c") == ["a", "b;c"]
    lines = make_lines(FILES, "cp !.! /bk;rm !.!", Path("/x"), AUTO_PATHS)
    assert lines == ["cp /w/'a b'.txt /bk", "rm /w/'a b'.txt", "cp /w/README /bk", "rm /w/README"]
    assert make_lines(FILES[1:], "echo !! !/ !\\ [!:]", Path("/w"), 0) == ["echo ! /w /w/ []"]


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a.txt", "b.txt", "c.c"):
        (tmp_path / name).write_text(name)
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def test_alt_l_writes_the_tagged_names_untags_them_and_the_panel_shows_the_list(place):
    HISTORY.add("command", "ls -l")
    app = navigator(place)
    seen = {}

    def tag(a):
        a.manager.left.marked = frozenset({"a.txt", "c.c"})

    def look(a):
        d = a.modal
        seen.update(title=d.title, name=d.file_name.value, action=d.action.value)
        d.action.value = ""

    run_app(app, [tag, KeyEvent("l", alt=True), lambda a: None, look, KeyEvent("enter"),
                  Until(lambda a: (place / "dnlist.txt").exists() and not a.manager.left.marked),
                  # The panel's re-read runs on a thread: the list is in it once that is back.
                  Until(lambda a: "dnlist.txt" in [e.name for e in a.manager.left.items], timeout=5),
                  lambda a: seen.update(listed="dnlist.txt" in [e.name for e in a.manager.left.items])])
    assert seen["title"] == "Make List File" and seen["name"] == "dnlist.txt" and seen["action"] == "ls -l"
    assert (place / "dnlist.txt").read_text() == "a.txt\nc.c\n"
    assert seen["listed"]


def _boxes(app, setup, *, ticking=None):
    """Alt+L over what *setup* tags: the boxes as the dialog opens, then
    *ticking* (a value for them) and OK with no action."""
    seen = {}

    def look(a):
        seen["opened"] = a.modal.options.value
        a.modal.action.value = ""
        if ticking is not None:
            a.modal.options.value = ticking

    run_app(app, [setup, KeyEvent("l", alt=True),
                  Until(lambda a: type(a.modal).__name__ == "MakeListDialog"), look, KeyEvent("enter"),
                  Until(lambda a: a.modal is None)])
    return seen["opened"]


def test_the_boxes_are_kept_in_the_settings(place):
    # DN's ``MakeListFileOptions``, kept in ``cfgMakeListFile``.
    from navigator.settings import SETTINGS

    def tag(a):
        a.manager.left.marked = frozenset({"a.txt"})

    _boxes(navigator(place), tag, ticking=AUTO_PATHS)
    assert (SETTINGS.make_list.store_paths, SETTINGS.make_list.auto_paths) == (False, True)
    assert re.search(r"^auto_paths\s*=\s*yes\b", SETTINGS.path.read_text(), re.M)


def test_one_directory_unticks_a_remembered_store_path_names(place):
    from navigator.settings import SETTINGS

    SETTINGS.make_list.store_paths = True

    def tag(a):
        a.manager.left.marked = frozenset({"a.txt", "b.txt"})

    assert _boxes(navigator(place), tag) & STORE_PATHS == 0
    assert SETTINGS.make_list.store_paths is False  # OK keeps the untick, as DN's did


def test_a_listing_of_two_directories_keeps_store_path_names(place):
    from navigator.lib.drives.listing import DirEntry
    from navigator.lib.file_ops.filefind import FindListing
    from navigator.settings import SETTINGS

    (place / "one").mkdir()
    (place / "two").mkdir()
    (place / "one" / "x.txt").write_text("x")
    (place / "two" / "y.txt").write_text("y")
    SETTINGS.make_list.store_paths = True
    found = FindListing(title="*.txt", origin=place, entries=[
        DirEntry("x.txt", False, 1, directory=place / "one"), DirEntry("y.txt", False, 1, directory=place / "two")])

    def setup(a):
        panel = a.manager.left
        panel.show_found(found)

    def tag(a):
        panel = a.manager.left
        panel.marked = frozenset(e.key for e in panel.items if e.name != "..")

    app = navigator(place)
    seen = {}

    def look(a):
        seen["opened"] = a.modal.options.value

    run_app(app, [setup, Until(lambda a: len(a.manager.left.items) == 3), tag, KeyEvent("l", alt=True),
                  Until(lambda a: type(a.modal).__name__ == "MakeListDialog"), look, KeyEvent("escape")])
    assert seen["opened"] & STORE_PATHS


def test_with_nothing_tagged_select_comes_first(place):
    app = navigator(place)
    seen = {}

    def mask(a):
        seen["first"] = a.modal.title
        a.modal.mask.value = "*.txt"

    def make(a):
        a.modal.action.value = ""

    run_app(app, [KeyEvent("l", alt=True), lambda a: None, mask, KeyEvent("enter"), lambda a: None,
                  make, KeyEvent("enter"), Until(lambda a: (place / "dnlist.txt").exists())])
    assert seen["first"] == "Select"
    assert (place / "dnlist.txt").read_text() == "a.txt\nb.txt\n"


def test_a_list_already_there_can_be_appended_to(place):
    (place / "dnlist.txt").write_text("old\n")
    app = navigator(place)

    def tag(a):
        a.manager.left.marked = frozenset({"b.txt"})

    def make(a):
        a.modal.action.value = ""

    # Whether the list is there is asked on a thread; the question comes after.
    asking = Until(lambda a: a.modal is not None and type(a.modal).__name__ != "MakeListDialog")
    run_app(app, [tag, KeyEvent("l", alt=True), lambda a: None, make, KeyEvent("enter"), asking,
                  KeyEvent("p", alt=True), Until(lambda a: (place / "dnlist.txt").read_text() != "old\n")])
    assert (place / "dnlist.txt").read_text() == "old\nb.txt\n"
