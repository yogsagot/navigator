"""What the panels do on the disk, done on another drive too -- the in-memory
one standing for a server: directory length, Auto refresh by polling, Find,
the trees, quick view, the information panel, comparing contents and
changing attributes."""

from __future__ import annotations

import stat
import threading
import time
from pathlib import PurePosixPath

import pytest

from conftest import FakeTerminal, Until, run_app, settle
from navkit.events import KeyEvent
from navigator.lib.drives import Location, mount, unmount
from navigator.lib.drives.memory import MemoryDrive


@pytest.fixture
def memory():
    drive = mount(MemoryDrive("parity"))
    drive.make("/top/a.txt", "alpha")
    drive.make("/top/sub/b.txt", "beta, longer")
    drive.make("/top/sub/deeper/c.log", "needle in here")
    drive.make("/other/a.txt", "alpha")
    drive.make("/other/sub/b.txt", "beta, LONGER")
    yield drive
    unmount(drive.site)


@pytest.fixture
def desk(memory, tmp_path, monkeypatch):
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))
    return app, memory


def names(panel):
    return [entry.name for entry in panel.items]


def test_a_directory_is_counted_on_another_drive(memory):
    from navigator.lib.file_ops.dirlength import CountJob, count_dir_length

    job = CountJob()
    assert count_dir_length(memory.location("/top"), job) == len("alpha") + len("beta, longer") + len(
        "needle in here")
    assert (job.files, job.directories) == (3, 2)


def test_auto_refresh_looks_again_on_a_drive_that_cannot_tell(memory):
    from navigator.lib.drives.base import PollWatch

    heard = threading.Event()
    watch = PollWatch(memory, memory.location("/top"), heard.set, 0.02)
    try:
        time.sleep(0.1)
        assert not heard.is_set()  # nothing changed, nothing said
        memory.make("/top/new.txt", "new")
        assert heard.wait(2)
    finally:
        watch.cancel()


def test_a_server_drive_polls_only_when_communications_says_so(memory, monkeypatch):
    from navigator.lib.drives.base import PollWatch
    from navigator.settings import SETTINGS

    monkeypatch.setattr(type(memory), "polled", True, raising=False)
    monkeypatch.setattr(SETTINGS.remote, "refresh", 0)
    assert not isinstance(memory.watch(memory.location("/top"), lambda: None), PollWatch)
    monkeypatch.setattr(SETTINGS.remote, "refresh", 5)
    watch = memory.watch(memory.location("/top"), lambda: None)
    assert isinstance(watch, PollWatch)
    watch.cancel()


def test_find_walks_another_drive_and_reads_its_files(memory):
    from navigator.lib.file_ops.filefind import FindJob, FindRequest, search

    job = FindJob()
    found = search(FindRequest(mask="*.txt"), memory.location("/top"), None, job)
    assert sorted(f"{entry.directory.path}/{entry.name}" for entry in found) == ["/top/a.txt", "/top/sub/b.txt"]
    job = FindJob()
    found = search(FindRequest(text="needle"), memory.location("/top"), None, job)
    assert [entry.name for entry in found] == ["c.log"]
    assert found[0].path_in(None) == memory.location("/top/sub/deeper/c.log")


def test_alt_f7_lists_what_it_found_on_another_drive_and_goes_to_one(desk):
    from navigator.lib.file_ops.filefind import FindRequest

    app, memory = desk
    seen = {}

    async def find(a):
        await a.manager._search_into(a.manager.left, FindRequest(mask="*.txt"), "Find: *.txt")

    run_app(app, [
        lambda a: setattr(a.manager.left, "location", memory.location("/top")),
        Until(lambda a: "sub" in names(a.manager.left)),
        lambda a: a.spawn(find(a)),
        Until(lambda a: a.manager.left.found is not None and not a.manager.left.found.live, timeout=5),
        lambda a: seen.update(found=sorted(names(a.manager.left))),
        lambda a: setattr(a.manager.left, "cursor", names(a.manager.left).index("b.txt")),
        lambda a: a.manager.left.go_to_entry(),
        Until(lambda a: a.manager.left.found is None and "b.txt" in names(a.manager.left)),
        lambda a: seen.update(at=a.manager.left.location, cursor=a.manager.left.selected.name),
    ])
    assert seen["found"] == ["..", "a.txt", "b.txt"]
    assert seen["at"] == memory.location("/top/sub") and seen["cursor"] == "b.txt"


