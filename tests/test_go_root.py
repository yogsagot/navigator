"""Ctrl+\\: DN's ``kbCtrlBSlsh``, ``Drive^.ChangeRoot`` and the cursor to the top."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest

from conftest import FakeTerminal, run_app, settle
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import Location, Site, mount, unmount
from navigator.lib.drives.memory import MemoryDrive


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "a" / "b").mkdir(parents=True)
    return tmp_path


def test_ctrl_backslash_goes_to_the_disks_root_the_cursor_on_top(place):
    app = Navigator(place / "a" / "b", place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [KeyEvent("\\", ctrl=True), lambda a: None, lambda a: None,
                  lambda a: seen.update(where=a.manager.left.location, cursor=a.manager.left.cursor),
                  KeyEvent("end"), KeyEvent("\\", ctrl=True), lambda a: None, lambda a: None,
                  lambda a: seen.update(again=(a.manager.left.location, a.manager.left.cursor))])
    assert seen["where"] == Location.of(Path("/")) and seen["cursor"] == 0
    assert seen["again"] == (Location.of(Path("/")), 0)


def test_a_remembered_cursor_at_the_root_is_not_used(place, monkeypatch):
    from navigator.lib.config import directory_settings

    monkeypatch.setattr(directory_settings, "cursor_of", lambda location: "tmp")
    app = Navigator(place / "a", place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [KeyEvent("\\", ctrl=True), lambda a: None, lambda a: None,
                  lambda a: seen.update(cursor=a.manager.left.cursor)])
    assert seen["cursor"] == 0


def test_the_tree_holding_the_keyboard_refuses_it(place):
    from navigator.widgets.manager.commands import GoRoot

    app = Navigator(place / "a" / "b", place, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [KeyEvent("t", ctrl=True), lambda a: None, KeyEvent("tab"), lambda a: None,
                  lambda a: seen.update(why=a.manager.refusal(GoRoot())),
                  KeyEvent("\\", ctrl=True), lambda a: None,
                  lambda a: seen.update(where=a.manager.left.location)])
    assert seen["why"] == "Only in a file panel, not beside it"
    assert seen["where"] == Location.of(place / "a" / "b")


def panel_on(location):
    from navigator.widgets.manager.panel.panel import Panel

    panel = Panel()
    panel.mounted()
    panel.location = location
    settle()
    return panel


def test_another_drives_root_is_its_own():
    drive = mount(MemoryDrive("roots"))
    try:
        drive.make("/x/y/z.txt", "z")
        drive.make("/top.txt", "t")
        panel = panel_on(drive.location("/x/y"))
        panel.go_root()
        settle()
        assert panel.location == drive.location("/") and panel.cursor == 0
    finally:
        unmount(drive.site)


def test_inside_an_archive_its_own_root(tmp_path):
    import zipfile

    from navigator.lib.drives import archive

    path = tmp_path / "a.zip"
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr("src/deep/x.txt", "x")
        zipped.writestr("README", "r")
    outer = Location.of(path)
    try:
        panel = panel_on(Location(Site("arc"), PurePosixPath("/src/deep"), outer))
        panel.go_root()
        settle()
        assert panel.location.outer == outer and str(panel.location.path) == "/"
        assert panel.cursor == 0
    finally:
        archive.close_all()


def test_a_find_listing_is_left_for_the_root(place):
    from navigator.lib.file_ops.filefind import FindListing

    panel = panel_on(Location.of(place / "a"))
    panel.show_found(FindListing(title="found", origin=place / "a", entries=[]))
    settle()
    assert panel.found is not None
    panel.go_root()
    settle()
    assert panel.found is None and panel.location == Location.of(Path("/")) and panel.cursor == 0
