"""The SMB drive (``navigator/lib/drives/smb.py``) through a stand-in for
``smbclient``: the same functions over a local directory, its shares its
subdirectories -- no SMB server is written in Python to test against.  What
is tested is the drive: UNC names, the share as the first name, the root
listing the shares known, logging in and what it asks, copying and erasing
through the one copier, and the link box's own SMB."""

from __future__ import annotations

import os
import types
from pathlib import Path, PurePosixPath

import pytest

from navigator.lib.drives import Location, Site, drive_of
from navigator.lib.drives import smb
from navigator.lib.drives.sessions import SESSIONS, Answers, NeedPassword
from navigator.lib.file_ops.filecopy import OVERWRITE, PRESERVE, CopyJob, CopyRequest, run as copy_run
from navigator.lib.file_ops.fileerase import ALL, EraseJob, EraseRequest, run as erase_run

PASSWORD = "secret"


class LogonFailure(Exception):
    """As ``smbprotocol.exceptions.LogonFailure`` is named."""


def fake_client(root: Path) -> types.ModuleType:
    """``smbclient``'s functions over *root*: ``\\\\host\\share\\x`` is ``root/share/x``."""
    calls: list[tuple[str, str]] = []

    def local(unc: str) -> str:
        assert unc.startswith("\\\\"), unc
        _host, _, rest = unc[2:].partition("\\")
        return str(root / rest.replace("\\", "/"))

    def checked(kwargs):
        if kwargs.get("password") != PASSWORD:
            raise LogonFailure("STATUS_LOGON_FAILURE")

    def register_session(server, username=None, password=None, port=445, connection_timeout=60,
                         connection_cache=None, **kwargs):
        calls.append(("register", server))
        checked({"password": password})

    def wrap(name, function):
        def call(path, *args, **kwargs):
            checked(kwargs)
            calls.append((name, path))
            extra = {key: kwargs[key] for key in ("ns", "follow_symlinks", "mode") if key in kwargs}
            mapped = [local(arg) if isinstance(arg, str) and arg.startswith("\\\\") else arg for arg in args]
            return function(local(path), *mapped, **extra)
        return call

    module = types.ModuleType("smbclient")
    module.calls = calls
    module.register_session = register_session
    module.reset_connection_cache = lambda **kwargs: calls.append(("reset", ""))
    module.scandir = wrap("scandir", lambda path: list(os.scandir(path)))
    module.stat = wrap("stat", os.stat)
    module.lstat = wrap("lstat", os.lstat)
    module.open_file = wrap("open_file", lambda path, mode="rb": open(path, mode))
    module.mkdir = wrap("mkdir", os.mkdir)
    module.rmdir = wrap("rmdir", os.rmdir)
    module.remove = wrap("remove", os.remove)
    module.rename = wrap("rename", os.rename)
    module.replace = wrap("replace", os.replace)
    module.readlink = wrap("readlink", os.readlink)
    module.utime = wrap("utime", os.utime)
    return module


@pytest.fixture
def server(tmp_path, monkeypatch):
    root = tmp_path / "server"
    (root / "public" / "docs" / "sub").mkdir(parents=True)
    (root / "public" / "docs" / "a.txt").write_text("alpha")
    (root / "public" / "docs" / "sub" / "b.txt").write_text("beta")
    (root / "private").mkdir()
    client = fake_client(root)
    monkeypatch.setattr(smb, "CLIENT", client)
    monkeypatch.setattr("navigator.lib.drives.credentials.keyring_available", lambda: False)
    client.root = root
    yield client
    SESSIONS.close_all()


SITE = Site("smb", "alice", "nas", 0)


def at(path: str) -> Location:
    return Location(SITE, PurePosixPath(path))


def connected():
    return SESSIONS.connect(SITE, Answers(password=PASSWORD, start="/public/docs"))


def test_a_password_is_asked_for_and_a_wrong_one_again(server):
    answers = Answers(start="/public")
    with pytest.raises(NeedPassword) as needed:
        SESSIONS.connect(SITE, answers)
    assert not needed.value.wrong and needed.value.user == "alice"
    answers.password = "wrong"
    with pytest.raises(NeedPassword) as again:
        SESSIONS.connect(SITE, answers)
    assert again.value.wrong
    answers.password = PASSWORD
    drive = SESSIONS.connect(SITE, answers)
    assert drive_of(at("/public")) is drive and drive.home == PurePosixPath("/public")


def test_names_go_as_unc_and_the_root_lists_the_shares_known(server):
    drive = connected()
    entries, error, _ = drive.scan(at("/public/docs"), True, "name", free=False)
    assert error is None and [e.name for e in entries] == ["..", "sub", "a.txt"]
    assert ("scandir", "\\\\nas\\public\\docs") in server.calls
    assert [e.name for e in drive.scan(at("/"), True, "name", free=False)[0]] == ["public"]
    drive.scan(at("/private"), True, "name", free=False)  # a share reached by its name
    assert [e.name for e in drive.scan(at("/"), True, "name", free=False)[0]] == ["private", "public"]
    assert drive.get_dir(at("/public/docs")) == "SMB:nas:/public/docs"


