"""Drives: ``navigator/lib/drives/`` -- where a panel is, and copying, erasing
and listing away from the local disk, on the in-memory drive."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

import pytest

from conftest import settle
from navigator.lib.drives import (
    LOCAL, DriveGone, Location, RemoteLocation, Site, drive_of, mount, unmount,
)
from navigator.lib.drives.memory import MemoryDrive
from navigator.lib.file_ops.filecopy import (
    MOVE, OVERWRITE, PRESERVE, CopyJob, CopyRequest, Failure, Overwrite, OverwriteAnswer,
    resolve_target, run as copy_run,
)
from navigator.lib.file_ops.fileerase import ALL, YES, EraseJob, EraseRequest, NotEmpty, run as erase_run


# -- Location -------------------------------------------------------------------------------------


def test_a_local_location_prints_as_its_path():
    for text in ("/", "/home/user/some dir", "relative/x", "."):
        assert str(Location.of(Path(text))) == str(Path(text))
        assert Location.parse(str(Path(text))) == Location.of(Path(text))


def test_a_remote_location_is_a_url_and_parses_back():
    place = Location(Site("sftp", "me", "example.org", 2222), PurePosixPath("/srv/a b/ü#1"))
    text = str(place)
    assert text.startswith("sftp://me@example.org:2222/srv/a%20b/")
    assert Location.parse(text) == place
    plain = Location(Site("sftp", "", "host", 0), PurePosixPath("/"))
    assert str(plain) == "sftp://host/"
    assert Location.parse("file:///tmp/x") == Location.of(Path("/tmp/x"))


def test_a_location_is_not_a_path():
    place = Location(Site("sftp", host="h"), PurePosixPath("/etc/passwd"))
    with pytest.raises(TypeError):
        os.fspath(place)
    with pytest.raises(RemoteLocation):
        place.local
    assert Location.of(Path("/tmp")).local == Path("/tmp")


def test_normalized_is_by_the_letters_alone():
    place = Location(Site("sftp", host="h"), PurePosixPath("/a/b/../c/./d"))
    assert place.normalized().path == PurePosixPath("/a/c/d")
    assert (place / "..").normalized().path == PurePosixPath("/a/c")
    assert Location(place.site, PurePosixPath("/")).is_root


def test_a_closed_drive_is_gone():
    with pytest.raises(DriveGone):
        drive_of(Location(Site("sftp", host="nowhere"), PurePosixPath("/")))
    assert drive_of(Location.of(Path("/"))) is LOCAL


# -- the in-memory drive ---------------------------------------------------------------------------


@pytest.fixture
def memory():
    drive = mount(MemoryDrive("test"))
    drive.make("/docs/a.txt", "alpha")
    drive.make("/docs/sub/b.txt", "beta")
    drive.make("/empty")
    yield drive
    unmount(drive.site)


def copy(sources, target, cwd, *, mode=OVERWRITE, options=PRESERVE, answers=()):
    asked: list = []
    queue = list(answers)

    def asker(question):
        asked.append(question)
        return queue.pop(0)

    job = CopyJob(asker=asker)
    done = copy_run(CopyRequest(list(sources), str(target), mode, options), job, cwd)
    return done, asked, job


def test_a_tree_copies_from_memory_to_the_disk(memory, tmp_path):
    source = memory.location("/docs")
    done, asked, job = copy([source], tmp_path, tmp_path)
    assert done == [source] and asked == []
    assert (tmp_path / "docs" / "a.txt").read_text() == "alpha"
    assert (tmp_path / "docs" / "sub" / "b.txt").read_text() == "beta"
    assert job.done_bytes == job.total_bytes == len("alpha") + len("beta")


def test_files_copy_from_the_disk_into_memory(memory, tmp_path):
    (tmp_path / "c.txt").write_text("gamma")
    (tmp_path / "tree" / "deep").mkdir(parents=True)
    (tmp_path / "tree" / "deep" / "d.txt").write_text("delta")
    done, _, _ = copy([tmp_path / "c.txt", tmp_path / "tree"], str(memory.location("/empty")) + "/", tmp_path)
    assert done == [tmp_path / "c.txt", tmp_path / "tree"]
    assert memory.read("/empty/c.txt") == b"gamma"
    assert memory.read("/empty/tree/deep/d.txt") == b"delta"


def test_a_relative_target_is_on_the_working_directory_s_drive(memory):
    destination = resolve_target("sub", [memory.location("/docs/a.txt")], memory.location("/docs"))
    assert destination.directory == memory.location("/docs/sub")


def test_a_move_on_one_drive_renames(memory):
    done, _, _ = copy([memory.location("/docs/a.txt")], str(memory.location("/empty")) + "/",
                      memory.location("/"), options=MOVE)
    assert done == [memory.location("/docs/a.txt")]
    assert memory.read("/empty/a.txt") == b"alpha"
    assert not memory.lexists(memory.location("/docs/a.txt"))


def test_a_move_between_drives_copies_then_deletes(memory, tmp_path):
    done, _, _ = copy([memory.location("/docs")], tmp_path, tmp_path, options=MOVE)
    assert done == [memory.location("/docs")]
    assert (tmp_path / "docs" / "sub" / "b.txt").read_text() == "beta"
    assert not memory.lexists(memory.location("/docs"))


def test_an_existing_file_in_memory_is_asked_about(memory, tmp_path):
    (tmp_path / "a.txt").write_text("new")
    from navigator.lib.file_ops.filecopy import ASK

    done, asked, _ = copy([tmp_path / "a.txt"], str(memory.location("/docs")) + "/", tmp_path, mode=ASK,
                          answers=[OverwriteAnswer("overwrite")])
    assert [type(q) for q in asked] == [Overwrite]
    assert asked[0].dest == memory.location("/docs/a.txt")
    assert memory.read("/docs/a.txt") == b"new"


def test_a_directory_cannot_go_into_itself_in_memory(memory):
    done, asked, _ = copy([memory.location("/docs")], str(memory.location("/docs/sub")) + "/",
                          memory.location("/"), answers=[True])
    assert done == [] and isinstance(asked[0], Failure)


def test_a_tree_in_memory_is_erased(memory):
    asked: list = []

    def asker(question):
        asked.append(question)
        return ALL

    job = EraseJob(asker=asker)
    done = erase_run(EraseRequest([memory.location("/docs"), memory.location("/empty")]), job)
    assert done == [memory.location("/docs"), memory.location("/empty")]
    assert [type(q) for q in asked] == [NotEmpty]
    assert memory.names(memory.location("/")) == []
    assert (job.done, job.total) == (5, 5)


# -- a panel on another drive ----------------------------------------------------------------------


def test_a_panel_lists_walks_and_climbs_another_drive(memory):
    from navigator.widgets.manager.panel.panel import Panel

    panel = Panel()
    panel.mounted()
    panel.location = memory.location("/docs")
    settle()
    assert [entry.name for entry in panel.items] == ["..", "sub", "a.txt"]
    assert panel.title_location == "mem://test/docs"
    with pytest.raises(RemoteLocation):
        panel.path
    panel.cursor = 1
    panel.enter()
    settle()
    assert panel.location == memory.location("/docs/sub")
    assert [entry.name for entry in panel.items] == ["..", "b.txt"]
    panel.go_up()
    settle()
    assert panel.location == memory.location("/docs")
    assert panel.selected.name == "sub"
    panel.go_up()
    settle()
    assert panel.location == memory.location("/")
    panel.go_up()  # the root of a drive with nowhere above it: the cursor goes home
    settle()
    assert panel.location == memory.location("/") and panel.cursor == 0


def test_a_panel_on_a_drive_that_closed_says_so(memory):
    from navigator.widgets.manager.panel.panel import Panel

    panel = Panel()
    panel.mounted()
    place = memory.location("/docs")
    unmount(memory.site)
    panel.location = place
    settle()
    assert panel.items == [] and "not accessible" in panel.error
    mount(memory)


# -- the file manager over another drive -----------------------------------------------------------


@pytest.fixture
def desk(tmp_path, monkeypatch):
    """A Navigator whose left panel is on the in-memory drive and right on *tmp_path*."""
    from conftest import FakeTerminal
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    drive = mount(MemoryDrive("desk"))
    drive.make("/files/one.txt", "first")
    drive.make("/files/dir/two.txt", "second")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))
    yield app, drive, tmp_path
    unmount(drive.site)


def on_memory(drive, name):
    def action(app):
        panel = app.manager.left
        if panel.location != drive.location("/files"):
            panel.location = drive.location("/files")
            return
        panel.cursor = [entry.name for entry in panel.items].index(name)
    return action


def test_f5_copies_from_a_panel_on_another_drive(desk):
    from conftest import IDLE, Until, run_app
    from navkit.events import KeyEvent
    from navigator.widgets.file_ops.copy_dialog import CopyDialog

    app, drive, there = desk
    seen = {}
    run_app(app, [
        on_memory(drive, "one.txt"), Until(lambda a: len(a.manager.left.items) == 3),
        on_memory(drive, "one.txt"),
        KeyEvent("f5"), Until(lambda a: isinstance(a.modal, CopyDialog)),
        lambda a: seen.update(target=a.modal.target.value),
        KeyEvent("enter"),
        Until(lambda a: "one.txt" in [entry.name for entry in a.manager.right.items], timeout=5),
    ])
    assert seen["target"] == f"{there}/one.txt"
    assert (there / "one.txt").read_text() == "first"


def test_f8_erases_on_another_drive_and_what_needs_the_disk_is_greyed(desk):
    from conftest import IDLE, Until, run_app
    from navkit.events import KeyEvent
    from navigator.widgets.manager.commands import ChangeAttributes, Copy, Delete, UuEncode, View

    app, drive, there = desk
    seen = {}

    def enabled(a):
        manager = a.manager
        seen["enabled"] = {name: manager.enables(command()) for name, command in
                           (("copy", Copy), ("delete", Delete), ("view", View), ("attributes", ChangeAttributes),
                            ("uu", UuEncode))}

    run_app(app, [
        on_memory(drive, "dir"), Until(lambda a: len(a.manager.left.items) == 3),
        on_memory(drive, "dir"), enabled,
        KeyEvent("f8"), Until(lambda a: a.modal is not None),
        lambda a: seen.update(dialog=type(a.modal).__name__),
        KeyEvent("enter"),
        Until(lambda a: type(a.modal).__name__ == "EraseQuery", timeout=5),  # dir/ is not empty
        lambda a: a.modal.close(YES),
        Until(lambda a: [entry.name for entry in a.manager.left.items] == ["..", "one.txt"], timeout=5),
        lambda a: seen.update(left=[entry.name for entry in a.manager.left.items]),
    ])
    assert seen["dialog"] == "DeleteDialog"
    assert seen["enabled"] == {"copy": True, "delete": True, "view": True, "attributes": True, "uu": False}
    assert not drive.lexists(drive.location("/files/dir"))
    assert seen["left"] == ["..", "one.txt"]


def test_usefile_fetches_notices_a_change_and_puts_it_back(memory):
    from navigator.lib.drives import usefile
    from navigator.lib.system.job import Job

    class Counting(Job):
        position = total = 0

    origin = memory.location("/docs/a.txt")
    use = usefile.fetch([origin], Counting())
    try:
        local = use.local_for(origin)
        assert local.read_text() == "alpha" and use.copies[0].size == 5
        assert usefile.changed(use) == []
        local.write_text("alpha, changed")
        assert usefile.changed(use) == use.copies
        assert usefile.conflicts(use.copies) == []
        usefile.upload(use.copies, Counting())
        assert memory.read("/docs/a.txt") == b"alpha, changed"
        assert usefile.changed(use) == []
        assert sorted(memory.names(memory.location("/docs"))) == ["a.txt", "sub"]
    finally:
        usefile.discard(use)
    assert not use.directory.exists()


def test_f4_on_another_drive_edits_a_copy_and_f2_puts_it_back(desk, monkeypatch):
    from conftest import Until, run_app
    from navkit.events import KeyEvent
    from navigator.settings import SETTINGS
    from navigator.widgets.editor.edit_window import EditWindow

    monkeypatch.setattr(SETTINGS.confirmations, "save", False)
    app, drive, there = desk
    seen = {}

    def editor(a):
        return next((w for w in a.shell.desktop.windows() if isinstance(w, EditWindow)), None)

    def opened(a):
        window = editor(a)
        seen.update(title=window.title, local=window.editor.path)

    run_app(app, [
        on_memory(drive, "one.txt"), Until(lambda a: len(a.manager.left.items) == 3),
        on_memory(drive, "one.txt"),
        KeyEvent("f4"), Until(lambda a: editor(a) is not None, timeout=5), opened,
        KeyEvent("x", char="x"), KeyEvent("f2"),
        Until(lambda a: drive.read("/files/one.txt") == b"xfirst", timeout=5),
        lambda a: editor(a).close(),
        Until(lambda a: not seen["local"].parent.exists(), timeout=5),
    ])
    assert seen["title"] == "Edit - mem://desk/files/one.txt"
    assert drive.read("/files/one.txt") == b"xfirst"


def test_f3_on_another_drive_views_a_copy_under_its_own_name(desk):
    from conftest import Until, run_app
    from navkit.events import KeyEvent
    from navigator.widgets.viewer.file_window import FileWindow

    app, drive, there = desk
    seen = {}

    def viewer(a):
        return next((w for w in a.shell.desktop.windows() if isinstance(w, FileWindow)), None)

    run_app(app, [
        on_memory(drive, "one.txt"), Until(lambda a: len(a.manager.left.items) == 3),
        on_memory(drive, "one.txt"),
        KeyEvent("f3"), Until(lambda a: viewer(a) is not None, timeout=5),
        lambda a: seen.update(title=viewer(a).title, size=viewer(a).viewer.source.size),
    ])
    assert seen == {"title": "mem://desk/files/one.txt", "size": 5}


# -- the SSH link box remembers whole connections ---------------------------------------------------


def test_a_connection_is_remembered_whole_newest_first_one_row_per_place(monkeypatch):
    from navigator.lib.drives.recent import Recent, recent, remember
    from navigator.settings import SETTINGS

    monkeypatch.setattr(SETTINGS.interface, "history_size", 2)
    remember(Recent("sftp", "one.example", "me", 2222, "/srv"))
    remember(Recent("sftp", "two.example"))
    remember(Recent("sftp", "one.example", "me", 2222, "/var/log"))  # again: moves up, new directory
    assert recent("sftp") == [Recent("sftp", "one.example", "me", 2222, "/var/log"), Recent("sftp", "two.example")]
    remember(Recent("sftp", "three.example", "root"))
    assert [link.host for link in recent()] == ["three.example", "one.example"]  # the oldest goes


def test_choosing_a_recent_connection_fills_every_line():
    from navigator.lib.drives.recent import Recent
    from navigator.widgets.drives.connect_dialog import ConnectDialog

    links = [Recent("sftp", "one.example", "me", 2222, "/srv"), Recent("sftp", "two.example")]
    dialog = ConnectDialog(recent=links)
    assert dialog.host.choices == ["me@one.example:2222  /srv", "two.example"]
    dialog.host.history.choose("me@one.example:2222  /srv")
    assert (dialog.host.value, dialog.user.value, dialog.port.value, dialog.directory.value) == (
        "one.example", "me", "2222", "/srv")
    request = dialog.accept()
    assert (request.host, request.user, request.port, request.path) == ("one.example", "me", 2222, "/srv")
    dialog.host.history.choose("two.example")
    assert (dialog.user.value, dialog.port.value, dialog.directory.value) == ("", "", "")
