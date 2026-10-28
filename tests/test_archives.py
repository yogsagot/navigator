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
def no_archives_left(monkeypatch):
    from navigator.widgets.file_ops.archive_dialog import archive_dialog

    # Create archive's box remembers its type and boxes for the session: not from test to test.
    monkeypatch.setattr(archive_dialog, "_session", dict(archive_dialog._session))
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


# -- Create archive: formats, levels, passwords, packing -------------------------------------------

needs_7z = pytest.mark.skipif(__import__("shutil").which("7z") is None and __import__("shutil").which("7zz") is None
                              and __import__("shutil").which("7za") is None, reason="no 7-Zip")
needs_zstd = pytest.mark.skipif(__import__("shutil").which("zstd") is None, reason="no zstd")


def packed(tmp_path, name, level, password=""):
    """*name* made in *tmp_path* from one compressible file at *level*; its size."""
    source = tmp_path / "text.txt"
    if not source.exists():
        source.write_bytes(Path(tarfile.__file__).read_bytes() + Path(zipfile.__file__).read_bytes())
    target = tmp_path / name
    done, _ = copy_in([source], f"{target}#/", tmp_path,
                      archive=archive.ArchiveOptions(level=level, password=password))
    assert done == [source]
    return target.stat().st_size


@pytest.mark.parametrize("name", ["a.zip", "a.tar.gz", "a.tar.bz2", "a.tar.xz",
                                  pytest.param("a.tar.zst", marks=needs_zstd),
                                  pytest.param("a.7z", marks=needs_7z)])
def test_a_new_archive_is_packed_at_the_level_asked(tmp_path, name):
    fastest = packed(tmp_path, "fast-" + name, "fastest")
    maximum = packed(tmp_path, "max-" + name, "maximum")
    assert maximum <= fastest
    drive = archive.open_archive(Location.of(tmp_path / ("max-" + name)))
    with drive.open_read(drive.at("/text.txt")) as reader:
        assert reader.read() == (tmp_path / "text.txt").read_bytes()


def test_store_writes_a_zip_s_new_members_uncompressed(tmp_path):
    packed(tmp_path, "s.zip", "store")
    with zipfile.ZipFile(tmp_path / "s.zip") as zipped:
        assert zipped.getinfo("text.txt").compress_type == zipfile.ZIP_STORED


def test_every_format_has_its_levels_and_a_plain_tar_none():
    for _, suffix, kind in archive.FORMATS:
        assert archive.new_kind("x" + suffix) == kind
        levels = archive.LEVELS.get(kind, {})
        assert (not levels) == (kind == ("tar", "")), suffix
        assert set(levels) <= set(archive.LEVEL_NAMES)


@needs_zstd
def test_a_tar_zst_is_entered_and_written_into_like_any_tar(tmp_path):
    (tmp_path / "one.txt").write_text("1")
    copy_in([tmp_path / "one.txt"], f"{tmp_path / 'z.tar.zst'}#/", tmp_path)
    assert (tmp_path / "z.tar.zst").read_bytes()[:4] == b"\x28\xb5\x2f\xfd"
    drive = archive.open_archive(Location.of(tmp_path / "z.tar.zst"))
    assert (drive.kind, drive.compression) == ("tar", "zst")
    (tmp_path / "two.txt").write_text("2")
    copy_in([tmp_path / "two.txt"], str(drive.at("/")) + "/", tmp_path)
    plain = drive._plain
    archive.close_all()
    assert plain is not None and not plain.exists()  # the decompressed copy goes with it
    drive = archive.open_archive(Location.of(tmp_path / "z.tar.zst"))
    with drive.open_read(drive.at("/one.txt")) as one, drive.open_read(drive.at("/two.txt")) as two:
        assert (one.read(), two.read()) == (b"1", b"2")


def test_a_tar_zst_with_nothing_to_read_it_says_what_to_install(tmp_path, monkeypatch):
    from navigator.lib.drives import zstd

    (tmp_path / "z.tar.zst").write_bytes(zstd.MAGIC + b"\0" * 16)
    monkeypatch.setattr(zstd, "_module", lambda: None)
    monkeypatch.setattr(zstd, "_program", lambda: None)
    with pytest.raises(archive.NeedsTool, match="zstd"):
        archive.open_archive(Location.of(tmp_path / "z.tar.zst"))
    assert archive.format_missing(("tar", "zst")) == zstd.MISSING


