"""The SFTP drive (``navigator/lib/drives/sftp.py``) against a real SFTP
server in a thread (``tests/sftp_server.py``): connecting and what it asks,
listing, copying both ways, saving over a file, and a dropped connection."""

from __future__ import annotations

import time
from pathlib import PurePosixPath

import pytest

paramiko = pytest.importorskip("paramiko")

from navigator.lib.drives import DriveGone, Location, Site, drive_of  # noqa: E402
from navigator.lib.drives.sessions import (  # noqa: E402
    SESSIONS, Answers, NeedPassword, UnknownHostKey,
)
from navigator.lib.file_ops.filecopy import OVERWRITE, PRESERVE, CopyJob, CopyRequest, run as copy_run  # noqa: E402

from sftp_server import PASSWORD, SftpServer  # noqa: E402


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """No ~/.ssh, no agent and no keyring of the user's own in the way."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("SSH_AUTH_SOCK", raising=False)
    monkeypatch.setattr("navigator.lib.drives.credentials.keyring_available", lambda: False)
    return home


@pytest.fixture
def server(tmp_path, isolated):
    root = tmp_path / "served"
    (root / "docs" / "sub").mkdir(parents=True)
    (root / "docs" / "a.txt").write_text("alpha")
    (root / "docs" / "sub" / "b.txt").write_text("beta")
    (root / "docs" / "link").symlink_to("a.txt")
    served = SftpServer(root)
    yield served
    SESSIONS.close_all()
    served.stop()


def site_of(server) -> Site:
    return Site("sftp", "tester", "127.0.0.1", server.port)


def connected(server):
    return SESSIONS.connect(site_of(server), Answers(password=PASSWORD, host_key="once"))


def test_an_unknown_host_key_is_asked_about_then_the_password(server):
    site = site_of(server)
    answers = Answers()
    with pytest.raises(UnknownHostKey) as unknown:
        SESSIONS.connect(site, answers)
    assert unknown.value.fingerprint.startswith("SHA256:")
    answers.host_key = "once"
    with pytest.raises(NeedPassword) as needed:
        SESSIONS.connect(site, answers)
    assert needed.value.user == "tester" and not needed.value.wrong
    answers.password = "wrong"
    with pytest.raises(NeedPassword) as again:
        SESSIONS.connect(site, answers)
    assert again.value.wrong
    answers.password = PASSWORD
    drive = SESSIONS.connect(site, answers)
    assert drive_of(Location(site, PurePosixPath("/"))) is drive
    assert drive.home == PurePosixPath("/")


def test_accept_and_save_writes_known_hosts_the_way_ssh_does(server, isolated):
    SESSIONS.connect(site_of(server), Answers(password=PASSWORD, host_key="save"))
    line = (isolated / ".ssh" / "known_hosts").read_text()
    assert line.startswith(f"[127.0.0.1]:{server.port} ssh-rsa ")
    SESSIONS.close_all()
    # Known now: nothing to ask the second time.
    SESSIONS.connect(site_of(server), Answers(password=PASSWORD))


def test_a_directory_is_listed_with_links_followed(server):
    drive = connected(server)
    place = Location(drive.site, PurePosixPath("/docs"))
    entries, error, free = drive.scan(place, True, "name", free=True)
    assert error is None and free is None
    names = {entry.name: entry for entry in entries}
    assert list(names) == ["..", "sub", "a.txt", "link"]
    assert names["link"].is_link and names["link"].link_target == "a.txt" and names["link"].size == 5
    assert names["sub"].is_dir
    assert drive.get_dir(place) == "SFTP:127.0.0.1:/docs"


def test_copies_go_both_ways(server, tmp_path):
    drive = connected(server)
    here = tmp_path / "here"
    here.mkdir()
    remote = Location(drive.site, PurePosixPath("/docs"))
    job = CopyJob(asker=lambda question: pytest.fail(f"asked {question}"))
    done = copy_run(CopyRequest([remote], str(here), OVERWRITE, PRESERVE), job, here)
    assert done == [remote]
    assert (here / "docs" / "sub" / "b.txt").read_text() == "beta"
    assert (here / "docs" / "link").is_symlink()
    (here / "up.bin").write_bytes(bytes(range(256)) * 5000)
    target = Location(drive.site, PurePosixPath("/docs/sub"))
    done = copy_run(CopyRequest([here / "up.bin"], str(target) + "/", OVERWRITE, PRESERVE), CopyJob(), here)
    assert done == [here / "up.bin"]
    assert (server.root / "docs" / "sub" / "up.bin").read_bytes() == bytes(range(256)) * 5000
    assert int((server.root / "docs" / "sub" / "up.bin").stat().st_mtime) == int((here / "up.bin").stat().st_mtime)


def test_a_file_put_back_replaces_the_original_in_one_step(server):
    from navigator.lib.drives import usefile
    from navigator.lib.system.job import Job

    class Counting(Job):
        position = total = 0

    drive = connected(server)
    origin = Location(drive.site, PurePosixPath("/docs/a.txt"))
    use = usefile.fetch([origin], Counting())
    try:
        use.copies[0].local.write_text("alpha, edited")
        usefile.upload(usefile.changed(use), Counting())
    finally:
        usefile.discard(use)
    assert (server.root / "docs" / "a.txt").read_text() == "alpha, edited"
    assert sorted(path.name for path in (server.root / "docs").iterdir()) == ["a.txt", "link", "sub"]


def test_a_dropped_connection_is_made_again_once(server):
    drive = connected(server)
    place = Location(drive.site, PurePosixPath("/docs"))
    assert drive.names(place)
    server.drop()
    for _ in range(50):
        if not drive.connection.alive:
            break
        time.sleep(0.02)
    assert sorted(drive.names(place)) == ["a.txt", "link", "sub"]
    assert server.connections == 2


def test_a_server_that_went_away_closes_the_drive(server):
    heard = []
    SESSIONS.add_listener(lambda site, why: heard.append(why))
    try:
        drive = connected(server)
        place = Location(drive.site, PurePosixPath("/docs"))
        server.stop()
        for _ in range(50):
            if not drive.connection.alive:
                break
            time.sleep(0.02)
        with pytest.raises(DriveGone):
            drive.names(place)
        for _ in range(50):
            if heard:
                break
            time.sleep(0.02)
    finally:
        SESSIONS._listeners.clear()
    assert heard == ["lost"]
    with pytest.raises(DriveGone):
        drive_of(place)


def test_without_paramiko_the_drive_says_what_to_install(monkeypatch):
    from navigator.lib.drives import sessions, sftp

    monkeypatch.setattr("importlib.util.find_spec", lambda name, *a: None)
    assert "navigator-fm[sftp]" in sftp.available()
    assert "navigator-fm[sftp]" in sessions.available("sftp")


# -- the screens: Navigator Link, its questions, and a server that goes away ------------------------


@pytest.fixture
def app_on(tmp_path, monkeypatch):
    from conftest import FakeTerminal
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    here = tmp_path / "here"
    here.mkdir()
    return Navigator(here, here, terminal=FakeTerminal(100, 30)), here


def modal_is(name):
    return lambda a: type(a.modal).__name__ == name


def test_navigator_link_asks_the_key_then_the_password_and_the_panel_goes_there(server, app_on):
    from conftest import Until, run_app
    from navkit.events import KeyEvent

    app, here = app_on
    seen = {}

    def fill(a):
        seen["dialog"] = a.modal.title
        a.modal.host.value = f"tester@127.0.0.1:{server.port}"
        a.modal.directory.value = "/docs"

    def password(a):
        seen["masked"] = a.modal.entry.entry.password
        seen["asked"] = a.modal.prompt
        a.modal.entry.value = PASSWORD

    run_app(app, [
        KeyEvent("f11", alt=True), Until(modal_is("ConnectDialog")), fill, KeyEvent("enter"),
        Until(modal_is("HostKeyQuery"), timeout=10),
        lambda a: seen.update(key=a.modal.prompt), KeyEvent("enter"),
        Until(modal_is("PasswordDialog"), timeout=10), password, KeyEvent("enter"),
        Until(lambda a: [e.name for e in a.manager.left.items] == ["..", "sub", "a.txt", "link"], timeout=10),
        lambda a: seen.update(title=a.manager.left.title_location, prompt=a.shell.command_prompt),
        lambda a: server.stop(),
        Until(lambda a: a.manager.left.location.is_local, timeout=15),
        Until(modal_is("Dialog"), timeout=5),
        lambda a: seen.update(lost=a.modal.prompt, back=a.manager.left.path),
        KeyEvent("enter"),
    ], timeout=60)
    assert "SHA256:" in seen["key"] and seen["masked"]
    assert seen["title"] == "SFTP:127.0.0.1:/docs" and seen["prompt"] == "SFTP:127.0.0.1:/docs$"
    assert seen["dialog"] == "SSH link (SFTP)" and seen["asked"] == f"SFTP (SSH) password for tester@127.0.0.1:"
    assert seen["lost"] == "Remote drive SFTP:127.0.0.1 is not accessible"
    assert seen["back"] == here
    from navigator.lib.drives.recent import Recent, recent

    assert recent("sftp") == [Recent("sftp", "127.0.0.1", "tester", server.port, "/docs")]


# -- keyboard-interactive and ProxyJump ----------------------------------------------------------------


def test_a_server_that_asks_its_own_questions_has_them_answered(tmp_path, isolated):
    from sftp_server import CODE, CODE_PROMPT

    root = tmp_path / "served"
    root.mkdir()
    (root / "x.txt").write_text("x")
    served = SftpServer(root, interactive=True)
    asked = []

    def answer(title, instructions, prompts):
        asked.append((title, instructions, prompts))
        return [CODE]

    try:
        site = Site("sftp", "tester", "127.0.0.1", served.port)
        with pytest.raises(NeedPassword):  # nobody to answer: a password is all it can ask
            SESSIONS.connect(site, Answers(host_key="once"))
        drive = SESSIONS.connect(site, Answers(host_key="once", interactive=answer))
        assert drive.names(Location(site, PurePosixPath("/"))) == ["x.txt"]
        assert asked == [("Two-factor", "Look at your phone", [(CODE_PROMPT, False)])]
        SESSIONS.close_all()
        with pytest.raises(DriveGone):  # cancelled: no password box after
            SESSIONS.connect(site, Answers(host_key="once", interactive=lambda *a: None))
    finally:
        SESSIONS.close_all()
        served.stop()


def test_proxyjump_goes_through_the_systems_ssh(isolated):
    from navigator.lib.drives.credentials import host_config

    ssh = isolated / ".ssh"
    ssh.mkdir()
    (ssh / "config").write_text("Host inner\n  HostName 10.0.0.5\n  Port 2200\n  ProxyJump bastion,other\n")
    config = host_config(Site("sftp", "", "inner", 0))
    assert (config.hostname, config.port) == ("10.0.0.5", 2200)
    assert config.proxy_command == "ssh -W 10.0.0.5:2200 bastion"
