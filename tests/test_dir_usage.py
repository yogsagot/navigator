"""Disk > Directory sizes' model: ``navigator/lib/file_ops/dirusage.py``."""

import os

import pytest

from navigator.lib.drives import mount, unmount
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops import dirusage


def tree(root):
    (root / "big").mkdir()
    (root / "big" / "deep").mkdir()
    (root / "big" / "deep" / "a").write_bytes(b"x" * 5000)
    (root / "big" / "b").write_bytes(b"x" * 3000)
    (root / "small").mkdir()
    (root / "small" / "c").write_bytes(b"x" * 10)
    (root / ".hidden").write_bytes(b"x" * 100)
    return root


def child(node, name):
    return next(each for each in node.children if each.name == name)


def test_totals_and_counts_add_up_from_the_bottom(tmp_path):
    root = dirusage.scan(tree(tmp_path))
    big = child(root, "big")
    files = 5000 + 3000 + 10 + 100
    dirs = sum(os.lstat(p).st_size for p in (tmp_path / "big", tmp_path / "big" / "deep", tmp_path / "small"))
    assert big.items == 3
    assert root.items == 7
    assert root.size == os.lstat(tmp_path).st_size + files + dirs
    assert big.size == os.lstat(tmp_path / "big").st_size + os.lstat(tmp_path / "big" / "deep").st_size + 8000
    assert child(big, "b").size == 3000 and child(big, "b").children is None
    assert root.usage == sum(each.usage for each in root.children) + os.lstat(tmp_path).st_blocks * 512


def test_a_link_to_a_directory_is_not_entered(tmp_path):
    tree(tmp_path)
    (tmp_path / "loop").symlink_to(tmp_path)
    root = dirusage.scan(tmp_path)
    link = child(root, "loop")
    assert link.is_link and link.children is None
    assert root.items == 8


def test_a_hard_link_counts_once(tmp_path):
    (tmp_path / "one").write_bytes(b"x" * 4000)
    os.link(tmp_path / "one", tmp_path / "two")
    root = dirusage.scan(tmp_path)
    first, second = sorted(root.children, key=lambda each: each.hardlink)
    assert not first.hardlink and second.hardlink
    assert second.size == 4000
    assert root.size == os.lstat(tmp_path).st_size + 4000


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads everything")
def test_a_directory_that_cannot_be_read_is_flagged_and_the_rest_goes_on(tmp_path):
    tree(tmp_path)
    shut = tmp_path / "shut"
    shut.mkdir()
    (shut / "inside").write_bytes(b"x")
    shut.chmod(0)
    try:
        root = dirusage.scan(tmp_path)
    finally:
        shut.chmod(0o755)
    assert child(root, "shut").unreadable
    assert child(child(root, "big"), "b").size == 3000


def test_the_starting_directory_unreadable_raises(tmp_path):
    with pytest.raises(OSError):
        dirusage.scan(tmp_path / "missing")


def test_another_file_system_is_listed_but_not_entered(tmp_path, monkeypatch):
    tree(tmp_path)
    real = os.lstat

    class Moved:
        def __init__(self, st):
            self._st = st

        def __getattr__(self, name):
            return 999 if name == "st_dev" else getattr(self._st, name)

    # The top is "another device" than everything under it, which is as good.
    monkeypatch.setattr(dirusage.os, "lstat", lambda path: Moved(real(path)))
    root = dirusage.scan(tmp_path)
    assert child(root, "big").other_fs and child(root, "big").children == []
    assert root.items == 3
    whole = dirusage.scan(tmp_path, one_filesystem=False)
    assert whole.items == 7


def test_a_stopped_job_ends_the_walk_with_none(tmp_path):
    job = dirusage.UsageJob()
    job.stop()
    assert dirusage.scan(tree(tmp_path), job) is None


def test_the_job_counts_as_it_goes(tmp_path):
    job = dirusage.UsageJob()
    dirusage.scan(tree(tmp_path), job)
    assert job.items == 7
    assert job.size >= 8110


def test_remove_takes_a_node_off_every_total_above_it(tmp_path):
    root = dirusage.scan(tree(tmp_path))
    big = child(root, "big")
    deep = child(big, "deep")
    before = (root.size, root.usage, root.items, big.size)
    dirusage.remove(deep)
    assert deep not in big.children and deep.parent is None
    assert root.size == before[0] - deep.size
    assert root.usage == before[1] - deep.usage
    assert root.items == before[2] - 2
    assert big.size == before[3] - deep.size


def test_ordered_sorts_by_size_name_and_items(tmp_path):
    root = dirusage.scan(tree(tmp_path))
    by_size = [each.name for each in dirusage.ordered(root, "size", apparent=True)]
    assert by_size[0] == "big"
    assert [each.name for each in dirusage.ordered(root, "name")] == [".hidden", "big", "small"]
    assert [each.name for each in dirusage.ordered(root, "name", descending=False)] == ["small", "big", ".hidden"]
    assert [each.name for each in dirusage.ordered(root, "items")][0] == "big"
    assert dirusage.ordered(root, "size", descending=False, apparent=True)[-1].name == "big"


def test_names_find_and_location_of_go_round(tmp_path):
    root = dirusage.scan(tree(tmp_path))
    deep = child(child(root, "big"), "deep")
    assert deep.names() == ["big", "deep"]
    assert root.find(["big", "deep"]) is deep
    assert root.find(["big", "nothing"]) is None
    assert dirusage.location_of(tmp_path, deep) == tmp_path / "big" / "deep"


def test_another_drive_is_walked_through_its_own_listing():
    drive = MemoryDrive("usage")
    mount(drive)
    try:
        top = drive.make("/top")
        drive.make("/top/sub")
        drive.make("/top/sub/f", b"x" * 700)
        drive.make("/top/g", b"x" * 30)
        root = dirusage.scan(top)
        assert root.items == 3
        assert child(child(root, "sub"), "f").size == 700
        # No blocks there: the room on the disk is the size.
        assert root.usage == root.size
    finally:
        unmount(drive.site)
