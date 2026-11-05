"""The read-only archive kinds -- deb, rpm, cpio, squashfs and an AppImage's
image -- and a single compressed file (``.gz``, ``.bz2``, ``.xz``, ``.zst``)
as an archive of one: ``navigator/lib/drives/{cpio,debpkg,rpmpkg,squashfs,
stream}.py`` behind :class:`navigator.lib.drives.archive.ArchiveDrive`, and
Ctrl+PgDn opening a file as an archive whatever its name."""

from __future__ import annotations

import bz2
import calendar
import errno
import gzip
import io
import lzma
import os
import shutil
import stat
import struct
import subprocess
import tarfile
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navigator.lib.drives import Location, archive, cpio, debpkg, squashfs, stream, zstd
from navigator.lib.file_ops.filecopy import OVERWRITE, PRESERVE, CopyJob, CopyRequest, run as copy_run


@pytest.fixture(autouse=True)
def no_archives_left():
    yield
    archive.close_all()


class Job:
    stopped, position, total = False, 0, 0

    def wait_while_paused(self):
        pass


# -- builders ---------------------------------------------------------------------------------------


def newc(entries) -> bytes:
    """A ``newc`` cpio of ``(name, mode, data, ino, nlink)``."""
    out = io.BytesIO()

    def pad(n):
        out.write(b"\0" * ((4 - out.tell() % 4) % 4))

    for name, mode, data, ino, nlink in [*entries, ("TRAILER!!!", 0, b"", 0, 1)]:
        raw = name.encode() + b"\0"
        fields = (ino, mode, 0, 0, nlink, 1_000_000_000, len(data), 0, 0, 0, 0, len(raw), 0)
        out.write(b"070701" + b"".join(b"%08X" % field for field in fields))
        out.write(raw)
        pad(4)
        out.write(data)
        pad(4)
    return out.getvalue()


def odc(entries) -> bytes:
    out = io.BytesIO()
    for name, mode, data, ino, nlink in [*entries, ("TRAILER!!!", 0, b"", 0, 1)]:
        raw = name.encode() + b"\0"
        out.write(b"070707" + b"%06o%06o%06o%06o%06o%06o%06o%011o%06o%011o" % (
            0, ino, mode, 0, 0, nlink, 0, 1_000_000_000, len(raw), len(data)))
        out.write(raw + data)
    return out.getvalue()


#: A tree as cpio entries: a directory, two names of one file (``newc``
#: gives the bytes to the last), and a link.
TREE = [
    ("usr", stat.S_IFDIR | 0o755, b"", 1, 2),
    ("usr/bin", stat.S_IFDIR | 0o755, b"", 2, 2),
    ("usr/bin/tool", stat.S_IFREG | 0o755, b"", 3, 2),
    ("usr/bin/also", stat.S_IFREG | 0o755, b"#!/bin/sh\n", 3, 2),
    ("usr/bin/sl", stat.S_IFLNK | 0o777, b"tool", 4, 1),
    ("dev/null", stat.S_IFCHR | 0o666, b"", 5, 1),
]


def ar(members) -> bytes:
    out = io.BytesIO()
    out.write(debpkg.MAGIC)
    for name, data in members:
        out.write(b"%-16s%-12d%-6d%-6d%-8o%-10d`\n" % (name.encode() + b"/", 1_000_000_000, 0, 0, 0o644,
                                                        len(data)))
        out.write(data)
        if len(data) % 2:
            out.write(b"\n")
    return out.getvalue()


def tar_bytes(mode, files) -> bytes:
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode=mode) as tarred:
        for name, data, kind in files:
            info = tarfile.TarInfo(name)
            info.mtime, info.uname, info.gname = 1_000_000_000, "root", "root"
            if kind == "dir":
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                tarred.addfile(info)
            elif kind == "sym":
                info.type, info.linkname = tarfile.SYMTYPE, data
                tarred.addfile(info)
            elif kind == "hard":
                info.type, info.linkname = tarfile.LNKTYPE, data
                tarred.addfile(info)
            else:
                info.size, info.mode = len(data), 0o644
                tarred.addfile(info, io.BytesIO(data))
    return out.getvalue()