@needs_7z
@pytest.mark.parametrize("name", ["p.7z", "p.zip"])
def test_a_password_encrypts_and_is_asked_for_and_kept_on_a_rewrite(tmp_path, name):
    packed(tmp_path, name, "normal", password="s3cret")
    outer = Location.of(tmp_path / name)
    for wrong in ("", "nope"):
        with pytest.raises(archive.NeedPassword):
            archive.open_archive(outer, password=wrong)
    drive = archive.open_archive(outer, password="s3cret")
    assert drive.tool
    (tmp_path / "more.txt").write_text("more")
    copy_in([tmp_path / "more.txt"], str(drive.at("/")) + "/", tmp_path)
    archive.close_all()
    with pytest.raises(archive.NeedPassword):
        archive.open_archive(outer)
    drive = archive.open_archive(outer, password="s3cret")
    with drive.open_read(drive.at("/more.txt")) as reader:
        assert reader.read() == b"more"


class StopWhilePacking(CopyJob):
    """Stops once the packing has counted its first bytes."""

    @property
    def stopped(self):
        return self.packing and self.done_bytes > 0


def test_stop_while_packing_leaves_no_archive_and_moves_nothing(tmp_path):
    from navigator.lib.file_ops.filecopy import MOVE

    big = tmp_path / "big.bin"
    big.write_bytes(bytes(range(256)) * 16384)  # four chunks
    job = StopWhilePacking(asker=lambda q: pytest.fail(f"asked {q}"))
    done = copy_run(CopyRequest([big], f"{tmp_path / 'b.zip'}#/", OVERWRITE, PRESERVE | MOVE), job, tmp_path)
    assert done == [] and big.exists()
    assert not (tmp_path / "b.zip").exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["big.bin"]


def test_stop_while_packing_into_an_archive_there_leaves_it_as_it_was(tmp_path):
    before = make_zip(tmp_path / "a.zip").read_bytes()
    big = tmp_path / "big.bin"
    big.write_bytes(bytes(range(256)) * 16384)
    drive = archive.open_archive(Location.of(tmp_path / "a.zip"))
    job = StopWhilePacking(asker=lambda q: pytest.fail(f"asked {q}"))
    assert copy_run(CopyRequest([big], str(drive.at("/")) + "/", OVERWRITE, PRESERVE), job, tmp_path) == []
    assert (tmp_path / "a.zip").read_bytes() == before
    assert not drive.dirty and "big.bin" not in drive.names(drive.at("/"))


def test_a_move_into_an_archive_deletes_the_sources_once_it_is_written(tmp_path):
    from navigator.lib.file_ops.filecopy import MOVE

    (tmp_path / "tree" / "sub").mkdir(parents=True)
    (tmp_path / "tree" / "sub" / "leaf.txt").write_text("leaf")
    seen = []

    class Watching(CopyJob):
        def __setattr__(self, name, value):
            if name == "packing" and value:
                seen.append((tmp_path / "tree" / "sub" / "leaf.txt").exists())
            super().__setattr__(name, value)

    job = Watching(asker=lambda q: pytest.fail(f"asked {q}"))
    done = copy_run(CopyRequest([tmp_path / "tree"], f"{tmp_path / 'm.tar.gz'}#/", OVERWRITE, PRESERVE | MOVE),
                    job, tmp_path)
    assert done == [tmp_path / "tree"] and seen == [True]  # still there while packing
    assert not (tmp_path / "tree").exists()
    with tarfile.open(tmp_path / "m.tar.gz") as tarred:
        assert tarred.extractfile("tree/sub/leaf.txt").read() == b"leaf"


def test_packing_is_counted_into_the_copy_s_job(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"a" * 1000)
    (tmp_path / "b.txt").write_bytes(b"b" * 500)
    job = CopyJob(asker=lambda q: pytest.fail(f"asked {q}"))
    copy_run(CopyRequest([tmp_path / "a.txt", tmp_path / "b.txt"], f"{tmp_path / 'c.zip'}#/", OVERWRITE, PRESERVE),
             job, tmp_path)
    assert (job.total_bytes, job.done_bytes) == (1500, 1500)
    assert job.dest == str(tmp_path / "c.zip") and not job.packing


