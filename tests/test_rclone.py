"""rclone remotes as a drive (``navigator/lib/drives/rclone.py``), against
``tests/fake_rclone.py`` -- a stand-in ``rclone`` whose ``rcd`` serves the
remote control on its Unix socket over a directory of the test's.

A real rclone is tried when one is installed, on an ``alias`` of a local directory
set up through the environment (``RCLONE_CONFIG_<NAME>_TYPE``).
"""

from __future__ import annotations

import errno
import json
import os
import shutil
import stat
import sys
import time
from pathlib import Path, PurePosixPath

import pytest

from navigator.lib.drives import DriveGone, Location, Site, drive_of, mounted
from navigator.lib.drives import credentials, rclone, sessions
from navigator.lib.drives.sessions import SESSIONS, Answers, NeedPassword
from navigator.lib.file_ops.filecopy import MOVE, OVERWRITE, PRESERVE, CopyJob, CopyRequest, run as copy_run
from navigator.lib.file_ops.fileerase import ALL, EraseJob, EraseRequest, run as erase_run

FAKE = Path(__file__).with_name("fake_rclone.py")


# -- what needs no rclone -----------------------------------------------------------------------------


def test_remote_names_keep_their_case_and_survive_the_url():
    for name in ("GDrive", "My Drive", "a@b", "x+y.z_-"):
        place = Location(Site("rclone", "", name), PurePosixPath("/a b/c"))
        assert Location.parse(str(place)) == place
    assert str(Location(Site("rclone", "", "My Drive"), PurePosixPath("/"))) == "rclone://My%20Drive/"


def test_listremotes_is_read():
    text = "gdrive:          drive\nMy Box:          box\nbare:\n\n"
    assert rclone.parse_listremotes(text) == [
        rclone.Remote("gdrive", "drive"), rclone.Remote("My Box", "box"), rclone.Remote("bare", "")]


@pytest.mark.parametrize("words, status, code", [
    ("object not found", 404, errno.ENOENT),
    ("error listing: directory not found", 404, errno.ENOENT),
    ("rmdir failed: directory not empty", 500, errno.ENOTEMPTY),
    ("googleapi: Error 403: Forbidden", 403, errno.EACCES),
    ("something odd", 500, errno.EIO),
    ("whatever", 404, errno.ENOENT),
])
def test_rclone_s_words_are_an_errno(words, status, code):
    assert rclone.os_error(words, "x", status).errno == code


def test_times_with_nanoseconds_are_read():
    assert rclone.moment("2023-11-14T22:13:20Z") == 1_700_000_000
    assert abs(rclone.moment("2023-11-14T22:13:20.123456789Z") - 1_700_000_000.123456789) < 1e-6
    assert rclone.moment("2023-11-14T23:13:20.5+01:00") == 1_700_000_000.5
    assert rclone.moment("") == 0 and rclone.moment("garbage") == 0


def test_the_scheme_is_named_and_needs_the_program(monkeypatch):
    assert sessions.protocol_sign("rclone") == "RCLONE"
    monkeypatch.setenv("PATH", "/nonexistent")
    assert sessions.available("rclone") == "rclone remotes need the rclone command"
    assert sessions.is_connection("rclone")


# -- against the stand-in -------------------------------------------------------------------------


@pytest.fixture
def fake(tmp_path, monkeypatch):
    """``rclone`` on ``PATH``, the fake; its state directory, where
    ``config.json`` says what remotes there are, and their files."""
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    state = tmp_path / "fake-state"
    (state / "remotes" / "Cloud").mkdir(parents=True)
    (state / "remotes" / "flat").mkdir(parents=True)
    script = bin_dir / "rclone"
    script.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_RCLONE_STATE", str(state))
    monkeypatch.delenv("RCLONE_CONFIG_PASS", raising=False)
    monkeypatch.setattr(credentials, "keyring_available", lambda: False)
    write_config(state, {"Cloud": {"type": "drive"}, "flat": {"type": "b2", "dirmove": False, "about": False}})
    yield state
    SESSIONS.close_all()


def write_config(state: Path, remotes: dict, password: str | None = None) -> None:
    (state / "config.json").write_text(json.dumps({"remotes": remotes, "password": password}))


def at(name: str, path: str = "/") -> Location:
    return Location(Site("rclone", "", name), PurePosixPath(path))


