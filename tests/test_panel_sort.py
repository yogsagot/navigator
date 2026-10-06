"""Alt+B and the *New Manager defaults*' sort: ``CM_SortBy`` and ``TFilesCollection.Compare``."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.panel import DirEntry, order_entries
from navml.widgets.menu.popup_menu import PopupMenu

FILE = 0o100644
RUN = 0o100755
DIR = 0o040755


def entry(name: str, mode: int = FILE, size: int = 0, mtime: float = 0.0) -> DirEntry:
    return DirEntry(name, mode == DIR, size, mode, mtime)


def names(entries) -> list[str]:
    return [e.name for e in entries]


ENTRIES = [
    entry("b.txt", size=5, mtime=3), entry("A.zip", size=50, mtime=1), entry("run", RUN, size=1, mtime=2),
    entry("zdir", DIR, mtime=9), entry("..", DIR), entry("adir", DIR, mtime=1), entry("c.png", size=7, mtime=5),
]


def test_name_puts_up_and_the_directories_first_and_ignores_case():
    assert names(order_entries(ENTRIES, "name")) == ["..", "adir", "zdir", "A.zip", "b.txt", "c.png", "run"]


def test_executables_and_archives_first_lead_the_files():
    ordered = order_entries(ENTRIES, "name", executables_first=True, archives_first=True)
    assert names(ordered) == ["..", "adir", "zdir", "run", "A.zip", "b.txt", "c.png"]
    ordered = order_entries(ENTRIES, "name", archives_first=True)
    assert names(ordered) == ["..", "adir", "zdir", "A.zip", "b.txt", "c.png", "run"]


def test_extension_sorts_by_what_follows_the_last_dot_none_first():
    ordered = order_entries(ENTRIES + [entry(".hidden")], "extension")
    assert names(ordered) == ["..", "adir", "zdir", ".hidden", "run", "c.png", "b.txt", "A.zip"]


def test_size_and_time_go_largest_and_newest_first_without_the_two_flags():
    flags = {"executables_first": True, "archives_first": True}
    assert names(order_entries(ENTRIES, "size", **flags)) == \
        ["..", "adir", "zdir", "A.zip", "c.png", "b.txt", "run"]
    assert names(order_entries(ENTRIES, "time", **flags)) == \
        ["..", "zdir", "adir", "c.png", "b.txt", "run", "A.zip"]


def test_type_is_dns_group_directories_executables_archives_then_the_rest():
    ordered = order_entries(ENTRIES + [entry("notes.md"), entry("plain")], "type")
    # image before document before none, as CATEGORIES orders them after archive
    assert names(ordered) == ["..", "adir", "zdir", "run", "A.zip", "c.png", "b.txt", "notes.md", "plain"]


def test_unsorted_keeps_the_directory_order_after_up():
    assert names(order_entries(ENTRIES, "unsorted", executables_first=True)) == \
        ["..", "b.txt", "A.zip", "run", "zdir", "adir", "c.png"]


# -- the panel ------------------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    # By name a, b, c; by size b, c, a; by time (newest first) c, b, a.
    for name, size, age in (("a.txt", 1, 30), ("b.txt", 300, 20), ("c.txt", 20, 10)):
        path = tmp_path / name
        path.write_bytes(b"x" * size)
        os.utime(path, (1_000_000 - age, 1_000_000 - age))
    (tmp_path / "sub").mkdir()
    return tmp_path


def listed(panel) -> list[str]:
    return [e.name for e in panel.items if e.name != ".."]


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def test_a_new_panel_takes_the_new_manager_defaults_sort(place):
    SETTINGS.panel_defaults.sort_by = "size"
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: seen.update(mode=a.manager.left.sort_mode, names=listed(a.manager.left))])
    assert seen == {"mode": "size", "names": ["sub", "b.txt", "c.txt", "a.txt"]}


def test_sort_by_re_sorts_keeping_the_cursor_on_its_entry(place):
    app = navigator(place)
    seen = {}

    def go(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("a.txt")
        panel.sort_by("time")

    run_app(app, [go, lambda a: None,
                  lambda a: seen.update(names=listed(a.manager.left),
                                        selected=a.manager.left.selected.name)])
    assert seen == {"names": ["sub", "c.txt", "b.txt", "a.txt"], "selected": "a.txt"}
    with pytest.raises(ValueError):
        app.manager.left.sort_by("colour")


def popup(app) -> PopupMenu | None:
    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


def test_alt_b_opens_centred_on_the_panels_mode_and_a_choice_re_sorts_that_panel(place):
    app = navigator(place)
    seen = {}
    run_app(app, [
        KeyEvent("b", alt=True), lambda a: None,
        lambda a: seen.update(current=popup(a).box.current, at=popup(a).at,
                              panel=(a.manager.left.offset(), a.manager.left.x, a.manager.left.y,
                                     a.manager.left.width, a.manager.left.height),
                              size=PopupMenu.measure(popup(a).menu, a, a.manager)),
        KeyEvent("s", "s"), lambda a: None,
        lambda a: seen.update(left=listed(a.manager.left), right=listed(a.manager.right),
                              mode=a.manager.left.sort_mode, box=popup(a)),
    ])
    assert seen["current"] == 0  # Name
    (ox, oy), x, y, width, height = seen["panel"]
    box_width, box_height = seen["size"]
    assert seen["at"] == (ox + x + (width - box_width) // 2, oy + y + (height - box_height) // 2)
    assert seen["mode"] == "size" and seen["box"] is None
    assert seen["left"] == ["sub", "b.txt", "c.txt", "a.txt"]
    assert seen["right"] == ["sub", "a.txt", "b.txt", "c.txt"]  # the other panel keeps its own


def test_escape_leaves_the_order_alone(place):
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("b", alt=True), lambda a: None, KeyEvent("escape"), lambda a: None,
                  lambda a: seen.update(mode=a.manager.left.sort_mode)])
    assert seen["mode"] == "name"