def test_a_new_archive_on_another_drive_is_made_there(tmp_path):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    memory = mount(MemoryDrive("arc-new"))
    try:
        directory = memory.make("/dir/keep", b"").parent
        (tmp_path / "up.txt").write_text("up")
        done, _ = copy_in([tmp_path / "up.txt"], f"{directory / 'new.tar.gz'}#/", tmp_path)
        assert done == [tmp_path / "up.txt"]
        with tarfile.open(fileobj=io.BytesIO(memory.read("/dir/new.tar.gz"))) as tarred:
            assert tarred.extractfile("up.txt").read() == b"up"
    finally:
        archive.close_all()
        unmount(memory.site)


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


# -- Extract to, Test, Extract archive -------------------------------------------------------------


def corrupt_zip(path: Path) -> Path:
    """*path*'s first member's bytes changed under its CRC."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zipped:
        zipped.writestr("good.txt", "fine")
        zipped.writestr("bad.txt", "damaged here")
    data = path.read_bytes()
    path.write_bytes(data.replace(b"damaged here", b"DAMAGED HERE"))
    return path


def test_test_reads_every_member_and_names_those_that_fail(tmp_path):
    class Job:
        stopped, position, total = False, 0, 0

        def wait_while_paused(self):
            pass

    good = archive.open_archive(Location.of(make_zip(tmp_path / "a.zip")))
    assert good.test(Job()) == []
    assert good.test(Job(), [good.at("/src")]) == []
    bad = archive.open_archive(Location.of(corrupt_zip(tmp_path / "bad.zip")))
    failures = bad.test(Job())
    assert [path for path, _ in failures] == ["bad.txt"] and "CRC" in failures[0][1]


def test_extract_without_path_names_puts_every_file_in_the_target(tmp_path):
    drive = archive.open_archive(Location.of(make_zip(tmp_path / "a.zip")))
    out = tmp_path / "flat"
    out.mkdir()
    request = CopyRequest([drive.at("/src")], str(out) + "/", OVERWRITE, PRESERVE, flatten=True)
    copy_run(request, CopyJob(), tmp_path)
    assert sorted(path.name for path in out.iterdir()) == ["main.py", "x.txt"]


def written(path, text):
    """Whether *path* holds *text* yet -- a file on a copier's thread may not."""
    try:
        return path.read_text() == text
    except OSError:
        return False


def modal_is(name):
    return lambda a: type(a.modal).__name__ == name


def test_extract_to_and_test_are_the_archive_panel_s(desk):
    from navigator.widgets.manager.commands import ArcTest, ExtractArchive, ExtractTo

    app, here = desk
    seen = {}

    def enabled(key):
        return lambda a: seen.update({key: {cls.__name__: a.manager.enables(cls())
                                            for cls in (ArcTest, ExtractArchive, ExtractTo)}})

    run_app(app, [
        at("a.zip"), enabled("disk"),
        KeyEvent("enter"), Until(lambda a: "README" in names(a)), enabled("inside"),
    ])
    assert seen["disk"] == {"ArcTest": False, "ExtractArchive": True, "ExtractTo": False}
    # Shift+F2 extracts inside one too: *Extract to...*.
    assert seen["inside"] == {"ArcTest": True, "ExtractArchive": True, "ExtractTo": True}


def test_extract_to_copies_the_selection_out_with_its_paths(desk):
    from navigator.widgets.manager.commands import ExtractTo

    app, here = desk
    seen = {}
    run_app(app, [
        at("a.zip"), KeyEvent("enter"), Until(lambda a: "README" in names(a)),
        at("src"), lambda a: a.spawn(a.run_command(ExtractTo)), Until(modal_is("ExtractDialog")),
        lambda a: seen.update(target=a.modal.target.value, options=a.modal.options.value),
        # Both files, whole: the copier is on a thread and need not write them
        # in the order the archive lists them.
        KeyEvent("enter"), Until(lambda a: written(here / "out" / "src" / "deep" / "x.txt", "x")
                                 and written(here / "out" / "src" / "main.py", "print('hi')\n"), timeout=5),
    ])
    assert seen == {"target": f"{here / 'out'}/", "options": 1}
    assert (here / "out" / "src" / "main.py").read_text() == "print('hi')\n"


def test_shift_f2_extracts_an_archive_from_outside_it(desk):
    app, here = desk
    run_app(app, [
        at("a.zip"), KeyEvent("f2", shift=True), Until(modal_is("ExtractDialog")),
        KeyEvent("enter"), Until(lambda a: (here / "out" / "README").exists(), timeout=5),
        Until(lambda a: archive.find(Location.of(here / "a.zip")) is None),
    ])
    assert (here / "out" / "src" / "deep" / "x.txt").read_text() == "x"
    assert (here / "out" / "empty").is_dir()