@pytest.fixture
def place(fake):
    """Cloud's root, connected, with things in it."""
    root = fake / "remotes" / "Cloud"
    (root / "sub").mkdir()
    (root / "a b.txt").write_text("alpha")
    (root / ".hidden").write_text("h")
    (root / "sub" / "c.txt").write_text("gamma")
    SESSIONS.connect(at("Cloud").site, Answers())
    return at("Cloud")


def calls(state: Path) -> list[str]:
    return [json.loads(line)[0] for line in (state / "calls.log").read_text().splitlines()]


def test_the_remotes_are_listed(fake):
    assert rclone.list_remotes() == [rclone.Remote("Cloud", "drive"), rclone.Remote("flat", "b2")]


def test_connecting_starts_one_daemon_and_learns_the_remote(place, fake):
    drive = drive_of(place)
    assert isinstance(drive, rclone.RcloneDrive) and drive.daemon.alive
    assert drive.kind == "drive" and rclone.FREE_SPACE in drive.capabilities
    assert ("Backend", "drive") in drive.describe() and drive.get_dir(place / "sub") == "RCLONE:Cloud:/sub"
    argv = [json.loads(line) for line in (fake / "argv.log").read_text().splitlines()]
    assert [each[0] for each in argv] == ["rcd"] and "--rc-serve" in argv[0]
    path = drive.daemon.path
    SESSIONS.close(place.site)
    assert not drive.daemon.alive and not os.path.exists(path)


def test_a_remote_not_set_up_is_refused(fake):
    with pytest.raises(DriveGone, match="no remote called Nowhere"):
        SESSIONS.connect(at("Nowhere").site, Answers())
    assert not mounted()


def test_an_encrypted_configuration_asks_its_password(fake):
    write_config(fake, {"Cloud": {"type": "drive"}}, password="hunter2")
    site = at("Cloud").site
    with pytest.raises(NeedPassword) as raised:
        SESSIONS.connect(site, Answers())
    assert not raised.value.wrong
    with pytest.raises(NeedPassword) as raised:
        SESSIONS.connect(site, Answers(password="wrong"))
    assert raised.value.wrong
    drive = SESSIONS.connect(site, Answers(password="hunter2"))
    assert drive.children(at("Cloud")) == []
    argv = (fake / "argv.log").read_text()
    assert "hunter2" not in argv


def test_a_directory_is_listed(place):
    drive = drive_of(place)
    entries, problem, free = drive.scan(place, False, "name", free=True)
    assert problem is None and free == ((1 << 40) - (1 << 30), "Cloud")
    assert [(each.name, each.is_dir, each.size) for each in entries] == [("sub", True, 0), ("a b.txt", False, 5)]
    entries, _, _ = drive.scan(place / "sub", True, "name", free=False)
    assert [each.name for each in entries] == ["..", "c.txt"]
    assert sorted(drive.names(place)) == [".hidden", "a b.txt", "sub"]
    entries, problem, _ = drive.scan(place / "none", False, "name", free=False)
    assert problem and [each.name for each in entries] == [".."]


def test_files_are_stated_read_and_written(place, fake):
    drive = drive_of(place)
    root = fake / "remotes" / "Cloud"
    facts = drive.stat(place / "a b.txt")
    assert facts.st_size == 5 and stat.S_ISREG(facts.st_mode)
    assert abs(facts.st_mtime - (root / "a b.txt").stat().st_mtime) < 1
    assert stat.S_ISDIR(drive.stat(place / "sub").st_mode) and stat.S_ISDIR(drive.stat(place).st_mode)
    with pytest.raises(FileNotFoundError):
        drive.stat(place / "none")
    with drive.open_read(place / "a b.txt") as handle:
        assert handle.read() == b"alpha"
    data = bytes(range(256)) * 1000
    with drive.open_write(place / "sub" / "new ünï.bin") as handle:
        for start in range(0, len(data), 7000):
            handle.write(data[start:start + 7000])
    assert (root / "sub" / "new ünï.bin").read_bytes() == data
    reader = drive.open_random(place / "sub" / "new ünï.bin")
    assert reader.read_at(1, 3) == bytes([1, 2, 3]) and reader.read_at(len(data) - 2, 10) == data[-2:]
    assert reader.read_at(len(data) + 5, 10) == b""
    with pytest.raises(OSError, match="append"):
        drive.open_write(place / "x", append=True)
    with pytest.raises(FileNotFoundError):
        drive.open_read(place / "none")


