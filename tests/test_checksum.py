"""File > Checksums: coreutils' ``*sum`` lists made and checked
(:mod:`navigator.lib.file_ops.checksum`), on the disk and on another drive."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import Location, mount, unmount
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops import checksum
from navigator.lib.file_ops.checksum import (
    ChecksumJob, algorithm_of, default_list_name, format_line, parse, parse_line, with_extension,
)
from navigator.settings import SETTINGS
from navigator.widgets.manager.commands import CalculateChecksums, VerifyChecksums


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# -- the format ------------------------------------------------------------------------------------


def test_a_line_is_the_digest_two_spaces_and_the_name():
    assert format_line("ab" * 32, "a b.txt") == "ab" * 32 + "  a b.txt"
    assert parse_line("ab" * 32 + "  a b.txt") == ("ab" * 32, "a b.txt", None)


def test_a_name_with_a_backslash_or_newline_is_escaped_and_read_back():
    line = format_line("ab" * 32, "we\\ird\nname")
    assert line == "\\" + "ab" * 32 + "  we\\\\ird\\nname"
    assert parse_line(line) == ("ab" * 32, "we\\ird\nname", None)


def test_binary_marks_and_bsd_lines_are_read():
    assert parse_line("AB" * 16 + " *file") == ("ab" * 16, "file", None)
    assert parse_line("SHA256 (my file) = " + "cd" * 32) == ("cd" * 32, "my file", "sha256")
    assert parse_line("BLAKE2b (x) = " + "ef" * 64) == ("ef" * 64, "x", "blake2b")


def test_lines_that_are_not_checksums_are_counted_and_comments_are_not():
    entries, malformed = parse("# made by hand\n\n" + "ab" * 32 + "  a\nnonsense\nzz  b\n")
    assert [name for _, name, _ in entries] == ["a"]
    assert malformed == 2


def test_the_algorithm_is_told_by_the_name_then_by_the_digest():
    assert algorithm_of("x.sha256sum") == "sha256"
    assert algorithm_of("X.MD5") == "md5"
    assert algorithm_of("SHA512SUMS") == "sha512"
    assert algorithm_of("release.b2sum", "00" * 64) == "blake2b"
    assert algorithm_of("list.txt", "00" * 20) == "sha1"
    assert algorithm_of("list.txt", "00" * 32) == "sha256"
    assert algorithm_of("list.txt", "00" * 64) == "sha512"  # not BLAKE2b, without a name saying so
    assert algorithm_of("list.txt") is None
    assert algorithm_of(".sha256") is None  # a dot-file, not a list


def test_the_list_name_follows_the_algorithm():
    assert default_list_name("photos", "sha256") == "photos.sha256sum"
    assert default_list_name("", "md5") == "checksums.md5sum"
    assert with_extension("photos.sha256sum", "blake2b") == "photos.b2sum"
    assert with_extension("photos", "sha1") == "photos.sha1sum"


# -- on the disk -----------------------------------------------------------------------------------


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"alpha\n")
    (tmp_path / "d" / "sub").mkdir(parents=True)
    (tmp_path / "d" / "sub" / "b").write_bytes(b"beta\n")
    (tmp_path / "d" / "c").write_bytes(b"gamma\n")
    return tmp_path


def test_a_tagged_directory_is_walked_to_the_bottom_with_names_from_the_list(tree):
    job = ChecksumJob()
    base = Location.of(tree)
    files = checksum.walk([base / "a.txt", base / "d"], job)
    assert [checksum.relative_name(location, base) for location, _ in files] == ["a.txt", "d/c", "d/sub/b"]
    assert job.total == 6 + 6 + 5 and job.files_total == 3
    lines = checksum.list_text(checksum.calculate(files, "sha256", job), base)
    assert lines[0] == f"{sha(b'alpha' + bytes([10]))}  a.txt"
    assert job.files_done == 3 and job.position == job.total


@pytest.mark.skipif(shutil.which("sha256sum") is None, reason="needs coreutils' sha256sum")
def test_coreutils_checks_what_calculate_wrote(tree):
    (tree / "we\\ird").write_bytes(b"x")
    base = Location.of(tree)
    job = ChecksumJob()
    files = checksum.walk([base / "a.txt", base / "d", base / "we\\ird"], job)
    (tree / "all.sha256sum").write_text("\n".join(checksum.list_text(checksum.calculate(files, "sha256", job), base))
                                        + "\n")
    run = subprocess.run(["sha256sum", "-c", "all.sha256sum"], cwd=tree, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr


def test_verify_tells_matched_changed_missing_and_malformed(tree):
    listing = tree / "all.sha256sum"
    listing.write_text(f"{sha(b'alpha' + bytes([10]))}  a.txt\n"
                       f"{sha(b'other')}  d/c\n"
                       f"{sha(b'gone')}  nowhere\n"
                       f"{'00' * 16}  wrong-length\n"
                       "junk\n")
    result = checksum.verify([Location.of(listing)], ChecksumJob())
    assert result.ok == 1
    assert [location.name for location in result.failed] == ["c"]
    assert [location.name for location in result.missing] == ["nowhere"]
    assert result.malformed == 2


def test_each_file_its_own_list(tree):
    job = ChecksumJob()
    base = Location.of(tree)
    written = checksum.write_each(checksum.walk([base / "a.txt"], job), "md5", job)
    assert [location.name for location in written] == ["a.txt.md5sum"]
    assert (tree / "a.txt.md5sum").read_text() == f"{hashlib.md5(b'alpha' + bytes([10])).hexdigest()}  a.txt\n"


# -- on another drive ------------------------------------------------------------------------------


@pytest.fixture
def memory():
    drive = mount(MemoryDrive("sums"))
    drive.make("/files/one.txt", "first")
    drive.make("/files/dir/two.txt", "second")
    yield drive
    unmount(drive.site)


def test_files_on_another_drive_are_read_through_it(memory):
    base = memory.location("/files")
    job = ChecksumJob()
    done = checksum.calculate(checksum.walk([base / "one.txt", base / "dir"], job), "sha1", job)
    lines = checksum.list_text(done, base)
    assert lines == [f"{hashlib.sha1(b'first').hexdigest()}  one.txt",
                     f"{hashlib.sha1(b'second').hexdigest()}  dir/two.txt"]
    memory.make("/files/files.sha1sum", "\n".join(lines) + "\n")
    memory.make("/files/dir/two.txt", "changed")
    result = checksum.verify([base / "files.sha1sum"], ChecksumJob())
    assert result.ok == 1 and [str(location.path) for location in result.failed] == ["/files/dir/two.txt"]


# -- the file manager ------------------------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    here = tmp_path / "photos"
    (here / "d").mkdir(parents=True)
    for name in ("a.txt", "b.txt", "d/c.txt"):
        (here / name).write_text(name)
    return here


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def test_calculate_writes_one_list_untags_the_files_and_the_name_follows_the_algorithm(place):
    app = navigator(place)
    seen = {}

    def start(a):
        a.manager.left.marked = frozenset({"a.txt", "d"})
        a.manager.spawn(a.manager.calculate_checksums(a.manager.left))

    def look(a):
        d = a.modal
        seen.update(title=d.title, name=d.list_name.value, algorithm=d.algorithm.value)
        d.algorithm.value = 0  # MD5

    run_app(app, [start, Until(lambda a: a.modal is not None), look, lambda a: None,
                  lambda a: seen.update(renamed=a.modal.list_name.value), KeyEvent("enter"),
                  Until(lambda a: (place / "photos.md5sum").exists() and not a.manager.left.marked)])
    assert seen == {"title": "Calculate Checksums", "name": "photos.sha256sum", "algorithm": 2,
                    "renamed": "photos.md5sum"}
    # In the panel's order, which lists directories first.
    assert (place / "photos.md5sum").read_text() == (f"{hashlib.md5(b'd/c.txt').hexdigest()}  d/c.txt\n"
                                                     f"{hashlib.md5(b'a.txt').hexdigest()}  a.txt\n")
    assert SETTINGS.checksum.algorithm == "md5"


def test_calculate_each_file_its_own_list(place):
    app = navigator(place)

    def start(a):
        a.manager.left.marked = frozenset({"a.txt", "b.txt"})
        a.manager.spawn(a.manager.calculate_checksums(a.manager.left))

    def each(a):
        a.modal.mode.value = 1

    run_app(app, [start, Until(lambda a: a.modal is not None), each, KeyEvent("enter"),
                  Until(lambda a: (place / "b.txt.sha256sum").exists())])
    assert (place / "a.txt.sha256sum").read_text() == f"{sha(b'a.txt')}  a.txt\n"


def test_verify_reports_and_tags_what_did_not_match(place):
    (place / "photos.sha256sum").write_text(f"{sha(b'a.txt')}  a.txt\n{sha(b'b.txt')}  b.txt\n"
                                            f"{sha(b'd/c.txt')}  d/c.txt\n")
    (place / "b.txt").write_text("changed")
    app = navigator(place)
    seen = {}

    def start(a):
        panel = a.manager.left
        panel.cursor = [entry.name for entry in panel.items].index("photos.sha256sum")
        seen["enabled"] = a.manager.enables(VerifyChecksums())
        a.manager.spawn(a.manager.verify_checksums(panel))

    def look(a):
        d = a.modal
        seen.update(title=d.title, summary=d.summary.text, bad=list(d.bad.items), marked=a.manager.left.marked)

    run_app(app, [start, Until(lambda a: a.modal is not None and a.modal.title == "Verify Checksums"), look,
                  KeyEvent("enter")])
    assert seen["enabled"] and seen["title"] == "Verify Checksums"
    assert "OK: 2" in seen["summary"] and "Failed: 1" in seen["summary"]
    assert len(seen["bad"]) == 1 and seen["bad"][0].startswith("FAILED") and seen["bad"][0].endswith("b.txt")
    assert seen["marked"] == frozenset({"b.txt"})


def test_the_commands_wait_for_something_to_work_on(place):
    app = navigator(place)
    seen = {}

    def look(a):
        panel = a.manager.left
        panel.cursor = [entry.name for entry in panel.items].index("d")
        seen["calculate"] = a.manager.enables(CalculateChecksums())
        seen["verify"] = a.manager.enables(VerifyChecksums())

    run_app(app, [look])
    assert seen == {"calculate": True, "verify": False}
