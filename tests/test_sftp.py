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
        KeyEvent("f11", alt=True), Until(modal_is("LinkManagerDialog")), fill, KeyEvent("enter"),
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
    # And why, as the reconnect found it: the server is gone.
    assert seen["lost"].startswith("Remote drive SFTP:127.0.0.1 is not accessible: Cannot connect to 127.0.0.1")
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


def test_proxyjump_names_every_host_on_the_way(isolated):
    from navigator.lib.drives.credentials import host_config

    ssh = isolated / ".ssh"
    ssh.mkdir()
    (ssh / "config").write_text("Host inner\n  HostName 10.0.0.5\n  Port 2200\n"
                                "  ProxyJump bastion,ops@other:2022,ssh://[fe80::1]:23\n")
    config = host_config(Site("sftp", "", "inner", 0))
    assert (config.hostname, config.port) == ("10.0.0.5", 2200)
    assert config.proxy_command is None
    assert config.jumps == [Site("sftp", "", "bastion", 0), Site("sftp", "ops", "other", 2022),
                            Site("sftp", "", "fe80::1", 23)]


def test_proxyjump_goes_through_two_hosts_and_each_asks_its_own(tmp_path, isolated):
    root = tmp_path / "served"
    root.mkdir()
    (root / "x.txt").write_text("x")
    first, second = (SftpServer(tmp_path, forwarding=True) for _ in range(2))
    target = SftpServer(root)
    ssh = isolated / ".ssh"
    ssh.mkdir()
    (ssh / "config").write_text(
        f"Host inner\n  HostName 127.0.0.1\n  Port {target.port}\n"
        f"  ProxyJump tester@127.0.0.1:{first.port},tester@127.0.0.1:{second.port}\n")
    site = Site("sftp", "tester", "inner", 0)
    answers = Answers()
    asked = []
    try:
        for _ in range(10):
            try:
                drive = SESSIONS.connect(site, answers)
                break
            except UnknownHostKey as unknown:
                asked.append(("key", unknown.hop))
                answers.for_hop(unknown.hop).host_key = "once"
            except NeedPassword as needed:
                asked.append(("password", needed.hop))
                answers.for_hop(needed.hop).password = PASSWORD
        assert drive.names(Location(site, PurePosixPath("/"))) == ["x.txt"]
        hops = [("127.0.0.1", first.port), ("127.0.0.1", second.port)]
        assert asked == [("key", hops[0]), ("password", hops[0]), ("key", hops[1]),
                         ("password", hops[1]), ("key", None), ("password", None)]
        connection = drive.connection
        assert len(connection.chain) == 2
        transports = [client.get_transport() for client in connection.chain]
        SESSIONS.close_all()
        # The jump hosts' connections go with the server's.
        assert connection.chain == [] and not any(each.is_active() for each in transports)
    finally:
        SESSIONS.close_all()
        for each in (first, second, target):
            each.stop()


# -- port forwards ------------------------------------------------------------------------------


def _echo_server():
    """A TCP server on the loopback that sends back what it is sent."""
    import socket
    import threading

    listener = socket.create_server(("127.0.0.1", 0))

    def serve():
        while True:
            try:
                sock, _ = listener.accept()
            except OSError:
                return

            def echo(sock=sock):
                with sock:
                    while data := sock.recv(4096):
                        sock.sendall(data)

            threading.Thread(target=echo, daemon=True).start()

    threading.Thread(target=serve, daemon=True).start()
    return listener, listener.getsockname()[1]


def _round_trip(sock, data=b"hello through the tunnel"):
    sock.sendall(data)
    got = b""
    while len(got) < len(data):
        part = sock.recv(4096)
        assert part, "the tunnel closed"
        got += part
    return got


@pytest.fixture
def forwarding(tmp_path, isolated):
    served = SftpServer(tmp_path, forwarding=True)
    echo, echo_port = _echo_server()
    yield served, echo_port
    SESSIONS.close_all()
    served.stop()
    echo.close()


