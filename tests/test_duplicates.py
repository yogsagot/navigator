"""Panel > Find duplicates: identical files as a listing that keeps its groups together."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.file_ops.duplicates import DuplicatesJob, DuplicatesRequest, find_duplicates
from navigator.lib.file_ops.filefind import CHUNK
from navigator.lib.system.job import Stopped
from navigator.widgets.manager.commands import FindDuplicates, Rescan


def groups(start: Path, request: DuplicatesRequest = DuplicatesRequest(), **kwargs) -> list[list[str]]:
    found = find_duplicates(request, start, DuplicatesJob(), **kwargs)
    return [[str(path.relative_to(start)) for path in group] for group in found]


# -- the model ---------------------------------------------------------------------------


def test_identical_files_are_grouped_and_single_ones_dropped(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "sub" / "b.txt").write_text("same")
    (tmp_path / "c.txt").write_text("diff")  # the same size, other bytes
    (tmp_path / "d.txt").write_text("unique and longer")
    assert groups(tmp_path) == [["a.txt", "sub/b.txt"]]


def test_the_full_hash_splits_what_the_quick_one_cannot(tmp_path):
    body = bytearray(b"x" * (3 * CHUNK))
    (tmp_path / "one").write_bytes(body)
    (tmp_path / "two").write_bytes(body)
    body[CHUNK + 10] = ord("y")  # past the first chunk, before the last
    (tmp_path / "three").write_bytes(body)
    assert groups(tmp_path) == [["one", "two"]]


def test_hard_links_are_one_file_and_symlinks_are_passed_over(tmp_path):
    (tmp_path / "a").write_text("data")
    os.link(tmp_path / "a", tmp_path / "b")
    (tmp_path / "c").symlink_to(tmp_path / "a")
    assert groups(tmp_path) == []
    (tmp_path / "d").write_text("data")
    assert groups(tmp_path) == [["a", "d"]]


def test_mask_size_hidden_and_depth_are_respected(tmp_path):
    (tmp_path / "sub").mkdir()
    for name in ("a.txt", "b.txt", "c.log", ".h.txt", "sub/d.txt"):
        (tmp_path / name).write_text("12345")
    (tmp_path / "e.txt").write_text("")
    (tmp_path / "f.txt").write_text("")
    assert groups(tmp_path, DuplicatesRequest(mask="*.txt")) == [[".h.txt", "a.txt", "b.txt", "sub/d.txt"]]
    assert groups(tmp_path, DuplicatesRequest(mask="*.txt"), show_hidden=False) == [["a.txt", "b.txt", "sub/d.txt"]]
    assert groups(tmp_path, DuplicatesRequest(mask="*.txt", recursive=False), show_hidden=False) == [["a.txt", "b.txt"]]
    assert groups(tmp_path, DuplicatesRequest(min_size=6)) == []


def test_the_groups_wasting_most_come_first(tmp_path):
    for name in ("s1", "s2", "s3"):
        (tmp_path / name).write_text("ab")  # 2 bytes wasted twice: 4
    for name in ("l2", "l1"):
        (tmp_path / name).write_text("abcdefgh")  # 8 bytes wasted once
    assert groups(tmp_path) == [["l1", "l2"], ["s1", "s2", "s3"]]


def test_a_stopped_job_raises(tmp_path):
    (tmp_path / "a").write_text("x")
    job = DuplicatesJob()
    job.stop()
    with pytest.raises(Stopped):
        find_duplicates(DuplicatesRequest(), tmp_path, job)


# -- the command -------------------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("small")
    (tmp_path / "z.txt").write_text("small")
    (tmp_path / "b.txt").write_text("much longer text")
    (tmp_path / "sub" / "y.txt").write_text("much longer text")
    (tmp_path / "alone.txt").write_text("nothing like it")
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def listed(app) -> bool:
    return app.manager.left.found is not None and app.modal is None


def keys(panel) -> list[str]:
    return [e.key for e in panel.items]


def test_the_box_asks_and_the_listing_keeps_its_groups_together(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.manager.left.focus(), lambda a: a.spawn(a.run_command(FindDuplicates)),
                  Until(lambda a: a.modal is not None),
                  lambda a: seen.update(box=a.modal.title), KeyEvent("enter"),
                  Until(listed), lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left), sort=a.manager.left.sort_mode,
                                        title=a.manager.left.found.title)])
    assert seen["box"] == "Find duplicates" and seen["sort"] == "name"
    assert seen["items"] == ["..", *(str(place / n) for n in ("b.txt", "sub/y.txt", "a.txt", "z.txt"))]
    assert seen["title"].startswith("Duplicates: ")


def test_ctrl_r_keeps_the_order_and_drops_what_was_erased(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.manager.find_duplicates(a.manager.left, DuplicatesRequest())), Until(listed),
                  lambda a: (place / "b.txt").unlink(),
                  lambda a: a.spawn(a.run_command(Rescan)),
                  Until(lambda a: len(a.manager.left.items) == 4), lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left))])
    assert seen["items"] == ["..", *(str(place / n) for n in ("sub/y.txt", "a.txt", "z.txt"))]


def test_nothing_alike_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "a").write_text("one")
    app = navigator(tmp_path)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.manager.find_duplicates(a.manager.left, DuplicatesRequest())),
                  Until(lambda a: a.modal is not None and a.modal.title == "Error"),
                  lambda a: seen.update(prompt=a.modal.prompt, found=a.manager.left.found), KeyEvent("enter")])
    assert seen == {"prompt": "No duplicate files found", "found": None}


def test_off_in_a_find_listing(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: seen.update(before=a.command_enabled(FindDuplicates())),
                  lambda a: a.spawn(a.manager.find_duplicates(a.manager.left, DuplicatesRequest())), Until(listed),
                  lambda a: a.manager.left.focus(),
                  lambda a: seen.update(after=a.command_enabled(FindDuplicates()))])
    assert seen == {"before": True, "after": False}


# -- on any drive ------------------------------------------------------------------------------


@pytest.fixture
def memory():
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = mount(MemoryDrive("dups"))
    yield drive
    unmount(drive.site)


def test_duplicates_are_found_on_another_drive(memory):
    memory.make("/files/a.txt", "same")
    memory.make("/files/sub/b.txt", "same")
    memory.make("/files/c.txt", "diff")
    found = find_duplicates(DuplicatesRequest(), memory.location("/files"), DuplicatesJob())
    assert [[str(place.path) for place in group] for group in found] == [["/files/a.txt", "/files/sub/b.txt"]]


def test_a_drive_whose_files_cannot_seek_still_tells_them_apart(memory, monkeypatch):
    import io

    class Stream(io.BytesIO):
        def seekable(self):
            return False

        def seek(self, *args):
            raise io.UnsupportedOperation("not seekable")

    real = memory.open_read
    monkeypatch.setattr(memory, "open_read", lambda location: Stream(real(location).read()))
    big = b"x" * (3 * CHUNK)
    memory.make("/files/one.bin", big)
    memory.make("/files/two.bin", big)
    memory.make("/files/other.bin", big[:-1] + b"y")  # the same head, the tail not
    found = find_duplicates(DuplicatesRequest(), memory.location("/files"), DuplicatesJob())
    assert [[place.name for place in group] for group in found] == [["one.bin", "two.bin"]]


def test_find_duplicates_lists_another_drive_s_copies(tmp_path, memory, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    memory.make("/files/a.txt", "same")
    memory.make("/files/b.txt", "same")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))
    seen = {}

    def go(a):
        a.manager.left.location = memory.location("/files")

    def look(a):
        seen["enabled"] = a.command_enabled(FindDuplicates(), a.manager.left)

    run_app(app, [
        go, Until(lambda a: len(a.manager.left.items) == 3), look,
        lambda a: a.manager.spawn(a.manager.find_duplicates(a.manager.left, DuplicatesRequest())),
        Until(lambda a: a.manager.left.found is not None, timeout=5),
        lambda a: seen.update(rows=[(e.name, str(e.directory)) for e in a.manager.left.items if e.name != ".."]),
    ])
    assert seen["enabled"] is True
    assert seen["rows"] == [("a.txt", "mem://dups/files"), ("b.txt", "mem://dups/files")]
