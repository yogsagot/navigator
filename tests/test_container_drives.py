"""Container and device drives: ``docker://``, ``podman://`` and ``adb://``
(``navigator/lib/drives/execdrive.py``, ``docker.py``, ``podman.py``,
``adb.py``), against ``tests/fake_engine.py`` -- a stand-in for the three
commands that runs what it is given on this machine, so the "container" is
the test's own ``tmp_path``.

A real engine is tried only when asked: ``NAVIGATOR_CONTAINER_TESTS=1``
with ``docker`` (or ``podman``) working, on an ``alpine`` container --
busybox's ``stat``, ``mv`` and ``touch``.
"""

from __future__ import annotations

import errno
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest

from navigator.lib.drives import DriveGone, Location, Site, drive_of, mounted
from navigator.lib.drives import adb, docker, execdrive, podman
from navigator.lib.drives.sessions import SESSIONS, Answers
from navigator.lib.file_ops.filecopy import MOVE, OVERWRITE, PRESERVE, CopyJob, CopyRequest, run as copy_run
from navigator.lib.file_ops.fileerase import ALL, EraseJob, EraseRequest, run as erase_run

FAKE = Path(__file__).with_name("fake_engine.py")


# -- parsing ----------------------------------------------------------------------------------------


GNU = (
    "41ed 4096 1700000000 1700000001 1000 1000 2 11 me me sub\n"
    "81a4 5 1700000100 1700000101 1000 1000 1 12 me me a b.txt\n"
    "a1ff 5 1700000200 1700000201 1000 1000 1 13 me me link\n"
    "81a4 0 1700000300 1700000301 0 0 1 14 root root two\nlines\n"
)


def test_stat_lines_are_read_with_spaces_and_newlines_in_names():
    found = execdrive.parse_stat(GNU.rstrip("\n"))
    assert [each.name for each in found] == ["sub", "a b.txt", "link", "two\nlines"]
    assert stat.S_ISDIR(found[0].st_mode) and found[1].st_size == 5
    assert stat.S_ISLNK(found[2].st_mode)
    assert found[1].st_mtime == 1700000100 and found[1].owner == "me:me"
    assert found[3].st_uid == 0 and found[3].st_ino == 14


def test_busybox_names_unknown_owners_by_number():
    found = execdrive.parse_stat("81a4 3 1 2 1234 1234 1 7 1234 1234 x")
    assert found[0].owner == "1234:1234"


def test_a_listing_follows_its_links_and_says_the_free_space():
    text = (GNU.replace("two\nlines\n", "two\n") + execdrive.LINKS_MARK + "\n" + "41ed 4096 1700000500\n"
            "sub\n" + execdrive.FREE_MARK + "\n" + "overlay 1000 10 990 1% /\n")
    stats, space = execdrive.parse_listing(text)
    link = stats[2]
    assert link.target == (0o40755, 4096, 1700000500.0) and link.link_text == "sub"
    assert space == (990 * 1024, "/")


def test_a_dangling_link_has_no_target():
    text = "a1ff 3 1 1 0 0 1 1 root root gone\n" + execdrive.LINKS_MARK + "\n-\nnowhere\n"
    stats, space = execdrive.parse_listing(text)
    assert stats[0].target is None and stats[0].link_text == "nowhere" and space is None


@pytest.mark.parametrize("words, code", [
    ("stat: cannot stat '/x': No such file or directory", errno.ENOENT),
    ("rmdir: '/d': Directory not empty", errno.ENOTEMPTY),
    ("mkdir: can't create directory 'x': File exists", errno.EEXIST),
    ("/x: Permission denied", errno.EACCES),
    ("rm: can't remove 'x': Read-only file system", errno.EROFS),
    ("ln: x: Symbolic link loop", errno.ELOOP),
    ("something odd", errno.EIO),
])
def test_a_tool_s_words_are_an_errno(words, code):
    error = execdrive.os_error(words, "/x")
    assert error.errno == code and error.filename == "/x"
    if code == errno.ENOENT:
        assert isinstance(error, FileNotFoundError)


def test_stamps_are_touch_s_in_utc():
    assert execdrive.stamp(0) == "197001010000.00"
    assert execdrive.stamp(1700000000.7) == "202311142213.20"


