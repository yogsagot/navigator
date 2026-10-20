"""The last commands that needed the disk, on another drive -- the in-memory
one standing for a server: Shift+F4, symlinks, Make list, Read file list, UU
encode and decode, and the dBase view."""

from __future__ import annotations

import asyncio
import struct
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navigator.lib.drives import Location, mount, unmount
from navigator.lib.drives.memory import MemoryDrive


@pytest.fixture
def memory():
    drive = mount(MemoryDrive("rest"))
    drive.make("/work/a.txt", "alpha")
    drive.make("/work/b.log", "beta")
    drive.make("/work/sub/c.txt", "gamma")
    yield drive
    unmount(drive.site)


@pytest.fixture
def desk(memory, tmp_path, monkeypatch):
    from navigator.__main__ import Navigator
    from navigator.settings import SETTINGS

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr(SETTINGS.confirmations, "save", False)
    monkeypatch.setattr(SETTINGS.confirmations, "create_dir", False)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))
    return app, memory, tmp_path


def at_work(memory):
    return [lambda a: setattr(a.manager.left, "location", memory.location("/work")),
            Until(lambda a: "a.txt" in [e.name for e in a.manager.left.items])]


def cursor_on(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [entry.name for entry in panel.items].index(name)
    return action


def modal_is(name):
    return lambda a: type(a.modal).__name__ == name


def test_nothing_is_greyed_for_being_off_the_disk(desk):
    from navigator.widgets.manager import commands
    from navigator.widgets.manager.manager import manager

    assert manager._LOCAL_ONLY == ()
    app, memory, _ = desk
    seen = {}
    run_app(app, [*at_work(memory), cursor_on("a.txt"), lambda a: seen.update(
        enabled={name: a.manager.enables(getattr(commands, name)()) for name in
                 ("EditNamed", "MakeLink", "MakeList", "ReadFileList", "UuEncode", "UuDecode", "ViewAsDataBase")})])
    assert all(seen["enabled"].values()), seen["enabled"]


def test_shift_f4_makes_a_new_file_on_another_drive_with_f2(desk):
    from navigator.widgets.editor.edit_window import EditWindow

    app, memory, _ = desk

    def editor(a):
        return next((w for w in a.shell.desktop.windows() if isinstance(w, EditWindow)), None)

    run_app(app, [
        *at_work(memory),
        KeyEvent("f4", shift=True), Until(lambda a: a.modal is not None),
        lambda a: setattr(a.modal.entry, "value", "sub/new.txt"), KeyEvent("enter"),
        Until(lambda a: editor(a) is not None, timeout=5),
        KeyEvent("n", char="n"), KeyEvent("f2"),
        Until(lambda a: memory.lexists(memory.location("/work/sub/new.txt")), timeout=5),
    ])
    assert memory.read("/work/sub/new.txt").startswith(b"n")


def test_a_link_is_made_on_its_drive_relative_or_not(memory):
    from navigator.lib.file_ops.filelink import make_link

    make_link(memory.location("/work/a.txt"), memory.location("/work/sub/to-a"), True)
    assert memory.readlink(memory.location("/work/sub/to-a")) == "../a.txt"
    make_link(memory.location("/work/a.txt"), memory.location("/work/abs"), False)
    assert memory.readlink(memory.location("/work/abs")) == "/work/a.txt"
    with pytest.raises(OSError):
        make_link(Path("/etc/hostname"), memory.location("/work/across"), False)


def test_make_list_writes_the_drives_own_paths_there(desk):
    app, memory, _ = desk

    def tag(a):
        panel = a.manager.left
        panel.marked = frozenset({"a.txt", "b.log"})

    run_app(app, [
        *at_work(memory), tag,
        KeyEvent("l", alt=True), Until(modal_is("MakeListDialog")),
        lambda a: setattr(a.modal.file_name, "value", "files.lst"),
        KeyEvent("enter"),
        Until(lambda a: memory.lexists(memory.location("/work/files.lst")), timeout=5),
    ])
    assert memory.read("/work/files.lst").decode().split() == ["a.txt", "b.log"]


def test_read_file_list_lists_what_a_list_on_another_drive_names(memory):
    from navigator.lib.file_ops.filefind import read_list_on_drive

    memory.make("/work/names.lst", "a.txt\nsub/c.txt\n*.log\nmissing.txt\n/work/a.txt\n")
    entries = read_list_on_drive(memory.location("/work/names.lst"), memory.location("/work"))
    assert [(str(entry.directory.path), entry.name) for entry in entries] == [
        ("/work", "a.txt"), ("/work/sub", "c.txt"), ("/work", "b.log")]


def test_uu_encode_and_decode_on_another_drive(desk):
    from navigator.lib.file_ops import uucode
    from navigator.widgets.manager.manager import Manager

    app, memory, _ = desk
    payload = bytes(range(256)) * 20
    memory.make("/work/blob.bin", payload)
    manager = app.manager
    place = memory.location("/work/blob.bin")

    class Job:
        stopped, position, total = False, 0, 0

        def wait_while_paused(self):
            pass

        def ask(self, question):
            return True

    def encode(job, local, staging):
        from navigator.lib.file_ops.filecopy import target_location

        dest = target_location("blob.uue", place.parent)
        request = uucode.EncodeRequest(local, str(staging / dest.name), lines=100_000)  # one section
        return uucode.encode(request, job, staging), dest.parent

    Manager._staged(place, encode)(Job())
    assert memory.lexists(memory.location("/work/blob.uue"))
    encoded = memory.location("/work/blob.uue")

    def decode(job, local, staging):
        return uucode.decode(local, staging, job), memory.location("/work/sub")

    Manager._staged(encoded, decode)(Job())
    assert memory.read("/work/sub/blob.bin") == payload


class Answering:
    """A job whose ``dlFileExist`` questions are answered from *answers*."""

    stopped, position, total = False, 0, 0

    def __init__(self, *answers):
        self.answers, self.asked = list(answers), []

    def wait_while_paused(self):
        pass

    def ask(self, question):
        self.asked.append(question.path)
        return self.answers.pop(0)


def test_uu_on_another_drive_asks_before_writing_over_a_file_there(desk):
    from navigator.lib.file_ops import uucode
    from navigator.lib.system.job import Stopped
    from navigator.widgets.manager.manager import Manager

    _, memory, _ = desk
    memory.make("/work/blob.bin", b"x" * 300)
    memory.make("/work/blob.uue", "old")
    place = memory.location("/work/blob.bin")

    def encode(job, local, staging):
        request = uucode.EncodeRequest(local, str(staging / "blob.uue"), lines=100_000)
        return uucode.encode(request, job, staging), place.parent

    # No: the encoding is abandoned, the file there left as it was.
    job = Answering("no")
    with pytest.raises(Stopped):
        Manager._staged(place, encode, uucode.ask_over_encoded)(job)
    assert job.asked == [memory.location("/work/blob.uue")]
    assert memory.read("/work/blob.uue") == b"old"
    Manager._staged(place, encode, uucode.ask_over_encoded)(Answering("yes"))
    assert b"begin 644 blob.bin" in memory.read("/work/blob.uue")

    memory.make("/work/sub/blob.bin", "kept")

    def decode(job, local, staging):
        return uucode.decode(local, staging, job, check_existing=False), memory.location("/work/sub")

    def ask(existing, job):
        return uucode.ask_over_decoded(existing, job, True)

    encoded = memory.location("/work/blob.uue")
    Manager._staged(encoded, decode, ask)(Answering("no"))
    assert memory.read("/work/sub/blob.bin") == b"kept"
    Manager._staged(encoded, decode, ask)(Answering("all"))
    assert memory.read("/work/sub/blob.bin") == b"x" * 300


def dbf_bytes() -> bytes:
    """A dBase III file: one character field NAME(8), two records."""
    header_len, record_len = 32 + 32 + 1, 1 + 8
    head = struct.pack("<BBBBIHH20x", 3, 126, 1, 1, 2, header_len, record_len)
    field = b"NAME".ljust(11, b"\0") + b"C" + b"\0" * 4 + bytes([8, 0]) + b"\0" * 14
    records = b" alpha   " + b" beta    "
    return head + field + b"\r" + records + b"\x1a"


def test_the_dbase_view_of_a_file_on_another_drive_puts_an_edit_back(desk):
    from navigator.widgets.viewer.db_window import DBWindow

    app, memory, _ = desk
    memory.make("/work/people.dbf", dbf_bytes())

    def window(a):
        return next((w for w in a.shell.desktop.windows() if isinstance(w, DBWindow)), None)

    run_app(app, [
        lambda a: setattr(a.manager.left, "location", memory.location("/work")),
        Until(lambda a: "people.dbf" in [e.name for e in a.manager.left.items]), cursor_on("people.dbf"),
        KeyEvent("f3"), Until(lambda a: window(a) is not None, timeout=5),
        lambda a: (setattr(window(a).viewer, "record", 0), setattr(window(a).viewer, "field", 0)),
        lambda a: a.spawn(window(a).edit_field()),
        Until(lambda a: a.modal is not None, timeout=5),
        lambda a: setattr(a.modal.line, "value", "gamma"), KeyEvent("enter"),
        Until(lambda a: b"gamma" in memory.read("/work/people.dbf"), timeout=5),
        lambda a: window(a).close(),
    ])
    assert memory.read("/work/people.dbf").count(b"beta") == 1
