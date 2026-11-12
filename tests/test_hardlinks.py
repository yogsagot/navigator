"""File > Links > Show hard links, and the *Links* column: a file's names."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app

from navigator.__main__ import Navigator
from navigator.lib.drives.listing import DirEntry, entry_at
from navigator.lib.file_ops import hardlinks
from navigator.lib.file_ops.hardlinks import HardLinksJob, find_names
from navigator.widgets.manager.commands import ShowHardLinks


@pytest.fixture
def place(tmp_path, monkeypatch):
    """``a.txt`` with three names, one hidden and one deep; ``single`` with one."""
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    # The walk starts at the mount point: here, the test's own directory.
    monkeypatch.setattr(hardlinks, "mount_point", lambda path: tmp_path)
    (tmp_path / "deep" / "er").mkdir(parents=True)
    (tmp_path / ".hid").mkdir()
    (tmp_path / "a.txt").write_text("a")
    os.link(tmp_path / "a.txt", tmp_path / "deep" / "er" / "b.txt")
    os.link(tmp_path / "a.txt", tmp_path / ".hid" / "c.txt")
    (tmp_path / "single").write_text("s")
    return tmp_path


# -- the model ---------------------------------------------------------------------------


def test_every_name_is_found_the_file_first(place):
    names = find_names(place / "a.txt", HardLinksJob())
    assert names.count == 3 and names.complete
    assert names.paths[0] == place / "a.txt"
    assert sorted(names.paths[1:]) == [place / ".hid" / "c.txt", place / "deep" / "er" / "b.txt"]


def test_the_walk_stops_once_every_name_is_found(place, monkeypatch):
    entered = []
    real = os.scandir

    def scandir(path):
        entered.append(Path(path))
        return real(path)

    monkeypatch.setattr(hardlinks.os, "scandir", scandir)
    (place / "zzz").mkdir()  # walked last: never reached
    find_names(place / "a.txt", HardLinksJob())
    assert place / "zzz" not in entered


def test_a_file_with_one_name_is_not_walked_for(place, monkeypatch):
    monkeypatch.setattr(hardlinks.os, "scandir", lambda path: pytest.fail("walked"))
    names = find_names(place / "single", HardLinksJob())
    assert names.paths == [place / "single"] and names.count == 1


def test_a_symlink_is_read_as_its_target(place):
    (place / "s").symlink_to("a.txt")
    names = find_names(place / "s", HardLinksJob())
    assert names.paths[0] == place / "a.txt" and names.count == 3


def test_a_name_not_reached_leaves_it_incomplete(place):
    os.link(place / "a.txt", place.parent / f"{place.name}-outside")
    try:
        names = find_names(place / "a.txt", HardLinksJob())
        assert names.count == 4 and len(names.paths) == 3 and not names.complete
    finally:
        os.unlink(place.parent / f"{place.name}-outside")


def test_a_stopped_job_ends_the_walk(place):
    job = HardLinksJob()
    job.stop()
    assert find_names(place / "a.txt", job).paths == [place / "a.txt"]


# -- the column ---------------------------------------------------------------------------


def test_the_links_column_counts_the_names(place):
    assert entry_at(place / "a.txt").display_links == "3"
    assert entry_at(place / "single").display_links == "1"
    assert DirEntry("..", True, 0, nlink=4).display_links == ""
    assert DirEntry("remote", False, 0).display_links == ""  # a drive that does not say


def test_the_panel_shows_the_column_when_asked(place):
    app = Navigator(place, place, terminal=FakeTerminal(200, 24))
    seen = {}

    def show(a):
        panel = a.manager.left
        panel.view_mode = "detailed"
        panel.columns = frozenset({"size", "links"})

    def look(a):
        panel = a.manager.left
        seen["keys"] = [key for key, _, _ in panel.detail_columns]
        panel.cursor = [e.name for e in panel.items].index("a.txt")
        seen["painted"] = a.terminal.painted

    run_app(app, [show, lambda a: None, look])
    assert seen["keys"] == ["name", "size", "links"]
    assert "Links" in seen["painted"]


# -- the command --------------------------------------------------------------------------


def listed(app) -> bool:
    """The listing is up and the panel shows it: what was found is listed by
    a read of its own once the search is done."""
    from conftest import _listed

    return app.manager.left.found is not None and app.modal is None and _listed(app)


def at(app, name: str) -> None:
    panel = app.manager.left
    panel.cursor = [e.name for e in panel.items].index(name)


def test_show_hard_links_lists_every_name_the_cursor_on_the_file(place):
    app = Navigator(place, place, terminal=FakeTerminal(120, 24))
    seen = {}
    run_app(app, [lambda a: a.manager.left.focus(), lambda a: at(a, "a.txt"),
                  lambda a: seen.update(enabled=a.command_enabled(ShowHardLinks())),
                  lambda a: a.spawn(a.run_command(ShowHardLinks)),
                  Until(listed), lambda a: None,
                  lambda a: seen.update(keys=[e.key for e in a.manager.left.items],
                                        title=a.manager.left.found.title,
                                        cursor=a.manager.left.selected.key,
                                        after=a.command_enabled(ShowHardLinks()))])
    assert seen["enabled"] is True
    assert seen["keys"][0] == ".."
    assert seen["keys"][1] == str(place / "a.txt")
    assert sorted(seen["keys"][2:]) == [str(place / ".hid" / "c.txt"), str(place / "deep" / "er" / "b.txt")]
    assert seen["title"] == "Links: a.txt"
    assert seen["cursor"] == str(place / "a.txt")
    assert seen["after"] is False  # not inside a listing


def test_off_on_a_file_with_one_name_and_on_a_directory(place):
    app = Navigator(place, place, terminal=FakeTerminal(120, 24))
    seen = {}
    run_app(app, [lambda a: a.manager.left.focus(),
                  lambda a: at(a, "single"), lambda a: seen.update(single=a.command_enabled(ShowHardLinks())),
                  lambda a: at(a, "deep"), lambda a: seen.update(directory=a.command_enabled(ShowHardLinks()))])
    assert seen == {"single": False, "directory": False}


def test_the_file_menu_has_the_entry(place):
    app = Navigator(place, place, terminal=FakeTerminal(120, 24))
    seen = {}
    run_app(app, [lambda a: seen.update(text=a.root.menu.file.item_for(ShowHardLinks).text)])
    assert seen["text"] == "Show ~h~ard links"
