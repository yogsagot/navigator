"""Alt+L: ``MakeListFile``, the tagged files written to a list file."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.makelist import AUTO_PATHS, STORE_PATHS, make_lines, templates
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
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
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
                  lambda a: None,
                  lambda a: seen.update(listed="dnlist.txt" in [e.name for e in a.manager.left.items])])
    assert seen["title"] == "Make List File" and seen["name"] == "dnlist.txt" and seen["action"] == "ls -l"
    assert (place / "dnlist.txt").read_text() == "a.txt\nc.c\n"
    assert seen["listed"]


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

    run_app(app, [tag, KeyEvent("l", alt=True), lambda a: None, make, KeyEvent("enter"), lambda a: None,
                  KeyEvent("p", alt=True), Until(lambda a: (place / "dnlist.txt").read_text() != "old\n")])
    assert (place / "dnlist.txt").read_text() == "old\nb.txt\n"
