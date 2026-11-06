"""File > Encoding > Convert text (navigator.lib.file_ops.textconv) -- a departure, asked for."""

from __future__ import annotations

import codecs
import os

from conftest import Until, run_app
from navkit.events import KeyEvent

from navigator.lib.drives import Location
from navigator.lib.editor import encodings
from navigator.lib.file_ops import textconv
from navigator.settings import SETTINGS


def run(paths, **options) -> textconv.TextJob:
    job = textconv.TextJob()
    files = textconv.plan([Location.of(path) for path in paths], job)
    textconv.convert(files, textconv.Options(**options), job)
    return job


def test_line_endings_are_made_one_kind(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"one\r\ntwo\rthree\n")
    job = run([tmp_path / "a.txt"], ending="lf")
    assert (tmp_path / "a.txt").read_bytes() == b"one\ntwo\nthree\n"
    assert len(job.converted) == 1
    run([tmp_path / "a.txt"], ending="crlf")
    assert (tmp_path / "a.txt").read_bytes() == b"one\r\ntwo\r\nthree\r\n"


def test_a_code_page_file_becomes_utf8_through_the_fallback(tmp_path):
    (tmp_path / "ru.txt").write_bytes("привет\r\n".encode("cp1251"))
    job = run([tmp_path / "ru.txt"], encoding=encodings.UTF8)
    # Not UTF-8, and nothing to read it as: left alone.
    assert job.skipped[0][1] == textconv.UNDECODABLE
    run([tmp_path / "ru.txt"], encoding=encodings.UTF8, fallback="cp1251", ending="lf")
    assert (tmp_path / "ru.txt").read_bytes() == "привет\n".encode()


def test_marks_are_read_and_written(tmp_path):
    (tmp_path / "bom.txt").write_bytes(codecs.BOM_UTF8 + "żółw\n".encode())
    run([tmp_path / "bom.txt"], encoding=encodings.UTF16_LE)
    assert (tmp_path / "bom.txt").read_bytes() == codecs.BOM_UTF16_LE + "żółw\n".encode("utf-16-le")
    run([tmp_path / "bom.txt"], encoding=encodings.UTF8)
    assert (tmp_path / "bom.txt").read_bytes() == "żółw\n".encode()


def test_what_cannot_be_converted_is_left_alone_and_said_why(tmp_path):
    (tmp_path / "bin").write_bytes(b"\x7fELF\x00\x01\x02")
    (tmp_path / "euro.txt").write_bytes("a\nprice €\n".encode())
    job = run([tmp_path], encoding="cp437")
    reasons = {os.path.basename(name): (kind, detail) for name, kind, detail in job.skipped}
    assert reasons == {"bin": (textconv.BINARY, ""), "euro.txt": (textconv.UNENCODABLE, "2:7")}
    assert (tmp_path / "euro.txt").read_bytes() == "a\nprice €\n".encode()


def test_a_file_already_so_is_not_written(tmp_path):
    path = tmp_path / "a.txt"
    path.write_bytes(b"x\n")
    os.utime(path, ns=(1_000_000_000, 1_000_000_000))
    job = run([path], ending="lf", encoding=encodings.UTF8)
    assert job.unchanged == [Location.of(path)] and not job.converted
    assert path.stat().st_mtime_ns == 1_000_000_000


def test_mode_is_kept_and_times_when_asked(tmp_path):
    path = tmp_path / "a.sh"
    path.write_bytes(b"echo\r\n")
    path.chmod(0o751)
    os.utime(path, ns=(1_000_000_000, 2_000_000_000))
    run([path], ending="lf", keep_times=True)
    assert path.read_bytes() == b"echo\n"
    assert path.stat().st_mode & 0o777 == 0o751
    assert path.stat().st_mtime_ns == 2_000_000_000
    assert sorted(os.listdir(tmp_path)) == ["a.sh"]


def test_a_hard_linked_file_is_written_into_so_the_links_stay(tmp_path):
    path = tmp_path / "a.txt"
    path.write_bytes(b"x\r\n")
    os.link(path, tmp_path / "b.txt")
    run([path], ending="lf")
    assert (tmp_path / "b.txt").read_bytes() == b"x\n"
    assert path.stat().st_ino == (tmp_path / "b.txt").stat().st_ino


def test_a_symbolic_link_stays_a_link(tmp_path):
    (tmp_path / "real.txt").write_bytes(b"x\r\n")
    (tmp_path / "link.txt").symlink_to("real.txt")
    run([tmp_path / "link.txt"], ending="lf")
    assert (tmp_path / "link.txt").is_symlink()
    assert (tmp_path / "real.txt").read_bytes() == b"x\n"


def test_file_encoding_convert_text_runs_over_the_tagged_files(tmp_path, quiet_console):
    from navigator.__main__ import Navigator
    from conftest import FakeTerminal

    (tmp_path / "a.txt").write_bytes(b"one\r\ntwo\r\n")
    SETTINGS.text_conversion.ending = "lf"
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = {}

    def start(a):
        a.manager.left.marked = frozenset({"a.txt"})
        a.manager.spawn(a.manager.convert_text(a.manager.left))

    run_app(app, [start, Until(lambda a: a.modal is not None),
                  lambda a: seen.update(title=a.modal.title), KeyEvent("enter"),
                  Until(lambda a: a.modal is not None and a.modal.title != seen["title"]),
                  lambda a: seen.update(prompt=a.modal.prompt, marked=a.manager.left.marked),
                  KeyEvent("enter")])
    assert seen["title"] == "Convert Text Files"
    assert (tmp_path / "a.txt").read_bytes() == b"one\ntwo\n"
    assert "1 file converted" in seen["prompt"] and not seen["marked"]


from test_editor import quiet_console  # noqa: E402,F401


def test_files_on_another_drive_are_converted_through_it():
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = mount(MemoryDrive("text"))
    try:
        drive.make("/files/a.txt", "one\r\ntwo\r\n")
        job = textconv.TextJob()
        textconv.convert(textconv.plan([drive.location("/files")], job), textconv.Options(ending="lf"), job)
        assert drive.read("/files/a.txt") == b"one\ntwo\n"
        assert len(job.converted) == 1 and not job.errors
        # The new file was renamed over the old: nothing left beside it.
        assert [name for name, _ in drive.children(drive.location("/files"))] == ["a.txt"]
    finally:
        unmount(drive.site)
