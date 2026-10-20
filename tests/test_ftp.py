"""The FTP drive (``navigator/lib/drives/ftp.py``) against a real FTP server
in a thread -- pyftpdlib's, rooted in a temp directory: logging in and what
it asks, listing with MLSD and with LIST, copying both ways, erasing, and the
link box's own FTP."""

from __future__ import annotations

import time
from pathlib import PurePosixPath

import pytest

pyftpdlib = pytest.importorskip("pyftpdlib")


from navigator.lib.drives import Location, Site, drive_of  # noqa: E402
from navigator.lib.drives.sessions import SESSIONS, Answers, NeedPassword  # noqa: E402
from navigator.lib.file_ops.filecopy import OVERWRITE, PRESERVE, CopyJob, CopyRequest, run as copy_run  # noqa: E402
from navigator.lib.file_ops.fileerase import ALL, EraseJob, EraseRequest, run as erase_run  # noqa: E402

PASSWORD = "secret"


class Server:
    """``tests/ftp_server.py`` in a process: :attr:`port`, :meth:`drop` to cut
    every connection (the process killed and started again on its port), and
    :meth:`stop`."""

    def __init__(self, root, *, mlsd: bool = True) -> None:
        self.root, self.mlsd = root, mlsd
        self.port = 0
        self._start()

    def _start(self) -> None:
        import subprocess
        import sys
        from pathlib import Path

        script = Path(__file__).with_name("ftp_server.py")
        args = [sys.executable, str(script), str(self.root), str(self.port)] + ([] if self.mlsd else ["list"])
        self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.port = int(self.process.stdout.readline())

    def drop(self) -> None:
        self.stop()
        for _ in range(50):
            try:
                self._start()
                return
            except ValueError:
                time.sleep(0.05)  # the port not let go of yet

    def stop(self) -> None:
        self.process.kill()
        self.process.wait()


@pytest.fixture
def isolated(monkeypatch):
    monkeypatch.setattr("navigator.lib.drives.credentials.keyring_available", lambda: False)


def serving(tmp_path, **kwargs):
    root = tmp_path / "served"
    (root / "docs" / "sub").mkdir(parents=True)
    (root / "docs" / "a.txt").write_text("alpha")
    (root / "docs" / "sub" / "b.txt").write_text("beta")
    return Server(root, **kwargs), root


@pytest.fixture(params=[True, False], ids=["mlsd", "list"])
def server(request, tmp_path, isolated):
    served, root = serving(tmp_path, mlsd=request.param)
    yield served
    SESSIONS.close_all()
    served.stop()


def site_of(server, user="tester") -> Site:
    return Site("ftp", user, "127.0.0.1", server.port)


def connected(server):
    return SESSIONS.connect(site_of(server), Answers(password=PASSWORD))


def test_a_user_with_no_password_is_asked_and_a_wrong_one_again(server):
    site = site_of(server)
    answers = Answers()
    with pytest.raises(NeedPassword) as needed:
        SESSIONS.connect(site, answers)
    assert not needed.value.wrong
    answers.password = "wrong"
    with pytest.raises(NeedPassword) as again:
        SESSIONS.connect(site, answers)
    assert again.value.wrong
    answers.password = PASSWORD
    drive = SESSIONS.connect(site, answers)
    assert drive_of(Location(site, PurePosixPath("/"))) is drive and drive.home == PurePosixPath("/")


def test_no_user_is_anonymous(server):
    drive = SESSIONS.connect(Site("ftp", "", "127.0.0.1", server.port), Answers())
    assert sorted(drive.names(Location(drive.site, PurePosixPath("/docs")))) == ["a.txt", "sub"]


def test_a_directory_is_listed_with_mlsd_or_list(server):
    drive = connected(server)
    place = Location(drive.site, PurePosixPath("/docs"))
    entries, error, _ = drive.scan(place, True, "name", free=False)
    assert error is None
    found = {entry.name: entry for entry in entries}
    assert list(found) == ["..", "sub", "a.txt"]
    assert found["sub"].is_dir and found["a.txt"].size == 5 and found["a.txt"].mtime > 0
    assert drive.get_dir(place) == "FTP:127.0.0.1:/docs"
    assert drive.stat(Location(drive.site, PurePosixPath("/docs/a.txt"))).st_size == 5