def _connect_with(server, *forwards):
    return SESSIONS.connect(site_of(server), Answers(password=PASSWORD, host_key="once", forwards=list(forwards)))


def test_a_local_forward_carries_a_connection_to_where_the_server_sees(forwarding):
    import socket

    from navigator.lib.drives.forwards import Forward

    server, echo_port = forwarding
    drive = _connect_with(server, Forward("L", 0, "", "127.0.0.1", echo_port))
    [opened] = drive.connection.tunnels.opened
    assert opened.error == "" and opened.port
    with socket.create_connection(("127.0.0.1", opened.port), timeout=5) as sock:
        assert _round_trip(sock) == b"hello through the tunnel"
    assert ("Forward", f"L 127.0.0.1:{opened.port} → 127.0.0.1:{echo_port}") in drive.describe()


def test_a_dynamic_forward_is_a_socks5_proxy(forwarding):
    import socket
    import struct

    from navigator.lib.drives.forwards import Forward

    server, echo_port = forwarding
    drive = _connect_with(server, Forward("D", 0))
    [opened] = drive.connection.tunnels.opened
    with socket.create_connection(("127.0.0.1", opened.port), timeout=5) as sock:
        sock.sendall(b"\x05\x01\x00")
        assert sock.recv(2) == b"\x05\x00"
        name = b"127.0.0.1"
        sock.sendall(b"\x05\x01\x00\x03" + bytes([len(name)]) + name + struct.pack("!H", echo_port))
        reply = b""
        while len(reply) < 10:
            reply += sock.recv(10 - len(reply))
        assert reply[:2] == b"\x05\x00"
        assert _round_trip(sock) == b"hello through the tunnel"


def test_a_remote_forward_carries_the_server_s_port_back_here(forwarding):
    import socket

    from navigator.lib.drives.forwards import Forward

    server, echo_port = forwarding
    drive = _connect_with(server, Forward("R", 0, "", "127.0.0.1", echo_port))
    [opened] = drive.connection.tunnels.opened
    assert opened.error == "" and opened.port
    # The test server listens on the loopback for its "remote" end.
    with socket.create_connection(("127.0.0.1", opened.port), timeout=5) as sock:
        assert _round_trip(sock) == b"hello through the tunnel"


def test_a_port_already_taken_is_said_and_the_connection_still_works(forwarding):
    import socket

    from navigator.lib.drives.forwards import Forward

    server, echo_port = forwarding
    with socket.create_server(("127.0.0.1", 0)) as taken:
        port = taken.getsockname()[1]
        drive = _connect_with(server, Forward("L", port, "", "127.0.0.1", echo_port))
        [opened] = drive.connection.tunnels.opened
        assert opened.error
        assert any(name == "Forward" and value.endswith(opened.error) for name, value in drive.describe())
        assert drive.names(Location(drive.site, PurePosixPath("/"))) is not None


def test_forwards_open_again_after_the_silent_reconnect_and_close_with_the_drive(forwarding):
    import socket

    from navigator.lib.drives.forwards import Forward

    server, echo_port = forwarding
    drive = _connect_with(server, Forward("L", 0, "", "127.0.0.1", echo_port))
    first = drive.connection.tunnels
    server.drop()
    for _ in range(100):
        if drive.connection.tunnels is not first and drive.connection.tunnels is not None:
            break
        time.sleep(0.02)
    again = drive.connection.tunnels
    assert again is not first
    [opened] = again.opened
    with socket.create_connection(("127.0.0.1", opened.port), timeout=5) as sock:
        assert _round_trip(sock) == b"hello through the tunnel"
    SESSIONS.close(drive.site)
    assert drive.connection.tunnels is None
    time.sleep(0.1)
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", opened.port), timeout=1).close()