def test_steps_change_what_is_there(place, fake):
    drive = drive_of(place)
    root = fake / "remotes" / "Cloud"
    drive.mkdir(place / "made")
    assert (root / "made").is_dir()
    with pytest.raises(FileExistsError):
        drive.mkdir(place / "made")
    drive.rename(place / "a b.txt", place / "renamed.txt")
    assert (root / "renamed.txt").read_text() == "alpha"
    with pytest.raises(FileExistsError):
        drive.rename(place / "renamed.txt", place / "sub")
    (root / "other.txt").write_text("other")
    with pytest.raises(FileExistsError):
        drive.rename(place / "other.txt", place / "renamed.txt")
    drive.replace(place / "other.txt", place / "renamed.txt")
    assert (root / "renamed.txt").read_text() == "other"
    drive.rename(place / "sub", place / "moved")
    assert (root / "moved" / "c.txt").read_text() == "gamma" and not (root / "sub").exists()
    with pytest.raises(OSError) as raised:
        drive.rmdir(place / "moved")
    assert raised.value.errno == errno.ENOTEMPTY
    drive.unlink(place / "renamed.txt")
    with pytest.raises(FileNotFoundError):
        drive.unlink(place / "renamed.txt")
    drive.rmdir(place / "made")
    assert not (root / "made").exists()


def test_a_remote_that_cannot_rename_directories_says_exdev(fake):
    (fake / "remotes" / "flat" / "d").mkdir()
    drive = SESSIONS.connect(at("flat").site, Answers())
    assert rclone.FREE_SPACE not in drive.capabilities
    with pytest.raises(OSError) as raised:
        drive.rename(at("flat", "/d"), at("flat", "/e"))
    assert raised.value.errno == errno.EXDEV


def test_a_tree_copies_in_and_out(place, fake, tmp_path):
    source = tmp_path / "here"
    (source / "deep").mkdir(parents=True)
    (source / "deep" / "d.txt").write_text("delta")
    done = copy_run(CopyRequest([source], str(place) + "/", OVERWRITE, PRESERVE), CopyJob(asker=lambda q: None),
                    tmp_path)
    assert done == [source]
    assert (fake / "remotes" / "Cloud" / "here" / "deep" / "d.txt").read_text() == "delta"
    back = tmp_path / "back"
    back.mkdir()
    done = copy_run(CopyRequest([place / "here"], str(back), OVERWRITE, MOVE), CopyJob(asker=lambda q: None),
                    tmp_path)
    assert done == [place / "here"]
    assert (back / "here" / "deep" / "d.txt").read_text() == "delta"
    assert not (fake / "remotes" / "Cloud" / "here").exists()


def test_a_tree_is_erased(place, fake):
    done = erase_run(EraseRequest([place / "sub"]), EraseJob(asker=lambda question: ALL))
    assert done == [place / "sub"] and not (fake / "remotes" / "Cloud" / "sub").exists()


def test_a_daemon_that_died_is_started_again_once(place, fake):
    drive = drive_of(place)
    first = drive.daemon.process.pid
    drive.daemon.process.kill()
    drive.daemon.process.wait()
    assert sorted(drive.names(place)) == [".hidden", "a b.txt", "sub"]
    assert drive.daemon.process.pid != first


def test_a_daemon_that_cannot_come_back_is_the_drive_lost(place, fake):
    drive = drive_of(place)
    heard = []
    SESSIONS.add_listener(lambda site, why: heard.append((site, why)))
    write_config(fake, {"Cloud": {"type": "drive"}}, password="now-locked")
    drive.daemon.process.kill()
    drive.daemon.process.wait()
    with pytest.raises(DriveGone, match="not running"):
        drive.children(place)
    deadline = time.monotonic() + 5
    while not heard and time.monotonic() < deadline:
        time.sleep(0.02)
    assert heard == [(place.site, "lost")]
    assert all(each.site != place.site for each in mounted())


# -- a real rclone ------------------------------------------------------------------------------------


