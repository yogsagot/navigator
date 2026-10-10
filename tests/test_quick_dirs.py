"""Alt+Backspace's directory history, DN's quick directories as bookmarks, and Panel > Change drive."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navml.history import HISTORY
from navml.widgets.menu.popup_menu import PopupMenu


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def into(name: str):
    def action(app):
        panel = app.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
        panel.enter()
    return action


def listed(path: Path) -> Until:
    """Until the left panel shows *path*'s listing, read on a thread."""
    return Until(lambda a: a.manager.left._listed == path and not a.manager.left.scanning, timeout=5)


def titled(title: str):
    return lambda a: a.modal is not None and getattr(a.modal, "title", None) == title


def test_the_panels_directories_are_tracked_and_alt_backspace_goes_back_to_one(place):
    app = navigator(place)
    seen = {}
    run_app(app, [into("one"), lambda a: None, KeyEvent("backspace"), lambda a: None, into("two"),
                  lambda a: None,
                  KeyEvent("backspace", alt=True), Until(titled("Directories History")),
                  lambda a: seen.update(listed=list(a.modal.places.items)),
                  KeyEvent("down"), KeyEvent("down"), KeyEvent("enter"), lambda a: None, lambda a: None,
                  lambda a: seen.update(path=a.manager.left.path)])
    assert seen["listed"][:3] == [str(place / "two"), str(place), str(place / "one")]
    assert seen["path"] == place / "one"


def test_delete_record_takes_one_out_and_the_box_stays(place):
    app = navigator(place)
    seen = {}
    run_app(app, [into("one"), lambda a: None, KeyEvent("backspace", alt=True), Until(titled("Directories History")),
                  KeyEvent("d", alt=True), lambda a: None,
                  lambda a: seen.update(listed=list(a.modal.places.items), still=a.modal is not None),
                  KeyEvent("escape")])
    assert str(place / "one") not in seen["listed"] and seen["still"]
    assert str(place / "one") not in HISTORY.entries("directories")


def test_without_track_directories_it_says_to_turn_it_on(place):
    SETTINGS.interface.track_directories = False
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("backspace", alt=True), Until(titled("Error")),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter")])
    assert seen["prompt"] == 'Set the interface option\n"Track directories" ON first'
    assert HISTORY.entries("directories") == []


def test_place_bookmark_moves_or_inserts_at_a_position(place):
    from navigator.bookmarks import add_bookmark, bookmarks, place_bookmark

    for name in ("a", "b", "c"):
        add_bookmark(place / name)
    place_bookmark(place / "c", 1)
    assert [Path(r.path).name for r in bookmarks()] == ["c", "a", "b"]
    place_bookmark(place / "new", 2)
    assert [Path(r.path).name for r in bookmarks()] == ["c", "new", "a", "b"]
    place_bookmark(place / "end", 99)
    assert [Path(r.path).name for r in bookmarks()][-1] == "end"


def test_alt_shift_n_bookmarks_at_n_alt_n_goes_and_alt_shift_0_opens_the_box(place):
    from navigator.bookmarks import add_bookmark, bookmarks

    add_bookmark(place / "two")
    app = navigator(place)
    seen = {}
    # Storing a bookmark and going to one are spawned tasks, and a panel reads
    # its directory on a thread: each step waits for what it reads, not for a
    # fixed number of frames, which is enough only on an unloaded machine.
    run_app(app, [
        into("one"), listed(place / "one"),
        KeyEvent("1", alt=True, shift=True), Until(titled("Confirm"), timeout=5),
        lambda a: seen.update(ask=a.modal.prompt), KeyEvent("y", alt=True), IDLE,
        lambda a: seen.update(order=[Path(r.path).name for r in bookmarks()]),
        into(".."), listed(place),
        KeyEvent("2", alt=True), listed(place / "two"),
        KeyEvent("!", "!", alt=True), Until(titled("Confirm"), timeout=5), KeyEvent("y", alt=True), IDLE,
        lambda a: seen.update(again=[Path(r.path).name for r in bookmarks()]),
        into(".."), listed(place),  # away from two, so Alt+1 has somewhere to go
        KeyEvent("1", alt=True), Until(lambda a: a.manager.left.path == place / "two", timeout=5),
        lambda a: seen.update(at=a.manager.left.path),
        KeyEvent("0", alt=True, shift=True),
        Until(lambda a: any(isinstance(c, PopupMenu) for c in a.root.children), timeout=5),
        lambda a: seen.update(box=True), KeyEvent("escape"),
    ], timeout=30)
    assert seen["ask"] == "Store this directory\nas bookmark 1?"
    assert seen["order"] == ["one", "two"]
    assert seen["again"] == ["two", "one"]  # two moved to the first place
    assert seen["at"] == place / "two" and seen["box"]


def test_an_alt_n_past_the_bookmarks_does_nothing(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("9", alt=True), lambda a: None, lambda a: seen.update(path=a.manager.left.path)])
    assert seen["path"] == place


def test_change_drive_and_the_two_lists_are_on_the_panel_menu(place):
    from navigator.widgets.manager.commands import ChangeDrive, DirHistory, ListOfDirs

    app = navigator(place)
    seen = {}

    def look(a):
        menu = a.manager.panel_menu
        commands = [getattr(item, "command", None) for item in menu.entries()]
        seen.update(present=[c in commands for c in (ChangeDrive, DirHistory, ListOfDirs)])

    run_app(app, [look])
    assert seen["present"] == [True, True, True]