def test_shift_f2_inside_an_archive_is_extract_to(desk):
    app, here = desk
    run_app(app, [
        at("a.zip"), KeyEvent("enter"), Until(lambda a: "README" in names(a)),
        at("README"), KeyEvent("f2", shift=True), Until(modal_is("ExtractDialog")),
        KeyEvent("enter"), Until(lambda a: (here / "out" / "README").exists(), timeout=5),
    ])
    assert not (here / "out" / "src").exists()  # the selection only, not the whole archive


def test_shift_f1_packs_the_selection_into_a_new_zip_in_the_other_panel(desk):
    import zipfile

    app, here = desk
    (here / "notes.txt").write_text("n\n")
    seen = {}
    run_app(app, [
        KeyEvent("r", ctrl=True), Until(lambda a: "notes.txt" in names(a)), at("notes.txt"),
        KeyEvent("f1", shift=True), Until(modal_is("ArchiveDialog")),
        lambda a: seen.update(target=a.modal.target.value),
        KeyEvent("enter"), Until(lambda a: (here / "out" / "notes.zip").exists(), timeout=5),
        Until(lambda a: archive.find(Location.of(here / "out" / "notes.zip")) is None, timeout=5),
    ])
    assert seen["target"] == f"{here / 'out' / 'notes.zip'}"
    with zipfile.ZipFile(here / "out" / "notes.zip") as packed:
        assert packed.read("notes.txt") == b"n\n"


@needs_zstd
def test_shift_f1_makes_the_type_chosen_and_moves_when_asked(desk):
    from navigator.widgets.file_ops.archive_dialog import archive_dialog as box

    app, here = desk
    (here / "notes.txt").write_text("n\n")
    made = here / "out" / "notes.tar.zst"

    def choose(a):
        a.modal.kind.value = 6  # TAR.ZST
        a.modal.options.value = box.PATHNAMES | box.MOVE_FILES

    run_app(app, [
        KeyEvent("r", ctrl=True), Until(lambda a: "notes.txt" in names(a)), at("notes.txt"),
        KeyEvent("f1", shift=True), Until(modal_is("ArchiveDialog")), choose,
        Until(lambda a: a.modal.target.value.endswith("notes.tar.zst")),
        KeyEvent("enter"), Until(lambda a: not (here / "notes.txt").exists(), timeout=5),
        Until(lambda a: archive.find(Location.of(made)) is None, timeout=5),
    ])
    drive = archive.open_archive(Location.of(made))
    with drive.open_read(drive.at("/notes.txt")) as reader:
        assert reader.read() == b"n\n"


def test_shift_f1_onto_an_archive_there_asks_and_adds_to_it(desk):
    app, here = desk
    (here / "notes.txt").write_text("n\n")
    make_zip(here / "out" / "notes.zip")
    asked = {}
    run_app(app, [
        KeyEvent("r", ctrl=True), Until(lambda a: "notes.txt" in names(a)), at("notes.txt"),
        KeyEvent("f1", shift=True), Until(modal_is("ArchiveDialog")), KeyEvent("enter"),
        Until(lambda a: a.modal is not None and a.modal.title == "Create archive"
              and type(a.modal).__name__ == "Dialog"),
        lambda a: asked.update(add=a.modal.ok.text, replace=a.modal.no.text),
        KeyEvent("enter"),
        Until(lambda a: "notes.txt" in zipfile.ZipFile(here / "out" / "notes.zip").namelist(), timeout=5),
        Until(lambda a: archive.find(Location.of(here / "out" / "notes.zip")) is None, timeout=5),
    ])
    assert asked == {"add": "~A~dd to it", "replace": "~R~eplace"}
    with zipfile.ZipFile(here / "out" / "notes.zip") as packed:
        assert packed.read("README") == b"read me" and packed.read("notes.txt") == b"n\n"


def test_a_password_typed_twice_differently_is_refused(desk):
    app, here = desk
    (here / "notes.txt").write_text("n\n")

    def password(text):
        def action(a):
            field = a.modal.password if type(a.modal).__name__ == "ArchiveDialog" else a.modal.entry
            field.value = text
        return action

    run_app(app, [
        KeyEvent("r", ctrl=True), Until(lambda a: "notes.txt" in names(a)), at("notes.txt"),
        KeyEvent("f1", shift=True), Until(modal_is("ArchiveDialog")),
        lambda a: setattr(a.modal.kind, "value", 0), password("one"),
        KeyEvent("enter"), Until(modal_is("PasswordDialog")), password("two"), KeyEvent("enter"),
        Until(lambda a: a.modal is not None and a.modal.title == "Error"), KeyEvent("enter"),
        Until(modal_is("ArchiveDialog")),
    ])
    assert not (here / "out" / "notes.zip").exists()