def test_a_profile_s_forwards_are_found_by_its_place(server):
    from navigator.lib.drives import profiles
    from navigator.lib.drives.forwards import Forward

    site = site_of(server)
    profiles.save("other", "sftp", "elsewhere", "tester", server.port, forwards="L 1:a:2")
    profiles.save("here", "sftp", site.host, site.user, site.port, forwards="D 1080\nnot a forward")
    assert profiles.forwards_for(site) == [Forward("D", 1080)]
    assert profiles.forwards_for(Site("sftp", "", "nowhere", 0)) == []
    profiles.replace("here", "here", "sftp", site.host, site.user, site.port)
    assert profiles.forwards_for(site) == [Forward("D", 1080)]


# -- the channel pool: no thread waits for good ------------------------------------------------------


def waiting_for_a_channel(connection):
    """``connection.take()`` on a thread, every channel held; its answer in the dict."""
    import threading

    out: dict = {}

    def run():
        try:
            out["channel"] = connection.take()
        except BaseException as error:  # noqa: BLE001 - the test looks at it
            out["error"] = error

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(0.2)
    assert thread.is_alive()  # waiting
    return thread, out


def test_a_thread_waiting_for_a_channel_gets_one_after_the_connection_is_made_again(server, monkeypatch):
    from navigator.lib.drives import sftp

    monkeypatch.setattr(sftp, "CHANNELS", 1)
    connection = connected(server).connection
    connection._pool.limit = 1
    held = connection.take()
    thread, out = waiting_for_a_channel(connection)
    connection.close(meant=False)  # the silent reconnect, as ``take`` makes it
    connection.open()
    thread.join(5)
    assert not thread.is_alive()
    assert "error" not in out, repr(out.get("error"))
    assert out["channel"].get_channel().get_transport() is connection.transport
    connection.give(held)  # the old transport's: thrown away, not counted
    connection.give(out["channel"])


def test_closing_the_drive_ends_a_thread_waiting_for_a_channel(server):
    connection = connected(server).connection
    connection._pool.limit = 1
    held = connection.take()
    thread, out = waiting_for_a_channel(connection)
    connection.close()
    thread.join(5)
    assert not thread.is_alive() and isinstance(out["error"], DriveGone)
    connection.give(held)


def test_a_keyring_that_will_not_keep_the_password_is_said_and_the_link_stays(server, app_on, monkeypatch):
    import sys
    import types

    from conftest import Until, run_app
    from navkit.events import KeyEvent
    from navml.widgets.toast import Toast

    # A keyring that is there but refuses (locked, its D-Bus gone).
    fake = types.ModuleType("keyring")
    fake.get_password = lambda service, account: None

    def refuse(service, account, password):
        raise RuntimeError("the collection is locked")

    fake.set_password = refuse
    monkeypatch.setitem(sys.modules, "keyring", fake)
    monkeypatch.setattr("navigator.lib.drives.credentials.keyring_available", lambda: True)
    app, here = app_on
    seen = {}

    def fill(a):
        a.modal.host.value = f"tester@127.0.0.1:{server.port}"
        a.modal.directory.value = "/docs"

    def password(a):
        a.modal.entry.value = PASSWORD
        a.modal.keep.value = 1  # *Save in keyring*

    def toasts(a):
        return [child.text for child in a.root.children if isinstance(child, Toast)]

    run_app(app, [
        KeyEvent("f11", alt=True), Until(modal_is("LinkManagerDialog")), fill, KeyEvent("enter"),
        Until(modal_is("HostKeyQuery"), timeout=10), KeyEvent("enter"),
        Until(modal_is("PasswordDialog"), timeout=10), password, KeyEvent("enter"),
        Until(lambda a: "a.txt" in [e.name for e in a.manager.left.items], timeout=10),
        Until(lambda a: toasts(a), timeout=5),
        lambda a: seen.update(toasts=toasts(a)),
    ], timeout=60)
    assert seen["toasts"] == ["The password was not saved in the keyring: the collection is locked"]


def test_save_password_says_why_it_did_not(monkeypatch):
    from navigator.lib.drives import credentials

    monkeypatch.setattr(credentials, "keyring_available", lambda: False)
    assert credentials.save_password(Site("sftp", host="h"), "x") == "no keyring is installed"
