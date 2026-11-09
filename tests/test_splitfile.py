"""File > Split/combine (navigator.lib.file_ops.splitfile): DN's LongCopy, by size, with TC's .crc."""

from __future__ import annotations

import os
import random
import zlib

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.drives import Location, mount, unmount
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops import splitfile
from navigator.lib.file_ops.splitfile import (
    CombineRequest, SplitError, SplitRequest, combine, mode_for, parse_size, part_name, read_crc, split,
)
from navigator.lib.file_ops.uucode import FileExists
from navigator.lib.system.job import Stopped
from navigator.settings import SETTINGS
from navigator.widgets.editor.loading import FileJob
from navigator.widgets.file_ops.combine_dialog import CombineDialog
from navigator.widgets.file_ops.exists_query import ExistsQuery
from navigator.widgets.file_ops.split_dialog import SplitDialog

DATA = random.Random(12).randbytes(2500)


class Asking(FileJob):
    """A job whose questions are answered in turn from *answers*, and kept."""

    def __init__(self, *answers: str) -> None:
        super().__init__()
        self.answers = list(answers)
        self.asked: list[object] = []

    def ask(self, question):
        self.asked.append(question)
        return self.answers.pop(0) if self.answers else "cancel"


def here(path) -> Location:
    return Location.of(path)


def split_into(tmp_path, size=1000, target="", checksum=True, job=None):
    source = tmp_path / "blob.bin"
    if not source.exists():
        source.write_bytes(DATA)
    return split(SplitRequest(here(source), target, here(tmp_path), size, checksum), job or FileJob())


# -- names -------------------------------------------------------------------------------------


@pytest.mark.parametrize("text, size", [("100M", 100 << 20), ("1.44M", int(1.44 * (1 << 20))), ("4g", 4 << 30),
                                        ("512 KB", 512 << 10), ("650MiB", 650 << 20), ("1234", 1234),
                                        ("1,5k", 1536)])
def test_sizes_read_in_powers_of_1024(text, size):
    assert parse_size(text) == size


@pytest.mark.parametrize("text", ["", "M", "-1", "0", "ten", "1.5X"])
def test_what_is_not_a_size_is_refused(text):
    with pytest.raises(SplitError):
        parse_size(text)


def test_parts_and_their_crc_combine_anything_else_splits():
    assert mode_for("a.iso.001") == mode_for("a.iso.017") == mode_for("a.1000") == "combine"
    assert mode_for("a.iso.crc", {"a.iso.001"}) == "combine"
    assert mode_for("a.iso.crc", set()) == mode_for("a.iso") == mode_for("a.01") == mode_for("a.000") == "split"
    assert part_name("a", 7) == "a.007" and part_name("a", 1000) == "a.1000"


def test_a_crc_reads_either_line_end_and_any_case():
    info = read_crc("FileName=x.iso\r\nSIZE=12\r\ncrc32=00ab12CD\r\nnoise\r\n")
    assert (info.filename, info.size, info.crc32) == ("x.iso", 12, 0xAB12CD)


# -- split -------------------------------------------------------------------------------------


def test_split_cuts_even_parts_and_writes_tcs_crc(tmp_path):
    (tmp_path / "blob.bin").write_bytes(DATA)
    os.utime(tmp_path / "blob.bin", (1_000_000, 1_000_000))
    split_into(tmp_path)
    sizes = [(tmp_path / f"blob.bin.{n:03d}").stat().st_size for n in (1, 2, 3)]
    assert sizes == [1000, 1000, 500] and not (tmp_path / "blob.bin.004").exists()
    assert b"".join((tmp_path / f"blob.bin.{n:03d}").read_bytes() for n in (1, 2, 3)) == DATA
    assert (tmp_path / "blob.bin.crc").read_text() == (
        f"filename=blob.bin\nsize=2500\ncrc32={zlib.crc32(DATA):08X}\n")
    assert (tmp_path / "blob.bin.002").stat().st_mtime == 1_000_000


def test_split_into_a_directory_or_under_another_name(tmp_path):
    (tmp_path / "out").mkdir()
    split_into(tmp_path, target="out/")
    assert (tmp_path / "out" / "blob.bin.003").exists()
    split_into(tmp_path, target="out/part", checksum=False)
    assert (tmp_path / "out" / "part.001").exists() and not (tmp_path / "out" / "part.crc").exists()


def test_a_file_no_larger_than_one_part_is_refused(tmp_path):
    with pytest.raises(SplitError):
        split_into(tmp_path, size=2500)
    assert not (tmp_path / "blob.bin.001").exists()


def test_parts_there_already_are_asked_about_and_stale_ones_removed(tmp_path):
    split_into(tmp_path, size=500)  # five parts
    job = Asking("all")
    split_into(tmp_path, size=1000, job=job)
    assert job.asked == [FileExists(tmp_path / "blob.bin.001")]
    assert not (tmp_path / "blob.bin.004").exists() and not (tmp_path / "blob.bin.005").exists()