def make_deb(path: Path, data_mode="w:xz") -> Path:
    control = tar_bytes("w:gz", [("./", None, "dir"), ("./control", b"Package: tool\nVersion: 1.2-3\n"
                                                                    b"Architecture: amd64\nDescription: x\n"
                                                                    b" more\n", "file"),
                                 ("./postinst", b"#!/bin/sh\n", "file")])
    data = tar_bytes(data_mode, [("./", None, "dir"), ("./usr/", None, "dir"), ("./usr/bin/", None, "dir"),
                                 ("./usr/bin/tool", b"binary", "file"),
                                 ("./usr/bin/same", "./usr/bin/tool", "hard"),
                                 ("./usr/bin/sl", "tool", "sym")])
    suffix = {"w:xz": ".xz", "w:gz": ".gz", "w": ""}[data_mode]
    path.write_bytes(ar([("debian-binary", b"2.0\n"), ("control.tar.gz", control),
                         (f"data.tar{suffix}", data)]))
    return path


def rpm_header(tags) -> bytes:
    index, store = b"", b""
    for tag, value in tags:
        index += struct.pack(">IIII", tag, 6, len(store), 1)
        store += value.encode() + b"\0"
    return b"\x8e\xad\xe8\x01\0\0\0\0" + struct.pack(">II", len(tags), len(store)) + index + store


def make_rpm(path: Path, payload=None) -> Path:
    lead = b"\xed\xab\xee\xdb" + b"\0" * 92
    signature = rpm_header([])  # 16 bytes: already a multiple of 8
    header = rpm_header([(1000, "tool"), (1001, "1.2"), (1002, "3.fc40"), (1022, "x86_64")])
    if payload is None:
        payload = gzip.compress(newc([(f"./{name}", *rest) for name, *rest in TREE]))
    path.write_bytes(lead + signature + header + payload)
    return path


def tree_on_disk(root: Path) -> Path:
    (root / "usr/bin").mkdir(parents=True)
    (root / "usr/bin/tool").write_text("#!/bin/sh\n")
    (root / "usr/bin/tool").chmod(0o755)
    (root / "usr/bin/a*b [c]").write_text("wild")
    (root / "usr/bin/sl").symlink_to("tool")
    return root


def mksquashfs(source: Path, target: Path) -> Path:
    if shutil.which("mksquashfs") is None or squashfs.program() is None:
        pytest.skip("needs squashfs-tools")
    subprocess.run(["mksquashfs", str(source), str(target), "-quiet", "-no-progress", "-all-root"],
                   check=True, capture_output=True)
    return target


def make_appimage(path: Path, image: Path) -> Path:
    """A type 2 AppImage's shape: an ELF64 header marked ``AI\\x02`` whose
    one section header ends where the image starts."""
    head = bytearray(64)
    head[:4] = b"\x7fELF"
    head[4], head[5], head[6] = 2, 1, 1
    head[8:11] = b"AI\x02"
    struct.pack_into("<Q", head, 0x28, 64)  # e_shoff
    struct.pack_into("<HH", head, 0x3A, 64, 1)  # e_shentsize, e_shnum
    path.write_bytes(bytes(head) + b"\0" * 64 + image.read_bytes())
    path.chmod(0o755)
    return path


def listing(drive) -> dict:
    return {path: member for path, member in drive._walk(drive.root)}


def read(drive, inner):
    with drive.open_read(drive.at(inner)) as reader:
        return reader.read()


# -- cpio ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("write", [newc, odc])
def test_a_cpio_lists_its_tree_and_reads_hard_links_and_links(tmp_path, write):
    path = tmp_path / "a.cpio"
    path.write_bytes(write(TREE))
    drive = archive.open_archive(Location.of(path))
    assert drive.kind == "cpio" and drive.get_dir(drive.at("/")) == "CPIO:a.cpio:/"
    found = listing(drive)
    assert "dev/null" not in found  # devices are not listed
    assert found["usr/bin/sl"].link == "tool"
    assert read(drive, "/usr/bin/also") == b"#!/bin/sh\n"
    if write is newc:  # the bytes went with the group's last name
        assert read(drive, "/usr/bin/tool") == b"#!/bin/sh\n"
    assert drive.stat(drive.at("/usr/bin/sl")).st_size == drive.stat(drive.at("/usr/bin/tool")).st_size
    assert drive.test(Job()) == []


def test_a_read_only_kind_greys_writing_and_refuses_it(tmp_path):
    path = tmp_path / "a.cpio"
    path.write_bytes(newc(TREE))
    drive = archive.open_archive(Location.of(path))
    assert not drive.can("write") and not drive.can("rename")
    for step in (lambda: drive.open_write(drive.at("/new")), lambda: drive.mkdir(drive.at("/d")),
                 lambda: drive.unlink(drive.at("/usr/bin/also")), lambda: drive.chmod(drive.at("/usr"), 0o700),
                 lambda: drive.rename(drive.at("/usr"), drive.at("/opt"))):
        with pytest.raises(OSError) as raised:
            step()
        assert raised.value.errno == errno.EROFS
    assert not drive.dirty