@pytest.mark.skipif(shutil.which("rclone") is None, reason="rclone is not installed")
def test_a_real_rclone_local_remote(tmp_path, monkeypatch):
    monkeypatch.setenv("RCLONE_CONFIG", str(tmp_path / "none.conf"))
    root = tmp_path / "files"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "c.txt").write_text("gamma")
    # An alias of a local directory: its root is the remote's.
    monkeypatch.setenv("RCLONE_CONFIG_NAVTEST_TYPE", "alias")
    monkeypatch.setenv("RCLONE_CONFIG_NAVTEST_REMOTE", str(root))
    monkeypatch.setattr(credentials, "keyring_available", lambda: False)
    base = Location(Site("rclone", "", "navtest"), PurePosixPath("/"))
    try:
        drive = SESSIONS.connect(base.site, Answers())
        assert "sub" in drive.names(base)
        with drive.open_write(base / "new.bin") as handle:
            handle.write(b"x" * 100_000)
        assert (root / "new.bin").read_bytes() == b"x" * 100_000
        assert drive.open_random(base / "sub" / "c.txt").read_at(1, 3) == b"amm"
        drive.rename(base / "new.bin", base / "sub" / "moved.bin")
        drive.unlink(base / "sub" / "moved.bin")
        drive.mkdir(base / "made")
        drive.rmdir(base / "made")
        with pytest.raises(FileNotFoundError):
            drive.stat(base / "none")
    finally:
        SESSIONS.close_all()


# -- the file manager -------------------------------------------------------------------------------


def make_app(tmp_path, monkeypatch):
    from conftest import FakeTerminal
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.lib.system.tempdir.private_dir", lambda: tmp_path / "private")
    (tmp_path / "private").mkdir(exist_ok=True)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(100, 30))


def _manager_with_live(a):
    from navigator.widgets.drives.link_manager import LinkManagerDialog

    return isinstance(a.modal, LinkManagerDialog) and bool(a.modal.live)


def test_rclone_s_link_lists_the_remotes_and_sends_the_panel_there(fake, tmp_path, monkeypatch):
    from conftest import Until, run_app
    from navkit.events import KeyEvent
    from navigator.widgets.shell.commands import RcloneLink

    (fake / "remotes" / "Cloud" / "inside").mkdir()
    app = make_app(tmp_path, monkeypatch)
    seen = {}

    def look(a):
        seen.update(rows=list(a.modal.links.items), title=a.modal.title, remote=a.modal.host.label_text,
                    user=a.modal.user.visible, port=a.modal.port.visible, configure=a.modal.configure.visible)
        a.modal.links.focus()
        a.modal.links.cursor = 1  # Cloud, under the heading

    def there(a):
        return a.manager.active_panel.location.site.scheme == "rclone"

    run_app(app, [lambda a: a.spawn(a.run_command(RcloneLink)), Until(_manager_with_live), look,
                  lambda a: seen.update(host=a.modal.host.value), KeyEvent("enter"), Until(there, timeout=10),
                  Until(lambda a: any(e.name == "inside" for e in a.manager.active_panel.items), timeout=10),
                  lambda a: seen.update(where=a.manager.active_panel.title_location)])
    assert seen["rows"] == ["── Configured ──", "Cloud  drive", "flat   b2"]
    assert seen["title"] == "rclone remote" and seen["remote"] == "Re~m~ote"
    assert not seen["user"] and not seen["port"] and seen["configure"]
    assert seen["host"] == "Cloud" and seen["where"] == "RCLONE:Cloud:/"


def test_configure_runs_rclone_config_in_a_window(fake, tmp_path, monkeypatch):
    from conftest import Until, run_app
    from navigator.widgets.shell.commands import RcloneLink

    app = make_app(tmp_path, monkeypatch)
    ran = []
    monkeypatch.setattr(type(app.shell), "run_in_window",
                        lambda self, command, **options: ran.append((command, options)) or None)

    def press(a):
        a.modal.spawn(a.modal.configure_remotes())

    run_app(app, [lambda a: a.spawn(a.run_command(RcloneLink)), Until(_manager_with_live), press,
                  Until(lambda a: ran, timeout=10)])
    command, options = ran[0]
    assert command.endswith("rclone config") and options["closes"] is False


def test_the_entry_is_greyed_without_rclone(fake, tmp_path, monkeypatch):
    from conftest import run_app
    from navigator.widgets.shell.commands import RcloneLink

    app = make_app(tmp_path, monkeypatch)
    seen = {}

    def without(a):
        seen["with"] = a.shell.refusal(RcloneLink())
        monkeypatch.setenv("PATH", "/nonexistent")
        seen["without"] = a.shell.refusal(RcloneLink())

    run_app(app, [without])
    assert seen == {"with": "", "without": "rclone remotes need the rclone command"}