@needs_7z
def test_enter_on_an_encrypted_archive_asks_its_password(desk):
    from navigator.lib.drives import arctool

    app, here = desk
    tree = here / "tree"
    tree.mkdir()
    (tree / "secret.txt").write_text("s")
    arctool.write_archive(here / "locked.7z", tree, password="pw")

    def answer(text):
        return lambda a: setattr(a.modal.entry, "value", text)

    run_app(app, [
        KeyEvent("r", ctrl=True), Until(lambda a: "locked.7z" in names(a)), at("locked.7z"),
        KeyEvent("enter"), Until(modal_is("PasswordDialog"), timeout=5), answer("wrong"), KeyEvent("enter"),
        Until(lambda a: a.modal is not None and "Wrong password" in str(a.modal.prompt), timeout=5),
        answer("pw"), KeyEvent("enter"),
        Until(lambda a: "secret.txt" in names(a), timeout=5),
    ])


def test_the_right_click_menu_offers_the_archive_commands_where_they_apply(desk):
    from navml.widgets.dialog.control.control import parse_shortcut
    from navml.widgets.menu.popup_menu import PopupMenu

    app, here = desk
    seen = {}

    def popup(a):
        return next((c for c in a.root.children if isinstance(c, PopupMenu)), None)

    def captions(key):
        return lambda a: seen.update({key: [parse_shortcut(e.text)[0] for e in popup(a).box.entries()
                                            if hasattr(e, "command")]})

    def right_click_cursor(a):
        from navml.widgets.menu.commands import ShowContextMenu

        a.spawn(a.manager.left.emit(ShowContextMenu()))

    run_app(app, [
        at("a.zip"), right_click_cursor, Until(lambda a: popup(a) is not None), captions("on_zip"),
        KeyEvent("escape"), Until(lambda a: popup(a) is None),
        at("a.zip"), KeyEvent("enter"), Until(lambda a: "README" in names(a)), at("README"),
        right_click_cursor, Until(lambda a: popup(a) is not None), captions("inside"),
        KeyEvent("escape"), Until(lambda a: popup(a) is None),
    ])
    assert "Extract archive..." in seen["on_zip"] and "Extract to..." not in seen["on_zip"]
    assert "Extract to..." in seen["inside"] and "Test archive" in seen["inside"]
    assert "Extract archive..." not in seen["inside"]


def test_test_archive_says_what_failed(desk):
    from navigator.widgets.manager.commands import ArcTest

    app, here = desk
    corrupt_zip(here / "bad.zip")
    seen = {}
    run_app(app, [
        lambda a: a.manager.left.reload(), Until(lambda a: "bad.zip" in names(a)),
        at("bad.zip"), KeyEvent("enter"), Until(lambda a: "good.txt" in names(a)),
        at(".."), lambda a: a.spawn(a.run_command(ArcTest)), Until(lambda a: type(a.modal).__name__ == "Dialog", timeout=5),
        lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter"),
    ])
    assert "1 error found in bad.zip:" in seen["prompt"] and "bad.txt" in seen["prompt"]


def test_an_archive_panel_has_its_own_columns_packed_and_ratio_among_them(desk):
    app, here = desk
    seen = {}

    def keys(a):
        return [key for key, _, _ in a.manager.left.detail_columns]

    run_app(app, [
        lambda a: setattr(a.manager.left, "view_mode", "detailed"),
        lambda a: seen.update(disk=keys(a)),
        at("a.zip"), KeyEvent("enter"), Until(lambda a: "README" in names(a)),
        at("README"), lambda a: seen.update(inside=keys(a), entry=a.manager.left.selected,
                                            wanted=a.manager.left.shown_columns),
    ])
    assert "packed" not in seen["disk"] and "ratio" not in seen["disk"]
    assert seen["wanted"] == {"size", "packed", "ratio", "attributes", "owner", "date"}
    # Half of 100 columns: the narrowest name gives up owner, attributes and ratio first.
    assert seen["inside"] == ["name", "size", "packed", "date"]
    entry = seen["entry"]
    assert entry.packed is not None and entry.display_ratio == f"{round(entry.packed * 100 / entry.size):>3}%"
