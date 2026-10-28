"""7z and rar through an archiver's command line
(``navigator/lib/drives/arctool.py``): the listings parsed -- from 7-Zip's
and unrar's own output, so these run everywhere -- and, where 7-Zip is
installed, a 7z entered, read, written into, rewritten and tested."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import time
from pathlib import Path

import pytest

from navigator.lib.drives import Location, archive, arctool

#: ``7zz l -slt -ba`` (7-Zip 23.01) of a solid 7z: two directories, files, a link.
SLT = """\
Path = dir
Size = 0
Packed Size = 0
Modified = 2026-10-20 21:18:30.0452772
Attributes = D drwxrwxr-x
CRC =
Encrypted = -
Method =
Block =

Path = a.txt
Size = 6
Packed Size = 20
Modified = 2026-10-20 21:18:30.0452772
Attributes = A -rw-rw-r--
CRC = 9F606EEC
Encrypted = -
Method = LZMA2:12
Block = 0

Path = dir/b.txt
Size = 5
Packed Size =
Modified = 2026-10-20 21:18:30.0452772
Attributes = A -rwxr-x---
CRC = E6E3A775
Encrypted = -
Method = LZMA2:12
Block = 0

Path = link
Size = 5
Packed Size =
Modified = 2026-10-20 21:18:30.0462772
Attributes = A lrwxrwxrwx
CRC = C1EBF7BA
Encrypted = -
Method = LZMA2:12
Block = 0
"""

#: ``unrar lta``'s technical listing of the same kind of thing.
UNRAR = """\
UNRAR 6.24 freeware      Copyright (c) 1993-2023 Alexander Roshal

Archive: t.rar
Details: RAR 5

        Name: dir/b.txt
        Type: File
        Size: 5
 Packed size: 17
       Ratio: 340%
       mtime: 2026-10-20 21:18:30,045277200
  Attributes: -rwxr-x---
       CRC32: E6E3A775
     Host OS: Unix
 Compression: RAR 5.0(v50) -m3 -md=128K

        Name: dir
        Type: Directory
  Attributes: drwxrwxr-x
       mtime: 2026-10-20 21:18:30,045277200

        Name: link
        Type: Unix symbolic link
      Target: a.txt
        Size: 5
  Attributes: lrwxrwxrwx