def test_docker_and_podman_ps_are_read():
    docker_out = ('{"ID":"abc","Names":"web","Image":"nginx:1","Status":"Up 2 hours"}\n'
                  '{"ID":"def","Names":"db,alias","Image":"postgres","Status":"Up"}\n')
    assert docker.parse_ps(docker_out) == [docker.Container("web", "nginx:1", "Up 2 hours", "abc"),
                                           docker.Container("db", "postgres", "Up", "def")]
    podman_out = '[{"Id":"fff","Names":["box"],"Image":"alpine","State":"running"}]'
    assert docker.parse_ps(podman_out) == [docker.Container("box", "alpine", "running", "fff")]
    assert docker.parse_ps("") == []


def test_adb_devices_are_read():
    out = ("* daemon started successfully\nList of devices attached\n"
           "R58M123ABC             device usb:1-1 product:beyond0 model:SM_G970F device:beyond0 transport_id:1\n"
           "192.168.1.5:5555       unauthorized transport_id:2\n\n")
    devices = adb.parse_devices(out)
    assert devices == [adb.Device("R58M123ABC", "device", "SM G970F"),
                       adb.Device("192.168.1.5:5555", "unauthorized", "")]
    assert devices[0].site() == Site("adb", "", "R58M123ABC")
    assert devices[1].site() == Site("adb", "", "192.168.1.5", 5555)


def test_names_keep_their_case_and_a_networked_serial_its_port():
    place = Location.parse("docker://WebApp/srv/x")
    assert place.site == Site("docker", "", "WebApp") and place.path == PurePosixPath("/srv/x")
    phone = Location.parse("adb://192.168.1.5:5555/sdcard")
    assert phone.site == Site("adb", "", "192.168.1.5", 5555)
    assert adb.serial_of(phone.site) == "192.168.1.5:5555"
    assert Location.parse(str(phone)) == phone
    assert Location.parse("adb://R58M123ABC/sdcard").site.host == "R58M123ABC"


def test_docker_s_failures_that_mean_the_container_is_gone():
    assert docker.lost("Error response from daemon: container web is not running", 125)
    assert docker.lost("Error: No such container: web", 1)
    assert docker.lost("rm: can't remove 'x': Permission denied", 1) is None
    assert adb.lost("adb: device 'R5' not found")
    assert adb.lost("error: device unauthorized.") == "Allow USB debugging on the device, then try again"
    assert adb.lost("sh: x: not found") is None


# -- the fake engine --------------------------------------------------------------------------------


@pytest.fixture
def engines(tmp_path, monkeypatch):
    """``docker``, ``podman`` and ``adb`` on ``PATH``, all the fake; its
    state directory, where ``containers.json`` and ``devices.json`` say
    what exists."""
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    state = tmp_path / "fake-state"
    state.mkdir()
    for name in ("docker", "podman", "adb"):
        script = bin_dir / name
        script.write_text(f'#!/bin/sh\nFAKE_ENGINE_NAME={name} exec "{sys.executable}" "{FAKE}" "$@"\n')
        script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_ENGINE_STATE", str(state))
    (state / "containers.json").write_text(json.dumps([
        {"name": "Box", "image": "alpine:3", "running": True, "workdir": str(tmp_path)},
        {"name": "stopped", "image": "alpine:3", "running": False},
    ]))
    (state / "devices.json").write_text(json.dumps([
        {"serial": "R58M123ABC", "state": "device", "model": "Pixel_7"},
        {"serial": "LOCKED1", "state": "unauthorized", "model": ""},
    ]))
    yield state
    SESSIONS.close_all()


def set_running(state: Path, name: str, running: bool) -> None:
    records = json.loads((state / "containers.json").read_text())
    for each in records:
        if each["name"] == name:
            each["running"] = running
    (state / "containers.json").write_text(json.dumps(records))


def at(scheme: str, host: str, path) -> Location:
    return Location(Site(scheme, "", host), PurePosixPath(str(path)))


@pytest.fixture(params=["docker", "podman", "adb"])
def place(request, engines, tmp_path):
    """A directory with things in it, on each kind of drive."""
    root = tmp_path / "there"
    (root / "sub").mkdir(parents=True)
    (root / "a b.txt").write_text("alpha")
    (root / ".hidden").write_text("h")
    (root / "sub" / "c.txt").write_text("gamma")
    os.symlink("sub", root / "link")
    host = "R58M123ABC" if request.param == "adb" else "Box"
    location = at(request.param, host, root)
    SESSIONS.connect(location.site, Answers())
    return location