def test_copies_go_both_ways_and_an_erase_takes_a_tree(server, tmp_path):
    drive = connected(server)
    here = tmp_path / "here"
    here.mkdir()
    remote = Location(drive.site, PurePosixPath("/docs"))
    job = CopyJob(asker=lambda question: pytest.fail(f"asked {question}"))
    assert copy_run(CopyRequest([remote], str(here), OVERWRITE, PRESERVE), job, here) == [remote]
    assert (here / "docs" / "sub" / "b.txt").read_text() == "beta"
    (here / "up.bin").write_bytes(bytes(range(256)) * 4000)
    target = Location(drive.site, PurePosixPath("/docs/sub"))
    done = copy_run(CopyRequest([here / "up.bin"], str(target) + "/", OVERWRITE, 0), CopyJob(), here)
    assert done == [here / "up.bin"]
    assert (server.root / "docs" / "sub" / "up.bin").read_bytes() == bytes(range(256)) * 4000
    done = erase_run(EraseRequest([remote]), EraseJob(asker=lambda question: ALL))
    assert done == [remote] and not (server.root / "docs").exists()


def test_mkdir_rename_and_put_back_over(server):
    from navigator.lib.drives import usefile
    from navigator.lib.system.job import Job

    class Counting(Job):
        position = total = 0

    drive = connected(server)
    at = lambda path: Location(drive.site, PurePosixPath(path))  # noqa: E731
    drive.mkdir(at("/made"))
    with pytest.raises(FileExistsError):
        drive.mkdir(at("/made"))
    drive.rename(at("/docs/a.txt"), at("/made/a.txt"))
    use = usefile.fetch([at("/made/a.txt")], Counting())
    try:
        use.copies[0].local.write_text("alpha, edited")
        usefile.upload(usefile.changed(use), Counting())
    finally:
        usefile.discard(use)
    assert (server.root / "made" / "a.txt").read_text() == "alpha, edited"
    assert sorted(path.name for path in (server.root / "made").iterdir()) == ["a.txt"]


def test_a_dropped_connection_is_made_again(server):
    drive = connected(server)
    place = Location(drive.site, PurePosixPath("/docs"))
    assert drive.names(place)
    server.drop()
    assert sorted(drive.names(place)) == ["a.txt", "sub"]


# -- the screens ---------------------------------------------------------------------------------------


def test_ftp_link_logs_in_and_the_panel_goes_there(tmp_path, isolated, monkeypatch):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.widgets.shell.commands import FtpLink

    served, root = serving(tmp_path)
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    here = tmp_path / "here"
    here.mkdir()
    app = Navigator(here, here, terminal=FakeTerminal(100, 30))
    seen = {}

    def fill(a):
        seen.update(title=a.modal.title, tls=a.modal.secure.visible)
        a.modal.host.value = f"tester@127.0.0.1:{served.port}"
        a.modal.directory.value = "/docs"

    def password(a):
        seen["asked"] = a.modal.prompt
        a.modal.entry.value = PASSWORD

    try:
        run_app(app, [
            lambda a: a.spawn(a.run_command(FtpLink)), Until(lambda a: type(a.modal).__name__ == "ConnectDialog"),
            fill, KeyEvent("enter"),
            Until(lambda a: type(a.modal).__name__ == "PasswordDialog", timeout=10), password, KeyEvent("enter"),
            Until(lambda a: [e.name for e in a.manager.left.items] == ["..", "sub", "a.txt"], timeout=10),
            lambda a: seen.update(where=a.manager.left.title_location),
        ], timeout=30)
    finally:
        SESSIONS.close_all()
        served.stop()
    assert seen["title"] == "FTP link" and seen["tls"]
    assert seen["asked"] == "FTP password for tester@127.0.0.1:"
    assert seen["where"] == "FTP:127.0.0.1:/docs"