def test_no_to_a_part_there_already_writes_nothing(tmp_path):
    split_into(tmp_path, size=500)
    before = (tmp_path / "blob.bin.001").read_bytes()
    with pytest.raises(Stopped):
        split_into(tmp_path, size=1000, job=Asking("no"))
    assert (tmp_path / "blob.bin.001").read_bytes() == before and (tmp_path / "blob.bin.005").exists()


def test_a_stopped_split_leaves_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(splitfile, "CHUNK", 100)
    job = FileJob()
    real = splitfile._step
    calls = []

    def step(j):
        calls.append(1)
        if len(calls) == 15:
            j.stop()
        real(j)

    monkeypatch.setattr(splitfile, "_step", step)
    with pytest.raises(Stopped):
        split_into(tmp_path, job=job)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["blob.bin"]


# -- combine -----------------------------------------------------------------------------------


@pytest.mark.parametrize("start", ["blob.bin.002", "blob.bin.crc"])
def test_combine_from_any_part_or_the_crc(tmp_path, start):
    split_into(tmp_path)
    (tmp_path / "out").mkdir()
    os.utime(tmp_path / "blob.bin.001", (2_000_000, 2_000_000))
    result = combine(CombineRequest(here(tmp_path / start), "out/", here(tmp_path)), FileJob())
    assert result.crc_checked
    assert (tmp_path / "out" / "blob.bin").read_bytes() == DATA
    assert (tmp_path / "out" / "blob.bin").stat().st_mtime == 2_000_000


def test_the_crcs_name_wins_and_a_set_without_one_is_combined_unchecked(tmp_path):
    split_into(tmp_path)
    (tmp_path / "blob.bin.crc").write_text(f"filename=original.iso\nsize=2500\ncrc32={zlib.crc32(DATA):08X}\n")
    combine(CombineRequest(here(tmp_path / "blob.bin.001"), "", here(tmp_path)), FileJob())
    assert (tmp_path / "original.iso").read_bytes() == DATA
    (tmp_path / "blob.bin.crc").unlink()
    result = combine(CombineRequest(here(tmp_path / "blob.bin.001"), "joined", here(tmp_path)), FileJob())
    assert not result.crc_checked and (tmp_path / "joined").read_bytes() == DATA


def test_a_missing_part_is_said_and_nothing_written(tmp_path):
    split_into(tmp_path)
    (tmp_path / "blob.bin.003").unlink()
    (tmp_path / "out").mkdir()
    with pytest.raises(SplitError, match=r"blob\.bin\.003"):
        combine(CombineRequest(here(tmp_path / "blob.bin.001"), "out/", here(tmp_path)), FileJob())
    assert not (tmp_path / "out" / "blob.bin").exists()


def test_a_stale_part_after_the_crcs_size_is_not_read(tmp_path):
    split_into(tmp_path)
    (tmp_path / "blob.bin.004").write_bytes(b"left from before")
    (tmp_path / "out").mkdir()
    combine(CombineRequest(here(tmp_path / "blob.bin.001"), "out/", here(tmp_path)), FileJob())
    assert (tmp_path / "out" / "blob.bin").read_bytes() == DATA


def test_a_damaged_part_keeps_the_file_and_says_so(tmp_path):
    split_into(tmp_path)
    damaged = bytearray((tmp_path / "blob.bin.002").read_bytes())
    damaged[10] ^= 0xFF
    (tmp_path / "blob.bin.002").write_bytes(bytes(damaged))
    (tmp_path / "out").mkdir()
    with pytest.raises(SplitError, match="damaged"):
        combine(CombineRequest(here(tmp_path / "blob.bin.001"), "out/", here(tmp_path)), FileJob())
    assert (tmp_path / "out" / "blob.bin").stat().st_size == 2500


def test_a_file_there_already_is_asked_about(tmp_path):
    split_into(tmp_path)
    (tmp_path / "blob.bin").write_bytes(b"other")
    with pytest.raises(Stopped):
        combine(CombineRequest(here(tmp_path / "blob.bin.001"), "", here(tmp_path)), Asking("no"))
    assert (tmp_path / "blob.bin").read_bytes() == b"other"
    combine(CombineRequest(here(tmp_path / "blob.bin.001"), "", here(tmp_path)), Asking("yes"))
    assert (tmp_path / "blob.bin").read_bytes() == DATA


