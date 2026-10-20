"""Archives as drives: ``navigator/lib/drives/archive.py``, DOS Navigator's
``TArcDrive`` -- zip and tar read through the standard library, Enter going in
and ``..`` coming back out on the archive, files copied out."""

from __future__ import annotations

import io
import tarfile
import time
import zipfile
from pathlib import Path

import pytest

from conftest import FakeTerminal, IDLE, Until, run_app
from navkit.events import KeyEvent
from navigator.lib.drives import DriveGone, Location, drive_of
from navigator.lib.drives import archive
from navigator.lib.file_ops.filecopy import OVERWRITE, PRESERVE, CopyJob, CopyRequest, run as copy_run


@pytest.fixture(autouse=True)
def no_archives_left():
    yield
    archive.close_all()


def make_zip(path: Path) -> Path:
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr("README", "read me")
        zipped.writestr("src/main.py", "print('hi')\n")
        zipped.writestr("src/deep/x.txt", "x")  # src/deep only implied
        zipped.writestr("empty/", "")
    return path


def make_tar(path: Path) -> Path:
    with tarfile.open(path, "w:gz") as tarred:
        for name, data in (("top.txt", b"top"), ("dir/inner.txt", b"inner")):
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(data), 1_000_000_000, 0o640
            info.uname, info.gname = "alice", "staff"
            tarred.addfile(info, io.BytesIO(data))
        link = tarfile.TarInfo("dir/to-top")
        link.type, link.linkname = tarfile.SYMTYPE, "../top.txt"
        tarred.addfile(link)
    return path


# -- the drive ----------------------------------------------------------------------------------------


def test_a_zip_lists_its_directories_the_implied_ones_too(tmp_path):
    outer = Location.of(make_zip(tmp_path / "a.zip"))
    drive = archive.open_archive(outer)
    assert drive_of(drive.at("/src")) is drive and drive.kind == "zip"
    entries, error, _ = drive.scan(drive.at("/"), True, "name", free=False)
    assert error is None and [e.name for e in entries] == ["..", "empty", "src", "README"]
    entries, _, _ = drive.scan(drive.at("/src"), True, "name", free=False)
    assert [(e.name, e.is_dir) for e in entries] == [("..", True), ("deep", True), ("main.py", False)]
    with drive.open_read(drive.at("/src/main.py")) as reader:
        assert reader.read() == b"print('hi')\n"
    assert drive.get_dir(drive.at("/src")) == "ZIP:a.zip:/src"
    assert drive.change_up(drive.at("/")) == (outer.parent, "a.zip")


def test_a_compressed_tar_keeps_owners_modes_and_links(tmp_path):
    drive = archive.open_archive(Location.of(make_tar(tmp_path / "b.tar.gz")))
    assert drive.kind == "tar" and drive.get_dir(drive.at("/")) == "TAR:b.tar.gz:/"
    entries, _, _ = drive.scan(drive.at("/dir"), True, "name", free=False)
    found = {e.name: e for e in entries}
    assert found["inner.txt"].display_owner == "alice:staff"
    assert found["inner.txt"].display_attributes == "rw-r-----"
    assert found["to-top"].is_link and found["to-top"].link_target == "../top.txt"
    assert found["to-top"].size == 3  # followed, inside the archive


def test_what_is_not_an_archive_says_so(tmp_path):
    (tmp_path / "fake.zip").write_text("not a zip at all")
    with pytest.raises(archive.NotAnArchive):
        archive.open_archive(Location.of(tmp_path / "fake.zip"))


def test_a_place_in_an_archive_prints_and_parses_back(tmp_path):
    drive = archive.open_archive(Location.of(make_zip(tmp_path / "a b.zip")))
    place = drive.at("/src/deep")
    assert str(place) == f"{tmp_path}/a b.zip#/src/deep"
    assert Location.parse(str(place)) == place
    archive.close_all()
    with pytest.raises(DriveGone):
        drive_of(place)


def test_a_tree_copies_out_of_an_archive(tmp_path):
    drive = archive.open_archive(Location.of(make_zip(tmp_path / "a.zip")))
    out = tmp_path / "out"
    out.mkdir()
    job = CopyJob(asker=lambda question: pytest.fail(f"asked {question}"))
    done = copy_run(CopyRequest([drive.at("/src")], str(out), OVERWRITE, PRESERVE), job, out)
    assert done == [drive.at("/src")]
    assert (out / "src" / "main.py").read_text() == "print('hi')\n"
    assert (out / "src" / "deep" / "x.txt").read_text() == "x"