def test_the_root_lists_the_disk_shares_the_server_names_and_those_known(server, monkeypatch):
    from test_dcerpc import SHARES, Pipe, bind_ack, response_stub, responses

    plain = server.open_file
    asked = []

    def open_file(path, mode="rb", file_type="file", **kwargs):
        if file_type == "pipe":
            asked.append((path, mode, kwargs.get("password")))
            return Pipe([bind_ack(), *responses(response_stub(SHARES), 2)])
        return plain(path, mode=mode, **kwargs)

    monkeypatch.setattr(server, "open_file", open_file)
    drive = connected()
    drive.scan(at("/private"), True, "name", free=False)  # reached by its name, listed or not
    names = [e.name for e in drive.scan(at("/"), True, "name", free=False)[0]]
    # Disk shares only: no IPC$, no administrative C$, no printer.
    assert names == ["media", "private", "public"]
    assert asked == [("\\\\nas\\IPC$\\srvsvc", "r+b", PASSWORD)]
    drive.scan(at("/"), True, "name", free=False)
    assert len(asked) == 1  # asked once a connection


def test_a_server_that_will_not_list_its_shares_leaves_those_known(server, monkeypatch):
    plain = server.open_file

    def open_file(path, mode="rb", file_type="file", **kwargs):
        if file_type == "pipe":
            raise PermissionError(13, "STATUS_ACCESS_DENIED")
        return plain(path, mode=mode, **kwargs)

    monkeypatch.setattr(server, "open_file", open_file)
    drive = connected()
    assert [e.name for e in drive.scan(at("/"), True, "name", free=False)[0]] == ["public"]


def test_copies_go_both_ways_and_an_erase_takes_a_tree(server, tmp_path):
    drive = connected()
    here = tmp_path / "here"
    here.mkdir()
    job = CopyJob(asker=lambda question: pytest.fail(f"asked {question}"))
    assert copy_run(CopyRequest([at("/public/docs")], str(here), OVERWRITE, PRESERVE), job, here) == [
        at("/public/docs")]
    assert (here / "docs" / "sub" / "b.txt").read_text() == "beta"
    (here / "up.txt").write_text("up")
    assert copy_run(CopyRequest([here / "up.txt"], str(at("/private")) + "/", OVERWRITE, 0), job,
                    here) == [here / "up.txt"]
    assert (server.root / "private" / "up.txt").read_text() == "up"
    assert erase_run(EraseRequest([at("/public/docs")]), EraseJob(asker=lambda q: ALL)) == [at("/public/docs")]
    assert not (server.root / "public" / "docs").exists()


def test_without_smbprotocol_the_drive_says_what_to_install(monkeypatch):
    from navigator.lib.drives import sessions

    monkeypatch.setattr(smb, "CLIENT", None)
    monkeypatch.setattr("importlib.util.find_spec", lambda name, *a: None)
    assert "navigator-fm[smb]" in smb.available()
    assert "navigator-fm[smb]" in sessions.available("smb")


def test_smb_link_asks_for_the_share_and_the_panel_goes_there(server, tmp_path, monkeypatch):
    from conftest import FakeTerminal, Until, run_app
    from navkit.events import KeyEvent
    from navigator.__main__ import Navigator
    from navigator.widgets.shell.commands import SmbLink

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    here = tmp_path / "here"
    here.mkdir()
    app = Navigator(here, here, terminal=FakeTerminal(100, 30))
    seen = {}

    def fill(a):
        seen.update(title=a.modal.title, share=a.modal.directory.label_text)
        a.modal.host.value = "alice@nas"
        a.modal.directory.value = "public/docs"

    def password(a):
        seen["asked"] = a.modal.prompt
        a.modal.entry.value = PASSWORD

    run_app(app, [
        lambda a: a.spawn(a.run_command(SmbLink)), Until(lambda a: type(a.modal).__name__ == "ConnectDialog"),
        fill, KeyEvent("enter"),
        Until(lambda a: type(a.modal).__name__ == "PasswordDialog", timeout=5), password, KeyEvent("enter"),
        Until(lambda a: [e.name for e in a.manager.left.items] == ["..", "sub", "a.txt"], timeout=5),
        lambda a: seen.update(where=a.manager.left.title_location),
    ])
    assert seen["title"] == "SMB link (Windows share)" and seen["share"] == "~S~hare/dir"
    assert seen["asked"] == "SMB (Windows share) password for alice@nas:"
    assert seen["where"] == "SMB:nas:/public/docs"