def test_a_cpio_gz_is_a_cpio_and_copies_out(tmp_path):
    path = tmp_path / "initrd.cpio.gz"
    path.write_bytes(gzip.compress(newc(TREE)))
    drive = archive.open_archive(Location.of(path))
    assert drive.kind == "cpio" and drive.compression == "gz"
    out = tmp_path / "out"
    out.mkdir()
    copy_run(CopyRequest([drive.at("/usr")], str(out), OVERWRITE, PRESERVE),
             CopyJob(asker=lambda question: pytest.fail(f"asked {question}")), out)
    assert (out / "usr/bin/also").read_bytes() == b"#!/bin/sh\n"
    assert os.readlink(out / "usr/bin/sl") == "tool"


def test_a_cut_cpio_is_no_archive(tmp_path):
    path = tmp_path / "cut.cpio"
    path.write_bytes(newc(TREE)[:50])
    with pytest.raises(archive.NotAnArchive):
        archive.open_archive(Location.of(path))


# -- deb and ar -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("data_mode", ["w:xz", "w:gz", "w"])
def test_a_deb_is_laid_out_as_dpkg_deb_unpacks_it(tmp_path, data_mode):
    drive = archive.open_archive(Location.of(make_deb(tmp_path / "tool_1.2-3_amd64.deb", data_mode)))
    assert drive.kind == "deb" and drive.sign == "DEB"
    found = listing(drive)
    assert {"usr/bin/tool", "usr/bin/same", "usr/bin/sl", "DEBIAN/control", "DEBIAN/postinst"} <= set(found)
    assert not any(path.startswith("debian-binary") or "data.tar" in path for path in found)
    assert read(drive, "/usr/bin/same") == b"binary"  # a hard link reads its target
    assert found["usr/bin/sl"].link == "tool"
    assert found["usr/bin/tool"].owner == "root:root"
    assert ("Package", "tool 1.2-3 (amd64)") in drive.describe()
    assert drive.test(Job()) == []
    assert not drive.can("write")


def test_a_deb_with_a_zst_data_tar_is_read(tmp_path):
    if not zstd.available():
        pytest.skip("needs zstd")
    plain, packed = tmp_path / "data.tar", tmp_path / "data.tar.zst"
    plain.write_bytes(tar_bytes("w", [("./usr/bin/tool", b"binary", "file")]))
    zstd.compress(plain, packed)
    deb = tmp_path / "z.deb"
    deb.write_bytes(ar([("debian-binary", b"2.0\n"), ("data.tar.zst", packed.read_bytes())]))
    drive = archive.open_archive(Location.of(deb))
    assert read(drive, "/usr/bin/tool") == b"binary"


def test_an_ar_that_is_no_package_lists_its_members(tmp_path):
    path = tmp_path / "libx.a"
    path.write_bytes(ar([("a.o", b"one"), ("b.o", b"two!")]))
    drive = archive.open_archive(Location.of(path))
    assert drive.kind == "ar" and sorted(listing(drive)) == ["a.o", "b.o"]
    assert read(drive, "/b.o") == b"two!"


# -- rpm ----------------------------------------------------------------------------------------------


def test_an_rpm_s_payload_is_its_files(tmp_path):
    drive = archive.open_archive(Location.of(make_rpm(tmp_path / "tool-1.2-3.fc40.x86_64.rpm")))
    assert drive.kind == "rpm"
    found = listing(drive)
    assert {"usr", "usr/bin", "usr/bin/also", "usr/bin/sl"} <= set(found)
    assert read(drive, "/usr/bin/tool") == b"#!/bin/sh\n"
    assert ("Package", "tool-1.2-3.fc40.x86_64") in drive.describe()
    assert drive.test(Job()) == []


@pytest.mark.parametrize("compress", [lzma.compress, bz2.compress, lambda data: data])
def test_an_rpm_payload_may_be_compressed_any_way(tmp_path, compress):
    drive = archive.open_archive(Location.of(make_rpm(tmp_path / "t.rpm", compress(newc(TREE)))))
    assert read(drive, "/usr/bin/also") == b"#!/bin/sh\n"


def test_an_rpm_large_file_payload_says_so_rather_than_running(tmp_path):
    with pytest.raises(archive.NeedsTool):
        archive.open_archive(Location.of(make_rpm(tmp_path / "big.rpm", gzip.compress(b"07070X" + b"0" * 200))))


# -- squashfs and AppImage ----------------------------------------------------------------------------