def copy_in(sources, target, cwd, **kwargs):
    asked = []
    from navigator.lib.file_ops.filecopy import CreateDirectory

    def asker(question):
        asked.append(question)
        if isinstance(question, CreateDirectory):
            return True
        pytest.fail(f"asked {question}")

    job = CopyJob(asker=asker)
    return copy_run(CopyRequest(list(sources), str(target), OVERWRITE, PRESERVE, **kwargs), job, cwd), asked


def test_files_and_a_tree_go_into_a_zip_and_it_is_written_anew(tmp_path):
    outer = Location.of(make_zip(tmp_path / "a.zip"))
    drive = archive.open_archive(outer)
    (tmp_path / "new.txt").write_text("new")
    (tmp_path / "tree" / "sub").mkdir(parents=True)
    (tmp_path / "tree" / "sub" / "leaf.txt").write_text("leaf")
    done, _ = copy_in([tmp_path / "new.txt", tmp_path / "tree"], str(drive.at("/src")) + "/", tmp_path)
    assert done == [tmp_path / "new.txt", tmp_path / "tree"]
    with zipfile.ZipFile(tmp_path / "a.zip") as zipped:
        assert zipped.read("src/new.txt") == b"new"
        assert zipped.read("src/tree/sub/leaf.txt") == b"leaf"
        assert zipped.read("src/main.py") == b"print('hi')\n"  # what was there stays
        assert zipped.getinfo("src/new.txt").compress_type == zipfile.ZIP_DEFLATED
    assert [e.name for e in drive.scan(drive.at("/src"), True, "name", free=False)[0]] == [
        "..", "deep", "tree", "main.py", "new.txt"]
    assert sorted(path.name for path in tmp_path.iterdir()) == ["a.zip", "new.txt", "tree"]


def test_a_compressed_tar_written_into_stays_compressed_and_keeps_its_owners(tmp_path):
    outer = Location.of(make_tar(tmp_path / "b.tar.gz"))
    drive = archive.open_archive(outer)
    (tmp_path / "add.txt").write_text("added")
    done, _ = copy_in([tmp_path / "add.txt"], str(drive.at("/dir")) + "/", tmp_path)
    assert done == [tmp_path / "add.txt"]
    assert (tmp_path / "b.tar.gz").read_bytes()[:2] == b"\x1f\x8b"
    with tarfile.open(tmp_path / "b.tar.gz") as tarred:
        assert tarred.extractfile("dir/add.txt").read() == b"added"
        assert tarred.getmember("dir/inner.txt").uname == "alice"
        assert tarred.getmember("dir/to-top").issym()


def test_erase_rename_and_mkdir_in_an_archive(tmp_path):
    from navigator.lib.file_ops.fileerase import ALL, EraseJob, EraseRequest, run as erase_run

    drive = archive.open_archive(Location.of(make_zip(tmp_path / "a.zip")))
    done = erase_run(EraseRequest([drive.at("/src"), drive.at("/README")]), EraseJob(asker=lambda q: ALL))
    assert done == [drive.at("/src"), drive.at("/README")]
    drive.mkdir(drive.at("/made"))
    drive.rename(drive.at("/empty"), drive.at("/renamed"))
    drive.finish()
    with zipfile.ZipFile(tmp_path / "a.zip") as zipped:
        assert sorted(zipped.namelist()) == ["made/", "renamed/"]


def test_a_copy_moved_out_of_an_archive_is_taken_out_of_it(tmp_path):
    from navigator.lib.file_ops.filecopy import MOVE

    drive = archive.open_archive(Location.of(make_zip(tmp_path / "a.zip")))
    out = tmp_path / "out"
    out.mkdir()
    done, _ = copy_in([drive.at("/README")], out, out, )
    assert done
    job = CopyJob(asker=lambda q: pytest.fail(f"asked {q}"))
    copy_run(CopyRequest([drive.at("/src")], str(out), OVERWRITE, MOVE), job, out)
    assert (out / "src" / "deep" / "x.txt").read_text() == "x"
    with zipfile.ZipFile(tmp_path / "a.zip") as zipped:
        assert not any(name.startswith("src") for name in zipped.namelist())


