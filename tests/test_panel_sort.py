"""Alt+B and the *New Manager defaults*' sort: ``CM_SortBy`` and ``TFilesCollection.Compare``."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent, MouseClickEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS, PanelDefaultsData
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
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
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
                              size=PopupMenu.measure(popup(a).menu, a, a.manager, "Sort by"),
                              title=popup(a).box.title),
        KeyEvent("s", "s"), lambda a: None,
        lambda a: seen.update(left=listed(a.manager.left), right=listed(a.manager.right),
                              mode=a.manager.left.sort_mode, box=popup(a)),
    ])
    assert seen["current"] == 0  # Name
    assert seen["title"] == "Sort by"
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


def test_a_new_panel_takes_the_new_manager_defaults_mode(place):
    assert PanelDefaultsData().view_mode == "detailed"
    SETTINGS.panel_defaults.view_mode = "list"
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: seen.update(left=a.manager.left.view_mode, right=a.manager.right.view_mode,
                                        header=a.manager.left.header)])
    assert seen == {"left": "list", "right": "list", "header": 1}


def test_the_new_manager_defaults_dialog_reads_and_answers_the_mode():
    from navigator.widgets.setup.fm_defaults_dialog import FMDefaultsDialog

    SETTINGS.panel_defaults.view_mode = "detailed"
    dialog = FMDefaultsDialog()
    assert dialog.view_mode.value == 1
    dialog.view_mode.value = 2
    assert dialog.accept()["view_mode"] == "list"


# -- reversed, and clicking a column's title -------------------------------------------


def test_reverse_turns_each_group_round_keeping_up_and_the_directories_first():
    assert names(order_entries(ENTRIES, "name", reverse=True)) == \
        ["..", "zdir", "adir", "run", "c.png", "b.txt", "A.zip"]
    assert names(order_entries(ENTRIES, "size", reverse=True)) == \
        ["..", "zdir", "adir", "run", "b.txt", "c.png", "A.zip"]
    ordered = order_entries(ENTRIES, "name", executables_first=True, reverse=True)
    assert names(ordered) == ["..", "zdir", "adir", "run", "c.png", "b.txt", "A.zip"]
    assert names(order_entries(ENTRIES, "unsorted", reverse=True)) == \
        names(order_entries(ENTRIES, "unsorted"))


def heading_click(app, key: str) -> MouseClickEvent:
    """A press on the left panel's title of column *key*, in screen cells."""
    panel = app.manager.left
    (ox, oy) = panel.offset()
    _, x, width = next(column for column in panel.detail_columns if column[0] == key)
    return MouseClickEvent(ox + panel.x + x + width // 2, oy + panel.y + panel.inset, "left", "press")


def heading_row(app) -> str:
    from navkit.screen import ScreenBuffer

    panel = app.manager.left
    buffer = ScreenBuffer(panel.width, panel.height)
    panel.render(buffer)
    return "".join(buffer.get(x, panel.inset)[0] or " " for x in range(panel.width))


def test_clicking_a_title_sorts_by_its_column_and_again_reverses_it(place):
    SETTINGS.panel_defaults.view_mode = "detailed"
    (place / "c.txt").chmod(0o600)
    (place / "a.txt").chmod(0o644)
    (place / "b.txt").chmod(0o644)
    app = Navigator(place, place, terminal=FakeTerminal(160, 24))  # wide enough for Attr
    seen = []

    def note(a):
        seen.append((a.manager.left.sort_mode, a.manager.left.sort_reverse, listed(a.manager.left),
                     heading_row(a)))

    run_app(app, [
        lambda a: a.post_event(heading_click(a, "size")), lambda a: None, note,
        lambda a: a.post_event(heading_click(a, "size")), lambda a: None, note,
        lambda a: a.post_event(heading_click(a, "attributes")), lambda a: None, note,
        lambda a: a.post_event(heading_click(a, "attributes")), lambda a: None, note,
    ])
    assert [row[:3] for row in seen] == [
        ("size", False, ["sub", "b.txt", "c.txt", "a.txt"]),
        ("size", True, ["sub", "a.txt", "c.txt", "b.txt"]),
        ("attributes", False, ["sub", "c.txt", "a.txt", "b.txt"]),  # rw------- first
        ("attributes", True, ["sub", "b.txt", "a.txt", "c.txt"]),
    ]
    assert "Attr↑" in seen[2][3] and "Attr↓" in seen[3][3]


def test_clicking_name_steps_through_name_and_extension_each_way(place):
    for name in ("a.log", "b.md"):
        (place / name).write_bytes(b"")
    SETTINGS.panel_defaults.view_mode = "detailed"
    app = navigator(place)
    seen = []
    click = lambda a: a.post_event(heading_click(a, "name"))
    note = lambda a: seen.append((a.manager.left.sort_mode, a.manager.left.sort_reverse,
                                  listed(a.manager.left), heading_row(a)))
    run_app(app, [lambda a: a.manager.left.sort_by("size"), lambda a: None,
                  *[step for _ in range(5) for step in (click, lambda a: None, note)]])
    assert [(mode, reverse, names) for mode, reverse, names, _ in seen] == [
        ("name", False, ["sub", "a.log", "a.txt", "b.md", "b.txt", "c.txt"]),
        ("name", True, ["sub", "c.txt", "b.txt", "b.md", "a.txt", "a.log"]),
        ("extension", False, ["sub", "a.log", "b.md", "a.txt", "b.txt", "c.txt"]),
        ("extension", True, ["sub", "c.txt", "b.txt", "a.txt", "b.md", "a.log"]),
        ("name", False, ["sub", "a.log", "a.txt", "b.md", "b.txt", "c.txt"]),
    ]
    marks = ["Name↑", "Name↓", "Name.↑", "Name.↓", "Name↑"]
    assert all(mark in row for (*_, row), mark in zip(seen, marks))


def test_the_sorted_column_title_carries_an_arrow_for_its_direction(place):
    SETTINGS.panel_defaults.view_mode = "detailed"
    app = navigator(place)
    seen = {}
    run_app(app, [
        lambda a: seen.update(name=heading_row(a)),
        lambda a: a.manager.left.sort_by("time"), lambda a: None,
        lambda a: seen.update(time=heading_row(a)),
        lambda a: a.manager.left.sort_by("time", reverse=True), lambda a: None,
        lambda a: seen.update(reversed=heading_row(a)),
        lambda a: a.manager.left.sort_by("extension"), lambda a: None,
        lambda a: seen.update(extension=heading_row(a)),
    ])
    assert "Name↑" in seen["name"] and "↓" not in seen["name"]
    assert "Date↓" in seen["time"] and "Name↑" not in seen["time"]
    assert "Date↑" in seen["reversed"]
    assert "Name.↑" in seen["extension"]


def test_alt_b_drops_the_reverse():
    panel_cls = __import__("navigator.widgets.manager.panel.panel", fromlist=["Panel"]).Panel
    panel = panel_cls()
    panel.sort_by("size", reverse=True)
    assert (panel.sort_mode, panel.sort_reverse) == ("size", True)
    panel.sort_by("name")
    assert (panel.sort_mode, panel.sort_reverse) == ("name", False)


def owned(name: str, uid: int, mode: int = FILE) -> DirEntry:
    return DirEntry(name, mode == DIR, 0, mode, 0.0, uid=uid, gid=uid)


def test_owner_sorts_by_user_and_group_then_name_directories_first():
    # 99999 has no name, so it shows (and sorts) as the number, before "root".
    entries = [owned("b", 0), owned("a", 0), owned("c", 99999), owned("d", 0, DIR), owned("e", 99999, DIR)]
    assert names(order_entries(entries, "owner")) == ["e", "d", "c", "a", "b"]
    assert names(order_entries(entries, "owner", reverse=True)) == ["d", "e", "b", "a", "c"]


def test_clicking_owner_sorts_by_it_ascending_and_marks_it(place):
    SETTINGS.panel_defaults.view_mode = "detailed"
    app = Navigator(place, place, terminal=FakeTerminal(160, 24))  # wide enough for Owner
    seen = []
    note = lambda a: seen.append((a.manager.left.sort_mode, a.manager.left.sort_reverse, heading_row(a)))
    click = lambda a: a.post_event(heading_click(a, "owner"))
    run_app(app, [click, lambda a: None, note, click, lambda a: None, note])
    assert [(mode, reverse) for mode, reverse, _ in seen] == [("owner", False), ("owner", True)]
    assert "Owner↑" in seen[0][2] and "Owner↓" in seen[1][2]


def test_attributes_sort_by_the_permission_bits_then_name_directories_first():
    entries = [entry("b", 0o100755), entry("a", 0o100644), entry("c", 0o100600),
               DirEntry("d", True, 0, 0o040700), entry("e", DIR)]
    assert names(order_entries(entries, "attributes")) == ["d", "e", "c", "a", "b"]
    assert names(order_entries(entries, "attributes", reverse=True)) == ["e", "d", "b", "a", "c"]


def painted_box(box) -> list[str]:
    from navkit.screen import ScreenBuffer

    inner = box.box
    buffer = ScreenBuffer(inner.width, inner.height)
    inner.render(buffer.view(0, 0, inner.width, inner.height))
    return ["".join(buffer.get(x, y)[0] or " " for x in range(inner.width)) for y in range(inner.height)]


def test_alt_b_offers_each_order_both_ways_ticking_the_panels_own(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 30))  # the whole box, unscrolled
    seen = {}
    run_app(app, [
        lambda a: a.manager.left.sort_by("size", reverse=True), lambda a: None,
        KeyEvent("b", alt=True), lambda a: None,
        lambda a: seen.update(rows=painted_box(popup(a)), current=popup(a).box.current),
        KeyEvent("down"), KeyEvent("down"), KeyEvent("enter"), lambda a: None,   # Time ↓
        lambda a: seen.update(after=(a.manager.left.sort_mode, a.manager.left.sort_reverse)),
        KeyEvent("b", alt=True), lambda a: None, KeyEvent("n", "n"), lambda a: None,
        lambda a: seen.update(letter=(a.manager.left.sort_mode, a.manager.left.sort_reverse)),
    ])
    rows = [row[2:].rstrip(" │") for row in seen["rows"][1:-1]]
    assert [row.split()[0] for row in rows] == [
        "Name", "Name", "Extension", "Extension", "Size", "√Size", "Time", "Time",
        "Attributes", "Attributes", "Owner", "Owner", "Type", "Type", "Unsorted"]
    arrows = ["↓", "↓", "↑", "↑", "↓", "↓", "↓"]                      # the reversed entries' only
    assert [row[-1] for row in rows[1:-1:2]] == arrows
    assert not any(arrow in row for row in rows[0:-1:2] for arrow in "↑↓")  # own direction: plain
    assert rows[5].startswith("√Size") and rows[5].endswith("↑")   # size reversed: smallest first
    assert sum("√" in row for row in rows) == 1
    assert rows[-1] == " Unsorted"                                    # no direction
    assert seen["current"] == 5
    assert seen["after"] == ("time", True)
    assert seen["letter"] == ("name", False)                          # the letter picks the own direction


def test_the_new_manager_defaults_dialog_reads_and_answers_the_direction():
    from navigator.widgets.setup.fm_defaults_dialog import FMDefaultsDialog

    SETTINGS.panel_defaults.sort_by = "time"
    SETTINGS.panel_defaults.sort_reverse = True
    dialog = FMDefaultsDialog()
    assert dialog.reverse.value == 1
    assert dialog.sort_by.items[3] == "~T~ime ↑" and dialog.sort_by.items[-1] == "~U~nsorted"
    dialog.reverse.value = 0
    assert dialog.sort_by.items[3] == "~T~ime"
    assert dialog.accept()["sort_reverse"] is False


def test_a_new_panel_takes_the_new_manager_defaults_direction(place):
    SETTINGS.panel_defaults.sort_by = "size"
    SETTINGS.panel_defaults.sort_reverse = True
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: seen.update(order=(a.manager.left.sort_mode, a.manager.left.sort_reverse),
                                        names=listed(a.manager.left))])
    assert seen == {"order": ("size", True), "names": ["sub", "a.txt", "c.txt", "b.txt"]}