def test_the_programs_are_found_or_said_missing(engines, monkeypatch):
    assert docker.available() is None and podman.available() is None and adb.available() is None
    monkeypatch.setenv("PATH", "/nonexistent")
    assert "docker" in docker.available()
    assert "podman" in podman.available()
    assert "adb" in adb.available()


@pytest.mark.parametrize("where", ["studio", "ANDROID_HOME", "ANDROID_SDK_ROOT"])
def test_adb_is_found_in_an_android_sdk_off_path(engines, tmp_path, monkeypatch, where):
    """Android Studio puts adb in ~/Android/Sdk/platform-tools and leaves PATH
    alone; the SDK's variables name another place.  Found there, adb runs by
    its full path, the drive's steps and the device list alike."""
    from navigator.lib.drives import remote_shell

    monkeypatch.setattr(adb, "sdk_dirs", adb.SDK_DIRS)
    home = tmp_path / "home"
    sdk = home / "Android" / "Sdk" if where == "studio" else tmp_path / "elsewhere" / "sdk"
    (sdk / "platform-tools").mkdir(parents=True)
    tool = sdk / "platform-tools" / "adb"
    shutil.copy(shutil.which("adb"), tool)
    monkeypatch.setenv("PATH", f"{Path(sys.executable).parent}:/usr/bin:/bin")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    if where != "studio":
        monkeypatch.setenv(where, str(sdk))
    assert adb.available() is None
    assert adb.program() == str(tool) == remote_shell.program("adb")
    assert adb.AdbDrive(Site("adb", "", "R5")).argv(["ls"])[0] == str(tool)
    assert [each.serial for each in adb.list_devices()] == ["R58M123ABC", "LOCKED1"]
    assert remote_shell.command(Location(Site("adb", "", "R5"), PurePosixPath("."))).startswith(str(tool))


def test_adb_on_path_wins_over_an_sdk_and_runs_by_name(engines, tmp_path, monkeypatch):
    monkeypatch.setattr(adb, "sdk_dirs", adb.SDK_DIRS)
    (tmp_path / "home" / "Android" / "Sdk" / "platform-tools").mkdir(parents=True)
    shutil.copy(shutil.which("adb"), tmp_path / "home" / "Android" / "Sdk" / "platform-tools" / "adb")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert adb.program() == shutil.which("adb")
    assert adb.command() == "adb"


def test_connecting_checks_the_container_runs(engines, tmp_path):
    drive = SESSIONS.connect(Site("docker", "", "Box"), Answers())
    assert drive.home == PurePosixPath(str(tmp_path))
    assert ("Image", "alpine:3") in drive.describe()
    with pytest.raises(DriveGone, match="not running"):
        SESSIONS.connect(Site("docker", "", "stopped"), Answers())
    with pytest.raises(DriveGone, match="No such container"):
        SESSIONS.connect(Site("podman", "", "nothere"), Answers())


def test_connecting_to_a_device(engines):
    drive = SESSIONS.connect(Site("adb", "", "R58M123ABC"), Answers())
    assert drive.home == adb.HOME
    assert ("Device", "Pixel_7 (R58M123ABC)") in drive.describe() and ("Android", "14") in drive.describe()
    with pytest.raises(DriveGone, match="USB debugging"):
        SESSIONS.connect(Site("adb", "", "LOCKED1"), Answers())
    with pytest.raises(DriveGone, match="not found"):
        SESSIONS.connect(Site("adb", "", "nothere"), Answers())


def test_a_directory_is_listed(place):
    drive = drive_of(place)
    entries, error, space = drive.scan(place, False, "name", free=True)
    assert error is None
    names = {entry.name: entry for entry in entries}
    assert set(names) == {"..", "sub", "link", "a b.txt"}
    assert names["link"].is_dir and names["link"].is_link and names["link"].link_target == "sub"
    assert names["a b.txt"].size == 5 and names["a b.txt"].owner
    assert space is not None and space[0] > 0
    shown, _, _ = drive.scan(place, True, "name", free=False, mask="*.txt")
    # The mask takes files only; hidden ones shown, ``.hidden`` is not a ``*.txt``.
    assert {entry.name for entry in shown} == {"..", "sub", "link", "a b.txt"}
    assert {name for name, _ in drive.children(place)} == {"sub", "link", "a b.txt", ".hidden"}