"""


def test_7_zip_s_technical_listing_is_parsed():
    members = {member.path: member for member in arctool.parse_slt(SLT)}
    assert list(members) == ["dir", "a.txt", "dir/b.txt", "link"]
    assert members["dir"].is_dir and not members["a.txt"].is_dir
    assert (members["a.txt"].size, members["a.txt"].packed) == (6, 20)
    # A solid block's later members have no packed size of their own.
    assert members["dir/b.txt"].packed is None
    assert members["dir/b.txt"].mode == 0o750
    assert members["link"].is_link
    assert members["a.txt"].mtime == time.mktime((2026, 10, 20, 21, 18, 30, 0, 0, -1))


def test_the_archive_s_own_block_is_not_a_member():
    head = "Path = t.7z\nType = 7z\nPhysical Size = 221\n\n"
    assert [member.path for member in arctool.parse_slt(head + SLT)][0] == "dir"


def test_unrar_s_technical_listing_is_parsed():
    members = {member.path: member for member in arctool.parse_unrar(UNRAR)}
    assert list(members) == ["dir/b.txt", "dir", "link"]
    assert (members["dir/b.txt"].size, members["dir/b.txt"].packed, members["dir/b.txt"].mode) == (5, 17, 0o750)
    assert members["dir"].is_dir and members["link"].is_link


def test_7z_and_rar_are_told_by_their_first_bytes(tmp_path):
    (tmp_path / "a").write_bytes(b"7z\xbc\xaf\x27\x1c\x00\x04")
    (tmp_path / "b").write_bytes(b"Rar!\x1a\x07\x01\x00")
    (tmp_path / "c").write_bytes(b"PK\x03\x04")
    assert [arctool.kind_of(tmp_path / name) for name in "abc"] == ["7z", "rar", None]


def test_without_a_tool_a_7z_says_what_to_install(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    path = tmp_path / "x.7z"
    path.write_bytes(b"7z\xbc\xaf\x27\x1c\x00\x04" + bytes(24))
    with pytest.raises(archive.NeedsTool, match="7-Zip"):
        archive.open_archive(Location.parse(str(path)))


# -- with 7-Zip ------------------------------------------------------------------------------------

needs_7z = pytest.mark.skipif(arctool.seven_zip() is None, reason="7-Zip (7zz or 7z) is not installed")


class Job:
    stopped, position, total = False, 0, 0

    def wait_while_paused(self):
        pass


@pytest.fixture
def seven(tmp_path):
    source = tmp_path / "src"
    (source / "dir" / "sub").mkdir(parents=True)
    (source / "a.txt").write_text("alpha")
    (source / "dir" / "b.txt").write_text("beta")
    os.chmod(source / "dir" / "b.txt", 0o750)
    (source / "link").symlink_to("a.txt")
    path = tmp_path / "t.7z"
    subprocess.run([arctool.seven_zip(), "a", "-snl", str(path), "."], cwd=source, check=True,
                   capture_output=True)
    yield Location.parse(str(path))
    archive.close_all()


@needs_7z
def test_a_7z_is_listed_and_read(seven):
    drive = archive.open_archive(seven)
    assert drive.kind == "7z" and drive.sign == "7Z"
    entries, error, _ = drive.scan(drive.at("/"), True, "name", free=False)
    names = {entry.name: entry for entry in entries}
    assert error is None and list(names) == ["..", "dir", "a.txt", "link"]
    assert names["link"].is_link and names["link"].link_target == "a.txt"
    assert names["a.txt"].packed is not None
    with drive.open_read(drive.at("/dir/b.txt")) as reader:
        assert reader.read() == b"beta"
    assert stat.S_IMODE(drive.stat(drive.at("/dir/b.txt")).st_mode) == 0o750
    assert drive.test(Job()) == []


@needs_7z
def test_a_7z_is_rewritten_with_what_changed(seven):
    drive = archive.open_archive(seven)
    with drive.open_write(drive.at("/new.txt")) as writer:
        writer.write(b"new")
    drive.unlink(drive.at("/a.txt"))
    drive.rename(drive.at("/dir"), drive.at("/moved"))
    drive.finish()
    assert drive.names(drive.at("/")) == ["link", "moved", "new.txt"]
    assert drive.names(drive.at("/moved")) == ["b.txt", "sub"]
    with drive.open_read(drive.at("/moved/b.txt")) as reader:
        assert reader.read() == b"beta"
    assert stat.S_IMODE(drive.stat(drive.at("/moved/b.txt")).st_mode) == 0o750
    assert drive.readlink(drive.at("/link")) == "a.txt"


@needs_7z
def test_a_new_7z_is_made_by_naming_it(tmp_path):
    outer = Location.parse(str(tmp_path / "fresh.7z"))
    drive = archive.open_archive(outer, create=True)
    drive.mkdir(drive.at("/empty"))
    drive.finish()
    assert arctool.kind_of(tmp_path / "fresh.7z") == "7z"
    assert drive.names(drive.at("/")) == ["empty"]
    archive.close_all()


@needs_7z
def test_a_damaged_7z_is_still_opened_and_test_names_what_failed(seven):
    path = Path(str(seven))
    data = bytearray(path.read_bytes())
    for offset in (34, 36):  # the packed data, just after the 32-byte start header
        data[offset] ^= 0xFF
    path.write_bytes(bytes(data))
    drive = archive.open_archive(seven)
    failures = drive.test(Job())
    assert failures and all(why for _, why in failures)


def test_a_listing_says_which_members_are_encrypted_and_where_links_point_and_skips_services():
    rar = arctool.parse_unrar(
        "        Name: l\n        Type: Unix symbolic link\n      Target: sub/a.txt\n        Size: 9\n"
        "  Attributes: lrwxrwxrwx\n\n        Name: a.txt\n        Type: File\n        Size: 3\n"
        "       Flags: encrypted \n\n        Name: QO\n        Type: Service\n        Size: 128\n\n"
        "     Service: EOF\n")
    assert [(m.path, m.is_link, m.target, m.encrypted) for m in rar] == [
        ("l", True, "sub/a.txt", False), ("a.txt", False, None, True)]
    seven = arctool.parse_slt(
        "Path = l\nSize = 9\nAttributes =  lrwxrwxrwx\nEncrypted = -\nSymbolic Link = sub/a.txt\n\n"
        "Path = a.txt\nSize = 3\nAttributes = A -rw-r--r--\nEncrypted = +\nSymbolic Link = \n")
    assert [(m.path, m.is_link, m.target, m.encrypted) for m in seven] == [
        ("l", True, "sub/a.txt", False), ("a.txt", False, None, True)]


def test_unrar_is_preferred_for_a_rar(monkeypatch):
    monkeypatch.setattr(arctool.shutil, "which", lambda name: f"/usr/bin/{name}")
    assert arctool.tool_for("rar") == ("unrar", "/usr/bin/unrar")
    monkeypatch.setattr(arctool.shutil, "which", lambda name: None if name == "unrar" else f"/usr/bin/{name}")
    assert arctool.tool_for("rar")[0] == "7z"


def test_an_empty_rar_is_refused_rather_than_made(tmp_path, monkeypatch):
    monkeypatch.setattr(arctool, "rar_program", lambda: "/usr/bin/rar")
    (tmp_path / "tree").mkdir()
    with pytest.raises(OSError, match="cannot be empty"):
        arctool.write_rar(tmp_path / "e.rar", tmp_path / "tree")
