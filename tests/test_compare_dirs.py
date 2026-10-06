"""Panel > Compare directories: ``CM_CompareDirs``, what each panel has that the other lacks or has older."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.dircompare import CompareRequest, differing, tagged
from navigator.widgets.manager.compare_dialog import CompareDialog
from navigator.widgets.manager.panel.panel import DirEntry


def file(name: str, size: int = 1, mtime: float = 100.0, mode: int = 0o100644) -> DirEntry:
    return DirEntry(name, False, size, mode, mtime)


def test_a_file_matches_one_of_its_name_passing_every_check_asked():
    mine = [file("same"), file("newer", mtime=200), file("only"), file("bigger", size=9),
            file("mode", mode=0o100755), DirEntry("dir", True, 0)]
    theirs = [file("same"), file("newer"), file("bigger"), file("mode"), file("Only")]
    assert differing(mine, theirs, CompareRequest()) == {"newer", "only", "bigger"}
    assert differing(mine, theirs, CompareRequest(size=False, time=False)) == {"only"}
    assert differing(mine, theirs, CompareRequest(attributes=True)) == {"newer", "only", "bigger", "mode"}
    # An older copy here matches a newer one there; a fraction of a second is no newer.
    assert differing([file("a", mtime=100.9)], [file("a", mtime=100.1)], CompareRequest()) == set()
    assert differing([file("a")], [file("a", mtime=200)], CompareRequest()) == set()


def test_contents_reads_both_files(tmp_path):
    for side, text in (("one", b"abc"), ("two", b"abd")):
        (tmp_path / side).mkdir()
        (tmp_path / side / "f").write_bytes(text)
        (tmp_path / side / "g").write_bytes(b"same")
    mine, theirs = [file("f", 3), file("g", 4)], [file("f", 3), file("g", 4)]
    request = CompareRequest(contents=True)
    assert differing(mine, theirs, request, tmp_path / "one", tmp_path / "two") == {"f"}


def test_select_tags_exactly_what_differs_and_unselect_only_untags():
    assert tagged(frozenset({"x", "dir"}), {"a"}, CompareRequest()) == {"a"}
    assert tagged(frozenset({"x", "a"}), {"a", "b"}, CompareRequest(select=False)) == {"x"}


def test_the_dialog_opens_on_size_and_time_and_select():
    assert CompareDialog().accept() == CompareRequest()


# -- the file manager -----------------------------------------------------------------


@pytest.fixture
def sides(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    layout = {
        "west": {"a": (b"1", 100), "b": (b"2", 300), "c": (b"3", 100), "d": (b"44", 100)},
        "east": {"a": (b"1", 100), "b": (b"2", 100), "d": (b"4", 100), "e": (b"5", 100)},
    }
    for side, files in layout.items():
        (tmp_path / side / "sub").mkdir(parents=True)
        for name, (data, mtime) in files.items():
            path = tmp_path / side / name
            path.write_bytes(data)
            os.utime(path, (mtime, mtime))
    return tmp_path


def navigator(sides: Path) -> Navigator:
    return Navigator(sides / "west", sides / "east", terminal=FakeTerminal(80, 24))


def compare(app) -> None:
    """What the menu entry runs."""
    app.manager.spawn(app.manager.compare_directories())


def tags(app) -> tuple[set[str], set[str]]:
    return set(app.manager.left.marked), set(app.manager.right.marked)


def test_ok_tags_on_each_side_what_the_other_lacks_or_has_older(sides):
    app = navigator(sides)
    seen = {}

    def before(a):
        a.manager.left.marked = frozenset({"a", "sub"})

    run_app(app, [before, compare, lambda a: None,
                  lambda a: seen.update(title=a.modal.title if a.modal else None),
                  KeyEvent("enter"), lambda a: None, lambda a: seen.update(tags=tags(a))])
    assert seen["title"] == "Compare directories"
    assert seen["tags"] == ({"b", "c", "d"}, {"d", "e"})


def test_unselect_only_takes_what_differs_out_of_the_tags(sides):
    app = navigator(sides)
    seen = {}

    def before(a):
        a.manager.left.marked = frozenset({"a", "c"})

    run_app(app, [before, compare, lambda a: None,
                  KeyEvent("u", alt=True), KeyEvent("enter"), lambda a: None,
                  lambda a: seen.update(tags=tags(a))])
    assert seen["tags"] == ({"a"}, set())


def test_escape_compares_nothing(sides):
    app = navigator(sides)
    seen = {}
    run_app(app, [compare, lambda a: None, KeyEvent("escape"), lambda a: None,
                  lambda a: seen.update(tags=tags(a))])
    assert seen["tags"] == (set(), set())


def test_compare_contents_finds_the_same_size_and_time_with_other_bytes(sides):
    (sides / "east" / "a").write_bytes(b"9")
    os.utime(sides / "east" / "a", (100, 100))
    app = navigator(sides)
    seen = {}
    run_app(app, [compare, lambda a: None,
                  KeyEvent("c", alt=True), KeyEvent("enter"),
                  Until(lambda a: a.manager.left.marked), lambda a: seen.update(tags=tags(a))])
    assert seen["tags"] == ({"a", "b", "c", "d"}, {"a", "d", "e"})


def test_a_hot_key_shared_with_cancel_goes_to_the_dialogs_own_control_first():
    import asyncio

    dialog = CompareDialog()
    assert asyncio.run(dialog.activate_shortcut("c"))
    assert dialog.options.value == 3 | 8  # *Compare contents* ticked, not Cancel pressed


def test_the_menu_entry_runs_it_and_ctrl_c_is_left_free(sides):
    from navigator.widgets.manager.commands import CompareDir

    app = navigator(sides)
    seen = {}

    def look(a):
        entry = next(item for item in a.manager.panel_menu.entries()
                     if getattr(item, "command", None) is CompareDir)
        seen.update(key=entry.key)

    run_app(app, [look, KeyEvent("c", ctrl=True), lambda a: None,
                  lambda a: seen.update(modal=a.modal)])
    assert seen["key"] in ("", None) and seen["modal"] is None