def test_a_squashfs_image_lists_and_reads_names_with_wildcards(tmp_path):
    image = mksquashfs(tree_on_disk(tmp_path / "tree"), tmp_path / "img.sqfs")
    drive = archive.open_archive(Location.of(image))
    assert drive.kind == "squashfs" and not drive.can("write")
    found = listing(drive)
    assert found["usr/bin/tool"].mode == 0o755 and found["usr/bin/tool"].owner == "root:root"
    assert found["usr/bin/sl"].link == "tool"
    assert read(drive, "/usr/bin/a*b [c]") == b"wild"  # a name, never a pattern
    assert read(drive, "/usr/bin/sl") == b"#!/bin/sh\n"
    assert drive.test(Job()) == []


def test_an_appimage_s_image_is_found_after_its_elf(tmp_path):
    image = mksquashfs(tree_on_disk(tmp_path / "tree"), tmp_path / "img.sqfs")
    app = make_appimage(tmp_path / "Tool-x86_64.AppImage", image)
    assert squashfs.offset_of(app) == 128
    drive = archive.open_archive(Location.of(app))
    assert read(drive, "/usr/bin/tool") == b"#!/bin/sh\n"
    assert ("Image", "AppImage, at 128") in drive.describe()


def test_an_elf_that_is_no_appimage_is_no_archive(tmp_path):
    path = tmp_path / "prog"
    path.write_bytes(b"\x7fELF" + b"\x02\x01\x01" + b"\0" * 100)
    assert squashfs.offset_of(path) is None
    with pytest.raises(archive.NotAnArchive):
        archive.open_archive(Location.of(path))


def test_squashfs_without_unsquashfs_says_what_to_install(tmp_path, monkeypatch):
    path = tmp_path / "img.sqfs"
    path.write_bytes(squashfs.MAGIC + b"\0" * 200)
    monkeypatch.setattr(squashfs, "program", lambda: None)
    with pytest.raises(archive.NeedsTool, match="squashfs-tools"):
        archive.open_archive(Location.of(path))


def test_the_lls_listing_is_parsed():
    text = ("drwxr-xr-x root/root                65 2026-11-05 18:34:19 \n"
            "-rw-r--r-- root/staff               5 2026-11-05 18:34:19 /a b -> c\n"
            "lrwxrwxrwx root/root                3 2026-11-05 18:34:19 /d/link -> ../x\n"
            "crw-r--r-- root/root          1,   3 2026-11-05 18:34:19 /dev/null\n")
    members = squashfs.parse_lls(text)
    assert [(m.path, m.size, m.owner, m.target) for m in members] == [
        ("a b -> c", 5, "root:staff", None), ("d/link", 3, "root:root", "../x")]
    assert members[0].mtime == calendar.timegm((2026, 11, 5, 18, 34, 19, 0, 0, 0))


# -- one compressed file ------------------------------------------------------------------------------

COMPRESSORS = {"gz": gzip.compress, "bz2": bz2.compress, "xz": lzma.compress}


def compressed(tmp_path, kind, data=b"line\n" * 1000, name="app.log"):
    path = tmp_path / f"{name}.{kind}"
    if kind == "zst":
        if not zstd.available():
            pytest.skip("needs zstd")
        plain = tmp_path / name
        plain.write_bytes(data)
        zstd.compress(plain, path)
        plain.unlink()
    else:
        path.write_bytes(COMPRESSORS[kind](data))
    return path


def unpack(path, kind):
    if kind == "zst":
        out = path.with_suffix(".out")
        zstd.decompress(path, out)
        return out.read_bytes()
    return {"gz": gzip.decompress, "bz2": bz2.decompress, "xz": lzma.decompress}[kind](path.read_bytes())


@pytest.mark.parametrize("kind", ["gz", "bz2", "xz", "zst"])
def test_a_single_compressed_file_is_an_archive_of_one(tmp_path, kind):
    drive = archive.open_archive(Location.of(compressed(tmp_path, kind)))
    assert drive.kind == archive.STREAM and drive.sign == kind.upper()
    assert drive.get_dir(drive.at("/")) == f"{kind.upper()}:app.log.{kind}:/"
    found = listing(drive)
    assert list(found) == ["app.log"] and found["app.log"].size == 5000
    assert read(drive, "/app.log") == b"line\n" * 1000
    assert drive.test(Job()) == []


@pytest.mark.parametrize("kind", ["gz", "bz2", "xz", "zst"])
def test_its_one_file_is_written_back_compressed_the_same_way(tmp_path, kind):
    path = compressed(tmp_path, kind)
    drive = archive.open_archive(Location.of(path))
    assert drive.can("write") and not drive.can("rename")
    with drive.open_write(drive.at("/app.log")) as writer:
        writer.write(b"edited\n")
    drive.finish()
    assert unpack(path, kind) == b"edited\n"
    assert read(drive, "/app.log") == b"edited\n" and listing(drive)["app.log"].size == 7