def test_a_missing_directory_says_so(place):
    drive = drive_of(place)
    _, error, _ = drive.scan(place / "nothere", False, "name", free=False)
    assert error == os.strerror(errno.ENOENT)
    with pytest.raises(FileNotFoundError):
        drive.children(place / "nothere")


def test_files_are_stated_read_and_written(place):
    drive = drive_of(place)
    facts = drive.stat(place / "a b.txt")
    assert facts.st_size == 5 and stat.S_ISREG(facts.st_mode)
    assert stat.S_ISLNK(drive.lstat(place / "link").st_mode) and stat.S_ISDIR(drive.stat(place / "link").st_mode)
    with pytest.raises(FileNotFoundError):
        drive.stat(place / "none")
    with drive.open_read(place / "a b.txt") as handle:
        assert handle.read() == b"alpha"
    with drive.open_write(place / "new.bin") as handle:
        handle.write(bytes(range(256)) * 10)
    assert Path(place.path / "new.bin").read_bytes() == bytes(range(256)) * 10
    with drive.open_write(place / "new.bin", append=True) as handle:
        handle.write(b"!")
    assert Path(place.path / "new.bin").stat().st_size == 2561
    reader = drive.open_random(place / "new.bin")
    assert reader.read_at(1, 3) == bytes([1, 2, 3]) and reader.read_at(2560, 10) == b"!"
    with pytest.raises(OSError):
        with drive.open_read(place / "none") as handle:
            handle.read()


def test_steps_change_what_is_there(place):
    drive = drive_of(place)
    drive.mkdir(place / "made")
    with pytest.raises(FileExistsError):
        drive.mkdir(place / "made")
    drive.rename(place / "a b.txt", place / "renamed.txt")
    with pytest.raises(FileExistsError):
        drive.rename(place / "renamed.txt", place / "sub")
    with pytest.raises(IsADirectoryError):
        drive.replace(place / "renamed.txt", place / "sub")
    Path(place.path / "other.txt").write_text("other")
    drive.replace(place / "other.txt", place / "renamed.txt")
    assert Path(place.path / "renamed.txt").read_text() == "other"
    drive.chmod(place / "renamed.txt", 0o600)
    assert stat.S_IMODE(Path(place.path / "renamed.txt").stat().st_mode) == 0o600
    drive.utime(place / "renamed.txt", 1_600_000_000 * 10**9, 1_500_000_000 * 10**9)
    assert Path(place.path / "renamed.txt").stat().st_mtime == 1_500_000_000
    with pytest.raises(OSError) as raised:
        drive.rmdir(place / "sub")
    assert raised.value.errno == errno.ENOTEMPTY
    drive.unlink(place / "renamed.txt")
    with pytest.raises(FileNotFoundError):
        drive.unlink(place / "renamed.txt")
    drive.rmdir(place / "made")
    assert not Path(place.path / "made").exists()


def test_a_symlink_is_made_in_a_container(engines, tmp_path):
    there = at("docker", "Box", tmp_path)
    drive = SESSIONS.connect(there.site, Answers())
    drive.symlink("target", there / "made-link")
    assert os.readlink(tmp_path / "made-link") == "target" and drive.readlink(there / "made-link") == "target"


def test_a_tree_copies_in_and_out_keeping_times(place, tmp_path):
    source = tmp_path / "here"
    (source / "deep").mkdir(parents=True)
    (source / "deep" / "d.txt").write_text("delta")
    os.utime(source / "deep" / "d.txt", (1_400_000_000, 1_400_000_000))
    done = copy_run(CopyRequest([source], str(place) + "/", OVERWRITE, PRESERVE), CopyJob(asker=lambda q: None),
                    tmp_path)
    assert done == [source]
    copied = Path(place.path / "here" / "deep" / "d.txt")
    assert copied.read_text() == "delta" and copied.stat().st_mtime == 1_400_000_000
    back = tmp_path / "back"
    back.mkdir()
    done = copy_run(CopyRequest([place / "here"], str(back), OVERWRITE, PRESERVE | MOVE),
                    CopyJob(asker=lambda q: None), tmp_path)
    assert done == [place / "here"]
    assert (back / "here" / "deep" / "d.txt").read_text() == "delta"
    assert not Path(place.path / "here").exists()