def test_a_target_naming_an_archive_not_there_makes_one(tmp_path):
    (tmp_path / "one.txt").write_text("1")
    for name in ("new.zip", "new.tar.xz"):
        done, _ = copy_in([tmp_path / "one.txt"], f"{tmp_path / name}#/inside/", tmp_path)
        assert done == [tmp_path / "one.txt"]
        assert archive.find(Location.of(tmp_path / name)) is None  # nobody holds it: let go
    with zipfile.ZipFile(tmp_path / "new.zip") as zipped:
        assert zipped.read("inside/one.txt") == b"1"
    assert (tmp_path / "new.tar.xz").read_bytes()[:6] == b"\xfd7zXZ\x00"
    with tarfile.open(tmp_path / "new.tar.xz") as tarred:
        assert tarred.extractfile("inside/one.txt").read() == b"1"


# -- a panel going in and out ------------------------------------------------------------------------


@pytest.fixture
def desk(tmp_path, monkeypatch):
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    make_zip(tmp_path / "a.zip")
    (tmp_path / "fake.zip").write_text("not a zip")
    (tmp_path / "out").mkdir()
    return Navigator(tmp_path, tmp_path / "out", terminal=FakeTerminal(100, 30)), tmp_path


def at(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [entry.name for entry in panel.items].index(name)
    return action


def names(app):
    return [entry.name for entry in app.manager.left.items]


def test_enter_goes_in_and_dot_dot_at_its_root_comes_back_on_the_archive(desk):
    app, here = desk
    seen = {}
    run_app(app, [
        at("a.zip"), KeyEvent("enter"), Until(lambda a: names(a) == ["..", "empty", "src", "README"]),
        lambda a: seen.update(title=a.manager.left.title_location, prompt=a.shell.command_prompt,
                              open=archive.find(Location.of(here / "a.zip")) is not None),
        at("src"), KeyEvent("enter"), Until(lambda a: names(a) == ["..", "deep", "main.py"]),
        KeyEvent("backspace"), Until(lambda a: "README" in names(a)),
        lambda a: seen.update(back_on=a.manager.left.selected.name),
        at(".."), KeyEvent("enter"), Until(lambda a: a.manager.left.location.is_local),
        IDLE, lambda a: seen.update(cursor=a.manager.left.selected.name),
        Until(lambda a: archive.find(Location.of(here / "a.zip")) is None),
    ])
    assert seen["title"] == "ZIP:a.zip:/" and seen["prompt"] == "ZIP:a.zip:/$" and seen["open"]
    assert seen["back_on"] == "src"
    assert seen["cursor"] == "a.zip"


def test_a_file_named_as_an_archive_that_is_none_is_run_as_a_file(desk, monkeypatch):
    app, here = desk
    opened = []
    async def on_open_file(self, event):
        opened.append(event.path)
        return True

    monkeypatch.setattr("navigator.widgets.shell.shell.Shell.on_open_file", on_open_file)
    run_app(app, [at("fake.zip"), KeyEvent("enter"), Until(lambda a: opened, timeout=5)])
    assert opened == [here / "fake.zip"]
    assert app.manager.left.location == Location.of(here)


def test_with_enter_opens_an_archive_off_enter_runs_it(desk, monkeypatch):
    from navigator.settings import SETTINGS

    monkeypatch.setattr(SETTINGS.file_manager, "enter_opens_archive", False)
    app, here = desk
    opened = []
    async def on_open_file(self, event):
        opened.append(event.path)
        return True

    monkeypatch.setattr("navigator.widgets.shell.shell.Shell.on_open_file", on_open_file)
    run_app(app, [at("a.zip"), KeyEvent("enter"), Until(lambda a: opened, timeout=5)])
    assert opened == [here / "a.zip"]


def test_f5_copies_out_and_everything_that_writes_is_there_inside(desk):
    from navigator.widgets.file_ops.copy_dialog import CopyDialog
    from navigator.widgets.manager.commands import Delete, Edit, MakeDirectory, RenameMove, View

    app, here = desk
    seen = {}

    def enabled(a):
        seen["enabled"] = {cls.__name__: a.manager.enables(cls()) for cls in
                           (Delete, Edit, MakeDirectory, RenameMove, View)}

    run_app(app, [
        at("a.zip"), KeyEvent("enter"), Until(lambda a: "README" in names(a)),
        at("README"), enabled,
        KeyEvent("f5"), Until(lambda a: isinstance(a.modal, CopyDialog)),
        lambda a: seen.update(target=a.modal.target.value), KeyEvent("enter"),
        Until(lambda a: (here / "out" / "README").exists(), timeout=5),
    ])
    assert seen["enabled"] == {"Delete": True, "Edit": True, "MakeDirectory": True, "RenameMove": True,
                               "View": True}
    assert seen["target"] == f"{here / 'out'}/README"
    assert (here / "out" / "README").read_text() == "read me"


def test_a_desktop_saved_in_an_archive_comes_back_beside_it(desk):
    from navigator.lib.config import desktop_state

    app, here = desk
    seen = {}
    run_app(app, [
        at("a.zip"), KeyEvent("enter"), Until(lambda a: "README" in names(a)),
        lambda a: seen.update(kept=desktop_state._panel(a.manager.left)),
    ])
    assert seen["kept"]["path"] == str(here) and seen["kept"]["cursor"] == "a.zip"


def test_an_archive_on_another_drive_is_fetched_entered_and_its_copy_goes_with_it(desk, tmp_path):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    app, here = desk
    memory = mount(MemoryDrive("arc"))
    memory.make("/pkg/remote.zip", make_zip(tmp_path / "source.zip").read_bytes())
    seen = {}

    def inside(a):
        drive = drive_of(a.manager.left.location)
        seen.update(title=a.manager.left.title_location, copy=drive.local)

    try:
        run_app(app, [
            lambda a: setattr(a.manager.left, "location", memory.location("/pkg")),
            Until(lambda a: "remote.zip" in names(a)), at("remote.zip"), KeyEvent("enter"),
            Until(lambda a: "README" in names(a), timeout=5), inside,
            KeyEvent("backspace"), Until(lambda a: "remote.zip" in names(a)),
            Until(lambda a: not seen["copy"].exists(), timeout=5),
        ])
    finally:
        unmount(memory.site)
    assert seen["title"] == "ZIP:remote.zip:/"


def test_f5_into_a_panel_in_an_archive_packs_the_file_into_it(desk):
    from navigator.widgets.file_ops.copy_dialog import CopyDialog

    app, here = desk
    (here / "out" / "packed.txt").write_text("packed")
    seen = {}

    def right_names(a):
        return [entry.name for entry in a.manager.right.items]

    run_app(app, [
        at("a.zip"), KeyEvent("enter"), Until(lambda a: "README" in names(a)),
        lambda a: a.manager.right.reload(),  # packed.txt came after the panels read
        Until(lambda a: "packed.txt" in right_names(a)),
        lambda a: a.manager.right.focus(),
        lambda a: setattr(a.manager.right, "cursor", right_names(a).index("packed.txt")),
        KeyEvent("f5"), Until(lambda a: isinstance(a.modal, CopyDialog)),
        lambda a: seen.update(target=a.modal.target.value), KeyEvent("enter"),
        Until(lambda a: "packed.txt" in names(a), timeout=5),
    ])
    assert seen["target"] == f"{here / 'a.zip'}#/packed.txt"
    with zipfile.ZipFile(here / "a.zip") as zipped:
        assert zipped.read("packed.txt") == b"packed"


def test_f4_and_f2_inside_an_archive_write_it_back(desk, monkeypatch):
    from navigator.settings import SETTINGS
    from navigator.widgets.editor.edit_window import EditWindow

    monkeypatch.setattr(SETTINGS.confirmations, "save", False)
    app, here = desk

    def editor(a):
        return next((w for w in a.shell.desktop.windows() if isinstance(w, EditWindow)), None)

    def packed(a):
        with zipfile.ZipFile(here / "a.zip") as zipped:
            return zipped.read("README")

    run_app(app, [
        at("a.zip"), KeyEvent("enter"), Until(lambda a: "README" in names(a)), at("README"),
        KeyEvent("f4"), Until(lambda a: editor(a) is not None, timeout=5),
        KeyEvent("x", char="x"), KeyEvent("f2"),
        Until(lambda a: packed(a) == b"xread me", timeout=5),
    ])


def test_an_archive_on_another_drive_written_into_goes_back_there(tmp_path):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    memory = mount(MemoryDrive("arc-write"))
    try:
        outer = memory.make("/remote.zip", make_zip(tmp_path / "source.zip").read_bytes())
        drive = archive.open_archive(outer)
        (tmp_path / "up.txt").write_text("up")
        done, _ = copy_in([tmp_path / "up.txt"], str(drive.at("/")) + "/", tmp_path)
        assert done == [tmp_path / "up.txt"]
        with zipfile.ZipFile(io.BytesIO(memory.read("/remote.zip"))) as zipped:
            assert zipped.read("up.txt") == b"up" and zipped.read("README") == b"read me"
    finally:
        archive.close_all()
        unmount(memory.site)