def test_nothing_is_added_to_or_taken_from_a_single_compressed_file(tmp_path):
    drive = archive.open_archive(Location.of(compressed(tmp_path, "gz")))
    for step in (lambda: drive.open_write(drive.at("/other")), lambda: drive.unlink(drive.at("/app.log")),
                 lambda: drive.mkdir(drive.at("/d")), lambda: drive.rename(drive.at("/app.log"), drive.at("/x"))):
        with pytest.raises(OSError) as raised:
            step()
        assert raised.value.errno == errno.EROFS


@pytest.mark.parametrize(("name", "member"), [("a.log.gz", "a.log"), ("A.SVGZ", "A"), ("x.Z", "x"),
                                              ("noext", "noext"), ("pic.svgz", "pic")])
def test_the_one_file_is_named_as_gunzip_names_it(name, member):
    assert stream.member_name(name, "gz") == member


def test_a_tar_gz_and_a_tar_zst_are_still_tars(tmp_path):
    path = tmp_path / "t.tar.gz"
    path.write_bytes(tar_bytes("w:gz", [("a", b"a", "file")]))
    assert archive.open_archive(Location.of(path)).kind == "tar"


def test_a_gz_that_is_broken_is_no_archive(tmp_path):
    path = tmp_path / "bad.gz"
    path.write_bytes(gzip.compress(b"x" * 10000)[:40])
    with pytest.raises(archive.NotAnArchive):
        archive.open_archive(Location.of(path))


# -- Enter and Ctrl+PgDn ------------------------------------------------------------------------------


@pytest.fixture
def desk(tmp_path, monkeypatch):
    from navigator.__main__ import Navigator

    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    make_deb(tmp_path / "tool.deb")
    compressed(tmp_path, "gz")
    (tmp_path / "plain.txt").write_text("not an archive")
    (tmp_path / "out").mkdir()
    return Navigator(tmp_path, tmp_path / "out", terminal=FakeTerminal(100, 30)), tmp_path


def at(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [entry.name for entry in panel.items].index(name)
    return action


def names(app):
    return [entry.name for entry in app.manager.left.items]


def test_enter_goes_into_a_deb_and_a_gz(desk):
    app, _ = desk
    seen = {}
    run_app(app, [
        at("tool.deb"), KeyEvent("enter"), Until(lambda a: "DEBIAN" in names(a), timeout=5),
        KeyEvent("ctrl+pageup"), Until(lambda a: a.manager.left.location.is_local),
        at("app.log.gz"), KeyEvent("enter"), Until(lambda a: names(a) == ["..", "app.log"], timeout=5),
        lambda a: seen.update(title=a.manager.left.title_location),
    ])
    assert seen["title"] == "GZ:app.log.gz:/"


def test_enter_runs_an_appimage_and_ctrl_pgdn_opens_it(desk, monkeypatch):
    app, here = desk
    tree = tree_on_disk(here / "tree")
    image = mksquashfs(tree, here / "img.sqfs")
    make_appimage(here / "Tool.AppImage", image)
    ran = []

    async def on_execute_file(self, event):
        ran.append(event)
        return True

    monkeypatch.setattr("navigator.widgets.shell.shell.Shell.on_execute_file", on_execute_file)
    run_app(app, [
        KeyEvent("ctrl+r"), Until(lambda a: "Tool.AppImage" in names(a)),
        at("Tool.AppImage"), KeyEvent("enter"), Until(lambda a: ran, timeout=5),
        at("Tool.AppImage"), KeyEvent("ctrl+pagedown"), Until(lambda a: "usr" in names(a), timeout=5),
    ])
    assert len(ran) == 1


def test_ctrl_pgdn_on_a_directory_goes_in_and_on_a_plain_file_says_so(desk):
    from navml.widgets.dialog.dialog import Dialog

    app, here = desk
    seen = {}
    run_app(app, [
        at("out"), KeyEvent("ctrl+pagedown"), Until(lambda a: a.manager.left.location == Location.of(here / "out")),
        KeyEvent("ctrl+pageup"), Until(lambda a: "plain.txt" in names(a)),
        at("plain.txt"), KeyEvent("ctrl+pagedown"),
        Until(lambda a: isinstance(a.modal, Dialog), timeout=5),
        lambda a: seen.update(prompt=str(a.modal.prompt)),
        KeyEvent("enter"),
    ])
    assert "plain.txt is not an archive" in seen["prompt"]
    assert app.manager.left.location == Location.of(here)