def test_a_tree_is_erased(place):
    job = EraseJob(asker=lambda question: ALL)
    done = erase_run(EraseRequest([place / "sub"]), job)
    assert done == [place / "sub"] and not Path(place.path / "sub").exists()


def test_a_container_stopped_is_the_drive_lost(engines, tmp_path):
    there = at("docker", "Box", tmp_path)
    drive = SESSIONS.connect(there.site, Answers())
    heard = []
    SESSIONS.add_listener(lambda site, why: heard.append((site, why)))
    set_running(engines, "Box", False)
    with pytest.raises(DriveGone, match="not running"):
        drive.children(there)
    assert heard == [(there.site, "lost")]
    assert all(each.site != there.site for each in mounted())


def test_a_container_with_a_user_runs_as_it(engines, tmp_path):
    drive = SESSIONS.connect(Site("docker", "www", "Box"), Answers())
    assert drive.argv(["true"]) == ["docker", "exec", "-u", "www", "Box", "true"]
    assert drive.argv(["cat"], stdin=True)[:3] == ["docker", "exec", "-i"]


def test_adb_quotes_the_words_it_sends():
    drive = adb.AdbDrive(Site("adb", "", "R5"))
    assert drive.argv(["stat", "--", "/sdcard/a b"]) == ["adb", "-s", "R5", "shell", "-T", "stat -- '/sdcard/a b'"]


def test_live_lists(engines):
    assert [each.name for each in docker.list_containers()] == ["Box"]
    assert [each.name for each in podman.list_containers()] == ["Box"]
    assert [each.serial for each in adb.list_devices()] == ["R58M123ABC", "LOCKED1"]


# -- a real engine, when asked ----------------------------------------------------------------------


def _real_engine() -> str | None:
    if os.environ.get("NAVIGATOR_CONTAINER_TESTS") != "1":
        return None
    for engine in ("docker", "podman"):
        if shutil.which(engine) and subprocess.run([engine, "info"], capture_output=True).returncode == 0:
            return engine
    return None


@pytest.mark.skipif(_real_engine() is None, reason="NAVIGATOR_CONTAINER_TESTS=1 and a working docker or podman")
def test_an_alpine_container(tmp_path):
    engine = _real_engine()
    assert engine is not None
    name = f"navigator-test-{os.getpid()}"
    subprocess.run([engine, "run", "-d", "--rm", "--name", name, "alpine:3", "sleep", "600"], check=True,
                   capture_output=True)
    try:
        there = Location(Site(engine, "", name), PurePosixPath("/tmp"))
        drive = SESSIONS.connect(there.site, Answers())
        source = tmp_path / "x y.txt"
        source.write_text("busybox")
        os.utime(source, (1_400_000_000, 1_400_000_000))
        copy_run(CopyRequest([source], "%s/" % there, OVERWRITE, PRESERVE), CopyJob(asker=lambda q: None),
                 tmp_path)
        assert drive.stat(there / "x y.txt").st_mtime == 1_400_000_000
        drive.rename(there / "x y.txt", there / "z.txt")
        entries, error, _ = drive.scan(there, True, "name", free=True)
        assert error is None and "z.txt" in {entry.name for entry in entries}
        with drive.open_read(there / "z.txt") as handle:
            assert handle.read() == b"busybox"
    finally:
        SESSIONS.close_all()
        subprocess.run([engine, "rm", "-f", name], capture_output=True)


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


def test_docker_s_link_lists_what_runs_and_sends_the_panel_there(engines, tmp_path, monkeypatch):
    from conftest import Until, run_app
    from navkit.events import KeyEvent
    from navigator.lib.drives import profiles
    from navigator.widgets.shell.commands import DockerLink

    profiles.save("kept", "docker", "Box", "", 0, "/etc")
    app = make_app(tmp_path, monkeypatch)
    seen = {}

    def look(a):
        seen.update(rows=list(a.modal.links.items), title=a.modal.title, container=a.modal.host.label_text,
                    port=a.modal.port.visible)
        a.modal.links.focus()
        a.modal.links.cursor = 2  # the running Box, under the heading

    def lines(a):
        seen.update(host=a.modal.host.value, chosen=a.modal.chosen, state=a.modal.missing.text)

    def there(a):
        panel = a.manager.active_panel
        return panel.location.site.scheme == "docker"

    run_app(app, [lambda a: a.spawn(a.run_command(DockerLink)), Until(_manager_with_live), look, lines,
                  KeyEvent("enter"), Until(there, timeout=10),
                  lambda a: seen.update(where=a.manager.active_panel.title_location)])
    assert seen["rows"] == ["kept", "── Running ──", "Box  alpine:3"]
    assert seen["title"] == "Docker container" and seen["container"] == "Cont~a~iner" and not seen["port"]
    # A running one fills the lines as a one-off: New would keep it.
    assert seen["host"] == "Box" and seen["chosen"] is None and seen["state"] == "Not saved — New keeps it"
    # No directory: the container's working directory, the fake's tmp_path.
    assert seen["where"] == f"DOCKER:Box:{tmp_path}"


