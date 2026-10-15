"""Alt+G: ``cmCountLen``, a directory's bytes in its size column."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.file_ops.dirlength import CountJob, count_dir_length


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
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
    job = CountJob()
    job.stop()
    assert count_dir_length(place / "big", job) is None


def test_a_job_adds_up_bytes_files_and_directories_over_several_counts(place):
    job = CountJob()
    assert count_dir_length(place / "big", job) == 3024
    assert (job.position, job.files, job.directories) == (3024, 3, 1)
    assert (job.here_size, job.here_files, job.here_directories) == (3024, 3, 1)
    assert count_dir_length(place / "small", job) == 7
    assert (job.position, job.files, job.directories) == (3031, 4, 1)
    assert (job.here_size, job.here_files, job.here_directories) == (7, 1, 0)


def test_the_counting_box_shows_the_total_alone_for_one_directory():
    from conftest import settle
    from navigator.widgets.file_ops.count_progress import CountProgress

    box = CountProgress()
    box.size, box.files, box.directories, box.directory = 1234567, 1234, 56, "/a/b"
    box.here_size = 99
    settle()
    rows = box.table.text.split("\n")
    assert [row.split() for row in rows] == [["Bytes", "1,234,567", "(1.2M)"], ["Files", "1,234"],
                                             ["Directories", "56"]]
    assert {len(row) for row in rows} == {box.table.width}
    assert not box.directory_row.visible


def test_the_counting_box_shows_this_directory_beside_the_total_for_several():
    from conftest import settle
    from navigator.widgets.file_ops.count_progress import CountProgress

    box = CountProgress(several=True)
    box.here_size, box.here_files, box.here_directories = 700, 4, 1
    box.size, box.files, box.directories = 9200, 8, 2
    box.directory = "/home/someone/a/rather/long/path/that/will/not/fit/in/the/row/at/all/whatever/it/does"
    settle()
    rows = box.table.text.split("\n")
    assert [row.split() for row in rows] == [["This", "directory", "Total"], ["Bytes", "700", "9,200", "(9.0K)"],
                                             ["Files", "4", "8"], ["Directories", "1", "2"]]
    assert {len(row) for row in rows} == {box.table.width}
    assert box.directory_row.visible
    assert box.directory_row.text.startswith("...") and box.directory_row.text.endswith("whatever/it/does")


@pytest.mark.parametrize("gigabytes", [99, 100, 999, 1000, 999 * 1024])
def test_the_counting_box_keeps_its_columns_lined_up_and_inside_as_the_numbers_grow(gigabytes):
    from conftest import settle
    from navigator.widgets.file_ops.count_progress import CountProgress

    box = CountProgress(several=True)
    box.here_size = box.size = gigabytes << 30
    box.here_files = box.files = 12
    settle()
    rows = box.table.text.split("\n")
    assert {len(row) for row in rows} == {box.table.width}
    assert rows[1].endswith(")") and rows[1].split()[0] == "Bytes"
    # The columns end where their headings do.
    here_end = rows[0].index("This directory") + len("This directory")
    assert rows[1][:here_end].endswith(")") and rows[2][:here_end].endswith("12")


def test_the_counting_box_grows_as_the_counts_gain_digits_and_keeps_its_least_width():
    from conftest import settle
    from navigator.widgets.file_ops.count_progress import CountProgress

    one, several = CountProgress(), CountProgress(several=True)
    settle()
    assert (one.modal_width, several.modal_width) == (50, 60)
    widths = []
    for gigabytes in (99, 100, 1000):
        several.here_size = several.size = gigabytes << 30
        settle()
        widths.append(several.modal_width)
        rows = several.table.text.split("\n")
        assert rows[1].startswith("Bytes  ") and rows[1].endswith(")")
    # Two columns each one digit wider, then a comma and a unit's digit more.
    assert widths[1] == widths[0] + 2 and widths[2] > widths[1]


def test_the_counting_box_is_never_wider_than_its_screen_and_a_row_too_long_keeps_its_end():
    from navigator.widgets.file_ops.count_progress import CountProgress

    box = CountProgress(several=True)
    huge = (999 << 50, 2 * (999 << 50), 4, 8, 1, 2)
    assert box.box_width(0, True, *huge) > 80
    assert box.box_width(80, True, *huge) == 80
    assert box.box_width(80, True, 0, 0, 0, 0, 0, 0) == 60
    rows = box.counts(80 - 6, True, *huge).split("\n")
    assert {len(row) for row in rows} == {74}
    assert rows[1].endswith("T)") and rows[0].endswith("Total")


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
    assert "7 bytes in 1 selected file " in seen["footer"]


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