def test_the_tree_of_another_drive_is_read_on_threads(desk):
    from navigator.widgets.tree.directory_tree.directory_tree import DirectoryTree

    app, memory = desk
    tree = DirectoryTree()
    seen = {}

    def show(a):
        a.root.add(tree)
        tree.show(memory.location("/top/sub/deeper"))

    run_app(app, [
        show, Until(lambda a: tree.selected_path == memory.location("/top/sub/deeper"), timeout=5),
        lambda a: seen.update(rows=[row.node.name for row in tree.items], background=tree.load_in_background),
        lambda a: tree.show(a.manager.left.path),  # back on the disk: a tree of the disk again
        lambda a: seen.update(local=tree.load_in_background),
    ])
    assert seen["rows"][:5] == ["/", "other", "top", "sub", "deeper"] and seen["background"]
    assert seen["local"] is False


def test_quick_view_shows_the_head_of_a_file_on_another_drive(desk):
    from navigator.widgets.viewer.quick_viewer import QuickViewer

    app, memory = desk
    quick = QuickViewer()
    seen = {}

    def show(a):
        a.root.add(quick)
        quick.show(memory.location("/top/a.txt"))

    run_app(app, [
        show, Until(lambda a: quick.viewer.source is not None, timeout=5),
        lambda a: seen.update(name=quick.viewer.path.name, size=quick.viewer.source.size,
                              copy=quick._use.directory),
        lambda a: quick.show(None),
        Until(lambda a: not seen["copy"].exists(), timeout=5),
    ])
    assert (seen["name"], seen["size"]) == ("a.txt", 5)


def test_the_information_panel_says_what_the_drive_says_of_itself(tmp_path):
    import zipfile

    from navigator.lib.drives import archive
    from navigator.widgets.manager.info_panel.info_panel import InfoPanel

    with zipfile.ZipFile(tmp_path / "a.zip", "w") as zipped:
        zipped.writestr("one.txt", "1" * 100)
    drive = archive.open_archive(Location.of(tmp_path / "a.zip"))
    try:
        info = InfoPanel()
        info.show(drive.at("/"), [])
        settle()
        text = "\n".join(line for line, _ in info.lines())
        assert "ZIP:a.zip:/" in text and "Files: ~1~" in text and "Unpacked: ~100~" in text
    finally:
        archive.close_all()


def test_contents_are_compared_across_drives(memory, tmp_path):
    from navigator.lib.file_ops.dircompare import same_bytes

    (tmp_path / "a.txt").write_text("alpha")
    assert same_bytes(memory.location("/top/a.txt"), tmp_path / "a.txt")
    assert not same_bytes(memory.location("/top/sub/b.txt"), memory.location("/other/sub/b.txt"))


def test_attributes_change_on_another_drive_down_a_tree(memory):
    from navigator.lib.file_ops import fileattr

    request = fileattr.AttrRequest([memory.location("/top")], set_bits=0o070, recurse=fileattr.ALL)
    done = fileattr.run(request, fileattr.AttrJob(asker=lambda q: pytest.fail(f"asked {q}")))
    assert done == [memory.location("/top")]
    for path in ("/top", "/top/a.txt", "/top/sub/deeper/c.log"):
        assert stat.S_IMODE(memory.stat(memory.location(path)).st_mode) & 0o070 == 0o070
    survey = fileattr.survey([memory.location("/top/a.txt")])
    assert survey.files == 1 and survey.mode & 0o070 == 0o070


def test_save_as_writes_to_another_drive_and_into_an_archive(memory, tmp_path):
    import zipfile

    from navigator.lib import viewer
    from navigator.lib.drives import archive

    (tmp_path / "source.txt").write_text("saved")
    viewer.save_as(tmp_path / "source.txt", memory.location("/top/saved.txt"))
    assert memory.read("/top/saved.txt") == b"saved"
    assert sorted(memory.names(memory.location("/top"))) == ["a.txt", "saved.txt", "sub"]
    drive = archive.open_archive(Location.of(tmp_path / "new.zip"), create=True)
    viewer.save_as(tmp_path / "source.txt", drive.at("/saved.txt"))
    archive.close_all()
    with zipfile.ZipFile(tmp_path / "new.zip") as zipped:
        assert zipped.read("saved.txt") == b"saved"


def test_the_file_dialog_hands_a_raw_name_back_as_typed(tmp_path):
    from navml.widgets.dialog.file_dialog import FileDialog

    dialog = FileDialog(directory=tmp_path)
    dialog.raw = lambda text: "://" in text
    dialog.target.value = "sftp://host/dir/name.txt"
    assert dialog.valid() and dialog.accept() == "sftp://host/dir/name.txt"
    dialog.target.value = "plain.txt"
    assert dialog.accept() == str(tmp_path / "plain.txt")