def test_new_keeps_a_running_container_and_ctrl_r_reads_again(engines, tmp_path, monkeypatch):
    from conftest import Until, run_app
    from navkit.events import KeyEvent
    from navigator.lib.drives import profiles
    from navigator.widgets.shell.commands import PodmanLink

    app = make_app(tmp_path, monkeypatch)
    seen = {}

    def choose(a):
        a.modal.links.focus()
        a.modal.links.cursor = 1

    def started(a):
        records = json.loads((engines / "containers.json").read_text())
        records.append({"name": "late", "image": "busybox", "running": True})
        (engines / "containers.json").write_text(json.dumps(records))

    run_app(app, [lambda a: a.spawn(a.run_command(PodmanLink)), Until(_manager_with_live), choose,
                  KeyEvent("insert"), Until(lambda a: a.modal.entries != []),
                  lambda a: seen.update(rows=list(a.modal.links.items), chosen=a.modal.chosen),
                  started, KeyEvent("r", ctrl=True), Until(lambda a: len(a.modal.live) == 2),
                  lambda a: seen.update(after=list(a.modal.links.items)), KeyEvent("escape")])
    assert [(row.name, row.scheme, row.host) for row in profiles.profiles()] == [("Box", "podman", "Box")]
    assert seen["rows"] == ["Box", "── Running ──", "Box  alpine:3"] and seen["chosen"] == 0
    assert seen["after"][-1] == "late  busybox"


def test_android_s_link_names_the_device_and_greys_without_adb(engines, tmp_path, monkeypatch):
    from conftest import Until, run_app
    from navigator.widgets.shell.commands import AdbLink, DockerLink

    app = make_app(tmp_path, monkeypatch)
    seen = {}

    def look(a):
        seen.update(rows=list(a.modal.links.items), serial=a.modal.host.label_text, user=a.modal.user.visible)

    def without(a):
        monkeypatch.setenv("PATH", "/nonexistent")
        seen.update(docker=a.shell.refusal(DockerLink()), adb=a.shell.refusal(AdbLink()))

    run_app(app, [lambda a: a.spawn(a.run_command(AdbLink)), Until(_manager_with_live), look,
                  lambda a: a.modal.close(None), without])
    assert seen["rows"] == ["── Connected ──", "Pixel 7 R58M123ABC", "LOCKED1 (unauthorized)"]
    assert seen["serial"] == "Se~r~ial" and not seen["user"]
    assert seen["docker"] == "Docker needs the docker command"
    assert seen["adb"].startswith("Android devices need the adb command")


def test_utilities_has_a_link_and_a_remote_shell_submenu(engines, tmp_path, monkeypatch):
    from conftest import run_app
    from navigator.widgets.shell.commands import (
        AdbLink, AdbShell, DockerLink, DockerShell, FtpLink, GvfsLink, NavyLink, PodmanLink, PodmanShell, S3Link,
        SmbLink, Terminal,
    )

    app = make_app(tmp_path, monkeypatch)
    seen = {}

    def commands(menu):
        return [getattr(item, "command", None) for item in menu.children if getattr(item, "command", None)]

    def look(a):
        menu = a.shell.menu
        seen.update(link=commands(menu.utilities_link), shell=commands(menu.utilities_shell),
                    top=commands(menu.utilities))

    run_app(app, [look])
    assert seen["link"] == [NavyLink, FtpLink, SmbLink, S3Link, GvfsLink, DockerLink, PodmanLink, AdbLink]
    assert seen["shell"] == [Terminal, DockerShell, PodmanShell, AdbShell]
    assert not {NavyLink, Terminal} & set(seen["top"])
