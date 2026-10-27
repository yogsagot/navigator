"""*Compare directories*' *Window, recursive*: two trees compared (``dirsync``),
and the copier's ``pairs`` that synchronizes them."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

import pytest

from navigator.lib.drives import mount, unmount
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops import dirsync, filecopy
from navigator.lib.file_ops.dircompare import CompareRequest
from navigator.lib.system.job import Stopped


def make(root: Path, files: dict[str, tuple[bytes, int]]) -> None:
    for name, (data, mtime) in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        os.utime(path, (mtime, mtime))


@pytest.fixture
def trees(tmp_path):
    make(tmp_path / "L", {"same": (b"1", 100), "newer": (b"2", 300), "older": (b"3", 100), "only": (b"4", 100),
                          "sub/deep": (b"5", 100), "sub/x": (b"6", 100), "lonely/a": (b"7", 100),
                          ".hidden": (b"8", 100), "clash": (b"9", 100)})
    make(tmp_path / "R", {"same": (b"1", 100), "newer": (b"2", 100), "older": (b"3", 300), "theirs": (b"4", 100),
                          "sub/deep": (b"X", 100), "sub/x": (b"6", 100), "clash/in": (b"9", 100)})
    return tmp_path / "L", tmp_path / "R"


def statuses(rows):
    return {str(row.path): row.status for row in rows}


def test_every_path_below_both_is_a_row_and_a_lonely_directory_one(trees):
    rows = dirsync.walk(*trees, CompareRequest(contents=True))
    assert statuses(rows) == {
        ".hidden": dirsync.LEFT_ONLY, "clash": dirsync.CONFLICT, "lonely": dirsync.LEFT_ONLY,
        "newer": dirsync.DIFFERS, "older": dirsync.DIFFERS, "only": dirsync.LEFT_ONLY, "same": dirsync.SAME,
        "sub/deep": dirsync.DIFFERS, "sub/x": dirsync.SAME, "theirs": dirsync.RIGHT_ONLY,
    }
    assert [str(row.path) for row in rows] == sorted(statuses(rows), key=lambda p: PurePosixPath(p).parts)


def test_dot_files_follow_the_panels(trees):
    assert ".hidden" not in statuses(dirsync.walk(*trees, CompareRequest(), show_hidden=False))


def test_time_differs_either_way_and_the_newer_side_wins(trees):
    rows = {str(row.path): row for row in dirsync.walk(*trees, CompareRequest())}
    assert (rows["newer"].newer, rows["newer"].action) == ("left", dirsync.COPY_RIGHT)
    assert (rows["older"].newer, rows["older"].action) == ("right", dirsync.COPY_LEFT)
    # Same size and time, other bytes: the same until contents are asked for.
    assert rows["sub/deep"].status == dirsync.SAME
    assert rows["only"].action == dirsync.COPY_RIGHT and rows["theirs"].action == dirsync.COPY_LEFT
    assert rows["clash"].action == dirsync.SKIP


def test_an_action_a_status_does_not_allow_is_refused(trees):
    rows = {str(row.path): row for row in dirsync.walk(*trees, CompareRequest())}
    assert dirsync.with_action(rows["only"], dirsync.COPY_LEFT) is rows["only"]
    assert dirsync.with_action(rows["only"], dirsync.DELETE).action == dirsync.DELETE
    assert dirsync.with_action(rows["newer"], dirsync.DELETE) is rows["newer"]
    changed = dirsync.with_action(rows["newer"], dirsync.COPY_LEFT)
    assert dirsync.with_action(changed, "default").action == dirsync.COPY_RIGHT


def test_the_plan_copies_each_way_and_deletes_from_the_side_a_row_is_on(trees):
    left, right = trees
    rows = {str(row.path): row for row in dirsync.walk(left, right, CompareRequest())}
    rows["theirs"] = dirsync.with_action(rows["theirs"], dirsync.DELETE)
    plan = dirsync.plan(list(rows.values()), left, right)
    assert set(plan.pairs) == {
        (left / ".hidden", right / ".hidden"), (left / "lonely", right / "lonely"),
        (left / "newer", right / "newer"), (right / "older", left / "older"), (left / "only", right / "only"),
    }
    assert plan.deletes == [right / "theirs"]
    totals = dirsync.summary(list(rows.values()))
    assert (totals.right, totals.left, totals.delete) == (4, 1, 1)


def test_the_walk_stops_when_the_job_does(trees):
    job = dirsync.SyncJob()
    job.stop()
    with pytest.raises(Stopped):
        dirsync.walk(*trees, CompareRequest(), job)


def test_a_tree_on_another_drive_is_walked_through_it(tmp_path):
    drive = mount(MemoryDrive("sync"))
    try:
        drive.make("/top/a.txt", "alpha")
        drive.make("/top/sub/b.txt", "beta")
        (tmp_path / "a.txt").write_text("alpha")
        rows = dirsync.walk(drive.location("/top"), tmp_path, CompareRequest(size=True, time=False))
        assert statuses(rows) == {"a.txt": dirsync.SAME, "sub": dirsync.LEFT_ONLY}
    finally:
        unmount(drive.site)


def test_pairs_copy_both_ways_in_one_job_and_keep_the_times(trees):
    left, right = trees
    request = filecopy.CopyRequest(sources=[], target="", mode=filecopy.OVERWRITE, options=filecopy.PRESERVE,
                                   pairs=[(left / "newer", right / "newer"), (right / "older", left / "older"),
                                          (left / "lonely", right / "lonely")])
    job = filecopy.CopyJob(asker=lambda question: pytest.fail(f"asked {question}"))
    done = filecopy.run(request, job, left)
    assert done == [left / "newer", right / "older", left / "lonely"]
    assert job.total_bytes == 3
    assert (right / "lonely" / "a").read_bytes() == b"7"
    assert os.stat(right / "newer").st_mtime == 300 and os.stat(left / "older").st_mtime == 300
    rows = dirsync.walk(left, right, CompareRequest())
    assert {str(row.path) for row in rows if row.status == dirsync.DIFFERS} == set()
