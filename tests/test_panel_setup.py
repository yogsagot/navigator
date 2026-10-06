"""Alt+S: *Panel Options*, one panel's order, display boxes and file mask."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.filetypes import in_filter
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.panel import scan_directory


def test_the_mask_is_dns_infilter_the_last_pattern_that_matches_decides():
    assert in_filter("a.c", "*") and in_filter("a.c", "") and in_filter("a.c", " ")
    assert in_filter("a.c", "*.c;*.h") and not in_filter("a.py", "*.c;*.h")
    assert in_filter("a.c", "*;-*.bak") and not in_filter("a.bak", "*;-*.bak")
    assert in_filter("keep.bak", "*;-*.bak;keep.*")
    assert not in_filter("a.c", "-*.bak")  # only exclusions: nothing is let through
    assert not in_filter("A.C", "*.c")  # case counts, as Select group's does


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "sub.txt").mkdir()
    (tmp_path / "keep.c").write_text("c")
    (tmp_path / "big.txt").write_text("x" * 100)
    (tmp_path / "note.txt").write_text("n")
    return tmp_path


def names(entries) -> list[str]:
    return [e.name for e in entries if e.name != ".."]


def test_a_mask_leaves_out_files_and_never_a_directory(place):
    entries, _ = scan_directory(place, True, mask="*.c")
    assert names(entries) == ["sub.txt", "keep.c"]
    entries, _ = scan_directory(place, True, mask="*;-*.txt")
    assert names(entries) == ["sub.txt", "keep.c"]


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def test_alt_s_opens_on_the_panels_own_values(place):
    SETTINGS.panel_defaults.files_highlight = False
    app = navigator(place)
    seen = {}

    def look(a):
        d = a.modal
        seen.update(title=d.title, sort=d.sort_by.value, display=d.display.value, mask=d.mask.value)

    run_app(app, [KeyEvent("s", alt=True), lambda a: None, look, KeyEvent("escape")])
    # Current file, Selected files, Free space, Executables and Archives first.
    assert seen == {"title": "Panel Options", "sort": 0, "display": 0b11010110, "mask": "*"}


def test_ok_gives_the_panel_its_own_order_boxes_and_mask_and_the_other_keeps_the_defaults(place):
    app = navigator(place)
    seen = {}

    def answer(a):
        d = a.modal
        d.sort_by.value = 2  # Size
        d.display.value &= ~(1 << 5)  # Files highlight off
        d.mask.value = "*.txt"

    run_app(app, [KeyEvent("s", alt=True), lambda a: None, answer, KeyEvent("enter"), lambda a: None,
                  lambda a: seen.update(
                      left=names(a.manager.left.items), right=names(a.manager.right.items),
                      sort=a.manager.left.sort_mode, mask=a.manager.left.file_mask,
                      highlight=(a.manager.left.shows("files_highlight"),
                                 a.manager.right.shows("files_highlight")),
                      own=a.manager.left.display is not None, follows=a.manager.right.display is None)])
    assert seen["left"] == ["sub.txt", "big.txt", "note.txt"]
    assert seen["right"] == ["sub.txt", "big.txt", "keep.c", "note.txt"]
    assert seen["sort"] == "size" and seen["mask"] == "*.txt"
    assert seen["highlight"] == (False, True) and seen["own"] and seen["follows"]


def test_a_panel_following_the_defaults_follows_them_live(place):
    app = navigator(place)
    seen = []

    def change(a):
        SETTINGS.panel_defaults.current_file = False

    run_app(app, [lambda a: seen.append(a.manager.left.shows("current_file")), change,
                  lambda a: seen.append(a.manager.left.shows("current_file"))])
    assert seen == [True, False]


def test_an_empty_mask_is_every_file(place):
    app = navigator(place)
    seen = {}

    def answer(a):
        a.modal.mask.value = "  "

    run_app(app, [KeyEvent("s", alt=True), lambda a: None, answer, KeyEvent("enter"), lambda a: None,
                  lambda a: seen.update(mask=a.manager.left.file_mask, count=len(names(a.manager.left.items)))])
    assert seen == {"mask": "*", "count": 4}