def test_split_and_combine_on_another_drive():
    drive = mount(MemoryDrive("split"))
    try:
        root = drive.location("/")
        with drive.open_write(root / "blob.bin") as out:
            out.write(DATA)
        drive.mkdir(root / "parts")
        split(SplitRequest(root / "blob.bin", "parts/", root, 1000), FileJob())
        assert sorted(drive.names(root / "parts")) == ["blob.bin.001", "blob.bin.002", "blob.bin.003",
                                                     "blob.bin.crc"]
        combine(CombineRequest(root / "parts" / "blob.bin.001", "joined.bin", root), FileJob())
        with drive.open_read(root / "joined.bin") as handle:
            assert handle.read() == DATA
    finally:
        unmount(drive.site)


# -- the command -------------------------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    for name in ("a", "b"):
        (tmp_path / name).mkdir()
    (tmp_path / "a" / "blob.bin").write_bytes(DATA)
    return tmp_path


def on(name: str):
    def action(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def command(a):
    from navigator.widgets.manager.commands import SplitCombine

    a.spawn(a.run_command(SplitCombine))


def test_split_into_the_other_panel_keeps_the_size(place):
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    seen = {}

    def choose(a):
        seen["target"] = a.modal.target.value
        a.modal.size.value = "1k"

    run_app(app, [on("blob.bin"), command, Until(lambda a: isinstance(a.modal, SplitDialog)), choose,
                  KeyEvent("enter"), Until(lambda a: (place / "b" / "blob.bin.crc").exists() and a.modal is None)])
    assert seen["target"] == f"{place / 'b'}/"
    assert [p.name for p in sorted((place / "b").iterdir())] == ["blob.bin.001", "blob.bin.002", "blob.bin.003",
                                                                "blob.bin.crc"]
    assert SETTINGS.split.size == "1k" and "size = 1k" in SETTINGS.path.read_text()


def test_a_part_at_the_cursor_combines(place):
    split(SplitRequest(here(place / "a" / "blob.bin"), "", here(place / "a"), 1000), FileJob())
    (place / "a" / "blob.bin").unlink()
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    run_app(app, [on("blob.bin.002"), command, Until(lambda a: isinstance(a.modal, CombineDialog)),
                  KeyEvent("enter"), Until(lambda a: (place / "b" / "blob.bin").exists() and a.modal is None)])
    assert (place / "b" / "blob.bin").read_bytes() == DATA


def right_on(name: str):
    return Until(lambda a: a.manager.right.selected is not None and a.manager.right.selected.name == name)


def test_split_puts_the_other_panel_s_cursor_on_the_first_part(place):
    """As F5 lands on what it made: the panel showing the parts leaves ``..``
    for the first of them."""
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    seen = {}
    run_app(app, [on("blob.bin"), command, Until(lambda a: isinstance(a.modal, SplitDialog)),
                  lambda a: setattr(a.modal.size, "value", "1k"), KeyEvent("enter"),
                  Until(lambda a: (place / "b" / "blob.bin.crc").exists() and a.modal is None),
                  right_on("blob.bin.001"), lambda a: seen.update(at=a.manager.right.selected.name)])
    assert seen == {"at": "blob.bin.001"}


def test_combine_puts_the_other_panel_s_cursor_on_the_file_made(place):
    split(SplitRequest(here(place / "a" / "blob.bin"), "", here(place / "a"), 1000), FileJob())
    (place / "a" / "blob.bin").unlink()
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    seen = {}
    run_app(app, [on("blob.bin.002"), command, Until(lambda a: isinstance(a.modal, CombineDialog)),
                  KeyEvent("enter"), Until(lambda a: (place / "b" / "blob.bin").exists() and a.modal is None),
                  right_on("blob.bin"), lambda a: seen.update(at=a.manager.right.selected.name)])
    assert seen == {"at": "blob.bin"}


def test_a_bad_size_keeps_the_dialog_up(place):
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    seen = {}
    run_app(app, [on("blob.bin"), command, Until(lambda a: isinstance(a.modal, SplitDialog)),
                  lambda a: setattr(a.modal.size, "value", "lots"), KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and not isinstance(a.modal, SplitDialog)),
                  lambda a: seen.update(title=a.modal.title)])
    assert seen["title"] == "Error"
    assert not (place / "b" / "blob.bin.001").exists()


def test_no_to_a_part_there_already_from_the_command(place):
    (place / "b" / "blob.bin.001").write_bytes(b"keep")
    app = Navigator(place / "a", place / "b", terminal=FakeTerminal(80, 25))
    run_app(app, [on("blob.bin"), command, Until(lambda a: isinstance(a.modal, SplitDialog)),
                  lambda a: setattr(a.modal.size, "value", "1000"), KeyEvent("enter"),
                  Until(lambda a: isinstance(a.modal, ExistsQuery)), KeyEvent("n", alt=True),
                  Until(lambda a: a.modal is None)])
    assert (place / "b" / "blob.bin.001").read_bytes() == b"keep"
    assert not (place / "b" / "blob.bin.002").exists()
