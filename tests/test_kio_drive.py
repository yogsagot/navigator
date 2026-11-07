"""KIO places as a drive (``navigator/lib/drives/kio.py``): the password put
into the URL kio-fuse is given, where kio-fuse shows the place, a refusal
that wants a password asked as one -- with kio-fuse and KIO stood in for."""

from __future__ import annotations

import errno
from pathlib import Path, PurePosixPath

import pytest

from navigator.lib.drives import kio as kio_drive
from navigator.lib.drives.location import Site
from navigator.lib.drives.sessions import Answers, NeedPassword
from navigator.lib.system import kio


def test_the_password_goes_after_the_user_quoted():
    site = Site("smb", "bob", "host")
    assert kio_drive.with_password("smb://bob@host/share", site, "p w/x") == "smb://bob:p%20w%2Fx@host/share"
    # One with no user in it gets the site's, and none given leaves the URL as it was.
    assert kio_drive.with_password("smb://host/share", site, "pw") == "smb://bob:pw@host/share"
    assert kio_drive.with_password("smb://bob@host/share", site, None) == "smb://bob@host/share"


def test_the_root_is_where_kio_fuse_shows_the_place_less_the_path_asked():
    local = Path("/run/user/1000/kio-fuse-x/smb/host/share/a/b")
    assert kio_drive.root_of(local, PurePosixPath("/a/b")) == (
        Path("/run/user/1000/kio-fuse-x/smb/host/share"), PurePosixPath("/"))
    # A path kio-fuse did not end the directory with: the directory stands for it.
    other = Path("/run/user/1000/kio-fuse-x/smb/host/elsewhere")
    assert kio_drive.root_of(other, PurePosixPath("/a/b")) == (other, PurePosixPath("/a/b"))
    assert kio_drive.root_of(other, PurePosixPath("/")) == (other, PurePosixPath("/"))


@pytest.fixture
def mounted(monkeypatch, tmp_path):
    """``kio.mount_url`` stood in for: what it was given, and what it does."""
    given: list[str] = []
    outcome: dict = {"raise": None, "at": tmp_path / "kio-fuse" / "smb" / "host" / "share"}

    def mount_url(uri: str) -> Path:
        given.append(uri)
        if outcome["raise"] is not None:
            raise outcome["raise"]
        outcome["at"].mkdir(parents=True, exist_ok=True)
        return outcome["at"]

    monkeypatch.setattr(kio, "mount_url", mount_url)
    return given, outcome


def test_connecting_is_kio_fuses_mount_with_the_password_in_the_url(mounted):
    given, outcome = mounted
    drive = kio_drive.connect(Site("smb", "bob", "host"), Answers(start="/share", password="secret"))
    assert given == ["smb://bob:secret@host/share"]
    assert isinstance(drive, kio_drive.KioDrive)
    assert ("Kind", "KIO") in drive.describe()
    drive.close()  # lets nothing go: kio-fuse forgets its URLs itself


def test_an_authentication_refusal_asks_for_a_password_and_says_a_wrong_one(mounted):
    given, outcome = mounted
    outcome["raise"] = OSError(errno.EACCES, "Authorization failed")
    with pytest.raises(NeedPassword) as first:
        kio_drive.connect(Site("smb", "bob", "host"), Answers(start="/share"))
    assert first.value.wrong is False
    with pytest.raises(NeedPassword) as again:
        kio_drive.connect(Site("smb", "bob", "host"), Answers(start="/share", password="nope"))
    assert again.value.wrong is True


def test_any_other_failure_is_said_as_it_is(mounted):
    given, outcome = mounted
    outcome["raise"] = OSError(errno.ENOENT, "kio-fuse is not running")
    with pytest.raises(OSError) as raised:
        kio_drive.connect(Site("smb", "bob", "host"), Answers(start="/share"))
    assert not isinstance(raised.value, NeedPassword) and raised.value.errno == errno.ENOENT


def test_available_says_why_not(monkeypatch):
    from navigator.lib.system import desktop

    monkeypatch.setattr(kio, "program", lambda which=None: None)
    assert kio_drive.available() == kio.NO_KIO
    monkeypatch.setattr(kio, "program", lambda which=None: "/usr/bin/kioclient")
    monkeypatch.setattr(desktop, "backend", lambda: None)
    assert kio_drive.available() == kio_drive.NOT_IN_USE
    monkeypatch.setattr(desktop, "backend", lambda: kio)
    assert kio_drive.available() is None
