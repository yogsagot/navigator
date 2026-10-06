"""Alt+G: ``cmCountLen``, a directory's bytes in its size column."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.dirlength import count_dir_length


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "big" / "deep").mkdir(parents=True)
    (tmp_path / "big" / "one").write_bytes(b"x" * 1000)
    (tmp_path / "big" / ".hidden").write_bytes(b"x" * 24)
    (tmp_path / "big" / "deep" / "two").write_bytes(b"x" * 2000)
    (tmp_path / "small").mkdir()
    (tmp_path / "small" / "three").write_bytes(b"x" * 7)
    (tmp_path / "file.txt").write_bytes(b"x" * 5)
    return tmp_path


def test_count_takes_every_file_beneath_dot_files_too_and_no_link_targets(place):
    os.symlink(place / "small", place / "big" / "link")
    os.symlink(place / "big", place / "big" / "deep" / "loop")
    links = len(os.readlink(place / "big" / "link")) + len(os.readlink(place / "big" / "deep" / "loop"))
    assert count_dir_length(place / "big") == 3024 + links
    assert count_dir_length(place / "missing") == 0


def test_a_stopped_count_is_none(place):
    class Job:
        stopped = True
        position = 0

    assert count_dir_length(place / "big", Job()) is None


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def to(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def sizes(panel) -> dict[str, object]:
    """Each name's counted bytes, or what its size column says while it has none."""
    return {e.name: e.size if e.counted else e.display_size.strip() for e in panel.items}


def test_alt_g_counts_the_directory_at_the_cursor_and_the_tagged_ones(place):
    app = navigator(place)
    seen = {}

    def tag(a):
        a.manager.left.marked = frozenset({"small"})

    run_app(app, [to("big"), tag, KeyEvent("g", alt=True), lambda a: None, lambda a: None,
                  lambda a: seen.update(sizes=sizes(a.manager.left),
                                        footer=a.manager.left.footer_text(),
                                        right=sizes(a.manager.right))])
    assert seen["sizes"]["big"] == 3024 and seen["sizes"]["small"] == 7
    assert seen["sizes"][".."] == "UP--DIR" and seen["right"]["big"] == "DIR"
    assert "7 bytes in 1 selected files" in seen["footer"]


def test_alt_g_on_up_counts_the_directory_listed(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to(".."), KeyEvent("g", alt=True), lambda a: None, lambda a: None,
                  lambda a: seen.update(sizes=sizes(a.manager.left))])
    assert seen["sizes"][".."] == 3036 and seen["sizes"]["big"] == "DIR"


def test_alt_g_on_a_file_with_nothing_tagged_does_nothing_and_a_re_read_forgets(place):
    app = navigator(place)
    seen = {}
    run_app(app, [to("file.txt"), KeyEvent("g", alt=True), lambda a: None,
                  lambda a: seen.update(file=sizes(a.manager.left)),
                  to("big"), KeyEvent("g", alt=True), lambda a: None, lambda a: None,
                  lambda a: seen.update(counted=sizes(a.manager.left)["big"]),
                  KeyEvent("r", ctrl=True), lambda a: None,
                  lambda a: seen.update(reread=sizes(a.manager.left)["big"])])
    assert seen["file"]["big"] == "DIR" and seen["file"]["small"] == "DIR"
    assert seen["counted"] == 3024 and seen["reread"] == "DIR"


def test_a_counted_directory_shows_its_size_where_dir_was():
    from navigator.widgets.manager.panel.panel import DirEntry

    entry = DirEntry("big", True, 0, 0o040755)
    assert entry.display_size.strip() == "DIR"
    entry.size, entry.counted = 3024, True
    assert entry.display_size.strip() == "3K"
    up = DirEntry("..", True, 0, 0o040755)
    up.size, up.counted = 12, True
    assert up.display_size.strip() == "12"
