"""File > Compare files' model: two texts aligned row against row (``filediff``)."""

from __future__ import annotations

import io

import pytest

from navigator.lib.drives import mount, unmount
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops import filediff
from navigator.lib.file_ops.filediff import DELETE, EQUAL, INSERT, REPLACE, align, compare, first_difference
from navigator.lib.system.job import Stopped


def rows(diff):
    """Each row as ``(kind, left line, right line)``."""
    return [(diff.kinds[row], diff.line("left", row), diff.line("right", row)) for row in range(diff.rows)]


def test_equal_lines_pair_and_a_change_stays_level():
    diff = align(b"a\nb\nc\n", b"a\nB\nc\n")
    assert rows(diff) == [(EQUAL, b"a", b"a"), (REPLACE, b"b", b"B"), (EQUAL, b"c", b"c")]
    assert diff.hunks == (1,) and (diff.added, diff.removed, diff.changed) == (0, 0, 1)


def test_a_line_one_side_lacks_faces_a_filler_row():
    diff = align(b"a\nb\nc\n", b"a\nc\nd\n")
    assert rows(diff) == [(EQUAL, b"a", b"a"), (DELETE, b"b", None), (EQUAL, b"c", b"c"), (INSERT, None, b"d")]
    assert diff.hunks == (1, 3) and (diff.added, diff.removed) == (1, 1)


def test_a_change_of_unequal_lengths_pairs_what_it_can_and_fills_the_rest():
    diff = align(b"x\none\ny\n", b"x\nuno\ndos\ntres\ny\n")
    assert rows(diff)[1:4] == [(REPLACE, b"one", b"uno"), (INSERT, None, b"dos"), (INSERT, None, b"tres")]
    assert diff.hunks == (1,) and diff.hunk_end(0) == 4
    assert (diff.changed, diff.added) == (1, 2)


def test_next_and_previous_differences_stop_at_the_ends():
    diff = align(b"a\nb\nc\nd\ne\n", b"a\nB\nc\nD\ne\n")
    assert diff.hunks == (1, 3)
    assert diff.next_hunk(-1) == 0 and diff.next_hunk(1) == 1 and diff.next_hunk(3) is None
    assert diff.previous_hunk(3) == 0 and diff.previous_hunk(1) is None
    assert diff.hunk_at(2) == 0 and diff.hunk_at(0) == -1


def test_line_endings_alone_are_no_difference_of_lines():
    diff = align(b"x\r\ny\r\n", b"x\ny")
    assert diff.hunks == () and diff.endings_differ
    assert not align(b"x\n", b"x\n").endings_differ


def test_the_alignment_stops_when_the_job_does():
    job = filediff.DiffJob()
    job.stop()
    with pytest.raises(Stopped):
        align(b"a\nb\n", b"c\nd\n", job)


def test_the_first_difference_is_a_byte_and_its_line():
    assert first_difference(io.BytesIO(b"ab\ncd"), io.BytesIO(b"ab\nce")) == (4, 2)
    assert first_difference(io.BytesIO(b"ab"), io.BytesIO(b"ab")) is None
    assert first_difference(io.BytesIO(b"ab"), io.BytesIO(b"abc")) == (2, 1)
    long = b"x" * 100_000
    assert first_difference(io.BytesIO(long + b"1"), io.BytesIO(long + b"2")) == (100_000, 1)


def test_compare_answers_identical_binary_and_text(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    one.write_bytes(b"same\n")
    two.write_bytes(b"same\n")
    assert compare(one, two) == filediff.Identical(5)
    one.write_bytes(b"\0\1\2\3")
    two.write_bytes(b"\0\1\7\3")
    assert compare(one, two) == filediff.DiffersAt(2, 1, 4, 4, "binary")
    one.write_text("a\nb\n")
    two.write_text("a\nc\n")
    assert compare(one, two).hunks == (1,)


def test_a_file_too_large_to_align_is_compared_byte_by_byte(tmp_path, monkeypatch):
    monkeypatch.setattr(filediff, "TEXT_LIMIT", 4)
    (tmp_path / "one").write_text("line\nline\n")
    (tmp_path / "two").write_text("line\nlime\n")
    assert compare(tmp_path / "one", tmp_path / "two") == filediff.DiffersAt(7, 2, 10, 10, "large")


def test_files_are_read_through_their_drives(tmp_path):
    drive = mount(MemoryDrive("diffs"))
    try:
        drive.make("/a.txt", "alpha\nbeta\n")
        (tmp_path / "a.txt").write_text("alpha\ngamma\n")
        diff = compare(drive.location("/a.txt"), tmp_path / "a.txt")
        assert rows(diff)[1] == (REPLACE, b"beta", b"gamma")
    finally:
        unmount(drive.site)


def test_a_large_range_is_cut_at_lines_unique_to_both_sides(monkeypatch):
    monkeypatch.setattr(filediff, "MATCHER_LIMIT", 4)
    diff = align(b"a\nx\nb\nc\ny\nd\n", b"a\nX\nb\nc\nY\nd\n")
    assert rows(diff) == [(EQUAL, b"a", b"a"), (REPLACE, b"x", b"X"), (EQUAL, b"b", b"b"), (EQUAL, b"c", b"c"),
                          (REPLACE, b"y", b"Y"), (EQUAL, b"d", b"d")]
    # A large range with no line unique to both is one change, not a search.
    diff = align(b"}\n\n}\n\n}\n\n", b"\n}\n\n}\n\n}\n")
    assert diff.rows == 6 and diff.hunks == (0,)


def test_a_third_of_the_lines_changed_aligns_without_the_matchers_worst_case():
    left = [b"line %d" % n for n in range(20_000)]
    right = [b"x" + line if n % 3 == 0 else line for n, line in enumerate(left)]
    diff = align(b"\n".join(left) + b"\n", b"\n".join(right) + b"\n")
    assert len(diff.hunks) == 6667 and diff.changed == 6667 and not diff.added and not diff.removed
